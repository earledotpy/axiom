import pytest

from axiom.gateways.model_gateway import (
    ModelGateway,
    ModelGatewayDisabledError,
    ModelGatewayError,
    PolicyDeniedError,
)
from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_resource_usage,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_session_and_task():
    session_id = create_session(operator_id="model-gateway-wrapper")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-model-gateway-wrapper",
        task_class="system_maintenance",
        task_type="model_gateway_wrapper_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    return session_id, task_id


def test_model_gateway_prepare_payload_injects_default_model_and_think_false():
    prepared = ModelGateway().prepare_payload({"prompt": "hello"})

    assert prepared["model"] == "qwen3:4b"
    assert prepared["think"] is False
    assert prepared["prompt"] == "hello"


def test_model_gateway_prepare_payload_preserves_explicit_model():
    prepared = ModelGateway().prepare_payload({"model": "custom:model", "prompt": "hello"})

    assert prepared["model"] == "custom:model"
    assert prepared["think"] is False


def test_model_gateway_prepare_payload_rejects_think_true():
    with pytest.raises(PolicyDeniedError):
        ModelGateway().prepare_payload({"model": "qwen3:4b", "think": True})


def test_model_gateway_rejects_non_dict_payload():
    with pytest.raises(ModelGatewayError):
        ModelGateway().prepare_payload("not-a-dict")


def test_model_gateway_allows_chat_and_generate_endpoints():
    gateway = ModelGateway()

    gateway.validate_endpoint("/api/chat")
    gateway.validate_endpoint("/api/generate")


def test_model_gateway_rejects_unsupported_endpoint():
    with pytest.raises(ModelGatewayError):
        ModelGateway().validate_endpoint("/api/embeddings")


def test_model_gateway_call_local_ollama_disabled_fails_closed():
    with pytest.raises(ModelGatewayDisabledError):
        ModelGateway().call_local_ollama_disabled(
            endpoint="/api/chat",
            payload={"model": "qwen3:4b", "messages": []},
        )


def test_model_gateway_dummy_response_records_provider_call_usage():
    session_id, task_id = make_session_and_task()

    result = ModelGateway().record_dummy_local_response(
        task_id=task_id,
        session_id=session_id,
        endpoint="/api/generate",
        payload={"prompt": "hello"},
        response_text="world",
    )

    usage = get_resource_usage(result.provider_call_usage_id)

    assert result.endpoint == "/api/generate"
    assert result.model == "qwen3:4b"
    assert result.response_text == "world"
    assert result.provider_usage_id > 0
    assert usage["resource_type"] == "provider_calls"
    assert usage["amount"] == 1
    assert usage["status"] == "unknown"
