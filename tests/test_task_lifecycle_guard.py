import pytest

from axiom.core.task_lifecycle_guard import (
    TaskLifecycleGuardError,
    evaluate_task_running_transition,
    require_task_running_transition_allowed,
    transition_task_to_running,
)
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
    task_type: str = "guard_test_task",
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
                    f"guard-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_evaluate_task_running_transition_allows_pending_manifest_bound_task():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="allowed_pending",
    )

    decision = evaluate_task_running_transition(task_id)

    assert decision.allowed is True
    assert decision.reason == "task_may_transition_to_running"
    assert decision.session_id == session_id


def test_evaluate_task_running_transition_blocks_missing_manifest():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=None,
        task_type="missing_manifest",
    )

    decision = evaluate_task_running_transition(task_id)

    assert decision.allowed is False
    assert decision.reason == "manifest_id_required_before_running"


def test_evaluate_task_running_transition_blocks_when_other_task_running():
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        status="running",
        manifest_id=MANIFEST_ID,
        task_type="already_running",
    )
    pending_task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="pending_blocked",
    )

    decision = evaluate_task_running_transition(pending_task_id)

    assert decision.allowed is False
    assert decision.reason == "session_already_has_running_task"
    assert len(decision.details["running_tasks"]) == 1


def test_require_task_running_transition_allowed_raises_when_blocked():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=None,
        task_type="require_blocked",
    )

    with pytest.raises(TaskLifecycleGuardError) as exc:
        require_task_running_transition_allowed(task_id)

    assert "manifest_id_required_before_running" in str(exc.value)


def test_transition_task_to_running_updates_pending_manifest_bound_task():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="transition_allowed",
    )

    decision = transition_task_to_running(task_id)

    assert decision.allowed is True
    assert decision.reason == "task_transitioned_to_running"

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, started_at
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    assert row["status"] == "running"
    assert row["started_at"] is not None


def test_transition_task_to_running_does_not_update_missing_manifest_task():
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=None,
        task_type="transition_missing_manifest",
    )

    with pytest.raises(TaskLifecycleGuardError):
        transition_task_to_running(task_id)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, started_at
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    assert row["status"] == "pending"
    assert row["started_at"] is None


def test_transition_task_to_running_blocks_second_running_task():
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        status="running",
        manifest_id=MANIFEST_ID,
        task_type="running_existing",
    )
    pending_task_id = _create_task(
        session_id=session_id,
        status="pending",
        manifest_id=MANIFEST_ID,
        task_type="running_second_blocked",
    )

    with pytest.raises(TaskLifecycleGuardError) as exc:
        transition_task_to_running(pending_task_id)

    assert "session_already_has_running_task" in str(exc.value)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status
            FROM tasks
            WHERE task_id = ?
            """,
            (pending_task_id,),
        ).fetchone()

    assert row["status"] == "pending"