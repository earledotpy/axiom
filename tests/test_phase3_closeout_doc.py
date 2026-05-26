from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase3_closeout.md"


def test_phase3_closeout_doc_exists():
    assert DOC.exists()


def test_phase3_closeout_doc_records_completed_phase3_surface():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 3 is closed",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "ManifestBinder JSON Schema validation",
        "ManifestBinder SHA256 verification",
        "ManifestBinder semantic validation",
        "ManifestBinder tool ID map validation",
        "ManifestBinder effective-capability derivation",
        "PolicyEngine seven-step tool authorization",
        "PlanInjectionScanner deterministic checks",
        "PlanInjectionScanner classifier-safe-pass path",
        "PlanInjectionScanner explicit return contract",
        "active_policy_manifest_rows_match_payload_identity",
        "standard tool source paths",
        "standard tool additional_checks",
        "checked_count: 15",
        "violation_count: 0",
        "369 passed",
    ]

    for phrase in required:
        assert phrase in text


def test_phase3_closeout_doc_records_verification_commands():
    text = DOC.read_text(encoding="utf-8")

    required = [
        r"python -m py_compile axiom\core\policy_security_audit.py",
        r"pytest tests\test_manifest_binder.py tests\test_policy_engine.py",
        "pytest tests -v",
        r"python tools\verify_foundation.py",
        r"python tools\audit_task_lifecycle.py",
        r"python tools\audit_task_execution.py",
        r"python tools\audit_policy_security.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase3_closeout_doc_preserves_prohibited_boundaries():
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
        "Telegram/operator control plane",
        "agent layer",
        "persistent scheduler service",
        "automatic scheduler-to-executor integration",
        "terminal shortcuts that mutate runtime state directly",
    ]

    for phrase in prohibited:
        assert phrase in text


def test_phase3_closeout_doc_records_phase4_entry_boundary():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "No Phase 3 implementation item remains before Phase 4",
        "Phase 4 must not begin until Jeremy explicitly authorizes",
        "ModelGateway cloud cascade requires provider/config approval",
        "MemoryGateway work must preserve sqlite-vec batch and database invariants",
        "NetworkGateway work requires Brave/free-tier approval before real fetches",
        "SandboxGateway work requires Windows Job Object specifics before real execution",
        "No real model, cloud, network, sandbox, memory, Telegram, agent, or scheduler authority is enabled by this closeout",
    ]

    for phrase in required:
        assert phrase in text
