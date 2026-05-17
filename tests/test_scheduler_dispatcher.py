from axiom.core.scheduler_dispatcher import dispatch_next_task
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


def _create_task(
    session_id: int,
    task_type: str,
    manifest_id: str | None = MANIFEST_ID,
    priority: int = 5,
    cancel_requested: int = 0,
) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 priority, manifest_id, cancel_requested)
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    session_id,
                    f"dispatch-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    priority,
                    manifest_id,
                    cancel_requested,
                ),
            ).lastrowid
        )


def test_dispatch_next_task_starts_one_manifest_bound_pending_task():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        task_type="dispatch_allowed",
        manifest_id=MANIFEST_ID,
    )

    result = dispatch_next_task(session_id=session_id)

    assert result.dispatched is True
    assert result.task_id == task_id
    assert result.status == "running"
    assert result.reason == "task_dispatched"
    assert result.heartbeat_id is not None

    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert row["status"] == "running"


def test_dispatch_next_task_ignores_pending_task_without_manifest():
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        task_type="dispatch_missing_manifest",
        manifest_id=None,
    )

    result = dispatch_next_task(session_id=session_id)

    assert result.dispatched is False
    assert result.task_id is None
    assert result.status == "idle"
    assert result.reason == "no_eligible_pending_task"


def test_dispatch_next_task_ignores_cancel_requested_pending_task():
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        task_type="dispatch_cancel_requested",
        manifest_id=MANIFEST_ID,
        cancel_requested=1,
    )

    result = dispatch_next_task(session_id=session_id)

    assert result.dispatched is False
    assert result.task_id is None
    assert result.status == "idle"
    assert result.reason == "no_eligible_pending_task"


def test_dispatch_next_task_blocks_when_session_already_has_running_task():
    session_id = _create_session()
    first_task_id = _create_task(
        session_id=session_id,
        task_type="dispatch_first",
        manifest_id=MANIFEST_ID,
    )
    second_task_id = _create_task(
        session_id=session_id,
        task_type="dispatch_second",
        manifest_id=MANIFEST_ID,
    )

    first = dispatch_next_task(session_id=session_id)
    second = dispatch_next_task(session_id=session_id)

    assert first.dispatched is True
    assert first.task_id == first_task_id

    assert second.dispatched is False
    assert second.task_id is None
    assert second.status == "blocked"
    assert second.reason == "session_already_has_running_task"

    with get_connection() as conn:
        second_task = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?",
            (second_task_id,),
        ).fetchone()

    assert second_task["status"] == "pending"


def test_dispatch_next_task_uses_priority_then_created_order():
    session_id = _create_session()
    low_priority = _create_task(
        session_id=session_id,
        task_type="dispatch_low_priority",
        manifest_id=MANIFEST_ID,
        priority=1,
    )
    high_priority = _create_task(
        session_id=session_id,
        task_type="dispatch_high_priority",
        manifest_id=MANIFEST_ID,
        priority=9,
    )

    result = dispatch_next_task(session_id=session_id)

    assert result.dispatched is True
    assert result.task_id == high_priority
    assert result.task_id != low_priority


def test_dispatch_next_task_keeps_lifecycle_audit_clean():
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        task_type="dispatch_audit_clean",
        manifest_id=MANIFEST_ID,
    )

    dispatch_next_task(session_id=session_id)

    audit = audit_task_lifecycle(session_id=session_id)

    assert audit.passed is True
    assert audit.violations == []