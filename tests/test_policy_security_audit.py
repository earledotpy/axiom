from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import axiom.core.policy_security_audit as audit_module
from axiom.core.policy_security_audit import (
    EXPECTED_TOOL_MAP_ID,
    POLICY_ROOT,
    TOOL_MAP_PATH,
    audit_policy_security,
)
from axiom.persistence.db import get_connection


SOURCE_POLICY_ROOT = POLICY_ROOT


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seed_active_manifest_row(
    *,
    manifest_id: str,
    manifest_type: str,
    relative_path: str,
    file_path: Path,
    role_name: str | None = None,
    command_name: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                manifest_id,
                manifest_type,
                relative_path,
                sha256_file(file_path),
                "axiom.manifest.v1",
                "1.0.0",
                role_name,
                command_name,
                "test",
                "test_fixture",
            ),
        )


def seed_active_role_manifest(file_path: Path, manifest: dict) -> None:
    seed_active_manifest_row(
        manifest_id=manifest["manifest_id"],
        manifest_type="role",
        relative_path=f"policy/role_manifests/{file_path.name}",
        file_path=file_path,
        role_name=manifest["role"]["role_name"],
    )


def seed_active_operator_manifest(file_path: Path, manifest: dict) -> None:
    seed_active_manifest_row(
        manifest_id=manifest["manifest_id"],
        manifest_type="operator_control",
        relative_path=f"policy/operator_control_manifests/{file_path.name}",
        file_path=file_path,
        command_name=manifest["operator_command"]["command_name"],
    )


def update_active_tool_map_sha(file_path: Path) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET sha256 = ?
            WHERE manifest_id = ?
            """,
            (sha256_file(file_path), EXPECTED_TOOL_MAP_ID),
        )


def copy_policy_audit_root(tmp_path: Path, monkeypatch) -> Path:
    policy_root = tmp_path / "policy"
    (policy_root / "schemas").mkdir(parents=True)
    (policy_root / "security_artifacts").mkdir(parents=True)

    manifest_schema = policy_root / "schemas" / "manifest_schema.json"
    tool_map_schema = policy_root / "schemas" / "tool_capability_map_schema.json"
    tool_map = policy_root / "security_artifacts" / "tool_capability_map.json"

    shutil.copyfile(audit_module.MANIFEST_SCHEMA_PATH, manifest_schema)
    shutil.copyfile(audit_module.TOOL_MAP_SCHEMA_PATH, tool_map_schema)
    shutil.copyfile(audit_module.TOOL_MAP_PATH, tool_map)

    monkeypatch.setattr(audit_module, "POLICY_ROOT", policy_root)
    monkeypatch.setattr(audit_module, "MANIFEST_SCHEMA_PATH", manifest_schema)
    monkeypatch.setattr(audit_module, "TOOL_MAP_SCHEMA_PATH", tool_map_schema)
    monkeypatch.setattr(audit_module, "TOOL_MAP_PATH", tool_map)

    return policy_root


def complete_operator_manifest(allowed_commands: list[str]) -> dict:
    return {
        "schema_version": "axiom.manifest.v1",
        "manifest_type": "operator_control",
        "manifest_id": "operator.status.v1",
        "manifest_version": "1.0.0",
        "approved_by_panel_version": "test",
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
                "read_scope": "none",
                "write_scope": "none",
                "may_create_tasks": False,
                "may_update_own_result": False,
                "may_update_other_tasks": False,
            },
            "filesystem": {
                "read": False,
                "write": False,
                "allowed_roots": [],
            },
            "operator_control": {
                "allowed_commands": allowed_commands,
            },
        },
        "allowed_tools": ["session_controller.status"],
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


def test_policy_security_audit_passes_with_seeded_security_artifact():
    result = audit_policy_security()

    assert result.passed is True
    assert result.violations == []
    assert "active_tool_capability_map_row_exists" in result.checked
    assert "manifest_binder_initializes" in result.checked
    assert "policy_engine_initializes" in result.checked
    assert "tool_capability_map_semantic_contracts" in result.checked
    assert "active_policy_manifests_validate_schema_and_policy" in result.checked
    assert "active_policy_manifest_rows_match_payload_identity" in result.checked
    assert "role_manifests_do_not_declare_operator_control_commands" in result.checked
    assert "operator_control_manifests_bind_single_command" in result.checked
    assert "plan_injection_scanner_enum_domains_match_schema" in result.checked
    assert "plan_injection_scanner_return_contract_is_stable" in result.checked


def test_policy_security_audit_fails_closed_on_tool_map_required_command_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    tool_map_path = policy_root / "security_artifacts" / "tool_capability_map.json"
    tool_map = load_json(tool_map_path)
    tool_map["tools"]["session_controller.status"]["required_command"] = "resume"
    write_json(tool_map_path, tool_map)
    update_active_tool_map_sha(tool_map_path)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "tool_capability_map_semantic_contracts"
        and violation.reason == "session_controller_required_command_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_when_standard_tool_declares_command_binding(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    tool_map_path = policy_root / "security_artifacts" / "tool_capability_map.json"
    tool_map = load_json(tool_map_path)
    tool_map["tools"]["model_gateway.call"]["required_command"] = "status"
    tool_map["tools"]["model_gateway.call"][
        "requires_manifest_type"
    ] = "operator_control"
    write_json(tool_map_path, tool_map)
    update_active_tool_map_sha(tool_map_path)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "tool_capability_map_semantic_contracts"
        and violation.reason == "standard_tool_declares_required_command"
        for violation in result.violations
    )
    assert any(
        violation.check == "tool_capability_map_semantic_contracts"
        and violation.reason == "standard_tool_declares_manifest_type"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_standard_tool_source_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    tool_map_path = policy_root / "security_artifacts" / "tool_capability_map.json"
    tool_map = load_json(tool_map_path)
    tool_map["tools"]["filesystem.read"][
        "source"
    ] = "allowed_capabilities.filesystem.write"
    write_json(tool_map_path, tool_map)
    update_active_tool_map_sha(tool_map_path)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "tool_capability_map_semantic_contracts"
        and violation.reason == "standard_tool_source_mismatch"
        and violation.details["tool_id"] == "filesystem.read"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_standard_tool_additional_check_drift(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    tool_map_path = policy_root / "security_artifacts" / "tool_capability_map.json"
    tool_map = load_json(tool_map_path)
    tool_map["tools"]["network_gateway.fetch"]["additional_checks"] = [
        "mode_allowlist_only",
        "request_matches_allowlist",
    ]
    write_json(tool_map_path, tool_map)
    update_active_tool_map_sha(tool_map_path)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "tool_capability_map_semantic_contracts"
        and violation.reason == "standard_tool_additional_checks_mismatch"
        and violation.details["tool_id"] == "network_gateway.fetch"
        for violation in result.violations
    )


def test_policy_security_audit_validates_active_role_manifest_schema_and_policy():
    role_path = SOURCE_POLICY_ROOT / "role_manifests" / "system_maintenance_noop.v1.json"
    role_manifest = load_json(role_path)
    seed_active_role_manifest(role_path, role_manifest)

    result = audit_policy_security()

    assert result.passed is True
    assert result.violations == []


def test_policy_security_audit_fails_closed_on_active_role_policy_incomplete(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    role_manifest = load_json(
        SOURCE_POLICY_ROOT / "role_manifests" / "system_maintenance_noop.v1.json"
    )
    del role_manifest["budget_policy"]

    role_path = policy_root / "role_manifests" / "system_maintenance_noop.v1.json"
    write_json(role_path, role_manifest)
    seed_active_role_manifest(role_path, role_manifest)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_policy_manifests_validate_schema_and_policy"
        and violation.reason == "manifest_binder_validation_failed"
        for violation in result.violations
    )
    assert any(
        violation.check == "active_policy_manifests_validate_schema_and_policy"
        and violation.reason == "policy_manifest_incomplete"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_when_role_declares_operator_command(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    role_manifest = load_json(
        SOURCE_POLICY_ROOT / "role_manifests" / "system_maintenance_noop.v1.json"
    )
    role_manifest["allowed_capabilities"]["operator_control"]["allowed_commands"] = [
        "status"
    ]

    role_path = policy_root / "role_manifests" / "system_maintenance_noop.v1.json"
    write_json(role_path, role_manifest)
    seed_active_role_manifest(role_path, role_manifest)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check
        == "role_manifests_do_not_declare_operator_control_commands"
        and violation.reason == "role_manifest_declares_operator_control_commands"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_role_row_identity_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    role_manifest = load_json(
        SOURCE_POLICY_ROOT / "role_manifests" / "system_maintenance_noop.v1.json"
    )

    role_path = policy_root / "role_manifests" / "system_maintenance_noop.v1.json"
    write_json(role_path, role_manifest)
    seed_active_manifest_row(
        manifest_id=role_manifest["manifest_id"],
        manifest_type="role",
        relative_path=f"policy/role_manifests/{role_path.name}",
        file_path=role_path,
        role_name="wrong_role_name",
    )

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_policy_manifest_rows_match_payload_identity"
        and violation.reason == "role_name_row_payload_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_operator_row_identity_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    operator_manifest = complete_operator_manifest(["status"])
    operator_path = (
        policy_root / "operator_control_manifests" / "operator.status.v1.json"
    )
    write_json(operator_path, operator_manifest)
    seed_active_manifest_row(
        manifest_id=operator_manifest["manifest_id"],
        manifest_type="operator_control",
        relative_path=f"policy/operator_control_manifests/{operator_path.name}",
        file_path=operator_path,
        command_name="resume",
    )

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_policy_manifest_rows_match_payload_identity"
        and violation.reason == "command_name_row_payload_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_policy_manifest_directory_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    role_manifest = load_json(
        SOURCE_POLICY_ROOT / "role_manifests" / "system_maintenance_noop.v1.json"
    )

    wrong_path = (
        policy_root / "operator_control_manifests" / "system_maintenance_noop.v1.json"
    )
    write_json(wrong_path, role_manifest)
    seed_active_manifest_row(
        manifest_id=role_manifest["manifest_id"],
        manifest_type="role",
        relative_path=f"policy/operator_control_manifests/{wrong_path.name}",
        file_path=wrong_path,
        role_name=role_manifest["role"]["role_name"],
    )

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_policy_manifest_rows_match_payload_identity"
        and violation.reason == "role_manifest_registered_outside_role_directory"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_operator_command_binding_mismatch(
    tmp_path,
    monkeypatch,
):
    policy_root = copy_policy_audit_root(tmp_path, monkeypatch)
    operator_manifest = complete_operator_manifest(["resume"])
    operator_path = (
        policy_root / "operator_control_manifests" / "operator.status.v1.json"
    )
    write_json(operator_path, operator_manifest)
    seed_active_operator_manifest(operator_path, operator_manifest)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "operator_control_manifests_bind_single_command"
        and violation.reason == "operator_control_command_binding_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_tool_map_sha_mismatch():
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET sha256 = ?
            WHERE manifest_id = ?
            """,
            ("0" * 64, EXPECTED_TOOL_MAP_ID),
        )

    result = audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_manifest_files_exist_and_match_sha"
        and violation.reason == "sha256_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_on_missing_active_tool_map_row():
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET active = 0
            WHERE manifest_id = ?
            """,
            (EXPECTED_TOOL_MAP_ID,),
        )

    result = audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "active_tool_capability_map_row_exists"
        and violation.reason == "missing_active_tool_capability_map"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_when_security_event_index_missing():
    with get_connection() as conn:
        conn.execute("DROP INDEX idx_security_events_type")

    result = audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "security_events_table_supports_audit_coverage"
        and violation.reason == "security_events_missing_indexes"
        for violation in result.violations
    )


def test_policy_security_audit_fails_closed_when_security_event_severity_domain_drifts(
    tmp_path,
    monkeypatch,
):
    schema_sql = audit_module.SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    drifted_schema = schema_sql.replace(
        "'info', 'warning', 'critical'",
        "'info', 'warning'",
    )
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text(drifted_schema, encoding="utf-8")
    monkeypatch.setattr(audit_module, "SCHEMA_SQL_PATH", schema_path)

    result = audit_module.audit_policy_security()

    assert result.passed is False
    assert any(
        violation.check == "security_events_table_supports_audit_coverage"
        and violation.reason == "security_events_severity_domain_mismatch"
        for violation in result.violations
    )


def test_policy_security_audit_resolves_tool_map_path_inside_policy_root():
    relative = "policy/security_artifacts/tool_capability_map.json"
    resolved = POLICY_ROOT / relative.removeprefix("policy/")

    assert resolved == TOOL_MAP_PATH
    assert resolved.exists()
    assert len(sha256_file(resolved)) == 64
