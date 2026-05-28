from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from tools.run_phase7_acceptance import (
    E2E_APPROVAL_EVENT_TYPE,
    E2E_OPERATOR_APPROVAL_TOKEN,
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
    canonical_test_paths,
    inspect_e2e_operator_approval,
    inspect_prerequisites,
)


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase7.md"
TOOL = ROOT / "tools" / "run_phase7_acceptance.py"
TERMINAL_TOOLS = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
TERMINAL_DOCTOR = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
TERMINAL_DOCS = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TERMINAL_HELP = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
TERMINAL_REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def create_prereq_db(path: Path, *, ready: bool = False) -> None:
    conn = sqlite3.connect(path)
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
            CREATE TABLE session_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            """
        )
        if ready:
            conn.execute(
                """
                INSERT INTO classifier_calibration_runs
                (calibration_run_id, model_name, ollama_host, threshold, passed,
                 false_positive_rate, false_negative_rate, approved_by_panel_version,
                 details_json)
                VALUES ('calibration.ready', 'qwen3:4b', 'http://localhost:11434',
                        0.8, 1, 0.0, 0.0, 'phase4_calibration_manual_approval',
                        '{"run_mode":"live","live":true}')
                """
            )
            conn.execute(
                """
                INSERT INTO model_profile_fingerprints
                (profile_label, model_name, ollama_host, thinking_mode,
                 calibration_run_id, is_current, registration_status)
                VALUES ('default', 'qwen3:4b', 'http://localhost:11434',
                        'disabled', 'calibration.ready', 1, 'current')
                """
            )
            conn.execute(
                """
                INSERT INTO sessions
                (safe_pass_enabled, safe_pass_disabled_reason, autonomous_operation_enabled)
                VALUES (1, NULL, 0)
                """
            )
        else:
            conn.execute(
                """
                INSERT INTO sessions
                (safe_pass_enabled, safe_pass_disabled_reason, autonomous_operation_enabled)
                VALUES (0, 'calibration_missing', 0)
                """
            )
        conn.commit()
    finally:
        conn.close()


def test_phase7b_canonical_test_paths_are_unique_and_present():
    paths = canonical_test_paths()

    assert len(paths) == len(set(paths))
    assert len(paths) == 18
    for path in paths:
        assert (ROOT / path).exists()


def test_phase7b_prerequisite_report_blocks_when_material_missing(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_prereq_db(db_path, ready=False)

    statuses = inspect_prerequisites(db_path)
    status_map = {item.name: item for item in statuses}

    assert status_map["classifier_calibration"].passed is False
    assert status_map["current_model_fingerprint"].passed is False
    assert status_map["safe_pass_readiness"].passed is False


def test_phase7b_prerequisite_report_passes_when_material_present(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_prereq_db(db_path, ready=True)

    statuses = inspect_prerequisites(db_path)
    status_map = {item.name: item for item in statuses}

    assert status_map["classifier_calibration"].passed is True
    assert status_map["current_model_fingerprint"].passed is True
    assert status_map["safe_pass_readiness"].passed is True


def test_phase7b_plan_refuses_e2e_when_blocked(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_prereq_db(db_path, ready=False)

    plan = build_phase7_acceptance_plan(
        include_e2e=True,
        operator_approved_e2e=False,
        db_path=db_path,
    )

    assert plan.passed is False
    assert plan.executed is False
    assert plan.e2e_ready is False
    assert E2E_TEST_PATH not in plan.command
    assert "explicit operator approval for full-goal E2E not supplied" in plan.e2e_blockers
    assert any(
        violation["reason"] == "e2e_requested_but_blocked"
        for violation in plan.violations
    )


def test_phase7b_plan_accepts_stored_e2e_operator_approval(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_prereq_db(db_path, ready=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO session_events (session_id, event_type, details_json)
            VALUES (1, ?, ?)
            """,
            (
                E2E_APPROVAL_EVENT_TYPE,
                json.dumps({"approval_token": E2E_OPERATOR_APPROVAL_TOKEN}),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    approval = inspect_e2e_operator_approval(db_path)
    plan = build_phase7_acceptance_plan(
        include_e2e=True,
        operator_approved_e2e=False,
        db_path=db_path,
    )
    isolated_gate_plan = build_phase7_acceptance_plan(
        include_e2e=True,
        operator_approved_e2e=False,
        use_stored_e2e_approval=False,
        db_path=db_path,
    )

    assert approval.passed is True
    assert plan.e2e_ready is True
    assert E2E_TEST_PATH in plan.command
    assert isolated_gate_plan.e2e_ready is False
    assert "explicit operator approval for full-goal E2E not supplied" in isolated_gate_plan.e2e_blockers


def test_phase7b_cli_json_reports_blocked_e2e_without_running_tests():
    result = subprocess.run(
        [sys.executable, "tools/run_phase7_acceptance.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in {0, 1}
    payload = json.loads(result.stdout)
    assert payload["acceptance_inventory_passed"] is True
    assert payload["executed"] is False
    assert payload["e2e_test_path"] == E2E_TEST_PATH
    assert "canonical_test_paths" in payload


def test_phase7b_doc_records_runner_and_approval_material():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "tools\\run_phase7_acceptance.py",
        "axiom-phase7-acceptance",
        "python tools\\run_phase7_acceptance.py --run",
        "classifier calibration approval material",
        "phase4_calibration_manual_approval",
        "python tools\\register_model_fingerprint.py",
    ]
    for phrase in required:
        assert phrase in text

    assert TOOL.exists()


def test_phase7b_terminal_surface_exposes_acceptance_runner():
    terminal_tools = TERMINAL_TOOLS.read_text(encoding="utf-8")
    doctor = TERMINAL_DOCTOR.read_text(encoding="utf-8")
    docs = TERMINAL_DOCS.read_text(encoding="utf-8")
    help_text = TERMINAL_HELP.read_text(encoding="utf-8")
    registry = json.loads(TERMINAL_REGISTRY.read_text(encoding="utf-8"))

    assert "function axiom-phase7-acceptance" in terminal_tools
    assert "tools\\run_phase7_acceptance.py" in terminal_tools
    assert "axiom-phase7-acceptance" in doctor
    assert "tools\\run_phase7_acceptance.py" in doctor
    assert "phase7-acceptance-runner" in docs
    assert "phase7-acceptance-runner-tool" in docs
    assert "axiom-phase7-acceptance Phase 7B acceptance runner/prerequisite gate" in help_text

    commands = {entry["name"]: entry for entry in registry["commands"]}
    command = commands["axiom-phase7-acceptance"]
    assert command["category"] == "verification"
    assert command["primary"] is True
    assert command["mutates_axiom_runtime"] is False
    assert command["risk"] == "low"
    assert command["backing_tools"] == ["tools/run_phase7_acceptance.py"]

