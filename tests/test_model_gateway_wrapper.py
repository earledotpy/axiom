import pytest

from axiom.gateways.model_gateway import (
    CloudCascadeConfig,
    CloudCascadeConfigError,
    CloudCascadeCallError,
    CloudCredentialsError,
    CloudCascadeNotApprovedError,
    CloudProviderConfig,
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
from axiom.persistence.db import get_connection

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


class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body


def approved_cloud_config(*providers, order=("groq",), real_calls_enabled=True):
    return CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version="phase4-test",
        provider_order=order,
        providers=providers
        or (
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
        real_calls_enabled=real_calls_enabled,
    )


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


def test_model_gateway_cloud_cascade_requires_provider_config_approval():
    config = CloudCascadeConfig(
        provider_configuration_approved=False,
        provider_order=("groq",),
        providers=(
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
    )

    readiness = ModelGateway().evaluate_cloud_cascade_readiness(config)

    assert readiness.ready is False
    assert readiness.reason == "provider_configuration_not_approved"
    assert readiness.provider_order == ("groq",)


def test_model_gateway_cloud_cascade_rejects_unknown_provider():
    config = CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version="phase4-test",
        provider_order=("unknown",),
        providers=(
            CloudProviderConfig(
                provider="unknown",
                model="test-model",
                api_key_env_var="UNKNOWN_API_KEY",
            ),
        ),
    )

    with pytest.raises(CloudCascadeConfigError):
        ModelGateway().evaluate_cloud_cascade_readiness(config)


def test_model_gateway_cloud_cascade_rejects_duplicate_provider_order():
    config = CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version="phase4-test",
        provider_order=("groq", "groq"),
        providers=(
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
    )

    with pytest.raises(CloudCascadeConfigError):
        ModelGateway().evaluate_cloud_cascade_readiness(config)


def test_model_gateway_cloud_cascade_requires_panel_version_when_approved():
    config = CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version=None,
        provider_order=("groq",),
        providers=(
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
    )

    readiness = ModelGateway().evaluate_cloud_cascade_readiness(config)

    assert readiness.ready is False
    assert readiness.reason == "approved_by_panel_version_missing"


def test_model_gateway_cloud_cascade_ready_config_still_does_not_call_cloud():
    config = CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version="phase4-test",
        provider_order=("groq",),
        providers=(
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
    )

    readiness = ModelGateway().evaluate_cloud_cascade_readiness(config)

    assert readiness.ready is True
    assert readiness.reason == "cloud_cascade_ready"

    with pytest.raises(ModelGatewayDisabledError):
        ModelGateway().call_cloud_cascade_disabled(config, {"messages": []})


def test_model_gateway_cloud_cascade_disabled_call_fails_closed_when_unapproved():
    config = CloudCascadeConfig(
        provider_configuration_approved=False,
        provider_order=("groq",),
        providers=(
            CloudProviderConfig(
                provider="groq",
                model="llama-test",
                api_key_env_var="GROQ_API_KEY",
            ),
        ),
    )

    with pytest.raises(CloudCascadeNotApprovedError):
        ModelGateway().call_cloud_cascade_disabled(config, {"messages": []})


def test_model_gateway_cloud_cascade_rejects_non_https_endpoint():
    config = approved_cloud_config(
        CloudProviderConfig(
            provider="groq",
            model="llama-test",
            api_key_env_var="GROQ_API_KEY",
            endpoint_url="http://api.groq.test/chat/completions",
        )
    )

    readiness = ModelGateway().evaluate_cloud_cascade_readiness(config)

    assert readiness.ready is False
    assert readiness.reason == "groq_endpoint_url_must_be_https"


def test_model_gateway_cloud_cascade_real_call_requires_explicit_enable():
    session_id, task_id = make_session_and_task()
    config = approved_cloud_config(real_calls_enabled=False)

    with pytest.raises(ModelGatewayDisabledError):
        ModelGateway().call_cloud_cascade(
            config,
            {"messages": [{"role": "user", "content": "hello"}]},
            task_id=task_id,
            session_id=session_id,
        )


def test_model_gateway_cloud_cascade_real_call_requires_api_key_env(monkeypatch):
    session_id, task_id = make_session_and_task()
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(CloudCredentialsError):
        ModelGateway().call_cloud_cascade(
            approved_cloud_config(),
            {"messages": [{"role": "user", "content": "hello"}]},
            task_id=task_id,
            session_id=session_id,
        )


def test_model_gateway_cloud_cascade_success_records_usage(monkeypatch):
    session_id, task_id = make_session_and_task()
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse(
            body={
                "choices": [
                    {
                        "message": {
                            "content": "cloud response",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 3,
                },
            }
        )

    result = ModelGateway(http_post=fake_post).call_cloud_cascade(
        approved_cloud_config(),
        {"messages": [{"role": "user", "content": "hello"}]},
        task_id=task_id,
        session_id=session_id,
    )

    usage = get_resource_usage(result.provider_call_usage_id)

    assert result.provider == "groq"
    assert result.model == "llama-test"
    assert result.response_text == "cloud response"
    assert not hasattr(result, "raw_response")
    assert usage["resource_type"] == "provider_calls"
    assert usage["amount"] == 1
    assert calls[0]["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert calls[0]["json"]["model"] == "llama-test"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-secret"
    assert calls[0]["timeout"] == 30

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT provider, model, status, actual_input_tokens, actual_output_tokens
            FROM provider_usage
            WHERE usage_id = ?
            """,
            (result.provider_usage_id,),
        ).fetchone()

    assert row["provider"] == "groq"
    assert row["model"] == "llama-test"
    assert row["status"] == "completed"
    assert row["actual_input_tokens"] == 7
    assert row["actual_output_tokens"] == 3


def test_model_gateway_cloud_cascade_fails_over_after_rate_limit(monkeypatch):
    session_id, task_id = make_session_and_task()
    monkeypatch.setenv("GROQ_API_KEY", "groq-secret")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-secret")
    responses = [
        FakeResponse(status_code=429, body={"error": "rate limited"}),
        FakeResponse(
            body={
                "choices": [
                    {
                        "message": {
                            "content": "fallback response",
                        },
                    }
                ],
            }
        ),
    ]

    def fake_post(url, json, headers, timeout):
        return responses.pop(0)

    config = approved_cloud_config(
        CloudProviderConfig(
            provider="groq",
            model="groq-model",
            api_key_env_var="GROQ_API_KEY",
        ),
        CloudProviderConfig(
            provider="openrouter",
            model="openrouter-model",
            api_key_env_var="OPENROUTER_API_KEY",
        ),
        order=("groq", "openrouter"),
    )

    result = ModelGateway(http_post=fake_post).call_cloud_cascade(
        config,
        {"messages": [{"role": "user", "content": "hello"}]},
        task_id=task_id,
        session_id=session_id,
    )

    assert result.provider == "openrouter"
    assert result.response_text == "fallback response"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT provider, status
            FROM provider_usage
            WHERE task_id = ?
              AND provider IN ('groq', 'openrouter')
            ORDER BY usage_id
            """,
            (task_id,),
        ).fetchall()

    assert [(row["provider"], row["status"]) for row in rows] == [
        ("groq", "rate_limited"),
        ("openrouter", "completed"),
    ]


def test_model_gateway_cloud_cascade_fails_closed_on_invalid_response(monkeypatch):
    session_id, task_id = make_session_and_task()
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")

    def fake_post(url, json, headers, timeout):
        return FakeResponse(body={"choices": []})

    with pytest.raises(CloudCascadeCallError):
        ModelGateway(http_post=fake_post).call_cloud_cascade(
            approved_cloud_config(),
            {"messages": [{"role": "user", "content": "hello"}]},
            task_id=task_id,
            session_id=session_id,
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT provider, status, error_info
            FROM provider_usage
            WHERE task_id = ?
              AND provider = 'groq'
            ORDER BY usage_id DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()

    assert row["provider"] == "groq"
    assert row["status"] == "failed"
    assert "response_error" in row["error_info"]
