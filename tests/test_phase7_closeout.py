from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.audit_phase7_closeout import audit_phase7_closeout


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase7.md"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
DOCTOR_MODULE = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase7e_closeout_audit_passes_current_surface():
    result = audit_phase7_closeout()

    assert result.passed is True
    assert result.violation_count == 0
    assert result.inventory_passed is True
    assert result.acceptance_report_passed is True
    assert result.acceptance_report_executed is False
    assert result.e2e_gate_passed is True
    assert result.e2e_gate_status in {"blocked", "ready"}
    assert "phase7_no_unsafe_shortcuts" in result.checked


def test_phase7e_closeout_audit_cli_reports_json_pass():
    result = subprocess.run(
        [sys.executable, "tools/audit_phase7_closeout.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["violation_count"] == 0
    assert payload["acceptance_report_executed"] is False


def test_phase7e_doc_records_closeout_state_and_remaining_material():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 7 is implemented through 7E",
        "108 canonical MVP acceptance rows",
        "runner executed: false",
        "gate_status: blocked",
        "explicit operator approval for full-goal E2E not supplied",
        "bounded E2E artifact now exists",
        "No state-changing enablement was performed",
        "python tools\\audit_phase7_closeout.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase7e_terminal_registry_docs_help_and_preflight_are_wired():
    tools = TOOLS_MODULE.read_text(encoding="utf-8")
    doctor = DOCTOR_MODULE.read_text(encoding="utf-8")
    docs = DOCS_MODULE.read_text(encoding="utf-8")
    help_text = HELP_MODULE.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    commands = {command["name"]: command for command in registry["commands"]}

    assert "function axiom-phase7-closeout" in tools
    assert "tools\\audit_phase7_closeout.py" in tools
    assert "11. Phase 7E closeout audit" in tools
    assert "axiom-phase7-closeout" in doctor
    assert "tools\\audit_phase7_closeout.py" in doctor
    assert "phase7-closeout" in docs
    assert "phase7-closeout-audit-tool" in docs
    assert "axiom-phase7-closeout Phase 7E closeout and hardening audit" in help_text

    command = commands["axiom-phase7-closeout"]
    assert command["category"] == "verification"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["backing_tools"] == ["tools/audit_phase7_closeout.py"]
    assert "tools/audit_phase7_closeout.py" in commands["axiom-preflight"]["backing_tools"]

