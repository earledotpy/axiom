from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from axiom.core.manual_noop_cycle import ManualNoopCycleError, run_manual_noop_cycle
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


def create_pending_noop_task(session_id: int) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status, manifest_id)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (
                    session_id,
                    "chain-manual-noop-cycle",
                    "system_maintenance",
                    "noop_executor_test",
                    "security.tool_capability_map.v1",
                ),
            ).lastrowid
        )


def test_manual_noop_cycle_requires_explicit_override():
    session_id = create_session()
    create_pending_noop_task(session_id)

    with pytest.raises(ManualNoopCycleError, match="requires explicit"):
        run_manual_noop_cycle(
            session_id=session_id,
            allow_when_autonomous_blocked=False,
        )


def test_manual_noop_cycle_dispatches_and_completes_pending_task():
    session_id = create_session()
    task_id = create_pending_noop_task(session_id)

    result = run_manual_noop_cycle(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.session_id == session_id
    assert result.task_id == task_id
    assert result.executed is True
    assert result.execution_result is not None
    assert result.execution_result["completed"] is True
    assert result.execution_audit["passed"] is True

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


def test_manual_noop_cycle_with_no_pending_task_does_not_execute():
    session_id = create_session()

    result = run_manual_noop_cycle(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.task_id is None
    assert result.executed is False
    assert result.execution_result is None
    assert result.execution_audit["passed"] is True


def test_manual_noop_cycle_cli_requires_override():
    session_id = create_session()
    create_pending_noop_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_manual_noop_cycle.py",
            str(session_id),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["cycle_completed"] is False
    assert payload["manual_test_override_required"] is True


def test_manual_noop_cycle_cli_dispatches_and_completes_with_override():
    session_id = create_session()
    task_id = create_pending_noop_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_manual_noop_cycle.py",
            str(session_id),
            "--allow-when-autonomous-blocked",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["executed"] is True
    assert payload["task_id"] == task_id
    assert payload["execution_audit"]["passed"] is True

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"