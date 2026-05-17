from __future__ import annotations

from dataclasses import dataclass

from axiom.persistence.db import get_connection


class MemoryGatewayError(RuntimeError):
    pass


class MemoryGatewayDisabledError(RuntimeError):
    pass


class MemoryBatchLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class MemoryGatewayHealth:
    healthy: bool
    vec_table_present: bool
    memory_table_present: bool
    max_vector_batch: int
    reason: str


class MemoryGateway:
    """
    Fail-closed MemoryGateway foundation.

    This phase verifies the memory/vector substrate and enforces batch limits.
    It does not generate embeddings, insert vectors, or perform semantic recall.
    """

    def __init__(self, max_vector_batch: int = 100):
        if max_vector_batch <= 0:
            raise ValueError("max_vector_batch must be positive")
        self.max_vector_batch = max_vector_batch

    def check_health(self) -> MemoryGatewayHealth:
        with get_connection() as conn:
            vec_row = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE name = 'memory_item_embeddings'
                """
            ).fetchone()

            memory_row = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE name = 'memory_items'
                """
            ).fetchone()

        vec_present = vec_row is not None
        memory_present = memory_row is not None

        if not vec_present:
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=False,
                memory_table_present=memory_present,
                max_vector_batch=self.max_vector_batch,
                reason="memory_item_embeddings_missing",
            )

        if not memory_present:
            return MemoryGatewayHealth(
                healthy=False,
                vec_table_present=True,
                memory_table_present=False,
                max_vector_batch=self.max_vector_batch,
                reason="memory_items_missing",
            )

        return MemoryGatewayHealth(
            healthy=True,
            vec_table_present=True,
            memory_table_present=True,
            max_vector_batch=self.max_vector_batch,
            reason="memory_gateway_substrate_present",
        )

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
