from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6.md"
ROADMAP = ROOT / "docs" / "phase6.md"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
DOCTOR_MODULE = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
REPORT_MODULE = ROOT / "ui" / "terminal" / "modules" / "50-terminal-report.ps1"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
LEDGER_PANEL = ROOT / "ui" / "terminal" / "modules" / "58-operator-commands.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase6e_preflight_runs_operator_command_ledger_audit_read_only():
    tools = TOOLS_MODULE.read_text(encoding="utf-8")

    assert "function axiom-operator-command-audit" in tools
    assert "tools\\audit_operator_command_ledger.py" in tools
    assert "6. Phase 6 operator command ledger audit" in tools
    assert "axiom-operator-command-audit" in tools
    assert "record_operator_command_intent.py" not in tools


def test_phase6e_terminal_surfaces_are_indexed_without_mutating_shortcut():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    commands = {command["name"]: command for command in registry["commands"]}

    assert "axiom-operator-commands" in commands
    assert "axiom-operator-command-audit" in commands
    assert commands["axiom-operator-commands"]["mutates_axiom_runtime"] is False
    assert commands["axiom-operator-command-audit"]["mutates_axiom_runtime"] is False
    assert commands["axiom-operator-command-audit"]["backing_tools"] == [
        "tools/audit_operator_command_ledger.py"
    ]

    all_registry_text = REGISTRY.read_text(encoding="utf-8")
    assert "record_operator_command_intent.py" not in all_registry_text


def test_phase6e_help_doctor_report_docs_cover_operator_visibility():
    help_text = HELP_MODULE.read_text(encoding="utf-8")
    doctor_text = DOCTOR_MODULE.read_text(encoding="utf-8")
    report_text = REPORT_MODULE.read_text(encoding="utf-8")
    docs_text = DOCS_MODULE.read_text(encoding="utf-8")
    panel_text = LEDGER_PANEL.read_text(encoding="utf-8")

    assert "axiom-operator-command-audit" in help_text
    assert "axiom-operator-commands" in help_text
    assert "axiom-operator-command-audit" in doctor_text
    assert "tools\\audit_operator_command_ledger.py" in doctor_text
    assert "Operator control visibility" in report_text
    assert "preflight hook" in report_text
    assert "runtime_mutation_shortcut: none" in report_text
    assert "phase6" in docs_text
    assert "mode=ro" in panel_text
    assert "record_operator_command_intent.py" in panel_text


def test_phase6e_doc_and_roadmap_are_current():
    doc = DOC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")

    required_doc_phrases = [
        "axiom-operator-commands",
        "axiom-operator-command-audit",
        "axiom-preflight step 6",
        "python tools\\audit_operator_command_ledger.py",
        "No terminal command calls",
        "tools\\record_operator_command_intent.py",
    ]

    for phrase in required_doc_phrases:
        assert phrase in doc

    assert "Slices 6A through 6" in roadmap
    assert "docs\\phase6.md" in roadmap
    assert "preflight read-only audit hook" in roadmap


