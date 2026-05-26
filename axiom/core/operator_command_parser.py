from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from axiom.core.manifest_binder import ManifestBinder


ROOT = Path(__file__).resolve().parents[2]
POLICY_ROOT = ROOT / "axiom" / "policy"
MANIFEST_SCHEMA_PATH = POLICY_ROOT / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA_PATH = POLICY_ROOT / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP_PATH = POLICY_ROOT / "security_artifacts" / "tool_capability_map.json"
OPERATOR_MANIFEST_DIR = POLICY_ROOT / "operator_control_manifests"


@dataclass(frozen=True)
class OperatorCommandParseResult:
    accepted: bool
    command_name: str | None
    manifest_id: str | None
    source_text: str
    payload: dict[str, Any]
    rejection_reason: str | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperatorCommandParser:
    """
    Local-only Phase 6 operator command parser.

    The parser validates local operator-control manifests and returns structured
    intent data. It does not execute commands and does not write the command
    ledger; that belongs to a later Phase 6 slice.
    """

    def __init__(
        self,
        *,
        operator_manifest_dir: Path = OPERATOR_MANIFEST_DIR,
        manifest_schema_path: Path = MANIFEST_SCHEMA_PATH,
        tool_map_schema_path: Path = TOOL_MAP_SCHEMA_PATH,
        tool_map_path: Path = TOOL_MAP_PATH,
    ) -> None:
        self.operator_manifest_dir = Path(operator_manifest_dir)
        self.binder = ManifestBinder(
            Path(manifest_schema_path),
            Path(tool_map_schema_path),
            Path(tool_map_path),
        )
        self._commands, self._aliases = self._load_operator_manifests()

    def parse(self, raw: str | dict[str, Any]) -> OperatorCommandParseResult:
        if isinstance(raw, str):
            return self._parse_text(raw)

        if isinstance(raw, dict):
            return self._parse_object(raw)

        return self._deny(
            source_text=repr(raw),
            reason="unsupported_input_type",
            details={"input_type": type(raw).__name__},
        )

    def _parse_text(self, text: str) -> OperatorCommandParseResult:
        source_text = text
        text = text.strip()
        if not text:
            return self._deny(
                source_text=source_text,
                reason="empty_command",
            )

        try:
            parts = shlex.split(text, posix=False)
        except ValueError as exc:
            return self._deny(
                source_text=source_text,
                reason="command_parse_error",
                details={"error": str(exc)},
            )

        if len(parts) != 1:
            return self._deny(
                source_text=source_text,
                reason="command_payload_not_allowed",
                details={"token_count": len(parts)},
            )

        return self._validate_command(parts[0], source_text=source_text, payload={})

    def _parse_object(self, data: dict[str, Any]) -> OperatorCommandParseResult:
        source_text = json.dumps(data, sort_keys=True)
        command = data.get("command")
        payload = data.get("payload", {})

        if not isinstance(command, str) or not command.strip():
            return self._deny(
                source_text=source_text,
                reason="command_field_missing_or_invalid",
                details={"command": command},
            )

        if not isinstance(payload, dict):
            return self._deny(
                source_text=source_text,
                reason="command_payload_must_be_object",
                details={"payload_type": type(payload).__name__},
            )

        return self._validate_command(command, source_text=source_text, payload=payload)

    def _validate_command(
        self,
        raw_command: str,
        *,
        source_text: str,
        payload: dict[str, Any],
    ) -> OperatorCommandParseResult:
        command_key = raw_command.strip()
        command_name = self._aliases.get(command_key, command_key)
        manifest = self._commands.get(command_name)

        if manifest is None:
            return self._deny(
                source_text=source_text,
                reason="unknown_operator_command",
                details={"command": raw_command},
            )

        operator_command = manifest["operator_command"]
        if operator_command["effect_class"] != "read_only":
            return self._deny(
                source_text=source_text,
                reason="operator_command_not_read_only",
                details={
                    "command_name": command_name,
                    "effect_class": operator_command["effect_class"],
                },
            )

        if operator_command["creates_task"] is not False:
            return self._deny(
                source_text=source_text,
                reason="operator_command_creates_task",
                details={"command_name": command_name},
            )

        if payload:
            return self._deny(
                source_text=source_text,
                reason="command_payload_not_allowed",
                details={
                    "command_name": command_name,
                    "payload_keys": sorted(payload),
                },
            )

        return OperatorCommandParseResult(
            accepted=True,
            command_name=command_name,
            manifest_id=manifest["manifest_id"],
            source_text=source_text,
            payload={},
            rejection_reason=None,
            details={
                "effect_class": operator_command["effect_class"],
                "creates_task": operator_command["creates_task"],
                "allowed_tool": manifest["allowed_tools"][0],
                "runtime_action_executed": False,
                "ledger_written": False,
            },
        )

    def _load_operator_manifests(
        self,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        commands: dict[str, dict[str, Any]] = {}
        aliases: dict[str, str] = {}

        if not self.operator_manifest_dir.exists():
            return commands, aliases

        for path in sorted(self.operator_manifest_dir.glob("*.json")):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.binder.validate_manifest(manifest)

            if manifest["manifest_type"] != "operator_control":
                continue

            command_name = manifest["operator_command"]["command_name"]
            if command_name in commands:
                raise ValueError(f"Duplicate operator command manifest: {command_name}")

            commands[command_name] = manifest
            aliases[command_name] = command_name
            for alias in manifest["operator_command"].get("telegram_aliases", []):
                aliases[alias] = command_name

        return commands, aliases

    @staticmethod
    def _deny(
        *,
        source_text: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> OperatorCommandParseResult:
        return OperatorCommandParseResult(
            accepted=False,
            command_name=None,
            manifest_id=None,
            source_text=source_text,
            payload={},
            rejection_reason=reason,
            details=details or {},
        )
