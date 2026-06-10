"""Path normalization and blocked-path precedence for Level 2A."""

from __future__ import annotations

import re


class PathNormalizationError(ValueError):
    """Raised when a control-plane path cannot be safely normalized."""


_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:/")


def normalize_control_path(
    raw_path: str,
    anchors: dict[str, str],
    *,
    windows_casefold: bool = True,
    internally_resolved_absolute: bool = False,
) -> str:
    if not isinstance(raw_path, str) or not raw_path:
        raise PathNormalizationError("path must be a non-empty string")

    path = raw_path.replace("\\", "/")
    token = None
    for candidate in sorted(anchors, key=len, reverse=True):
        if path == candidate or path.startswith(candidate + "/"):
            token = candidate
            break
    if token is not None:
        base = anchors[token].replace("\\", "/").rstrip("/")
        suffix = path[len(token) :].lstrip("/")
        path = f"{base}/{suffix}" if suffix else base
    elif path.startswith("/") or _DRIVE_PATTERN.match(path):
        if not internally_resolved_absolute:
            raise PathNormalizationError("unanchored absolute path rejected")
    else:
        raise PathNormalizationError("path must start with an approved workspace token")

    if _DRIVE_PATTERN.match(path) and not internally_resolved_absolute:
        raise PathNormalizationError("drive-letter path rejected")

    segments = [segment for segment in path.split("/") if segment != ""]
    if any(segment in {".", ".."} for segment in segments):
        raise PathNormalizationError("traversal or current-directory segment rejected")

    normalized = "/" + "/".join(segments)
    if windows_casefold:
        normalized = normalized.lower()
    return normalized.rstrip("/") if normalized != "/" else normalized


def _matches(candidate: str, blocked: str) -> bool:
    blocked = blocked.rstrip("/")
    candidate = candidate.rstrip("/")
    return candidate == blocked or candidate.startswith(blocked + "/")


def path_is_blocked(path: str, blocked_paths: list[str] | tuple[str, ...]) -> bool:
    return any(_matches(path, blocked) for blocked in blocked_paths)


def enforce_allowed_not_blocked(path: str, allowed_paths: list[str], blocked_paths: list[str]) -> bool:
    if path_is_blocked(path, blocked_paths):
        return False
    return any(_matches(path, allowed) for allowed in allowed_paths)
