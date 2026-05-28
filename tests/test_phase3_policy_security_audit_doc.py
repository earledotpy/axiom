from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase3.md"


def test_phase3_policy_security_audit_doc_exists():
    assert DOC.exists()


def test_phase3_policy_security_audit_doc_records_implemented_surface():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 3 is active",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "axiom/core/policy_security_audit.py",
        "tools/audit_policy_security.py",
        "tests/test_policy_security_audit.py",
        "tool_capability_map_semantic_contracts",
        "active_policy_manifests_validate_schema_and_policy",
        "active_policy_manifest_rows_match_payload_identity",
        "manifest row-to-payload identity",
        "standard tool source paths match expected policy objects",
        "standard tool additional_checks match expected enforcement checks",
        "standard tools do not declare operator-control command bindings",
        "session_controller tools bind one schema-valid operator command each",
        "role_manifests_do_not_declare_operator_control_commands",
        "operator_control_manifests_bind_single_command",
        "plan_injection_scanner_return_contract_is_stable",
        "security_events_table_supports_audit_coverage",
        "checked_count: 15",
        "violation_count: 0",
    ]

    for phrase in required:
        assert phrase in text


def test_phase3_policy_security_audit_doc_records_verification_commands():
    text = DOC.read_text(encoding="utf-8")

    required = [
        r"python -m py_compile axiom\core\policy_security_audit.py tests\test_policy_security_audit.py",
        r"pytest tests\test_policy_security_audit.py -v",
        "pytest tests -v",
        r"python tools\verify_foundation.py",
        r"python tools\audit_task_lifecycle.py",
        r"python tools\audit_task_execution.py",
        r"python tools\audit_policy_security.py",
        r"python tools\supervisor_health_check.py <SESSION_ID>",
        "Do not type angle brackets literally",
    ]

    for phrase in required:
        assert phrase in text


def test_phase3_policy_security_audit_doc_preserves_prohibited_boundaries():
    text = DOC.read_text(encoding="utf-8")

    prohibited = [
        "autonomous operation",
        "safe-pass enablement",
        "model profile promotion",
        "classifier calibration approval",
        "real Ollama /api/chat or /api/generate calls",
        "real cloud model/provider calls",
        "real NetworkGateway fetches",
        "real SandboxGateway process execution",
        "real MemoryGateway embedding writes/query",
        "Telegram/operator control execution",
        "agent layer",
        "persistent scheduler service",
        "automatic scheduler-to-executor integration",
        "terminal shortcuts that mutate runtime state directly",
        "register_manifests.py automatic execution",
    ]

    for phrase in prohibited:
        assert phrase in text

