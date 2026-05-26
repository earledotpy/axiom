from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from axiom.core.manifest_binder import ManifestBinder, ManifestValidationError


ROOT = Path(__file__).resolve().parents[1]
POLICY_ROOT = ROOT / "axiom" / "policy"
MANIFEST_SCHEMA = POLICY_ROOT / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = POLICY_ROOT / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = POLICY_ROOT / "security_artifacts" / "tool_capability_map.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def binder() -> ManifestBinder:
    return ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)


def base_role_manifest() -> dict:
    return {
        "schema_version": "axiom.manifest.v1",
        "manifest_type": "role",
        "manifest_id": "role.test.v1",
        "manifest_version": "1.0.0",
        "approved_by_panel_version": "test",
        "description": "Test role manifest.",
        "role": {
            "role_name": "test",
            "role_tier": "system",
            "allowed_task_classes": ["system_maintenance"],
            "may_create_child_tasks": False,
            "may_commit_task_tree": False,
        },
        "budget_policy": {
            "max_estimated_input_tokens": 0,
            "max_estimated_output_tokens": 0,
            "max_provider_calls": 0,
            "max_wall_clock_seconds": 30,
        },
        "allowed_capabilities": {
            "model": {
                "allow_model_calls": False,
                "allowed_provider_groups": [],
                "allow_local_classifier": False,
            },
            "task_queue": {
                "read_scope": "assigned_task",
                "write_scope": "own_result",
                "may_create_tasks": False,
                "may_update_own_result": True,
                "may_update_other_tasks": False,
            },
            "filesystem": {
                "read": False,
                "write": False,
                "allowed_roots": [],
            },
            "operator_control": {
                "allowed_commands": [],
            },
        },
        "allowed_tools": [],
        "forbidden_tools": [],
        "network_policy": {
            "mode": "deny_all",
            "allowlist": [],
            "denylist": [
                {
                    "scheme": "*",
                    "host": "*",
                    "port": "*",
                    "path_prefix": "*",
                    "methods": ["*"],
                    "reason": "No network access is allowed.",
                }
            ],
            "redirect_policy": "deny",
            "timeout_seconds": 0,
            "max_response_bytes": 0,
        },
        "sandbox_policy": {
            "allowed": False,
            "max_ram_mb": 0,
            "max_wall_clock_seconds": 0,
            "network_access": "denied",
        },
        "memory_policy": {
            "read": False,
            "write": False,
            "max_query_results": 0,
            "write_requires_dedupe": True,
        },
        "audit_policy": {
            "log_task_id": True,
            "log_manifest_id": True,
            "log_tool_calls": True,
            "log_policy_denials": True,
        },
    }


def base_operator_manifest() -> dict:
    manifest = base_role_manifest()
    del manifest["role"]
    manifest.update(
        {
            "manifest_type": "operator_control",
            "manifest_id": "operator.status.v1",
            "description": "Test operator status manifest.",
            "operator_command": {
                "command_name": "status",
                "telegram_aliases": ["/status"],
                "creates_task": False,
                "created_task_class": "operator_control",
                "allowed_when_autonomous_disabled": True,
                "allowed_when_safe_pass_disabled": True,
                "effect_class": "read_only",
            },
            "authorization_policy": {
                "telegram_operator_whitelist_required": True,
                "capability_token_required": True,
                "requires_active_session": True,
            },
            "allowed_tools": ["session_controller.status"],
        }
    )
    manifest["budget_policy"]["max_wall_clock_seconds"] = 30
    manifest["allowed_capabilities"]["operator_control"]["allowed_commands"] = [
        "status"
    ]
    return manifest


def test_manifest_binder_verifies_file_integrity(tmp_path: Path):
    path = tmp_path / "artifact.json"
    path.write_text('{"ok": true}', encoding="utf-8")
    expected_sha = ManifestBinder.sha256_file(path)

    actual_sha = ManifestBinder.verify_file_integrity(path, expected_sha)

    assert actual_sha == expected_sha


def test_manifest_binder_fails_closed_on_sha_mismatch(tmp_path: Path):
    path = tmp_path / "artifact.json"
    path.write_text('{"ok": true}', encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="SHA256 mismatch"):
        ManifestBinder.verify_file_integrity(path, "0" * 64)


def test_manifest_binder_fails_closed_on_manifest_schema_mismatch():
    manifest = base_role_manifest()
    del manifest["manifest_version"]

    with pytest.raises(ValidationError):
        binder().validate_manifest(manifest)


def test_manifest_binder_fails_closed_on_invalid_tool_id():
    manifest = base_role_manifest()
    manifest["allowed_tools"] = ["unknown.tool"]

    with pytest.raises(ValidationError):
        binder().validate_manifest(manifest)


def test_manifest_binder_fails_closed_on_operator_command_mismatch():
    manifest = base_operator_manifest()
    manifest["allowed_capabilities"]["operator_control"]["allowed_commands"] = [
        "resume"
    ]

    with pytest.raises(ManifestValidationError, match="allowed_commands must equal"):
        binder().validate_manifest(manifest)


def test_manifest_binder_fails_closed_on_allowed_forbidden_overlap():
    manifest = base_role_manifest()
    manifest["allowed_tools"] = ["model_gateway.call"]
    manifest["forbidden_tools"] = ["model_gateway.call"]

    with pytest.raises(ManifestValidationError, match="both allowed and forbidden"):
        binder().validate_manifest(manifest)


def test_manifest_binder_derives_effective_operator_capabilities():
    capabilities = binder().derive_effective_capabilities(base_operator_manifest())

    assert capabilities["effective_tool_ids"] == ["session_controller.status"]
    assert capabilities["effective_tools"]["session_controller.status"][
        "required_command"
    ] == "status"
    assert capabilities["effective_tools"]["session_controller.status"][
        "requires_manifest_type"
    ] == "operator_control"


def test_manifest_binder_derivation_excludes_ungranted_capability_source():
    manifest = base_role_manifest()
    manifest["allowed_tools"] = ["model_gateway.call"]
    manifest["allowed_capabilities"]["model"]["allow_model_calls"] = False

    capabilities = binder().derive_effective_capabilities(manifest)

    assert capabilities["allowed_tool_ids"] == ["model_gateway.call"]
    assert capabilities["effective_tool_ids"] == []
