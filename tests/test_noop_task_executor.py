from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from axiom.core.noop_task_executor import (
    NoopTaskExecutionError,
    complete_running_noop_task,
    execute_noop_task,
)
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


def create_task(
    session_id: int,
    status: str = "pending",
    manifest_id: str | None = "security.tool_capability_map.v1",
) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status, manifest_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    "chain-noop-executor-test",
                    "system_maintenance",
                    "noop_executor_test",
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_noop_executor_completes_manifest_bound_pending_task():
    session_id = create_session()
    task_id = create_task(session_id)

    result = execute_noop_task(task_id)

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.started is True
    assert result.completed is True
    assert result.start_heartbeat_id > 0
    assert result.completion_heartbeat_id > 0
    assert result.result_text == "No-op task execution completed."
    assert result.result_json["executor"] == "noop_task_executor"
    assert result.result_json["side_effects"] == "none"
    assert result.result_json["tools_used"] == []
    assert result.result_json["model_calls"] == []
    assert result.result_json["network_calls"] == []
    assert result.result_json["sandbox_calls"] == []

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, result_text, result_json
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"
    assert row["result_text"] == "No-op task execution completed."

    stored_json = json.loads(row["result_json"])
    assert stored_json["executor"] == "noop_task_executor"
    assert stored_json["side_effects"] == "none"


def test_noop_executor_rejects_missing_task():
    with pytest.raises(NoopTaskExecutionError, match="Task not found"):
        execute_noop_task(999999)


def test_noop_executor_rejects_non_pending_task():
    session_id = create_session()
    task_id = create_task(session_id, status="completed")

    with pytest.raises(NoopTaskExecutionError, match="requires pending task"):
        execute_noop_task(task_id)


def test_noop_executor_rejects_task_without_manifest():
    session_id = create_session()
    task_id = create_task(session_id, manifest_id=None)

    with pytest.raises(NoopTaskExecutionError, match="requires manifest-bound task"):
        execute_noop_task(task_id)


def test_execute_noop_task_cli_completes_task():
    session_id = create_session()
    task_id = create_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/execute_noop_task.py",
            str(task_id),
            "--manual-test-override",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["completed"] is True
    assert payload["task_id"] == task_id

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"


def test_execute_noop_task_cli_rejects_non_pending_task():
    session_id = create_session()
    task_id = create_task(session_id, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "tools/execute_noop_task.py",
            str(task_id),
            "--manual-test-override",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["executed"] is False
    assert "requires pending task" in payload["error"]
    
    
def test_execute_noop_task_cli_blocks_without_manual_test_override_when_autonomous_blocked():
    session_id = create_session()
    task_id = create_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/execute_noop_task.py",
            str(task_id),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1

    payload = json.loads(result.stdout)
    assert payload["executed"] is False
    assert payload["error"] == "autonomous_readiness_not_available"
    assert payload["manual_test_override_required"] is True

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "pending"
    
    
def test_complete_running_noop_task_completes_already_running_task():
    session_id = create_session()
    task_id = create_task(session_id, status="running")

    result = complete_running_noop_task(task_id)

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.started is True
    assert result.completed is True
    assert result.start_heartbeat_id == 0
    assert result.completion_heartbeat_id > 0

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, result_text, result_json
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"
    assert row["result_text"] == "No-op task execution completed."

    payload = json.loads(row["result_json"])
    assert payload["executor"] == "noop_task_executor"
    assert payload["side_effects"] == "none"