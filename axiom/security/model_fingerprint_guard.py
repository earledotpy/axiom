from __future__ import annotations

import re
from typing import Any


class ModelFingerprintGuard:
    """
    Minimal fingerprint guard foundation.

    The full fingerprint registration and profile verification flow is deferred
    until classifier calibration and model profile registration are available.
    """

    @staticmethod
    def _infer_thinking_mode(data: dict[str, Any]) -> str:
        """
        Arbiter rule:
        - Inspect only the Ollama /api/show `parameters` field.
        - Return "disabled" only when a line matches: think false
        - Otherwise return "unknown".
        """
        params = str(data.get("parameters", ""))

        if re.search(r"(?i)^\s*think\s+false\s*$", params, re.MULTILINE):
            return "disabled"

        return "unknown"
