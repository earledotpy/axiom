from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class OllamaPrereqError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaPrereqResult:
    host: str
    model: str
    reachable: bool
    tags_available: bool
    model_present: bool
    show_available: bool
    details_present: bool
    parameters_present: bool
    quantization_level: str | None
    profile_thinking_mode: str
    runtime_thinking_enforcement: str
    fingerprint_registration_ready: bool
    reason: str
    raw_show: dict[str, Any] | None = None


class OllamaPrereqInspector:
    """
    Read-only Ollama prerequisite inspector.

    This class does not call /api/generate or /api/chat.
    It does not mutate AXIOM database state.
    It only checks host/model readiness for later fingerprint registration.

    Important distinction:
    - profile_thinking_mode is inferred only from /api/show parameters.
    - runtime_thinking_enforcement is AXIOM's policy requirement when the profile
      does not persist an explicit think false setting.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen3:4b",
        timeout_seconds: int = 5,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def inspect(self) -> OllamaPrereqResult:
        tags = self._post_json("/api/tags", payload={})
        if tags is None:
            tags = self._get_json("/api/tags")

        if tags is None:
            return OllamaPrereqResult(
                host=self.host,
                model=self.model,
                reachable=False,
                tags_available=False,
                model_present=False,
                show_available=False,
                details_present=False,
                parameters_present=False,
                quantization_level=None,
                profile_thinking_mode="unknown",
                runtime_thinking_enforcement="unverified",
                fingerprint_registration_ready=False,
                reason="ollama_tags_unavailable",
            )

        model_names = self._extract_model_names(tags)
        model_present = self.model in model_names

        if not model_present:
            return OllamaPrereqResult(
                host=self.host,
                model=self.model,
                reachable=True,
                tags_available=True,
                model_present=False,
                show_available=False,
                details_present=False,
                parameters_present=False,
                quantization_level=None,
                profile_thinking_mode="unknown",
                runtime_thinking_enforcement="unverified",
                fingerprint_registration_ready=False,
                reason="model_not_present",
            )

        show = self._post_json("/api/show", payload={"model": self.model})

        if show is None:
            return OllamaPrereqResult(
                host=self.host,
                model=self.model,
                reachable=True,
                tags_available=True,
                model_present=True,
                show_available=False,
                details_present=False,
                parameters_present=False,
                quantization_level=None,
                profile_thinking_mode="unknown",
                runtime_thinking_enforcement="unverified",
                fingerprint_registration_ready=False,
                reason="ollama_show_unavailable",
            )

        details = show.get("details")
        parameters = show.get("parameters")
        quantization_level = None

        if isinstance(details, dict):
            quantization_level = details.get("quantization_level")

        profile_thinking_mode = self._infer_thinking_mode_from_parameters(parameters)

        if profile_thinking_mode == "disabled":
            runtime_thinking_enforcement = "profile_verified"
            fingerprint_registration_ready = True
        else:
            runtime_thinking_enforcement = "gateway_required"
            fingerprint_registration_ready = True

        return OllamaPrereqResult(
            host=self.host,
            model=self.model,
            reachable=True,
            tags_available=True,
            model_present=True,
            show_available=True,
            details_present=isinstance(details, dict),
            parameters_present=isinstance(parameters, str),
            quantization_level=quantization_level,
            profile_thinking_mode=profile_thinking_mode,
            runtime_thinking_enforcement=runtime_thinking_enforcement,
            fingerprint_registration_ready=fingerprint_registration_ready,
            reason="ollama_prerequisites_inspected",
            raw_show=show,
        )

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

    def _get_json(self, path: str) -> dict[str, Any] | None:
        url = f"{self.host}{path}"

        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _extract_model_names(tags: dict[str, Any]) -> set[str]:
        names: set[str] = set()

        for item in tags.get("models", []):
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            model = item.get("model")

            if isinstance(name, str):
                names.add(name)

            if isinstance(model, str):
                names.add(model)

        return names

    @staticmethod
    def _infer_thinking_mode_from_parameters(parameters: Any) -> str:
        if not isinstance(parameters, str):
            return "unknown"

        for line in parameters.splitlines():
            normalized = " ".join(line.strip().lower().split())
            if normalized == "think false":
                return "disabled"

        return "unknown"