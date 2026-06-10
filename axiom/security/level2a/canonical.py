"""RFC 8785-style JSON canonicalization for Level 2A payloads.

This implementation intentionally rejects floats. Level 2A mandate payloads are
defined as float-free so the canonical form can avoid IEEE 754 edge cases while
remaining deterministic for the supported JSON subset.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize(payload: Any) -> bytes:
    """Return canonical UTF-8 JSON bytes for a float-free JSON payload."""

    _reject_unsupported(payload)
    return _emit(payload).encode("utf-8")


def _reject_unsupported(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("ERR_FLOAT_NOT_ALLOWED")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("ERR_NON_STRING_JSON_KEY")
            _reject_unsupported(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsupported(item)
        return
    if value is None or isinstance(value, (str, bool, int)):
        return
    raise ValueError(f"ERR_UNSUPPORTED_JSON_VALUE:{type(value).__name__}")


def _emit(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_emit(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.append(f"{_emit(key)}:{_emit(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise ValueError(f"ERR_UNSUPPORTED_JSON_VALUE:{type(value).__name__}")
