from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from axiom.core.governance_records import (
    DEFAULT_RECORD_ROOT,
    id_timestamp,
    list_records,
    load_record_by_id,
    slug,
    unique,
    utc_now,
    write_record,
)

COMMAND_MANIFEST_SCHEMA = "axiom.command_manifest.v0.1"
COMMAND_INTENT_SCHEMA = "axiom.command_intent.v0.1"


@dataclass(frozen=True)
class CommandParseResult:
    accepted: bool
    command: str | None
    manifest_id: str | None
    payload: dict[str, Any]
    rejection_reason: str | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CommandIntentResult:
    recorded: bool
    path: str | None
    intent: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_command_manifest(
    *,
    command: str,
    effect_class: str = "record_intent",
    allowed_payload_keys: Iterable[str] = (),
    requires_confirmation: bool = False,
    summary: str = "",
) -> dict[str, Any]:
    command = command.strip()
    if not command.startswith("/axiom:"):
        raise ValueError("governance command must use /axiom:* namespace")
    manifest_id = f"CMF-{id_timestamp()}-{slug(command)}"
    return {
        "schema": COMMAND_MANIFEST_SCHEMA,
        "manifest_id": manifest_id,
        "created_utc": utc_now(),
        "authority_status": "advisory_only",
        "command": command,
        "effect_class": effect_class.strip() or "record_intent",
        "allowed_payload_keys": unique(allowed_payload_keys),
        "requires_confirmation": bool(requires_confirmation),
        "runtime_action_allowed": False,
        "summary": summary.strip(),
        "status": "active",
        "lifecycle_state": "command_manifest",
    }


def create_command_manifest(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> CommandIntentResult:
    payload = build_command_manifest(**kwargs)
    path = write_record(record_root, "command_manifests", f"{payload['manifest_id']}.json", payload)
    return CommandIntentResult(recorded=True, path=str(path), intent=payload)


def list_command_manifests(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "command_manifests"):
        rows.append(
            {
                "path": str(path),
                "manifest_id": payload.get("manifest_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "command": payload.get("command", ""),
                "effect_class": payload.get("effect_class", ""),
                "authority_status": payload.get("authority_status", "unknown"),
                "status": payload.get("status", ""),
            }
        )
    return sorted(rows, key=lambda item: (item["command"], item["created_utc"]))


def load_command_manifest(manifest_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "command_manifests", manifest_id)


def _active_manifest_for_command(command: str, *, record_root: Path) -> dict[str, Any] | None:
    candidates = [
        payload
        for _, payload in list_records(record_root, "command_manifests")
        if payload.get("command") == command and payload.get("status", "active") == "active"
    ]
    return candidates[-1] if candidates else None


def parse_governance_command(
    raw: str | dict[str, Any],
    *,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> CommandParseResult:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return CommandParseResult(False, None, None, {}, "empty_command", {})
        try:
            parts = shlex.split(text, posix=False)
        except ValueError as exc:
            return CommandParseResult(False, None, None, {}, "command_parse_error", {"error": str(exc)})
        if not parts:
            return CommandParseResult(False, None, None, {}, "empty_command", {})
        command = parts[0]
        payload: dict[str, Any] = {}
        if len(parts) > 1:
            return CommandParseResult(False, command, None, {}, "command_payload_not_json_object", {"token_count": len(parts)})
    elif isinstance(raw, dict):
        command_value = raw.get("command")
        if not isinstance(command_value, str):
            return CommandParseResult(False, None, None, {}, "command_field_missing_or_invalid", {})
        command = command_value.strip()
        payload_value = raw.get("payload", {})
        if not isinstance(payload_value, dict):
            return CommandParseResult(False, command, None, {}, "command_payload_must_be_object", {})
        payload = payload_value
    else:
        return CommandParseResult(False, None, None, {}, "unsupported_input_type", {"input_type": type(raw).__name__})

    if not command.startswith("/axiom:"):
        return CommandParseResult(False, command, None, payload, "native_cli_command_not_axiom_authority", {})

    manifest = _active_manifest_for_command(command, record_root=record_root)
    if manifest is None:
        return CommandParseResult(False, command, None, payload, "unknown_axiom_command", {})

    allowed = set(manifest.get("allowed_payload_keys", []))
    extra = sorted(set(payload) - allowed)
    if extra:
        return CommandParseResult(False, command, manifest.get("manifest_id"), payload, "command_payload_key_not_allowed", {"extra_keys": extra})

    if manifest.get("runtime_action_allowed") is not False:
        return CommandParseResult(False, command, manifest.get("manifest_id"), payload, "runtime_action_not_allowed", {})

    return CommandParseResult(
        True,
        command,
        manifest.get("manifest_id"),
        payload,
        None,
        {
            "effect_class": manifest.get("effect_class"),
            "requires_confirmation": manifest.get("requires_confirmation", False),
            "runtime_action_executed": False,
            "ledger_written": False,
        },
    )


def record_command_intent(
    raw: str | dict[str, Any],
    *,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> CommandIntentResult:
    parsed = parse_governance_command(raw, record_root=record_root)
    intent_id = f"INT-{id_timestamp()}-{slug(parsed.command or 'REJECTED')}"
    payload = {
        "schema": COMMAND_INTENT_SCHEMA,
        "intent_id": intent_id,
        "created_utc": utc_now(),
        "authority_status": "advisory_only",
        "command": parsed.command or "",
        "manifest_id": parsed.manifest_id or "",
        "payload": parsed.payload,
        "parse_status": "accepted" if parsed.accepted else "rejected",
        "rejection_reason": parsed.rejection_reason,
        "details": parsed.details,
        "runtime_action_executed": False,
        "ledger_written": False,
        "status": "recorded" if parsed.accepted else "rejected",
        "lifecycle_state": "command_intent",
    }
    if not parsed.accepted:
        return CommandIntentResult(recorded=False, path=None, intent=payload)
    path = write_record(record_root, "command_intents", f"{intent_id}.json", payload)
    return CommandIntentResult(recorded=True, path=str(path), intent=payload)


def list_command_intents(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "command_intents"):
        rows.append(
            {
                "path": str(path),
                "intent_id": payload.get("intent_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "command": payload.get("command", ""),
                "manifest_id": payload.get("manifest_id", ""),
                "parse_status": payload.get("parse_status", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["intent_id"]))
