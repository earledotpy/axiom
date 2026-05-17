import pytest

from axiom.core.task_lifecycle_audit import audit_task_lifecycle
from axiom.core.task_starter import TaskStartError, start_task
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
    task_type: str = "starter_test_task",
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
                    f"starter-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_start_task_transitions_to_running_and_writes_heartbeat():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="start_allowed",
    )

    result = start_task(task_id)

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.status == "running"
    assert result.heartbeat_id > 0

    with get_connection() as conn:
        task = conn.execute(
            """
            SELECT status, started_at
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        heartbeat = conn.execute(
            """
            SELECT active_task_id, active_chain_id, scheduler_state,
                   last_action, last_blocking_operation_type
            FROM scheduler_heartbeat
            WHERE heartbeat_id = ?
            """,
            (result.heartbeat_id,),
        ).fetchone()

    assert task["status"] == "running"
    assert task["started_at"] is not None
    assert heartbeat["active_task_id"] == task_id
    assert heartbeat["scheduler_state"] == "running"
    assert heartbeat["last_action"] == "task_started"
    assert heartbeat["last_blocking_operation_type"] == "task_execution"


def test_start_task_rejects_missing_manifest_and_writes_no_heartbeat():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=None,
        task_type="start_missing_manifest",
    )

    with pytest.raises(TaskStartError):
        start_task(task_id)

    with get_connection() as conn:
        task = conn.execute(
            "SELECT status, started_at FROM tasks WHERE task_id = ?",
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

    assert task["status"] == "pending"
    assert task["started_at"] is None
    assert heartbeat_count == 0


def test_start_task_rejects_second_running_task():
    session_id = _create_session()

    first_task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="start_first",
    )
    second_task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="start_second_blocked",
    )

    start_task(first_task_id)

    with pytest.raises(TaskStartError) as exc:
        start_task(second_task_id)

    assert "session_already_has_running_task" in str(exc.value)

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (second_task_id,),
        ).fetchone()

    assert row["status"] == "pending"


def test_start_task_keeps_lifecycle_audit_clean_for_started_task():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="audit_clean_started",
    )

    start_task(task_id)

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []