from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY_GATE = ROOT / "docs" / "phase6.md"
ROADMAP = ROOT / "docs" / "phase6.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"


def test_phase6_entry_gate_doc_records_required_scope_lock():
    text = ENTRY_GATE.read_text(encoding="utf-8")

    required = [
        "Phase 6A is the authorized entry-gate slice",
        "Jeremy explicitly authorizes the bounded slice",
        "Phase 5 agent boundary audit passes",
        "The proposed slice does not enable autonomous operation",
        "The proposed slice does not connect external chat or Telegram runtime",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6_entry_gate_doc_preserves_prohibitions():
    text = ENTRY_GATE.read_text(encoding="utf-8")

    prohibited = [
        "autonomous operation",
        "safe-pass enablement",
        "scheduler-to-agent automation",
        "scheduler-to-executor automation",
        "real model calls",
        "cloud cascade calls",
        "network fetches",
        "sandbox execution",
        "memory writes",
        "Telegram bot runtime",
        "external command ingestion",
        "agent task creation",
        "child task commits",
        "operator command execution from external adapters",
    ]

    for phrase in prohibited:
        assert phrase in text


def test_phase6_entry_gate_doc_records_command_taxonomy_and_denials():
    text = ENTRY_GATE.read_text(encoding="utf-8")

    approved = [
        "read_only_status",
        "read_only_audit",
        "read_only_queue_inspection",
        "read_only_task_inspection",
        "local_intent_record",
        "local_intent_reject",
        "local_intent_authorization_marker",
        "design_only_external_adapter",
    ]

    denied = [
        "autonomous_enablement",
        "safe_pass_enablement",
        "model_profile_promotion",
        "gateway_runtime_call",
        "network_runtime_call",
        "sandbox_runtime_call",
        "memory_write_runtime_call",
        "scheduler_start",
        "agent_execution",
        "external_command_execution",
    ]

    for phrase in approved + denied:
        assert phrase in text


def test_phase6_entry_gate_doc_records_rollback_and_verification():
    text = ENTRY_GATE.read_text(encoding="utf-8")

    required = [
        "remove docs\\phase6.md",
        "remove Phase 6A references from docs\\phase6.md",
        "remove phase6 from ui\\terminal\\modules\\52-docs.ps1",
        "python tools\\verify_foundation.py",
        "python tools\\audit_task_lifecycle.py",
        "python tools\\audit_task_execution.py",
        "python tools\\audit_policy_security.py",
        "python tools\\audit_agent_boundary.py",
        "pytest tests\\test_phase6_entry_gate_doc.py -v",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6_roadmap_and_terminal_docs_index_entry_gate():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs_module = DOCS_MODULE.read_text(encoding="utf-8")

    assert "docs\\phase6.md" in roadmap
    assert "phase6" in docs_module
    assert "docs\\phase6.md" in docs_module


