from axiom.core.scheduler import Scheduler
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
    task_type: str = "scheduler_run_once_test",
    manifest_id: str | None = MANIFEST_ID,
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
                    f"scheduler-run-once-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_scheduler_run_once_blocks_by_default_when_autonomous_not_ready():
    session_id = _create_session()
    task_id = _create_pending_task(
        session_id=session_id,
        task_type="run_once_blocked_default",
    )

    result = Scheduler().run_once(session_id=session_id)

    assert result.tick_status == "blocked"
    assert result.reason == "autonomous_not_ready"
    assert result.dispatched_task_id is None

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "pending"


def test_scheduler_run_once_manual_override_dispatches_task():
    session_id = _create_session()
    task_id = _create_pending_task(
        session_id=session_id,
        task_type="run_once_manual_dispatch",
    )

    result = Scheduler().run_once(
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


def test_scheduler_run_once_manual_override_idles_without_pending_task():
    session_id = _create_session()

    result = Scheduler().run_once(
        session_id=session_id,
        allow_when_autonomous_blocked=True,
    )

    assert result.tick_status == "idle"
    assert result.reason == "no_eligible_pending_task"
    assert result.dispatched_task_id is None