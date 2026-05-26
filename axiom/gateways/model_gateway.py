from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

from axiom.persistence.repositories import (
    record_provider_usage,
    record_resource_usage,
    update_provider_usage_status,
)


class PolicyDeniedError(RuntimeError):
    pass


class ModelGatewayError(RuntimeError):
    pass


class ModelGatewayDisabledError(RuntimeError):
    pass


class CloudCascadeConfigError(RuntimeError):
    pass


class CloudCascadeNotApprovedError(RuntimeError):
    pass


class CloudCascadeCallError(RuntimeError):
    pass


class CloudCredentialsError(RuntimeError):
    pass


APPROVED_CLOUD_PROVIDERS = {"cerebras", "groq", "openrouter", "sambanova"}
DEFAULT_CLOUD_ENDPOINTS = {
    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "sambanova": "https://api.sambanova.ai/v1/chat/completions",
}
TERMINAL_PROVIDER_STATUSES = {
    "completed",
    "failed",
    "rate_limited",
    "quota_exhausted",
    "abandoned_session_crash",
}


@dataclass(frozen=True)
class ModelGatewayConfig:
    host: str = "http://localhost:11434"
    model: str = "qwen3:4b"
    fingerprint_timeout_seconds: int = 5


@dataclass(frozen=True)
class CloudProviderConfig:
    provider: str
    model: str
    api_key_env_var: str
    enabled: bool = True
    endpoint_url: str | None = None
    timeout_seconds: int = 30


@dataclass(frozen=True)
class CloudCascadeConfig:
    provider_configuration_approved: bool = False
    approved_by_panel_version: str | None = None
    provider_order: tuple[str, ...] = ()
    providers: tuple[CloudProviderConfig, ...] = ()
    real_calls_enabled: bool = False


@dataclass(frozen=True)
class CloudCascadeReadiness:
    ready: bool
    reason: str
    provider_order: tuple[str, ...]
    approved_by_panel_version: str | None


@dataclass(frozen=True)
class CloudModelResponse:
    provider: str
    model: str
    response_text: str
    provider_usage_id: int
    provider_call_usage_id: int


@dataclass(frozen=True)
class DummyModelResponse:
    endpoint: str
    model: str
    response_text: str
    provider_usage_id: int
    provider_call_usage_id: int


def prepare_local_ollama_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Enforce AXIOM local Ollama thinking-mode policy.

    Rule:
    - Caller may not set think=True.
    - Every local Ollama payload must be sent with think=False.
    - Other caller options are preserved.
    """
    if payload.get("think") is True:
        raise PolicyDeniedError("Caller may not override local Ollama thinking mode")

    prepared = dict(payload)
    prepared["think"] = False
    return prepared


def evaluate_cloud_cascade_readiness(
    config: CloudCascadeConfig,
) -> CloudCascadeReadiness:
    provider_names = [provider.provider for provider in config.providers]
    duplicate_providers = {
        provider for provider in provider_names if provider_names.count(provider) > 1
    }

    if duplicate_providers:
        raise CloudCascadeConfigError(
            f"Duplicate cloud provider config: {sorted(duplicate_providers)!r}"
        )

    unknown_providers = [
        provider for provider in provider_names if provider not in APPROVED_CLOUD_PROVIDERS
    ]
    if unknown_providers:
        raise CloudCascadeConfigError(
            f"Unknown cloud provider config: {unknown_providers!r}"
        )

    duplicate_order = {
        provider
        for provider in config.provider_order
        if config.provider_order.count(provider) > 1
    }
    if duplicate_order:
        raise CloudCascadeConfigError(
            f"Duplicate cloud provider order entry: {sorted(duplicate_order)!r}"
        )

    unknown_order = [
        provider
        for provider in config.provider_order
        if provider not in APPROVED_CLOUD_PROVIDERS
    ]
    if unknown_order:
        raise CloudCascadeConfigError(
            f"Unknown cloud provider order entry: {unknown_order!r}"
        )

    configured = {provider.provider: provider for provider in config.providers}
    enabled_provider_order = tuple(
        provider
        for provider in config.provider_order
        if provider in configured and configured[provider].enabled
    )

    if not config.provider_configuration_approved:
        return CloudCascadeReadiness(
            ready=False,
            reason="provider_configuration_not_approved",
            provider_order=enabled_provider_order,
            approved_by_panel_version=config.approved_by_panel_version,
        )

    if not config.approved_by_panel_version:
        return CloudCascadeReadiness(
            ready=False,
            reason="approved_by_panel_version_missing",
            provider_order=enabled_provider_order,
            approved_by_panel_version=config.approved_by_panel_version,
        )

    if not enabled_provider_order:
        return CloudCascadeReadiness(
            ready=False,
            reason="no_enabled_cloud_providers",
            provider_order=enabled_provider_order,
            approved_by_panel_version=config.approved_by_panel_version,
        )

    for provider_name in enabled_provider_order:
        provider = configured[provider_name]
        if not provider.model:
            return CloudCascadeReadiness(
                ready=False,
                reason=f"{provider_name}_model_missing",
                provider_order=enabled_provider_order,
                approved_by_panel_version=config.approved_by_panel_version,
            )
        if not provider.api_key_env_var:
            return CloudCascadeReadiness(
                ready=False,
                reason=f"{provider_name}_api_key_env_var_missing",
                provider_order=enabled_provider_order,
                approved_by_panel_version=config.approved_by_panel_version,
            )
        if provider.timeout_seconds <= 0:
            return CloudCascadeReadiness(
                ready=False,
                reason=f"{provider_name}_timeout_seconds_invalid",
                provider_order=enabled_provider_order,
                approved_by_panel_version=config.approved_by_panel_version,
            )
        endpoint_url = provider.endpoint_url or DEFAULT_CLOUD_ENDPOINTS[provider_name]
        if not endpoint_url.startswith("https://"):
            return CloudCascadeReadiness(
                ready=False,
                reason=f"{provider_name}_endpoint_url_must_be_https",
                provider_order=enabled_provider_order,
                approved_by_panel_version=config.approved_by_panel_version,
            )

    return CloudCascadeReadiness(
        ready=True,
        reason="cloud_cascade_ready",
        provider_order=enabled_provider_order,
        approved_by_panel_version=config.approved_by_panel_version,
    )


def _extract_chat_response_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise CloudCascadeCallError("cloud provider response missing choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise CloudCascadeCallError("cloud provider response choice is invalid")

    message = first_choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    text = first_choice.get("text")
    if isinstance(text, str):
        return text

    raise CloudCascadeCallError("cloud provider response missing text content")


def _usage_tokens(response_json: dict[str, Any]) -> tuple[int | None, int | None]:
    usage = response_json.get("usage")
    usage_obj = usage if isinstance(usage, dict) else {}

    input_tokens = usage_obj.get("prompt_tokens")
    output_tokens = usage_obj.get("completion_tokens")

    if input_tokens is None:
        input_tokens = usage_obj.get("input_tokens")
    if output_tokens is None:
        output_tokens = usage_obj.get("output_tokens")
    if input_tokens is None:
        input_tokens = response_json.get("input_tokens_count")
    if output_tokens is None:
        output_tokens = response_json.get("output_tokens_count")

    return (
        input_tokens if isinstance(input_tokens, int) else None,
        output_tokens if isinstance(output_tokens, int) else None,
    )


def _status_for_http_status(status_code: int) -> str:
    if status_code == 429:
        return "rate_limited"
    if status_code in {402, 403}:
        return "quota_exhausted"
    return "failed"


class ModelGateway:
    """
    Fail-closed local ModelGateway foundation.

    This phase validates local Ollama payload policy and records dummy accounting.
    It does not perform HTTP requests to Ollama.
    """

    ALLOWED_ENDPOINTS = {"/api/chat", "/api/generate"}

    def __init__(
        self,
        config: ModelGatewayConfig | None = None,
        http_post: Any | None = None,
    ):
        self.config = config or ModelGatewayConfig()
        self._http_post = http_post or requests.post

    def prepare_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ModelGatewayError("payload must be a dict")

        prepared = prepare_local_ollama_payload(payload)

        if "model" not in prepared:
            prepared["model"] = self.config.model

        return prepared

    def validate_endpoint(self, endpoint: str) -> None:
        if endpoint not in self.ALLOWED_ENDPOINTS:
            raise ModelGatewayError(f"Unsupported local Ollama endpoint: {endpoint}")

    def call_local_ollama_disabled(self, endpoint: str, payload: dict[str, Any]) -> None:
        self.validate_endpoint(endpoint)
        self.prepare_payload(payload)

        raise ModelGatewayDisabledError(
            "Real local Ollama calls are not implemented in this phase"
        )

    def evaluate_cloud_cascade_readiness(
        self,
        config: CloudCascadeConfig,
    ) -> CloudCascadeReadiness:
        return evaluate_cloud_cascade_readiness(config)

    def call_cloud_cascade_disabled(
        self,
        config: CloudCascadeConfig,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise ModelGatewayError("payload must be a dict")

        readiness = self.evaluate_cloud_cascade_readiness(config)
        if not readiness.ready:
            raise CloudCascadeNotApprovedError(
                f"Cloud cascade is not ready: {readiness.reason}"
            )

        raise ModelGatewayDisabledError(
            "Real cloud model calls are not implemented in this Phase 4 slice"
        )

    def call_cloud_cascade(
        self,
        config: CloudCascadeConfig,
        payload: dict[str, Any],
        *,
        task_id: int,
        session_id: int,
    ) -> CloudModelResponse:
        if not isinstance(payload, dict):
            raise ModelGatewayError("payload must be a dict")

        readiness = self.evaluate_cloud_cascade_readiness(config)
        if not readiness.ready:
            raise CloudCascadeNotApprovedError(
                f"Cloud cascade is not ready: {readiness.reason}"
            )

        if not config.real_calls_enabled:
            raise ModelGatewayDisabledError(
                "Real cloud model calls require real_calls_enabled=True"
            )

        configured = {provider.provider: provider for provider in config.providers}
        last_error: str | None = None

        for provider_name in readiness.provider_order:
            provider = configured[provider_name]
            api_key = os.environ.get(provider.api_key_env_var)
            if not api_key:
                last_error = f"{provider_name}_api_key_env_var_not_set"
                continue

            provider_usage_id = record_provider_usage(
                session_id=session_id,
                task_id=task_id,
                provider=provider_name,
                status="started",
                model=provider.model,
            )

            provider_call_usage_id = record_resource_usage(
                task_id=task_id,
                resource_type="provider_calls",
                amount=1,
                limit_value=None,
                status="unknown",
                details={
                    "provider": provider_name,
                    "model": provider.model,
                    "usage_source": "model_gateway_cloud_cascade",
                },
            )

            request_payload = dict(payload)
            request_payload["model"] = provider.model

            endpoint_url = provider.endpoint_url or DEFAULT_CLOUD_ENDPOINTS[provider_name]
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            try:
                response = self._http_post(
                    endpoint_url,
                    json=request_payload,
                    headers=headers,
                    timeout=provider.timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = f"{provider_name}_request_error: {exc}"
                update_provider_usage_status(
                    provider_usage_id,
                    "failed",
                    error_info=last_error,
                )
                continue

            if response.status_code >= 400:
                status = _status_for_http_status(response.status_code)
                last_error = f"{provider_name}_http_{response.status_code}"
                update_provider_usage_status(
                    provider_usage_id,
                    status,
                    error_info=last_error,
                )
                continue

            try:
                response_json = response.json()
                if not isinstance(response_json, dict):
                    raise CloudCascadeCallError("cloud provider JSON response is not an object")
                response_text = _extract_chat_response_text(response_json)
            except (ValueError, CloudCascadeCallError) as exc:
                last_error = f"{provider_name}_response_error: {exc}"
                update_provider_usage_status(
                    provider_usage_id,
                    "failed",
                    error_info=last_error,
                )
                continue

            actual_input_tokens, actual_output_tokens = _usage_tokens(response_json)
            update_provider_usage_status(
                provider_usage_id,
                "completed",
                actual_input_tokens=actual_input_tokens,
                actual_output_tokens=actual_output_tokens,
                actuals_unavailable=0
                if actual_input_tokens is not None or actual_output_tokens is not None
                else 1,
            )

            return CloudModelResponse(
                provider=provider_name,
                model=provider.model,
                response_text=response_text,
                provider_usage_id=provider_usage_id,
                provider_call_usage_id=provider_call_usage_id,
            )

        if last_error and last_error.endswith("_api_key_env_var_not_set"):
            raise CloudCredentialsError(last_error)
        raise CloudCascadeCallError(last_error or "cloud_cascade_no_provider_succeeded")

    def record_dummy_local_response(
        self,
        task_id: int,
        session_id: int,
        endpoint: str,
        payload: dict[str, Any],
        response_text: str,
        status: str = "completed",
    ) -> DummyModelResponse:
        self.validate_endpoint(endpoint)
        prepared = self.prepare_payload(payload)

        provider_usage_id = record_provider_usage(
            session_id=session_id,
            task_id=task_id,
            provider="ollama_local",
            status=status,
            model=prepared["model"],
        )

        provider_call_usage_id = record_resource_usage(
            task_id=task_id,
            resource_type="provider_calls",
            amount=1,
            limit_value=None,
            status="unknown",
            details={
                "provider": "ollama_local",
                "endpoint": endpoint,
                "model": prepared["model"],
                "usage_source": "model_gateway_dummy_response",
            },
        )

        return DummyModelResponse(
            endpoint=endpoint,
            model=prepared["model"],
            response_text=response_text,
            provider_usage_id=provider_usage_id,
            provider_call_usage_id=provider_call_usage_id,
        )
