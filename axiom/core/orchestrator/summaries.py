"""Deterministic operator summary formatting for offline Level 2A events."""

from __future__ import annotations

from typing import Iterable


def format_operator_summary(
    *,
    event_type: str,
    severity: str,
    title: str,
    primary_facts: Iterable[str],
    required_action: str,
    untrusted_agent_commentary: str | None = None,
) -> str:
    _require_text(event_type, "event_type")
    _require_text(severity, "severity")
    _require_text(title, "title")
    _require_text(required_action, "required_action")
    facts = list(primary_facts)
    if not facts or any(not isinstance(fact, str) or not fact for fact in facts):
        raise ValueError("ERR_INVALID_PRIMARY_FACTS")

    lines = [
        "AXIOM OPERATOR SUMMARY",
        f"event_type: {event_type}",
        f"severity: {severity}",
        f"title: {title}",
        "primary_summary:",
    ]
    lines.extend(f"- {fact}" for fact in facts)
    lines.extend(
        [
            f"required_action: {required_action}",
            "untrusted_agent_commentary:",
        ]
    )
    if untrusted_agent_commentary:
        lines.append(untrusted_agent_commentary)
    else:
        lines.append("<none>")
    return "\n".join(lines)


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"ERR_INVALID_{field.upper()}")
