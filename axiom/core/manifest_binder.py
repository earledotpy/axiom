from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ManifestValidationError(RuntimeError):
    pass


SESSION_CONTROLLER_TOOL_COMMANDS = {
    "session_controller.status": "status",
    "session_controller.cancel_current_chain": "cancel_current_chain",
    "session_controller.pause_after_current": "pause_after_current",
    "session_controller.resume": "resume",
    "session_controller.shutdown_after_current": "shutdown_after_current",
    "session_controller.run_classifier_validation": "run_classifier_validation",
    "session_controller.enable_autonomous": "enable_autonomous",
    "session_controller.reconcile_provider_usage": "reconcile_provider_usage",
}


class ManifestBinder:
    def __init__(self, manifest_schema_path: Path, tool_map_schema_path: Path, tool_map_path: Path):
        self.manifest_schema_path = Path(manifest_schema_path)
        self.tool_map_schema_path = Path(tool_map_schema_path)
        self.tool_map_path = Path(tool_map_path)
        self.manifest_validator = Draft202012Validator(self._load_json(self.manifest_schema_path))
        self.tool_map_validator = Draft202012Validator(self._load_json(self.tool_map_schema_path))
        self.tool_capability_map = self.load_and_validate_tool_capability_map()
        self.tool_ids = set(self.tool_capability_map["tools"].keys())

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def verify_file_integrity(cls, path: Path, expected_sha256: str) -> str:
        path = Path(path)
        if not path.exists():
            raise ManifestValidationError(f"Registered manifest file missing: {path}")

        if len(expected_sha256) != 64:
            raise ManifestValidationError("Expected SHA256 must be a 64-character hex digest")

        actual_sha256 = cls.sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise ManifestValidationError(
                f"SHA256 mismatch for {path}: expected {expected_sha256}, got {actual_sha256}"
            )

        return actual_sha256

    def load_and_validate_tool_capability_map(self) -> dict[str, Any]:
        tool_map = self._load_json(self.tool_map_path)
        self.tool_map_validator.validate(tool_map)
        self.validate_tool_capability_map_semantics(tool_map)
        return tool_map

    def validate_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_validator.validate(manifest)
        self.validate_operator_control_binding(manifest)
        self.validate_tool_ids(manifest)
        self.validate_allowed_forbidden_disjoint(manifest)

    def derive_effective_capabilities(self, manifest: dict[str, Any]) -> dict[str, Any]:
        self.validate_manifest(manifest)

        allowed_tools = set(manifest.get("allowed_tools", []))
        forbidden_tools = set(manifest.get("forbidden_tools", []))
        effective_tools: dict[str, dict[str, Any]] = {}

        for tool_id in sorted(allowed_tools - forbidden_tools):
            tool_entry = self.tool_capability_map["tools"][tool_id]
            source_value = self._resolve_source_path(manifest, tool_entry.get("source"))
            if self._capability_source_permits(tool_entry, source_value):
                effective_tools[tool_id] = {
                    "source": tool_entry.get("source"),
                    "required_command": tool_entry.get("required_command"),
                    "requires_manifest_type": tool_entry.get("requires_manifest_type"),
                    "additional_checks": tool_entry.get("additional_checks", []),
                }

        return {
            "manifest_id": manifest.get("manifest_id"),
            "manifest_type": manifest.get("manifest_type"),
            "allowed_tool_ids": sorted(allowed_tools),
            "forbidden_tool_ids": sorted(forbidden_tools),
            "effective_tool_ids": sorted(effective_tools),
            "effective_tools": effective_tools,
        }

    def validate_tool_ids(self, manifest: dict[str, Any]) -> None:
        for field_name in ("allowed_tools", "forbidden_tools"):
            for tool_id in manifest.get(field_name, []):
                if tool_id not in self.tool_ids:
                    raise ManifestValidationError(f"{tool_id} is not in loaded tool_capability_map")

    @staticmethod
    def validate_allowed_forbidden_disjoint(manifest: dict[str, Any]) -> None:
        allowed_tools = set(manifest.get("allowed_tools", []))
        forbidden_tools = set(manifest.get("forbidden_tools", []))
        overlap = allowed_tools & forbidden_tools
        if overlap:
            raise ManifestValidationError(
                f"Tools may not be both allowed and forbidden: {sorted(overlap)}"
            )

    @staticmethod
    def validate_operator_control_binding(manifest: dict[str, Any]) -> None:
        manifest_type = manifest["manifest_type"]
        allowed_commands = manifest["allowed_capabilities"]["operator_control"]["allowed_commands"]

        if manifest_type == "role":
            if allowed_commands != []:
                raise ManifestValidationError("Role manifests may not declare operator-control commands")
            return

        if manifest_type == "operator_control":
            command_name = manifest["operator_command"]["command_name"]
            if allowed_commands != [command_name]:
                raise ManifestValidationError(
                    "Operator-control manifest allowed_commands must equal [operator_command.command_name]"
                )
            return

        raise ManifestValidationError(f"Unknown manifest_type: {manifest_type}")

    @staticmethod
    def validate_tool_capability_map_semantics(tool_map: dict[str, Any]) -> None:
        tools = tool_map["tools"]
        for tool_id, expected_command in SESSION_CONTROLLER_TOOL_COMMANDS.items():
            entry = tools[tool_id]
            if entry["source"] != "allowed_capabilities.operator_control.allowed_commands":
                raise ManifestValidationError(f"{tool_id} must use operator_control allowed_commands source")
            if entry["required_command"] != expected_command:
                raise ManifestValidationError(f"{tool_id} required_command must be {expected_command}")
            if entry["requires_manifest_type"] != "operator_control":
                raise ManifestValidationError(f"{tool_id} must require operator_control manifest type")

    @staticmethod
    def _resolve_source_path(manifest: dict[str, Any], path: str | None) -> Any:
        if not path:
            return None

        current: Any = manifest
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)

        return current

    @staticmethod
    def _capability_source_permits(tool_entry: dict[str, Any], source_value: Any) -> bool:
        required_command = tool_entry.get("required_command")

        if required_command is not None:
            return isinstance(source_value, list) and required_command in source_value

        return bool(source_value)
