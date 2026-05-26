from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.audit_phase7_acceptance_inventory import (
    audit_phase7_acceptance_inventory,
    parse_acceptance_rows,
)


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase7_acceptance_inventory.md"
TOOL = ROOT / "tools" / "audit_phase7_acceptance_inventory.py"
TERMINAL_TOOLS = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
TERMINAL_DOCTOR = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
TERMINAL_DOCS = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TERMINAL_HELP = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
TERMINAL_REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase7a_parses_v113_canonical_acceptance_rows():
    rows = parse_acceptance_rows()
    row_ids = [row.row_id for row in rows]

    assert len(rows) == 108
    assert row_ids[0] == 1
    assert row_ids[-1] == 108
    assert row_ids == list(range(1, 109))


def test_phase7a_acceptance_inventory_audit_passes_and_names_blockers():
    result = audit_phase7_acceptance_inventory()

    assert result.passed is True
    assert result.acceptance_row_count == 108
    assert result.first_row_id == 1
    assert result.last_row_id == 108
    assert result.bucket_count == 8
    assert "classifier calibration approval material" in result.e2e_blockers
    assert "current model fingerprint registration" in result.e2e_blockers


def test_phase7a_acceptance_inventory_cli_reports_json_pass():
    result = subprocess.run(
        [sys.executable, "tools/audit_phase7_acceptance_inventory.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["acceptance_row_count"] == 108
    assert payload["violations"] == []


def test_phase7a_doc_records_inventory_map_gaps_and_audit():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "108 canonical MVP acceptance rows",
        "1..108",
        "Rows 84 and 85 require explicit under-30-second CLI timing evidence.",
        "tests/e2e/test_full_goal_flow_minimum.py",
        "classifier calibration approval material",
        "model fingerprint registration",
        "python tools\\audit_phase7_acceptance_inventory.py",
    ]

    for phrase in required:
        assert phrase in text

    assert TOOL.exists()


def test_phase7a_terminal_surface_exposes_read_only_inventory_audit():
    terminal_tools = TERMINAL_TOOLS.read_text(encoding="utf-8")
    doctor = TERMINAL_DOCTOR.read_text(encoding="utf-8")
    docs = TERMINAL_DOCS.read_text(encoding="utf-8")
    help_text = TERMINAL_HELP.read_text(encoding="utf-8")
    registry = json.loads(TERMINAL_REGISTRY.read_text(encoding="utf-8"))

    assert "function axiom-phase7-inventory" in terminal_tools
    assert "tools\\audit_phase7_acceptance_inventory.py" in terminal_tools
    assert "9. Phase 7A acceptance inventory audit" in terminal_tools
    assert "axiom-phase7-inventory" in doctor
    assert "tools\\audit_phase7_acceptance_inventory.py" in doctor
    assert "phase7-acceptance-inventory" in docs
    assert "phase7-acceptance-inventory-audit" in docs
    assert "axiom-phase7-inventory  Phase 7A v1.13 acceptance inventory audit" in help_text

    commands = {entry["name"]: entry for entry in registry["commands"]}
    command = commands["axiom-phase7-inventory"]
    assert command["category"] == "verification"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["backing_tools"] == ["tools/audit_phase7_acceptance_inventory.py"]
    assert "tools/audit_phase7_acceptance_inventory.py" in commands["axiom-preflight"]["backing_tools"]
