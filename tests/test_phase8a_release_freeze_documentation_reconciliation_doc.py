from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase8a_release_freeze_documentation_reconciliation.md"


def test_phase8a_doc_records_release_freeze_scope_and_current_proof():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 8A is a release-freeze/documentation-reconciliation slice.",
        "Phase 7 E2E readiness/passing is now recorded.",
        "acceptance_inventory_passed = true",
        "e2e_ready = true",
        "e2e_blockers = []",
        "final mapped acceptance run: 130 passed in 23.08s",
        "approved live classifier calibration run present",
        "current model fingerprint tied to approved calibration present",
        "safe-pass readiness enabled in latest session",
        "explicit operator approval material supplied",
    ]

    for phrase in required:
        assert phrase in text


def test_phase8a_doc_preserves_runtime_boundaries_and_non_goals():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "safe-pass readiness may be enabled for the bounded Phase 7 E2E path",
        "autonomous_operation_enabled remains false / 0",
        "scheduler-to-agent automation remains unauthorized",
        "scheduler-to-executor automation remains unauthorized",
        "live Telegram polling remains explicit/manual and not a default service",
        "terminal surfaces remain read-only unless backed by approved tools",
        "No feature work belongs in Phase 8A.",
        "Telegram polling startup or registration",
        "gateway authority changes",
    ]

    for phrase in required:
        assert phrase in text


def test_phase8a_doc_records_verification_commands_and_exit_criteria():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Set-Location C:\\axiom",
        ".\\venv\\Scripts\\Activate.ps1",
        "axiom-preflight",
        "axiom-phase7",
        "python tools\\run_phase7_acceptance.py --json",
        "python tools\\run_phase7_acceptance.py --run --include-e2e --operator-approved-e2e",
        "python tools\\audit_phase6_closeout.py",
        "python tools\\audit_agent_boundary.py",
        "python tools\\audit_telegram_gateway.py",
        "pytest tests -v",
        "no runtime feature work is included",
        "Any later runtime expansion requires a separately approved phase",
    ]

    for phrase in required:
        assert phrase in text
