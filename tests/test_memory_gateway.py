import pytest

from axiom.gateways.memory_gateway import (
    MemoryBatchLimitError,
    MemoryGateway,
    MemoryGatewayDisabledError,
    MemoryGatewayError,
)


def test_memory_gateway_health_is_present():
    health = MemoryGateway().check_health()

    assert health.healthy is True
    assert health.vec_table_present is True
    assert health.memory_table_present is True
    assert health.max_vector_batch == 100
    assert health.reason == "memory_gateway_substrate_present"


def test_memory_gateway_rejects_non_positive_batch_limit():
    with pytest.raises(ValueError):
        MemoryGateway(max_vector_batch=0)


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
