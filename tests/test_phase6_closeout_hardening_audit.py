from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.audit_phase6_closeout import audit_phase6_closeout


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6.md"
ROADMAP = ROOT / "docs" / "phase6.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "diagnostics" / "52-docs.ps1"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "utilities" / "20-axiom-tools.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "safety" / "90-safety-help.ps1"
DOCTOR_MODULE = ROOT / "ui" / "terminal" / "modules" / "diagnostics" / "49-doctor.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase6i_closeout_audit_passes_current_surface():
    result = audit_phase6_closeout()

    assert result.passed is True
    assert result.violation_count == 0
    assert "phase6_v113_alignment" in result.checked
    assert "phase6_operator_cognitive_load" in result.checked


def test_phase6i_closeout_audit_cli_reports_json_pass():
    result = subprocess.run(
        [sys.executable, "tools/audit_phase6_closeout.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["violation_count"] == 0


def test_phase6i_doc_records_alignment_hardening_and_deferred_work():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 6 is implemented through 6I",
        "Implement Telegram Gateway after operator whitelist mechanism is specified.",
        "Implement CommandParser and OperatorControlInserter.",
        "Enforce operator-control manifests and capability-token boundaries.",
        "terminal Telegram panel reads SQLite mode=ro only",
        "live Telegram polling",
        "webhook registration",
        "outbound Telegram replies",
        "terminal confirmation shortcut",
        "automatic execution after confirmation",
        "python tools\\audit_phase6_closeout.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6i_roadmap_and_terminal_registry_are_current():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs = DOCS_MODULE.read_text(encoding="utf-8")
    tools = TOOLS_MODULE.read_text(encoding="utf-8")
    help_text = HELP_MODULE.read_text(encoding="utf-8")
    doctor = DOCTOR_MODULE.read_text(encoding="utf-8")
    registry_text = REGISTRY.read_text(encoding="utf-8")
    registry = json.loads(registry_text)
    commands = {command["name"]: command for command in registry["commands"]}

    assert "Slices 6A through 6I are implemented" in roadmap
    assert "### 6I. Closeout And Hardening Audit" in roadmap
    assert "docs\\phase6.md" in roadmap
    assert "tools\\audit_phase6_closeout.py" in roadmap
    assert "phase6" in docs
    assert "phase6" in docs
    assert "function axiom-phase6-audit" in tools
    assert "8. Phase 6I closeout audit" in tools
    assert "axiom-phase6-audit" in help_text
    assert "axiom-phase6-audit" in doctor
    assert "axiom-phase6-audit" in commands
    assert commands["axiom-phase6-audit"]["mutates_axiom_runtime"] is False
    assert commands["axiom-phase6-audit"]["backing_tools"] == [
        "tools/audit_phase6_closeout.py"
    ]


