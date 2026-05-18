from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axiom.core.noop_task_executor import execute_noop_task
from axiom.core.task_execution_audit import audit_task_execution
from axiom.persistence.db import get_connection, init_db

ROOT = Path(__file__).resolve().parents[1]


def create_session() -> int:
    init_db()
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO sessions
                (safe_pass_enabled, autonomous_operation_enabled, safe_pass_disabled_reason)
                VALUES (0, 0, 'no_stored_profile')
                """
            ).lastrowid
        )


def create_noop_task(
    session_id: int,
    status: str = "pending",
    result_text: str | None = None,
    result_json: str | None = None,
) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 manifest_id, result_text, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    "chain-task-execution-audit",
                    "system_maintenance",
                    "noop_executor_test",
                    status,
                    "security.tool_capability_map.v1",
                    result_text,
                    result_json,
                ),
            ).lastrowid
        )


def valid_noop_result_json() -> str:
    return json.dumps(
        {
            "executor": "noop_task_executor",
            "task_id": 1,
            "task_type": "noop_executor_test",
            "task_class": "system_maintenance",
            "executed": True,
            "side_effects": "none",
            "tools_used": [],
            "model_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
        },
        sort_keys=True,
    )


def test_task_execution_audit_passes_for_latest_session_with_completed_noop_task():
    session_id = create_session()
    task_id = create_noop_task(session_id)

    execute_noop_task(task_id)

    result = audit_task_execution()

    assert result.passed is True
    assert result.scope == "latest_session"
    assert result.session_id == session_id
    assert result.checked_task_count == 1
    assert result.violations == []


def test_task_execution_audit_detects_running_noop_task():
    session_id = create_session()
    create_noop_task(session_id, status="running")

    result = audit_task_execution()

    assert result.passed is False
    assert result.checked_task_count == 1
    assert result.violations[0].reason == "noop_execution_task_still_running"


def test_task_execution_audit_detects_missing_result_text():
    session_id = create_session()
    create_noop_task(
        session_id,
        status="completed",
        result_text=None,
        result_json=valid_noop_result_json(),
    )

    result = audit_task_execution()

    assert result.passed is False
    assert any(v.reason == "missing_result_text" for v in result.violations)


def test_task_execution_audit_detects_invalid_result_json():
    session_id = create_session()
    create_noop_task(
        session_id,
        status="completed",
        result_text="done",
        result_json="{not json",
    )

    result = audit_task_execution()

    assert result.passed is False
    assert any(v.reason.startswith("invalid_result_json") for v in result.violations)


def test_task_execution_audit_detects_forbidden_side_effect_claims():
    session_id = create_session()
    payload = json.loads(valid_noop_result_json())
    payload["network_calls"] = ["https://example.com"]

    create_noop_task(
        session_id,
        status="completed",
        result_text="done",
        result_json=json.dumps(payload),
    )

    result = audit_task_execution()

    assert result.passed is False
    assert any(v.reason == "forbidden_network_calls_claimed" for v in result.violations)


def test_task_execution_audit_defaults_to_latest_session_only():
    old_session_id = create_session()
    create_noop_task(old_session_id, status="running")

    latest_session_id = create_session()

    result = audit_task_execution()

    assert result.passed is True
    assert result.session_id == latest_session_id
    assert result.checked_task_count == 0


def test_task_execution_audit_all_sessions_detects_historical_violations():
    old_session_id = create_session()
    create_noop_task(old_session_id, status="running")

    create_session()

    result = audit_task_execution(all_sessions=True)

    assert result.passed is False
    assert result.scope == "all_sessions"
    assert any(v.session_id == old_session_id for v in result.violations)


def test_audit_task_execution_cli_reports_clean_latest_session():
    session_id = create_session()
    task_id = create_noop_task(session_id)
    execute_noop_task(task_id)

    result = subprocess.run(
        [sys.executable, "tools/audit_task_execution.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "passed: True" in result.stdout
    assert "violations:" in result.stdout
    assert "- none" in result.stdout


def test_audit_task_execution_cli_json_reports_violation():
    session_id = create_session()
    create_noop_task(session_id, status="running")

    result = subprocess.run(
        [sys.executable, "tools/audit_task_execution.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1

    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert payload["violations"][0]["reason"] == "noop_execution_task_still_running"