import pytest

from axiom.gateways.memory_gateway import (
    MemoryAuthorization,
    MemoryBatchLimitError,
    MemoryEmbeddingProviderError,
    MemoryEmbeddingProviderConfigError,
    MemoryGateway,
    MemoryGatewayDisabledError,
    MemoryGatewayError,
    MemoryGatewayConfig,
    MemoryGatewayNotApprovedError,
    MemoryWriteItem,
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderConfig,
)


class FakeEmbeddingProvider:
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.calls = []

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        self.calls.append((list(texts), model))
        vectors = []
        for text in texts:
            vector = [0.0] * self.dim
            if "alpha" in text.lower() or "first" in text.lower():
                vector[0] = 1.0
            elif "beta" in text.lower() or "second" in text.lower():
                vector[1] = 1.0
            else:
                vector[2] = 1.0
            vectors.append(vector)
        return vectors


class FakeHttpResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self.payload = payload or {"embeddings": [[0.0] * 768]}

    def json(self):
        return self.payload


class FakeHttpTransport:
    def __init__(self, response: FakeHttpResponse | None = None):
        self.response = response or FakeHttpResponse()
        self.calls = []

    def post(self, url, *, json, timeout):
        self.calls.append({"url": url, "json": dict(json), "timeout": timeout})
        return self.response


def enabled_gateway(provider: FakeEmbeddingProvider | None = None) -> MemoryGateway:
    return MemoryGateway(
        config=MemoryGatewayConfig(
            real_operations_enabled=True,
            embedding_provider_approved=True,
            approved_by_panel_version="test",
        ),
        embedding_provider=provider or FakeEmbeddingProvider(),
    )


def memory_auth(**overrides) -> MemoryAuthorization:
    values = {
        "manifest_id": "role.system_maintenance_noop.v1",
        "task_id": 1,
        "read": True,
        "write": True,
        "max_query_results": 5,
        "write_requires_dedupe": True,
    }
    values.update(overrides)
    return MemoryAuthorization(**values)


def test_memory_gateway_health_is_present():
    health = MemoryGateway().check_health()

    assert health.healthy is True
    assert health.vec_table_present is True
    assert health.memory_table_present is True
    assert health.content_model_index_present is True
    assert health.embedding_dim == 768
    assert health.max_vector_batch == 100
    assert health.reason == "memory_gateway_sqlite_vec_invariants_present"


def test_memory_gateway_require_invariants_returns_health_when_valid():
    health = MemoryGateway().require_invariants()

    assert health.healthy is True
    assert health.reason == "memory_gateway_sqlite_vec_invariants_present"


def test_memory_gateway_rejects_non_positive_batch_limit():
    with pytest.raises(ValueError):
        MemoryGateway(max_vector_batch=0)


def test_memory_gateway_rejects_non_positive_expected_embedding_dim():
    with pytest.raises(ValueError):
        MemoryGateway(expected_embedding_dim=0)


def test_memory_gateway_health_fails_on_embedding_dim_contract_mismatch():
    health = MemoryGateway(expected_embedding_dim=1536).check_health()

    assert health.healthy is False
    assert health.reason == "memory_items_embedding_dim_contract_mismatch"


def test_memory_gateway_health_fails_when_content_model_index_missing():
    from axiom.persistence.db import get_connection

    with get_connection() as conn:
        conn.execute("DROP INDEX idx_memory_items_content_model")

    health = MemoryGateway().check_health()

    assert health.healthy is False
    assert health.content_model_index_present is False
    assert health.reason == "memory_items_content_model_index_missing"


def test_memory_gateway_require_invariants_fails_closed_when_index_missing():
    from axiom.persistence.db import get_connection

    with get_connection() as conn:
        conn.execute("DROP INDEX idx_memory_items_content_model")

    with pytest.raises(MemoryGatewayError):
        MemoryGateway().require_invariants()


def test_memory_gateway_accepts_batch_at_limit():
    MemoryGateway(max_vector_batch=100).require_batch_size(100)


def test_memory_gateway_rejects_batch_above_limit():
    with pytest.raises(MemoryBatchLimitError):
        MemoryGateway(max_vector_batch=100).require_batch_size(101)


def test_memory_gateway_rejects_negative_batch_size():
    with pytest.raises(MemoryBatchLimitError):
        MemoryGateway(max_vector_batch=100).require_batch_size(-1)


def test_memory_gateway_query_rejects_empty_text():
    with pytest.raises(MemoryGatewayError):
        MemoryGateway().query_disabled("")


def test_memory_gateway_query_rejects_non_positive_top_k():
    with pytest.raises(MemoryGatewayError):
        MemoryGateway().query_disabled("test", top_k=0)


def test_memory_gateway_query_fails_closed():
    with pytest.raises(MemoryGatewayDisabledError):
        MemoryGateway().query_disabled("test", top_k=5)


def test_memory_gateway_query_enforces_batch_limit():
    with pytest.raises(MemoryBatchLimitError):
        MemoryGateway(max_vector_batch=100).query_disabled("test", top_k=101)


def test_memory_gateway_write_rejects_empty_items():
    with pytest.raises(MemoryGatewayError):
        MemoryGateway().write_disabled([])


def test_memory_gateway_write_fails_closed():
    with pytest.raises(MemoryGatewayDisabledError):
        MemoryGateway().write_disabled([{"text": "hello"}])


def test_memory_gateway_write_enforces_batch_limit():
    with pytest.raises(MemoryBatchLimitError):
        MemoryGateway(max_vector_batch=2).write_disabled(
            [{"text": "one"}, {"text": "two"}, {"text": "three"}]
        )


def test_memory_gateway_real_write_requires_explicit_enablement():
    with pytest.raises(MemoryGatewayDisabledError):
        MemoryGateway(embedding_provider=FakeEmbeddingProvider()).write(
            [MemoryWriteItem(content="alpha memory")],
            memory_auth(),
        )


def test_memory_gateway_real_write_requires_provider_approval():
    gateway = MemoryGateway(
        config=MemoryGatewayConfig(real_operations_enabled=True),
        embedding_provider=FakeEmbeddingProvider(),
    )

    with pytest.raises(MemoryGatewayNotApprovedError):
        gateway.write([MemoryWriteItem(content="alpha memory")], memory_auth())


def test_memory_gateway_real_write_requires_embedding_provider():
    gateway = MemoryGateway(
        config=MemoryGatewayConfig(
            real_operations_enabled=True,
            embedding_provider_approved=True,
            approved_by_panel_version="test",
        )
    )

    with pytest.raises(MemoryEmbeddingProviderError):
        gateway.write([MemoryWriteItem(content="alpha memory")], memory_auth())


def test_memory_gateway_real_write_rejects_unauthorized_manifest_policy():
    with pytest.raises(MemoryGatewayNotApprovedError):
        enabled_gateway().write(
            [MemoryWriteItem(content="alpha memory")],
            memory_auth(write=False),
        )


def test_memory_gateway_real_write_inserts_memory_item_and_sparse_vector():
    provider = FakeEmbeddingProvider()
    result = enabled_gateway(provider).write(
        [MemoryWriteItem(content="alpha memory", metadata={"source": "test"})],
        memory_auth(),
    )

    assert len(result) == 1
    assert result[0].status == "indexed"
    assert result[0].memory_item_id > 0
    assert provider.calls == [(["alpha memory"], "nomic-embed-text")]

    from axiom.persistence.db import get_connection

    with get_connection() as conn:
        item = conn.execute(
            """
            SELECT content, metadata_json, embedding_status
            FROM memory_items
            WHERE memory_item_id = ?
            """,
            (result[0].memory_item_id,),
        ).fetchone()
        vector = conn.execute(
            """
            SELECT rowid
            FROM memory_item_embeddings
            WHERE rowid = ?
            """,
            (result[0].memory_item_id,),
        ).fetchone()

    assert item["content"] == "alpha memory"
    assert item["metadata_json"] == '{"source":"test"}'
    assert item["embedding_status"] == "indexed"
    assert vector["rowid"] == result[0].memory_item_id


def test_memory_gateway_real_write_dedupes_by_content_and_model():
    gateway = enabled_gateway()
    first = gateway.write([MemoryWriteItem(content="alpha memory")], memory_auth())
    second = gateway.write([MemoryWriteItem(content="alpha memory")], memory_auth())

    assert first[0].status == "indexed"
    assert second[0].status == "deduped"
    assert second[0].memory_item_id == first[0].memory_item_id
    assert second[0].dedupe_source_memory_item_id == first[0].memory_item_id


def test_memory_gateway_real_write_rejects_duplicate_batch_content():
    with pytest.raises(MemoryGatewayError):
        enabled_gateway().write(
            [
                MemoryWriteItem(content="alpha memory"),
                MemoryWriteItem(content="alpha memory"),
            ],
            memory_auth(),
        )


def test_memory_gateway_real_query_returns_nearest_indexed_items():
    gateway = enabled_gateway()
    gateway.write(
        [
            MemoryWriteItem(content="alpha first", metadata={"rank": 1}),
            MemoryWriteItem(content="beta second", metadata={"rank": 2}),
        ],
        memory_auth(),
    )

    results = gateway.query("alpha lookup", top_k=2, authorization=memory_auth())

    assert [result.content for result in results] == ["alpha first", "beta second"]
    assert results[0].metadata == {"rank": 1}
    assert results[0].distance == 0.0
    assert all(result.embedding_model == "nomic-embed-text" for result in results)


def test_memory_gateway_real_query_enforces_authorized_top_k():
    with pytest.raises(MemoryBatchLimitError):
        enabled_gateway().query(
            "alpha lookup",
            top_k=6,
            authorization=memory_auth(max_query_results=5),
        )


def test_memory_gateway_real_query_rejects_unauthorized_read():
    with pytest.raises(MemoryGatewayNotApprovedError):
        enabled_gateway().query(
            "alpha lookup",
            top_k=1,
            authorization=memory_auth(read=False),
        )


def test_memory_gateway_real_query_rejects_wrong_embedding_dimension():
    gateway = enabled_gateway(FakeEmbeddingProvider(dim=3))

    with pytest.raises(MemoryEmbeddingProviderError):
        gateway.query("alpha lookup", top_k=1, authorization=memory_auth())


def test_ollama_embedding_provider_rejects_non_local_host():
    with pytest.raises(MemoryEmbeddingProviderConfigError):
        OllamaEmbeddingProvider(
            OllamaEmbeddingProviderConfig(host="https://api.example.com")
        )


def test_ollama_embedding_provider_rejects_host_path_query_or_fragment():
    for host in (
        "http://localhost:11434/foo",
        "http://localhost:11434?x=1",
        "http://localhost:11434#frag",
    ):
        with pytest.raises(MemoryEmbeddingProviderConfigError):
            OllamaEmbeddingProvider(OllamaEmbeddingProviderConfig(host=host))


def test_ollama_embedding_provider_rejects_wrong_endpoint_path():
    with pytest.raises(MemoryEmbeddingProviderConfigError):
        OllamaEmbeddingProvider(
            OllamaEmbeddingProviderConfig(endpoint_path="/api/embeddings")
        )


def test_ollama_embedding_provider_posts_to_current_embed_endpoint():
    transport = FakeHttpTransport(
        FakeHttpResponse(payload={"embeddings": [[1.0] + [0.0] * 767]})
    )
    provider = OllamaEmbeddingProvider(http_transport=transport)

    vectors = provider.embed(["alpha memory"], "nomic-embed-text")

    assert len(vectors) == 1
    assert vectors[0][0] == 1.0
    assert transport.calls == [
        {
            "url": "http://localhost:11434/api/embed",
            "json": {
                "model": "nomic-embed-text",
                "input": ["alpha memory"],
            },
            "timeout": 30,
        }
    ]


def test_ollama_embedding_provider_supports_batch_embedding():
    transport = FakeHttpTransport(
        FakeHttpResponse(
            payload={
                "embeddings": [
                    [1.0] + [0.0] * 767,
                    [0.0, 1.0] + [0.0] * 766,
                ]
            }
        )
    )
    provider = OllamaEmbeddingProvider(http_transport=transport)

    vectors = provider.embed(["alpha", "beta"], "nomic-embed-text")

    assert len(vectors) == 2
    assert transport.calls[0]["json"]["input"] == ["alpha", "beta"]


def test_ollama_embedding_provider_rejects_http_error():
    provider = OllamaEmbeddingProvider(
        http_transport=FakeHttpTransport(FakeHttpResponse(status_code=500))
    )

    with pytest.raises(MemoryEmbeddingProviderError):
        provider.embed(["alpha"], "nomic-embed-text")


def test_ollama_embedding_provider_rejects_missing_embeddings():
    provider = OllamaEmbeddingProvider(
        http_transport=FakeHttpTransport(FakeHttpResponse(payload={"embedding": []}))
    )

    with pytest.raises(MemoryEmbeddingProviderError):
        provider.embed(["alpha"], "nomic-embed-text")


def test_ollama_embedding_provider_rejects_wrong_dimension():
    provider = OllamaEmbeddingProvider(
        http_transport=FakeHttpTransport(
            FakeHttpResponse(payload={"embeddings": [[1.0, 2.0, 3.0]]})
        )
    )

    with pytest.raises(MemoryEmbeddingProviderError):
        provider.embed(["alpha"], "nomic-embed-text")


def test_memory_gateway_uses_ollama_embedding_provider_for_write_and_query():
    transport = FakeHttpTransport(
        FakeHttpResponse(
            payload={
                "embeddings": [
                    [1.0] + [0.0] * 767,
                ]
            }
        )
    )
    provider = OllamaEmbeddingProvider(http_transport=transport)
    gateway = enabled_gateway(provider)

    write_result = gateway.write([MemoryWriteItem(content="alpha memory")], memory_auth())
    query_result = gateway.query("alpha memory", top_k=1, authorization=memory_auth())

    assert write_result[0].status == "indexed"
    assert query_result[0].content == "alpha memory"
    assert len(transport.calls) == 2
