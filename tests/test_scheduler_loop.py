from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from axiom.core.scheduler_loop import run_scheduler_loop
from axiom.persistence.db import get_connection, init_db

ROOT = Path(__file__).resolve().parents[1]


def create_fail_closed_session() -> int:
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


def create_pending_manifest_bound_task(session_id: int) -> int:
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
                    "chain-scheduler-loop-test",
                    "system_maintenance",
                    "scheduler_loop_test",
                    "security.tool_capability_map.v1",
                ),
            ).lastrowid
        )


def test_scheduler_loop_blocks_by_default_when_autonomous_not_ready():
    session_id = create_fail_closed_session()
    create_pending_manifest_bound_task(session_id)

    result = run_scheduler_loop(
        session_id=session_id,
        max_ticks=3,
        allow_when_autonomous_blocked=False,
    )

    assert result.ticks_requested == 3
    assert result.ticks_run == 1
    assert result.stopped_reason == "blocked"
    assert result.final_tick_status == "blocked"

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status
            FROM tasks
            WHERE session_id = ?
            ORDER BY task_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    assert row["status"] == "pending"


def test_scheduler_loop_manual_override_dispatches_one_task_then_stops_running():
    session_id = create_fail_closed_session()
    task_id = create_pending_manifest_bound_task(session_id)

    result = run_scheduler_loop(
        session_id=session_id,
        max_ticks=3,
        allow_when_autonomous_blocked=True,
    )

    assert result.ticks_requested == 3
    assert result.ticks_run == 1
    assert result.final_tick_status in {"running", "dispatched"}

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "running"


def test_scheduler_loop_rejects_zero_max_ticks():
    session_id = create_fail_closed_session()

    with pytest.raises(ValueError):
        run_scheduler_loop(session_id=session_id, max_ticks=0)


def test_run_scheduler_loop_cli_blocks_without_override():
    session_id = create_fail_closed_session()
    create_pending_manifest_bound_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_loop.py",
            str(session_id),
            "--max-ticks",
            "3",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"stopped_reason": "blocked"' in result.stdout

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status
            FROM tasks
            WHERE session_id = ?
            ORDER BY task_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    assert row["status"] == "pending"


def test_run_scheduler_loop_cli_allows_manual_override():
    session_id = create_fail_closed_session()
    task_id = create_pending_manifest_bound_task(session_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_loop.py",
            str(session_id),
            "--max-ticks",
            "3",
            "--allow-when-autonomous-blocked",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "running"