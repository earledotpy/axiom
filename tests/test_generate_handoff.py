import json
import subprocess
import sys
from pathlib import Path

from tools.generate_handoff import build_handoff_markdown, write_handoff


ROOT = Path(__file__).resolve().parents[1]


def fake_snapshot() -> dict:
    return {
        "snapshot_created_at_utc": "2026-05-16T00-00-00Z",
        "project_root": "C:\\axiom",
        "pytest": {"last_known_target": "201 passed"},
        "bootstrap": {
            "passed": True,
            "operational_mode": "fail_closed_non_autonomous",
        },
        "autonomous_readiness": {
            "allowed": False,
            "blocking_reasons": [
                "no_current_trusted_model_profile",
                "safe_pass_disabled",
                "autonomous_operation_disabled",
            ],
        },
        "supervisor_health": {
            "checked": True,
            "reason": "supervisor_health_ok",
            "health": {
                "healthy": True,
                "scheduler_stale": False,
                "running_count": 0,
                "active_task_present": False,
                "active_task_status": None,
            },
        },
        "status": {},
        "foundation_verification": {
            "fail_closed_coherent": True,
        },
        "database_state": {
            "latest_model_profiles": [
                {
                    "profile_id": 19,
                    "profile_label": "default",
                    "model_name": "qwen3:4b",
                    "ollama_host": "http://localhost:11434",
                    "ollama_model_tag": "qwen3:4b",
                    "ollama_model_digest": "Qwen3",
                    "quantization": "Q4_K_M",
                    "parameter_size": "4.0B",
                    "model_family": "qwen3",
                    "model_format": "gguf",
                    "thinking_mode": "unknown",
                    "thinking_mode_rule_version": "gateway_required_v1",
                    "calibration_run_id": "pending_calibration",
                    "is_current": 0,
                    "registration_status": "candidate",
                    "registered_at": "2026-05-16T00:00:00Z",
                }
            ],
            "latest_sessions": [
                {
                    "session_id": 1,
                    "created_at": "2026-05-16T00:00:00Z",
                    "scheduler_status": "initializing",
                    "safe_pass_enabled": 0,
                    "safe_pass_disabled_reason": "no_stored_profile",
                    "safe_pass_disabled_at": "2026-05-16T00:00:00Z",
                    "autonomous_operation_enabled": 0,
                    "shutdown_requested": 0,
                }
            ],
        },
        "source_documents": {
            "phase3_policy_security_audit": {
                "path": "docs\\phase3.md",
                "exists": True,
                "purpose": "Read-only Phase 3 policy/security audit source handoff.",
            },
        },
        "execution_readiness": {
            "checked": True,
            "ready": False,
            "session_id": 1,
            "lifecycle_audit_passed": True,
            "execution_audit_passed": True,
            "supervisor_health_passed": True,
            "pending_manifest_bound_task_count": 0,
            "running_task_count": 0,
            "reasons": ["no_pending_tasks"],
        },
    }


def test_build_handoff_markdown_contains_core_state():
    markdown = build_handoff_markdown(fake_snapshot())

    assert "# AXIOM Project Handoff" in markdown
    assert "fail_closed_non_autonomous" in markdown
    assert "no_current_trusted_model_profile" in markdown
    assert "qwen3:4b" in markdown
    assert "candidate" in markdown
    assert "pytest tests -v" in markdown
    assert "## Source Documents" in markdown
    assert "docs\\phase3.md" in markdown
    
    assert "## Supervisor Health" in markdown
    assert "supervisor_health_ok" in markdown
    assert "Running count" in markdown
    assert "Active task present" in markdown

    assert "## Execution Readiness" in markdown
    assert "- Checked: `" in markdown
    assert "- Ready: `" in markdown
    assert "- Lifecycle audit passed: `" in markdown
    assert "- Execution audit passed: `" in markdown
    assert "- Supervisor health passed: `" in markdown
    assert "- Pending manifest-bound task count: `" in markdown
    assert "- Running task count: `" in markdown
    assert "Reasons:" in markdown


def test_write_handoff_creates_markdown_from_snapshot(tmp_path):
    snapshot_path = tmp_path / "project_state_snapshot_test.json"
    snapshot_path.write_text(json.dumps(fake_snapshot()), encoding="utf-8")

    output_path = write_handoff(snapshot_path=snapshot_path, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert "AXIOM Project Handoff" in output_path.read_text(encoding="utf-8")


def test_generate_handoff_cli_writes_file():
    result = subprocess.run(
        [sys.executable, "tools/generate_handoff.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "wrote AXIOM handoff:" in result.stdout


def test_handoff_ignores_model_profiles_not_matching_snapshot_profile_label():
    snapshot = {
        "profile_label": "default",
        "tool_version": "test",
        "snapshot_created_at_utc": "2026-05-17T00-00-00Z",
        "project_root": "C:\\axiom",
        "bootstrap_validation": {
            "passed": True,
            "operational_mode": "fail_closed_non_autonomous",
        },
        "autonomous_readiness": {
            "allowed": False,
            "blocking_reasons": ["no_current_trusted_model_profile"],
        },
        "foundation_verification": {
            "foundation_passed": True,
            "operational_mode": "fail_closed_non_autonomous",
            "supervisor_health": {
                "checked": True,
                "reason": "supervisor_health_ok",
                "healthy": True,
                "scheduler_stale": False,
                "running_count": 0,
                "active_task_present": False,
                "active_task_status": None,
            },
        },
        "supervisor_health": {
            "checked": True,
            "reason": "supervisor_health_ok",
            "healthy": True,
            "scheduler_stale": False,
            "running_count": 0,
            "active_task_present": False,
            "active_task_status": None,
        },
        "database_state": {
            "latest_model_profiles": [
                {
                    "profile_label": "not_default_test_profile",
                    "model_name": "qwen3:4b",
                    "registration_status": "current",
                    "is_current": 1,
                }
            ],
            "latest_sessions": [],
        },
    }

    markdown = build_handoff_markdown(snapshot)

    assert "not_default_test_profile" not in markdown
    assert "No model profile rows found." in markdown
    
    
def test_handoff_includes_task_execution_audit_section():
    snapshot = {
        "profile_label": "default",
        "tool_version": "test",
        "snapshot_created_at_utc": "2026-05-17T00-00-00Z",
        "project_root": "C:\\axiom",
        "pytest": {"last_known_target": "test"},
        "bootstrap_validation": {
            "passed": True,
            "operational_mode": "fail_closed_non_autonomous",
        },
        "autonomous_readiness": {
            "allowed": False,
            "blocking_reasons": ["no_current_trusted_model_profile"],
        },
        "foundation_verification": {
            "foundation_passed": True,
            "operational_mode": "fail_closed_non_autonomous",
            "fail_closed_coherent": True,
        },
        "supervisor_health": {
            "checked": True,
            "reason": "supervisor_health_ok",
            "health": {
                "healthy": True,
                "scheduler_stale": False,
                "running_count": 0,
                "active_task_present": False,
                "active_task_status": None,
            },
        },
        "task_execution_audit": {
            "checked": True,
            "passed": True,
            "scope": "latest_session",
            "session_id": 123,
            "checked_task_count": 0,
            "violation_count": 0,
        },
        "database_state": {
            "latest_model_profiles": [],
            "latest_sessions": [],
        },
    }

    markdown = build_handoff_markdown(snapshot)

    assert "## Task Execution Audit" in markdown
    assert "- Checked: `True`" in markdown
    assert "- Passed: `True`" in markdown
    assert "- Scope: `latest_session`" in markdown
    assert "- Violation count: `0`" in markdown


def test_handoff_includes_policy_security_audit_section():
    snapshot = {
        "profile_label": "default",
        "tool_version": "test",
        "snapshot_created_at_utc": "2026-05-17T00-00-00Z",
        "project_root": "C:\\axiom",
        "pytest": {"last_known_target": "test"},
        "bootstrap_validation": {
            "passed": True,
            "operational_mode": "fail_closed_non_autonomous",
        },
        "autonomous_readiness": {
            "allowed": False,
            "blocking_reasons": ["no_current_trusted_model_profile"],
        },
        "foundation_verification": {
            "foundation_passed": True,
            "operational_mode": "fail_closed_non_autonomous",
            "fail_closed_coherent": True,
        },
        "supervisor_health": {
            "checked": True,
            "reason": "supervisor_health_ok",
            "health": {
                "healthy": True,
                "scheduler_stale": False,
                "running_count": 0,
                "active_task_present": False,
                "active_task_status": None,
            },
        },
        "policy_security_audit": {
            "checked": True,
            "passed": True,
            "checked_count": 14,
            "violation_count": 0,
            "audit": {
                "checked": [
                    "tool_capability_map_semantic_contracts",
                    "active_policy_manifests_validate_schema_and_policy",
                    "role_manifests_do_not_declare_operator_control_commands",
                    "operator_control_manifests_bind_single_command",
                    "plan_injection_scanner_return_contract_is_stable",
                    "security_events_table_supports_audit_coverage",
                ],
            },
        },
        "source_documents": {
            "phase3_policy_security_audit": {
                "path": "docs\\phase3.md",
                "exists": True,
                "purpose": "Read-only Phase 3 policy/security audit source handoff.",
            },
        },
        "database_state": {
            "latest_model_profiles": [],
            "latest_sessions": [],
        },
    }

    markdown = build_handoff_markdown(snapshot)

    assert "## Policy Security Audit" in markdown
    assert "- Checked: `True`" in markdown
    assert "- Passed: `True`" in markdown
    assert "- Checked count: `14`" in markdown
    assert "Violation count" in markdown
    assert "tool_capability_map_semantic_contracts" in markdown
    assert "active_policy_manifests_validate_schema_and_policy" in markdown
    assert "role_manifests_do_not_declare_operator_control_commands" in markdown
    assert "operator_control_manifests_bind_single_command" in markdown
    assert "plan_injection_scanner_return_contract_is_stable" in markdown
    assert "security_events_table_supports_audit_coverage" in markdown
    assert "## Source Documents" in markdown
    assert "docs\\phase3.md" in markdown


def test_handoff_verification_commands_include_phase3_audits_and_session_note():
    markdown = build_handoff_markdown(fake_snapshot())

    assert "python tools\\verify_foundation.py" in markdown
    assert "python tools\\audit_task_lifecycle.py" in markdown
    assert "python tools\\audit_task_execution.py" in markdown
    assert "python tools\\audit_policy_security.py" in markdown
    assert "python tools\\supervisor_health_check.py <SESSION_ID>" in markdown
    assert "Do not type angle brackets literally" in markdown

