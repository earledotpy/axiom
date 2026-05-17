from axiom.core.scheduler_tick import run_scheduler_tick
from axiom.core.task_lifecycle_audit import audit_task_lifecycle
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


def _create_pending_task(
    session_id: int,
    manifest_id: str | None = MANIFEST_ID,
    task_type: str = "scheduler_tick_test_task",
) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 manifest_id)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (
                    session_id,
                    f"scheduler-tick-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_scheduler_tick_blocks_when_autonomous_not_ready_by_default():
    session_id = _create_session()
    task_id = _create_pending_task(
        session_id=session_id,
        task_type="tick_blocked_default",
    )

    result = run_scheduler_tick(session_id=session_id)

    assert result.tick_status == "blocked"
    assert result.reason == "autonomous_not_ready"
    assert result.dispatched_task_id is None

    with get_connection() as conn:
        task = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert task["status"] == "pending"


def test_scheduler_tick_manual_override_dispatches_one_task():
    session_id = _create_session()
    task_id = _create_pending_task(
        session_id=session_id,
        task_type="tick_manual_dispatch",
    )

    result = run_scheduler_tick(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.tick_status == "running"
    assert result.reason == "task_dispatched"
    assert result.dispatched_task_id == task_id
    assert result.heartbeat_id is not None

    audit = audit_task_lifecycle(session_id=session_id)
    assert audit.passed is True
    assert audit.violations == []


def test_scheduler_tick_manual_override_idles_when_no_pending_task():
    session_id = _create_session()

    result = run_scheduler_tick(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.tick_status == "idle"
    assert result.reason == "no_eligible_pending_task"
    assert result.dispatched_task_id is None


def test_scheduler_tick_blocks_on_lifecycle_audit_failure_even_with_override():
    session_id = _create_session()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks
            (session_id, chain_id, task_class, task_type, status,
             manifest_id)
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (
                session_id,
                f"scheduler-tick-bad-chain-{session_id}-one",
                "system_maintenance",
                "bad_running_one",
                MANIFEST_ID,
            ),
        )
        conn.execute(
            """
            INSERT INTO tasks
            (session_id, chain_id, task_class, task_type, status,
             manifest_id)
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (
                session_id,
                f"scheduler-tick-bad-chain-{session_id}-two",
                "system_maintenance",
                "bad_running_two",
                MANIFEST_ID,
            ),
        )

    result = run_scheduler_tick(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.tick_status == "blocked"
    assert result.reason == "task_lifecycle_audit_failed"
    assert result.dispatched_task_id is None