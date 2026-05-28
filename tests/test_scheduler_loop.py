from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from axiom.core.noop_task_executor import NoopTaskExecutionError
from axiom.core.scheduler_loop import run_scheduler_loop
from axiom.core.task_lifecycle_audit import audit_task_lifecycle
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


def create_pending_manifest_bound_task(
    session_id: int,
    task_type: str = "manual_noop",
) -> int:
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
                    f"chain-scheduler-loop-test-{task_type}",
                    "system_maintenance",
                    task_type,
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


def test_scheduler_loop_manual_override_completes_manual_noop_task_then_idles():
    session_id = create_fail_closed_session()
    task_id = create_pending_manifest_bound_task(session_id)

    result = run_scheduler_loop(
        session_id=session_id,
        max_ticks=3,
        allow_when_autonomous_blocked=True,
    )

    assert result.ticks_requested == 3
    assert result.ticks_run == 2
    assert result.stopped_reason == "idle"
    assert result.final_tick_status == "idle"
    assert result.execution_result is not None
    assert result.execution_result["task_id"] == task_id
    assert result.execution_result["completed"] is True
    assert result.execution_result["result_json"]["task_type"] == "manual_noop"
    assert result.tick_results[0]["execution_result"]["task_id"] == task_id

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status, result_json FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"
    stored_result = json.loads(row["result_json"])
    assert stored_result["executor"] == "noop_task_executor"
    assert stored_result["side_effects"] == "none"


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
    payload = json.loads(result.stdout)
    assert payload["execution_result"]["completed"] is True
    assert payload["execution_result"]["task_id"] == task_id

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "completed"


def test_scheduler_loop_rejects_automatic_execution_for_non_manual_noop_task():
    session_id = create_fail_closed_session()
    task_id = create_pending_manifest_bound_task(
        session_id,
        task_type="scheduler_loop_test",
    )

    with pytest.raises(
        NoopTaskExecutionError,
        match="Automatic execution only authorized for manual_noop tasks",
    ):
        run_scheduler_loop(
            session_id=session_id,
            max_ticks=3,
            allow_when_autonomous_blocked=True,
        )

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "running"


def test_scheduler_loop_completes_manual_noop_tasks_sequentially():
    session_id = create_fail_closed_session()
    first_task_id = create_pending_manifest_bound_task(session_id)
    second_task_id = create_pending_manifest_bound_task(session_id)

    result = run_scheduler_loop(
        session_id=session_id,
        max_ticks=2,
        allow_when_autonomous_blocked=True,
    )

    assert result.ticks_run == 2
    assert [tick["dispatched_task_id"] for tick in result.tick_results] == [
        first_task_id,
        second_task_id,
    ]
    assert [
        tick["execution_result"]["task_id"] for tick in result.tick_results
    ] == [first_task_id, second_task_id]

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT task_id, status
            FROM tasks
            WHERE task_id IN (?, ?)
            ORDER BY task_id
            """,
            (first_task_id, second_task_id),
        ).fetchall()

    assert [row["status"] for row in rows] == ["completed", "completed"]


def test_scheduler_loop_does_not_instantiate_gateways_for_manual_noop_execution():
    session_id = create_fail_closed_session()
    create_pending_manifest_bound_task(session_id)

    with (
        patch("axiom.gateways.model_gateway.ModelGateway") as model_gateway,
        patch("axiom.gateways.network_gateway.NetworkGateway") as network_gateway,
        patch("axiom.gateways.sandbox_gateway.SandboxGateway") as sandbox_gateway,
        patch("axiom.gateways.memory_gateway.MemoryGateway") as memory_gateway,
        patch("axiom.gateways.telegram_gateway.TelegramGateway") as telegram_gateway,
    ):
        result = run_scheduler_loop(
            session_id=session_id,
            max_ticks=1,
            allow_when_autonomous_blocked=True,
        )

    assert result.execution_result is not None
    model_gateway.assert_not_called()
    network_gateway.assert_not_called()
    sandbox_gateway.assert_not_called()
    memory_gateway.assert_not_called()
    telegram_gateway.assert_not_called()


def test_scheduler_loop_manual_noop_completion_preserves_lifecycle_audit():
    session_id = create_fail_closed_session()
    task_id = create_pending_manifest_bound_task(session_id)

    result = run_scheduler_loop(
        session_id=session_id,
        max_ticks=1,
        allow_when_autonomous_blocked=True,
    )

    assert result.execution_result is not None
    assert result.execution_result["task_id"] == task_id

    audit = audit_task_lifecycle(session_id=session_id)
    assert audit.passed is True
    assert audit.violations == []
