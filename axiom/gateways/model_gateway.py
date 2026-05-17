from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.persistence.repositories import record_provider_usage, record_resource_usage


class PolicyDeniedError(RuntimeError):
    pass


class ModelGatewayError(RuntimeError):
    pass


class ModelGatewayDisabledError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelGatewayConfig:
    host: str = "http://localhost:11434"
    model: str = "qwen3:4b"
    fingerprint_timeout_seconds: int = 5


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


class ModelGateway:
    """
    Fail-closed local ModelGateway foundation.

    This phase validates local Ollama payload policy and records dummy accounting.
    It does not perform HTTP requests to Ollama.
    """

    ALLOWED_ENDPOINTS = {"/api/chat", "/api/generate"}

    def __init__(self, config: ModelGatewayConfig | None = None):
        self.config = config or ModelGatewayConfig()

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
