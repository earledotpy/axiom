from __future__ import annotations

import sqlite3
from pathlib import Path

from tools.run_phase7_acceptance import (
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
    inspect_prerequisites,
)


def create_ready_phase7_db(path: Path) -> None:
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
            """
        )
        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, model_name, ollama_host, threshold, passed,
             false_positive_rate, false_negative_rate, approved_by_panel_version,
             details_json)
            VALUES ('calibration.e2e.ready', 'qwen3:4b', 'http://localhost:11434',
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
                    'disabled', 'calibration.e2e.ready', 1, 'current')
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


def test_full_goal_flow_minimum_selects_e2e_only_after_local_gate_material(tmp_path):
    db_path = tmp_path / "axiom-ready.db"
    create_ready_phase7_db(db_path)

    prerequisites = {item.name: item for item in inspect_prerequisites(db_path)}
    assert prerequisites["classifier_calibration"].passed is True
    assert prerequisites["current_model_fingerprint"].passed is True
    assert prerequisites["safe_pass_readiness"].passed is True

    plan = build_phase7_acceptance_plan(
        run=False,
        include_e2e=True,
        operator_approved_e2e=True,
        db_path=db_path,
    )

    assert plan.passed is True
    assert plan.executed is False
    assert plan.e2e_ready is True
    assert plan.e2e_test_present is True
    assert plan.e2e_blockers == []
    assert E2E_TEST_PATH in plan.command


def test_full_goal_flow_minimum_preserves_operator_approval_gate(tmp_path):
    db_path = tmp_path / "axiom-ready.db"
    create_ready_phase7_db(db_path)

    plan = build_phase7_acceptance_plan(
        run=True,
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
