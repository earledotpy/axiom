from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tools.approve_phase7_e2e_readiness import approve_phase7_e2e_readiness
from tools.run_phase7_acceptance import (
    E2E_OPERATOR_APPROVAL_TOKEN,
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
)


def create_ready_db(path: Path, *, with_material: bool = True) -> None:
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
                thinking_mode_rule_version TEXT,
                calibration_run_id TEXT NOT NULL,
                is_current INTEGER NOT NULL,
                registration_status TEXT NOT NULL,
                registered_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            CREATE TABLE sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                safe_pass_enabled INTEGER NOT NULL,
                safe_pass_disabled_reason TEXT,
                safe_pass_disabled_at TEXT,
                safe_pass_alert_sent INTEGER NOT NULL DEFAULT 0,
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
            CREATE TABLE security_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                task_id INTEGER,
                event_type TEXT NOT NULL,
                reason TEXT,
                severity TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL DEFAULT '2026-05-25T00:00:00Z'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, safe_pass_disabled_reason, autonomous_operation_enabled)
            VALUES (0, 'calibration_missing', 0)
            """
        )
        if with_material:
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
                 thinking_mode_rule_version, calibration_run_id, is_current,
                 registration_status)
                VALUES ('default', 'qwen3:4b', 'http://localhost:11434',
                        'disabled', 'gateway_required_v1', 'calibration.ready',
                        1, 'current')
                """
            )
        conn.commit()
    finally:
        conn.close()


def test_phase7_readiness_approval_refuses_missing_material(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_ready_db(db_path, with_material=False)

    result = approve_phase7_e2e_readiness(
        approval_token=E2E_OPERATOR_APPROVAL_TOKEN,
        enable_safe_pass=True,
        approve_e2e=True,
        db_path=db_path,
    )

    assert result.passed is False
    assert result.safe_pass_enabled is False
    assert result.e2e_approval_recorded is False
    assert any(
        violation["check"] == "classifier_calibration"
        for violation in result.violations
    )


def test_phase7_readiness_approval_records_safe_pass_and_e2e_approval(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_ready_db(db_path, with_material=True)

    result = approve_phase7_e2e_readiness(
        approval_token=E2E_OPERATOR_APPROVAL_TOKEN,
        enable_safe_pass=True,
        approve_e2e=True,
        db_path=db_path,
    )
    plan = build_phase7_acceptance_plan(
        include_e2e=True,
        operator_approved_e2e=False,
        db_path=db_path,
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        session = conn.execute(
            "SELECT safe_pass_enabled, autonomous_operation_enabled FROM sessions WHERE session_id = 1"
        ).fetchone()
        approval = conn.execute(
            """
            SELECT details_json
            FROM session_events
            WHERE event_type = 'phase7_full_goal_e2e_approved'
            ORDER BY event_id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    assert result.passed is True
    assert result.safe_pass_enabled is True
    assert result.e2e_approval_recorded is True
    assert result.event_ids["full_goal_e2e_approval"] > 0
    assert session["safe_pass_enabled"] == 1
    assert session["autonomous_operation_enabled"] == 0
    assert approval is not None
    assert json.loads(approval["details_json"])["approval_token"] == E2E_OPERATOR_APPROVAL_TOKEN
    assert plan.e2e_ready is True
    assert E2E_TEST_PATH in plan.command


def test_phase7_readiness_approval_requires_explicit_flags(tmp_path):
    db_path = tmp_path / "axiom.db"
    create_ready_db(db_path, with_material=True)

    result = approve_phase7_e2e_readiness(
        approval_token="wrong",
        enable_safe_pass=False,
        approve_e2e=False,
        db_path=db_path,
    )

    reasons = {violation["reason"] for violation in result.violations}
    assert result.passed is False
    assert "invalid_phase7_e2e_approval_token" in reasons
    assert "enable_safe_pass_flag_required" in reasons
    assert "approve_e2e_flag_required" in reasons

