from __future__ import annotations

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

    def load_and_validate_tool_capability_map(self) -> dict[str, Any]:
        tool_map = self._load_json(self.tool_map_path)
        self.tool_map_validator.validate(tool_map)
        self.validate_tool_capability_map_semantics(tool_map)
        return tool_map

    def validate_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_validator.validate(manifest)
        self.validate_operator_control_binding(manifest)
        self.validate_tool_ids(manifest)

    def validate_tool_ids(self, manifest: dict[str, Any]) -> None:
        for field_name in ("allowed_tools", "forbidden_tools"):
            for tool_id in manifest.get(field_name, []):
                if tool_id not in self.tool_ids:
                    raise ManifestValidationError(f"{tool_id} is not in loaded tool_capability_map")

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
