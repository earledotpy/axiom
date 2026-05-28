from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from tools.audit_phase7_e2e_gate import audit_phase7_e2e_gate
from tools.run_phase7_acceptance import (
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
    inspect_prerequisites,
)


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase7.md"
TOOL = ROOT / "tools" / "audit_phase7_e2e_gate.py"
TERMINAL_TOOLS = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
TERMINAL_DOCTOR = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
TERMINAL_DOCS = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TERMINAL_HELP = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
TERMINAL_REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase7c_e2e_gate_audit_passes_and_names_operator_approval():
    result = audit_phase7_e2e_gate()

    assert result.passed is True
    assert "explicit_operator_approval_is_required" in result.checks
    assert "explicit operator approval for full-goal E2E not supplied" in result.e2e_blockers
    assert result.violations == []


def test_phase7c_cli_json_reports_pass():
    result = subprocess.run(
        [sys.executable, "tools/audit_phase7_e2e_gate.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["e2e_test_path"] == E2E_TEST_PATH
    assert "blocked_e2e_request_records_violation" in payload["checks"]


def test_phase7c_include_e2e_without_approval_does_not_execute_or_select_e2e():
    plan = build_phase7_acceptance_plan(
        run=True,
        include_e2e=True,
        operator_approved_e2e=False,
    )

    assert plan.executed is False
    assert E2E_TEST_PATH not in plan.command
    assert any(
        violation["reason"] == "e2e_requested_but_blocked"
        for violation in plan.violations
    )


def test_phase7c_unapproved_calibration_material_does_not_satisfy_gate(tmp_path):
    db_path = tmp_path / "axiom.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE classifier_calibration_runs (
                calibration_run_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                ollama_host TEXT NOT NULL,
                threshold REAL NOT NULL,
                passed INTEGER NOT NULL,
                false_positive_rate REAL,
                false_negative_rate REAL,
                approved_by_panel_version TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            CREATE TABLE model_profile_fingerprints (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_label TEXT NOT NULL,
                model_name TEXT NOT NULL,
                ollama_host TEXT NOT NULL,
                thinking_mode TEXT NOT NULL,
                calibration_run_id TEXT NOT NULL,
                is_current INTEGER NOT NULL,
                registration_status TEXT NOT NULL,
                registered_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            CREATE TABLE sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                safe_pass_enabled INTEGER NOT NULL,
                safe_pass_disabled_reason TEXT,
                autonomous_operation_enabled INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, model_name, ollama_host, threshold, passed,
             false_positive_rate, false_negative_rate, approved_by_panel_version)
            VALUES ('calibration.unapproved', 'qwen3:4b', 'http://localhost:11434',
                    0.8, 1, 0.0, 0.0, 'test')
            """
        )
        conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, thinking_mode,
             calibration_run_id, is_current, registration_status)
            VALUES ('default', 'qwen3:4b', 'http://localhost:11434',
                    'disabled', 'calibration.unapproved', 1, 'current')
            """
        )
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, safe_pass_disabled_reason, autonomous_operation_enabled)
            VALUES (1, NULL, 0)
            """
        )
        conn.commit()
    finally:
        conn.close()

    statuses = {item.name: item for item in inspect_prerequisites(db_path)}

    assert statuses["classifier_calibration"].passed is False
    assert statuses["current_model_fingerprint"].passed is False
    assert statuses["safe_pass_readiness"].passed is True


def test_phase7c_simulated_calibration_material_does_not_satisfy_gate(tmp_path):
    db_path = tmp_path / "axiom.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE classifier_calibration_runs (
                calibration_run_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                ollama_host TEXT NOT NULL,
                threshold REAL NOT NULL,
                passed INTEGER NOT NULL,
                false_positive_rate REAL,
                false_negative_rate REAL,
                approved_by_panel_version TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            CREATE TABLE model_profile_fingerprints (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_label TEXT NOT NULL,
                model_name TEXT NOT NULL,
                ollama_host TEXT NOT NULL,
                thinking_mode TEXT NOT NULL,
                calibration_run_id TEXT NOT NULL,
                is_current INTEGER NOT NULL,
                registration_status TEXT NOT NULL,
                registered_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            CREATE TABLE sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                safe_pass_enabled INTEGER NOT NULL,
                safe_pass_disabled_reason TEXT,
                autonomous_operation_enabled INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, model_name, ollama_host, threshold, passed,
             false_positive_rate, false_negative_rate, approved_by_panel_version,
             details_json)
            VALUES ('calibration.simulated', 'qwen3:4b', 'http://localhost:11434',
                    0.8, 1, 0.0, 0.0, 'phase4_calibration_manual_approval',
                    '{"run_mode":"simulation","live":false}')
            """
        )
        conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, thinking_mode,
             calibration_run_id, is_current, registration_status)
            VALUES ('default', 'qwen3:4b', 'http://localhost:11434',
                    'disabled', 'calibration.simulated', 1, 'current')
            """
        )
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, safe_pass_disabled_reason, autonomous_operation_enabled)
            VALUES (1, NULL, 0)
            """
        )
        conn.commit()
    finally:
        conn.close()

    statuses = {item.name: item for item in inspect_prerequisites(db_path)}

    assert statuses["classifier_calibration"].passed is False
    assert statuses["classifier_calibration"].detail == (
        "approved passing calibration run lacks live provenance"
    )
    assert statuses["current_model_fingerprint"].passed is False
    assert statuses["current_model_fingerprint"].detail == (
        "current model fingerprint calibration lacks live provenance"
    )
    assert statuses["safe_pass_readiness"].passed is True


def test_phase7c_doc_records_gate_scope_and_current_blockers():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "python tools\\audit_phase7_e2e_gate.py",
        "axiom-phase7-e2e-gate",
        "gate_status: blocked",
        "explicit operator approval for full-goal E2E not supplied",
        "docs\\phase7.md",
    ]
    for phrase in required:
        assert phrase in text

    assert TOOL.exists()


def test_phase7c_terminal_surface_exposes_e2e_gate_audit():
    terminal_tools = TERMINAL_TOOLS.read_text(encoding="utf-8")
    doctor = TERMINAL_DOCTOR.read_text(encoding="utf-8")
    docs = TERMINAL_DOCS.read_text(encoding="utf-8")
    help_text = TERMINAL_HELP.read_text(encoding="utf-8")
    registry = json.loads(TERMINAL_REGISTRY.read_text(encoding="utf-8"))

    assert "function axiom-phase7-e2e-gate" in terminal_tools
    assert "tools\\audit_phase7_e2e_gate.py" in terminal_tools
    assert "axiom-phase7-e2e-gate" in doctor
    assert "tools\\audit_phase7_e2e_gate.py" in doctor
    assert "phase7-e2e-gate-audit" in docs
    assert "phase7-e2e-gate-audit-tool" in docs
    assert "axiom-phase7-e2e-gate Phase 7C full-goal E2E gate audit" in help_text

    commands = {entry["name"]: entry for entry in registry["commands"]}
    command = commands["axiom-phase7-e2e-gate"]
    assert command["category"] == "verification"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["backing_tools"] == ["tools/audit_phase7_e2e_gate.py"]

