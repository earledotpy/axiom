from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.audit_phase9_closeout import audit_phase9_closeout


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase9.md"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
DOCTOR_MODULE = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase9_closeout_audit_passes_current_surface():
    result = audit_phase9_closeout()

    assert result.passed is True
    assert result.violation_count == 0
    assert result.command_registered is True
    assert result.preflight_registered is True
    assert result.runtime_guard_count == 6
    assert "phase9_no_unsafe_direct_shortcuts" in result.checked


def test_phase9_closeout_audit_cli_reports_json_pass():
    result = subprocess.run(
        [sys.executable, "tools/audit_phase9_closeout.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["violation_count"] == 0
    assert payload["command_registered"] is True
    assert payload["preflight_registered"] is True


def test_phase9_doc_records_closeout_scope_and_prohibitions():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 9 is closed",
        "automatic scheduler-to-executor integration for manual_noop tasks",
        "fail_closed_non_autonomous",
        "one-running-task invariant remains enforced",
        "verification commands: pytest tests",
        "no real model, cloud, network, sandbox, memory, Telegram, agent, or general task scheduler authority is enabled",
        "general scheduler-to-executor automation beyond `manual_noop`",
        "direct terminal shortcuts for dispatch, task start, no-op execution, or scheduler loop execution",
    ]

    for phrase in required:
        assert phrase in text


def test_phase9_terminal_registry_docs_help_and_preflight_are_wired():
    tools = TOOLS_MODULE.read_text(encoding="utf-8")
    doctor = DOCTOR_MODULE.read_text(encoding="utf-8")
    docs = DOCS_MODULE.read_text(encoding="utf-8")
    help_text = HELP_MODULE.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    commands = {command["name"]: command for command in registry["commands"]}

    assert "function axiom-phase9-closeout" in tools
    assert "tools\\audit_phase9_closeout.py" in tools
    assert "12. Phase 9 closeout audit" in tools
    assert "axiom-phase9-closeout" in doctor
    assert "tools\\audit_phase9_closeout.py" in doctor
    assert "phase9-closeout" in docs
    assert "phase9-closeout-audit-tool" in docs
    assert "axiom-phase9-closeout Phase 9 closeout audit" in help_text

    command = commands["axiom-phase9-closeout"]
    assert command["category"] == "verification"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["status"] == "implemented"
    assert command["backing_tools"] == ["tools/audit_phase9_closeout.py"]
    assert "tools/audit_phase9_closeout.py" in commands["axiom-preflight"]["backing_tools"]
