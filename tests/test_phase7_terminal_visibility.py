from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase7_terminal_visibility.md"
MODULE = ROOT / "ui" / "terminal" / "modules" / "60-phase7.ps1"
DOCTOR = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
DOCS = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
HELP = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase7d_terminal_module_is_report_only():
    text = MODULE.read_text(encoding="utf-8")

    required = [
        "function axiom-phase7",
        "tools\\run_phase7_acceptance.py', '--json",
        "tools\\audit_phase7_e2e_gate.py', '--json",
        "acceptance/gate reports only; no E2E execution",
        "approved classifier calibration run",
        "explicit operator approval for full-goal E2E",
    ]
    for phrase in required:
        assert phrase in text

    forbidden = [
        "--include-e2e",
        "--operator-approved-e2e",
        "--write-db",
        "register_model_fingerprint.py",
        "safe-pass enabled",
    ]
    for phrase in forbidden:
        assert phrase not in text

    assert 'Write-AxiomUiLine ""' not in text


def test_phase7d_doc_records_terminal_visibility_boundary():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "axiom-phase7",
        "ui\\terminal\\modules\\60-phase7.ps1",
        "python tools\\run_phase7_acceptance.py --json",
        "python tools\\audit_phase7_e2e_gate.py --json",
        "runner executed: false",
    ]
    for phrase in required:
        assert phrase in text


def test_phase7d_terminal_registry_docs_help_and_doctor_are_wired():
    doctor = DOCTOR.read_text(encoding="utf-8")
    docs = DOCS.read_text(encoding="utf-8")
    help_text = HELP.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert "60-phase7.ps1" in doctor
    assert "axiom-phase7" in doctor
    assert "phase7-terminal-visibility" in docs
    assert "phase7-terminal-module" in docs
    assert "axiom-phase7             Phase 7 acceptance/E2E gate panel" in help_text

    commands = {entry["name"]: entry for entry in registry["commands"]}
    command = commands["axiom-phase7"]
    assert command["category"] == "state_visibility"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["status"] == "implemented"
