from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

import requests
import sqlite_vec
from axiom.persistence.db import get_connection


class MemoryGatewayError(RuntimeError):
    pass


class MemoryGatewayDisabledError(RuntimeError):
    pass


class MemoryBatchLimitError(RuntimeError):
    pass


class MemoryGatewayNotApprovedError(RuntimeError):
    pass


class MemoryEmbeddingProviderError(RuntimeError):
    pass


class MemoryEmbeddingProviderConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class MemoryGatewayHealth:
    healthy: bool
    vec_table_present: bool
    memory_table_present: bool
    content_model_index_present: bool
    embedding_dim: int | None
    max_vector_batch: int
    reason: str


@dataclass(frozen=True)
class MemoryGatewayConfig:
    real_operations_enabled: bool = False
    embedding_provider_approved: bool = False
    approved_by_panel_version: str | None = None
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    retention_days: int | None = None


@dataclass(frozen=True)
class MemoryAuthorization:
    manifest_id: str
    task_id: int
    read: bool
    write: bool
    max_query_results: int
    write_requires_dedupe: bool


@dataclass(frozen=True)
class MemoryWriteItem:
    content: str
    metadata: dict | None = None
    session_id: int | None = None
    source_task_id: int | None = None


@dataclass(frozen=True)
class MemoryWriteResult:
    memory_item_id: int
    status: str
    content_sha256: str
    dedupe_source_memory_item_id: int | None = None


@dataclass(frozen=True)
class MemoryQueryResult:
    memory_item_id: int
    content: str
    metadata: dict | None
    distance: float
    embedding_model: str


@dataclass(frozen=True)
class OllamaEmbeddingProviderConfig:
    host: str = "http://localhost:11434"
    endpoint_path: str = "/api/embed"
    timeout_seconds: int = 30
    expected_embedding_dim: int = 768


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        ...


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> dict[str, Any]:
        ...


class HttpTransport(Protocol):
    def post(
        self,
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ) -> HttpResponse:
        ...


class OllamaEmbeddingProvider:
    """
    Local-only Ollama embedding provider.

    This provider uses Ollama's current /api/embed endpoint. It is intentionally
    separate from ModelGateway chat/generate paths and does not call /api/chat or
    /api/generate.
    """

    def __init__(
        self,
        config: OllamaEmbeddingProviderConfig | None = None,
        http_transport: HttpTransport | None = None,
    ):
        self.config = config or OllamaEmbeddingProviderConfig()
        self.http_transport = http_transport or requests
        self.endpoint_url = self._validate_and_build_endpoint()

    def _validate_and_build_endpoint(self) -> str:
        parsed = urlparse(self.config.host)
        if parsed.scheme != "http":
            raise MemoryEmbeddingProviderConfigError(
                "Ollama embedding host must use local http"
            )
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise MemoryEmbeddingProviderConfigError(
                "Ollama embedding host must not include path, query, or fragment"
            )
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise MemoryEmbeddingProviderConfigError(
                "Ollama embedding host must be localhost"
            )
        if parsed.port not in {11434, None}:
            raise MemoryEmbeddingProviderConfigError(
                "Ollama embedding host must use port 11434"
            )
        if self.config.endpoint_path != "/api/embed":
            raise MemoryEmbeddingProviderConfigError(
                "Ollama embedding endpoint must be /api/embed"
            )
        if self.config.timeout_seconds <= 0:
            raise MemoryEmbeddingProviderConfigError("timeout_seconds must be positive")
        if self.config.expected_embedding_dim <= 0:
            raise MemoryEmbeddingProviderConfigError(
                "expected_embedding_dim must be positive"
            )

        host = self.config.host.rstrip("/")
        return f"{host}{self.config.endpoint_path}"

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        if not texts:
            raise MemoryEmbeddingProviderError("texts must not be empty")
        if any(not text.strip() for text in texts):
            raise MemoryEmbeddingProviderError("texts must not contain empty entries")
        if not model.strip():
            raise MemoryEmbeddingProviderError("model must not be empty")

        try:
            response = self.http_transport.post(
                self.endpoint_url,
                json={
                    "model": model,
                    "input": texts,
                },
                timeout=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise MemoryEmbeddingProviderError(f"Ollama embed request failed: {exc}") from exc

        status_code = int(response.status_code)
        if status_code >= 400:
            raise MemoryEmbeddingProviderError(
                f"Ollama embed request failed with HTTP {status_code}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise MemoryEmbeddingProviderError("Ollama embed response was not JSON") from exc

        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list):
            raise MemoryEmbeddingProviderError(
                "Ollama embed response missing embeddings list"
            )
        if len(embeddings) != len(texts):
            raise MemoryEmbeddingProviderError(
                "Ollama embed response returned wrong batch size"
            )

        vectors: list[list[float]] = []
        for embedding in embeddings:
            if not isinstance(embedding, list):
                raise MemoryEmbeddingProviderError(
                    "Ollama embed response contained non-list embedding"
                )
            vector = [float(value) for value in embedding]
            if len(vector) != self.config.expected_embedding_dim:
                raise MemoryEmbeddingProviderError(
                    "Ollama embed response returned wrong embedding dimension"
                )
            vectors.append(vector)

        return vectors


def _normalize_sql(sql: str | None) -> str:
    if not sql:
        return ""
    return " ".join(sql.lower().split())


class MemoryGateway:
    """
    Fail-closed MemoryGateway foundation.

    This phase verifies the memory/vector substrate and enforces batch limits.
    It does not generate embeddings, insert vectors, or perform semantic recall.
    """

    EXPECTED_EMBEDDING_DIM = 768
    CONTENT_MODEL_INDEX = "idx_memory_items_content_model"

    def __init__(
        self,
        max_vector_batch: int = 100,
        expected_embedding_dim: int = EXPECTED_EMBEDDING_DIM,
        config: MemoryGatewayConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        if max_vector_batch <= 0:
            raise ValueError("max_vector_batch must be positive")
        if expected_embedding_dim <= 0:
            raise ValueError("expected_embedding_dim must be positive")
        self.max_vector_batch = max_vector_batch
        self.expected_embedding_dim = expected_embedding_dim
        self.config = config or MemoryGatewayConfig(embedding_dim=expected_embedding_dim)
        self.embedding_provider = embedding_provider

        if self.config.embedding_dim != self.expected_embedding_dim:
            raise ValueError("config.embedding_dim must match expected_embedding_dim")
        if self.config.retention_days is not None and self.config.retention_days <= 0:
            raise ValueError("retention_days must be positive when provided")

    def check_health(self) -> MemoryGatewayHealth:
        with get_connection() as conn:
            vec_row = conn.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE name = 'memory_item_embeddings'
                """
            ).fetchone()

            memory_row = conn.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE name = 'memory_items'
                """
            ).fetchone()

            index_row = conn.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE type = 'index'
                  AND name = ?
                """,
                (self.CONTENT_MODEL_INDEX,),
            ).fetchone()

        vec_present = vec_row is not None
        memory_present = memory_row is not None
        index_present = index_row is not None

        if not vec_present:
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=False,
                memory_table_present=memory_present,
                content_model_index_present=index_present,
                embedding_dim=None,
                max_vector_batch=self.max_vector_batch,
                reason="memory_item_embeddings_missing",
            )

        if not memory_present:
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=True,
                memory_table_present=False,
                content_model_index_present=index_present,
                embedding_dim=None,
                max_vector_batch=self.max_vector_batch,
                reason="memory_items_missing",
            )

        memory_sql = _normalize_sql(memory_row["sql"])
        vec_sql = _normalize_sql(vec_row["sql"])
        index_sql = _normalize_sql(index_row["sql"] if index_row else None)
        expected_dim = self.expected_embedding_dim

        if (
            f"embedding_dim integer not null default {expected_dim}" not in memory_sql
            or f"check (embedding_dim = {expected_dim})" not in memory_sql
        ):
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=True,
                memory_table_present=True,
                content_model_index_present=index_present,
                embedding_dim=None,
                max_vector_batch=self.max_vector_batch,
                reason="memory_items_embedding_dim_contract_mismatch",
            )

        if (
            "create virtual table" not in vec_sql
            or "using vec0" not in vec_sql
            or f"embedding float[{expected_dim}]" not in vec_sql
        ):
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=True,
                memory_table_present=True,
                content_model_index_present=index_present,
                embedding_dim=expected_dim,
                max_vector_batch=self.max_vector_batch,
                reason="memory_item_embeddings_vec0_contract_mismatch",
            )

        if (
            not index_present
            or "unique index" not in index_sql
            or "on memory_items(content_sha256, embedding_model)" not in index_sql
        ):
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=True,
                memory_table_present=True,
                content_model_index_present=False,
                embedding_dim=expected_dim,
                max_vector_batch=self.max_vector_batch,
                reason="memory_items_content_model_index_missing",
            )

        return MemoryGatewayHealth(
            healthy=True,
            vec_table_present=True,
            memory_table_present=True,
            content_model_index_present=True,
            embedding_dim=expected_dim,
            max_vector_batch=self.max_vector_batch,
            reason="memory_gateway_sqlite_vec_invariants_present",
        )

    def require_invariants(self) -> MemoryGatewayHealth:
        health = self.check_health()
        if not health.healthy:
            raise MemoryGatewayError(f"MemoryGateway invariant check failed: {health.reason}")
        return health

    def require_batch_size(self, batch_size: int) -> None:
        if batch_size < 0:
            raise MemoryBatchLimitError("batch_size must be non-negative")

        if batch_size > self.max_vector_batch:
            raise MemoryBatchLimitError(
                f"vector batch size {batch_size} exceeds limit {self.max_vector_batch}"
            )

    def query_disabled(self, query_text: str, top_k: int = 5) -> None:
        if not query_text.strip():
            raise MemoryGatewayError("query_text must not be empty")

        if top_k <= 0:
            raise MemoryGatewayError("top_k must be positive")

        self.require_batch_size(top_k)

        raise MemoryGatewayDisabledError(
            "Memory semantic query is not implemented in this phase"
        )

    def write_disabled(self, items: list[dict]) -> None:
        self.require_batch_size(len(items))

        if not items:
            raise MemoryGatewayError("items must not be empty")

        raise MemoryGatewayDisabledError(
            "Memory write is not implemented in this phase"
        )

    def _require_real_operations(self) -> None:
        self.require_invariants()

        if not self.config.real_operations_enabled:
            raise MemoryGatewayDisabledError(
                "Memory real write/query requires real_operations_enabled"
            )
        if not self.config.embedding_provider_approved:
            raise MemoryGatewayNotApprovedError("embedding provider is not approved")
        if not self.config.approved_by_panel_version:
            raise MemoryGatewayNotApprovedError(
                "approved_by_panel_version is required for real memory operations"
            )
        if self.embedding_provider is None:
            raise MemoryEmbeddingProviderError("embedding_provider is required")

    def _require_read_authorization(
        self, authorization: MemoryAuthorization, top_k: int
    ) -> None:
        if not authorization.manifest_id:
            raise MemoryGatewayNotApprovedError("manifest_id is required")
        if authorization.task_id <= 0:
            raise MemoryGatewayNotApprovedError("task_id must be positive")
        if not authorization.read:
            raise MemoryGatewayNotApprovedError("memory read is not authorized")
        if authorization.max_query_results <= 0:
            raise MemoryGatewayNotApprovedError("max_query_results must be positive")
        if top_k > authorization.max_query_results:
            raise MemoryBatchLimitError(
                f"top_k {top_k} exceeds authorized max {authorization.max_query_results}"
            )

    def _require_write_authorization(self, authorization: MemoryAuthorization) -> None:
        if not authorization.manifest_id:
            raise MemoryGatewayNotApprovedError("manifest_id is required")
        if authorization.task_id <= 0:
            raise MemoryGatewayNotApprovedError("task_id must be positive")
        if not authorization.write:
            raise MemoryGatewayNotApprovedError("memory write is not authorized")
        if not authorization.write_requires_dedupe:
            raise MemoryGatewayNotApprovedError("memory write requires dedupe")

    def _embed(self, texts: list[str]) -> list[list[float]]:
        provider = self.embedding_provider
        if provider is None:
            raise MemoryEmbeddingProviderError("embedding_provider is required")

        try:
            vectors = provider.embed(texts, self.config.embedding_model)
        except Exception as exc:
            raise MemoryEmbeddingProviderError(f"embedding provider failed: {exc}") from exc

        if len(vectors) != len(texts):
            raise MemoryEmbeddingProviderError("embedding provider returned wrong batch size")

        for vector in vectors:
            if len(vector) != self.expected_embedding_dim:
                raise MemoryEmbeddingProviderError(
                    "embedding provider returned wrong embedding dimension"
                )

        return vectors

    @staticmethod
    def _content_sha256(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _metadata_to_json(metadata: dict | None) -> str | None:
        if metadata is None:
            return None
        return json.dumps(metadata, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _metadata_from_json(metadata_json: str | None) -> dict | None:
        if metadata_json is None:
            return None
        return json.loads(metadata_json)

    def write(
        self,
        items: list[MemoryWriteItem],
        authorization: MemoryAuthorization,
    ) -> list[MemoryWriteResult]:
        self._require_real_operations()
        self._require_write_authorization(authorization)
        self.require_batch_size(len(items))

        if not items:
            raise MemoryGatewayError("items must not be empty")

        contents = [item.content.strip() for item in items]
        if any(not content for content in contents):
            raise MemoryGatewayError("item content must not be empty")
        if len(set(contents)) != len(contents):
            raise MemoryGatewayError("write batch contains duplicate content")

        vectors = self._embed(contents)
        results: list[MemoryWriteResult] = []

        with get_connection() as conn:
            for item, content, vector in zip(items, contents, vectors):
                content_sha256 = self._content_sha256(content)
                existing = conn.execute(
                    """
                    SELECT memory_item_id
                    FROM memory_items
                    WHERE content_sha256 = ?
                      AND embedding_model = ?
                      AND embedding_status != 'soft_deleted'
                    """,
                    (content_sha256, self.config.embedding_model),
                ).fetchone()

                if existing is not None:
                    results.append(
                        MemoryWriteResult(
                            memory_item_id=int(existing["memory_item_id"]),
                            status="deduped",
                            content_sha256=content_sha256,
                            dedupe_source_memory_item_id=int(existing["memory_item_id"]),
                        )
                    )
                    continue

                cursor = conn.execute(
                    """
                    INSERT INTO memory_items
                    (session_id, source_task_id, content, content_sha256,
                     metadata_json, embedding_model, embedding_dim, embedding_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                    """,
                    (
                        item.session_id,
                        item.source_task_id,
                        content,
                        content_sha256,
                        self._metadata_to_json(item.metadata),
                        self.config.embedding_model,
                        self.expected_embedding_dim,
                    ),
                )
                memory_item_id = int(cursor.lastrowid)
                conn.execute(
                    """
                    INSERT INTO memory_item_embeddings(rowid, embedding)
                    VALUES (?, ?)
                    """,
                    (memory_item_id, sqlite_vec.serialize_float32(vector)),
                )
                conn.execute(
                    """
                    UPDATE memory_items
                    SET embedding_status = 'indexed'
                    WHERE memory_item_id = ?
                    """,
                    (memory_item_id,),
                )
                results.append(
                    MemoryWriteResult(
                        memory_item_id=memory_item_id,
                        status="indexed",
                        content_sha256=content_sha256,
                    )
                )

        return results

    def query(
        self,
        query_text: str,
        top_k: int,
        authorization: MemoryAuthorization,
    ) -> list[MemoryQueryResult]:
        self._require_real_operations()
        self._require_read_authorization(authorization, top_k)
        self.require_batch_size(top_k)

        if not query_text.strip():
            raise MemoryGatewayError("query_text must not be empty")
        if top_k <= 0:
            raise MemoryGatewayError("top_k must be positive")

        query_vector = self._embed([query_text.strip()])[0]

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    mi.memory_item_id,
                    mi.content,
                    mi.metadata_json,
                    mi.embedding_model,
                    vec.distance
                FROM memory_item_embeddings AS vec
                JOIN memory_items AS mi
                  ON mi.memory_item_id = vec.rowid
                WHERE vec.embedding MATCH ?
                  AND k = ?
                  AND mi.embedding_status = 'indexed'
                  AND mi.embedding_model = ?
                ORDER BY vec.distance
                """,
                (
                    sqlite_vec.serialize_float32(query_vector),
                    top_k,
                    self.config.embedding_model,
                ),
            ).fetchall()

        return [
            MemoryQueryResult(
                memory_item_id=int(row["memory_item_id"]),
                content=row["content"],
                metadata=self._metadata_from_json(row["metadata_json"]),
                distance=float(row["distance"]),
                embedding_model=row["embedding_model"],
            )
            for row in rows
        ]
