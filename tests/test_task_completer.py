import json

import pytest

from axiom.core.task_completer import TaskCompletionError, complete_task
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
    task_type: str = "completer_test_task",
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
                    f"completer-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_complete_task_updates_running_task_and_writes_clear_heartbeat():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    result = complete_task(
        task_id,
        result_text="done",
        result_json={"ok": True},
    )

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.status == "completed"
    assert result.heartbeat_id > 0

    with get_connection() as conn:
        task = conn.execute(
            """
            SELECT status, completed_at, result_text, result_json
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

    assert task["status"] == "completed"
    assert task["completed_at"] is not None
    assert task["result_text"] == "done"
    assert json.loads(task["result_json"]) == {"ok": True}

    assert heartbeat["active_task_id"] is None
    assert heartbeat["active_chain_id"] is None
    assert heartbeat["scheduler_state"] == "ready"
    assert heartbeat["last_action"] == "task_completed"
    assert heartbeat["last_blocking_operation_type"] == "task_execution"
    assert heartbeat["last_blocking_operation_completed_at"] is not None


def test_complete_task_rejects_pending_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id, status="pending")

    with pytest.raises(TaskCompletionError) as exc:
        complete_task(task_id)

    assert "task_not_running" in str(exc.value)


def test_complete_task_rejects_already_completed_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    complete_task(task_id)

    with pytest.raises(TaskCompletionError) as exc:
        complete_task(task_id)

    assert "task_not_running" in str(exc.value)


def test_complete_task_keeps_lifecycle_audit_clean():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    complete_task(task_id)

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []
    
def test_audit_ignores_historical_start_heartbeat_after_completion():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        task_type="historical_heartbeat_completed",
    )

    start_task(task_id)
    complete_task(task_id)

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
    assert rows[-1]["last_action"] == "task_completed"

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []