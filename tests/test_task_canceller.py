import json

import pytest

from axiom.core.task_canceller import TaskCancellationError, cancel_task
from axiom.core.task_completer import complete_task
from axiom.core.task_failer import fail_task
from axiom.core.task_lifecycle_audit import audit_task_lifecycle
from axiom.core.task_starter import start_task
from axiom.persistence.db import get_connection, init_db


MANIFEST_ID = "security.tool_capability_map.v1"


def _create_session() -> int:
    init_db()
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO sessions
                (safe_pass_enabled, autonomous_operation_enabled,
                 safe_pass_disabled_reason)
                VALUES (0, 0, 'no_stored_profile')
                """
            ).lastrowid
        )


def _create_task(
    session_id: int,
    status: str = "pending",
    manifest_id: str | None = MANIFEST_ID,
    task_type: str = "canceller_test_task",
) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 manifest_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    f"canceller-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_cancel_pending_task_sets_cancelled_without_heartbeat():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        task_type="cancel_pending",
    )

    result = cancel_task(
        task_id,
        reason="unit_test_pending_cancel",
        details={"phase": "pending"},
    )

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.status == "cancelled"
    assert result.heartbeat_id is None
    assert result.details["previous_status"] == "pending"

    with get_connection() as conn:
        task = conn.execute(
            """
            SELECT status, cancel_requested, completed_at, error_info
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        heartbeat_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM scheduler_heartbeat
            WHERE active_task_id = ?
            """,
            (task_id,),
        ).fetchone()["count"]

    assert task["status"] == "cancelled"
    assert task["cancel_requested"] == 1
    assert task["completed_at"] is not None
    assert heartbeat_count == 0

    error_info = json.loads(task["error_info"])
    assert error_info["event_type"] == "task_cancelled"
    assert error_info["reason"] == "unit_test_pending_cancel"
    assert error_info["details"] == {"phase": "pending"}


def test_cancel_running_task_clears_heartbeat():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        task_type="cancel_running",
    )

    start_task(task_id)
    result = cancel_task(
        task_id,
        reason="unit_test_running_cancel",
        details={"phase": "running"},
    )

    assert result.status == "cancelled"
    assert result.heartbeat_id is not None
    assert result.details["previous_status"] == "running"

    with get_connection() as conn:
        task = conn.execute(
            """
            SELECT status, cancel_requested, completed_at, error_info
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        heartbeat = conn.execute(
            """
            SELECT active_task_id, active_chain_id, scheduler_state,
                   last_action, last_blocking_operation_type,
                   last_blocking_operation_completed_at
            FROM scheduler_heartbeat
            WHERE heartbeat_id = ?
            """,
            (result.heartbeat_id,),
        ).fetchone()

    assert task["status"] == "cancelled"
    assert task["cancel_requested"] == 1
    assert task["completed_at"] is not None

    error_info = json.loads(task["error_info"])
    assert error_info["reason"] == "unit_test_running_cancel"

    assert heartbeat["active_task_id"] is None
    assert heartbeat["active_chain_id"] is None
    assert heartbeat["scheduler_state"] == "ready"
    assert heartbeat["last_action"] == "task_cancelled"
    assert heartbeat["last_blocking_operation_type"] == "task_execution"
    assert heartbeat["last_blocking_operation_completed_at"] is not None


def test_cancel_task_rejects_completed_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    complete_task(task_id)

    with pytest.raises(TaskCancellationError) as exc:
        cancel_task(task_id)

    assert "task_not_cancellable" in str(exc.value)


def test_cancel_task_rejects_failed_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    fail_task(task_id)

    with pytest.raises(TaskCancellationError) as exc:
        cancel_task(task_id)

    assert "task_not_cancellable" in str(exc.value)


def test_cancel_task_rejects_already_cancelled_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    cancel_task(task_id)

    with pytest.raises(TaskCancellationError) as exc:
        cancel_task(task_id)

    assert "task_not_cancellable" in str(exc.value)


def test_cancel_running_task_keeps_lifecycle_audit_clean():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    cancel_task(task_id)

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []


def test_audit_ignores_historical_start_heartbeat_after_cancellation():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        task_type="historical_heartbeat_cancelled",
    )

    start_task(task_id)
    cancel_task(task_id)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT heartbeat_id, active_task_id, last_action
            FROM scheduler_heartbeat
            WHERE session_id = ?
            ORDER BY heartbeat_id
            """,
            (session_id,),
        ).fetchall()

    assert len(rows) >= 2
    assert rows[-2]["active_task_id"] == task_id
    assert rows[-2]["last_action"] == "task_started"
    assert rows[-1]["active_task_id"] is None
    assert rows[-1]["last_action"] == "task_cancelled"

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []