from axiom.core.scheduler import (
    check_one_running_task_invariant,
    get_latest_scheduler_heartbeat,
    is_scheduler_heartbeat_stale,
    write_scheduler_heartbeat,
)
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session, create_task, transition_task_status

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def force_task_status(task_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id),
        )


def test_scheduler_heartbeat_is_stale_when_missing():
    session_id = create_session(operator_id="scheduler-missing-heartbeat")

    assert is_scheduler_heartbeat_stale(session_id, threshold_seconds=120) is True


def test_scheduler_heartbeat_write_and_read_latest():
    session_id = create_session(operator_id="scheduler-heartbeat")

    heartbeat_id = write_scheduler_heartbeat(session_id, scheduler_state="running")
    latest = get_latest_scheduler_heartbeat(session_id)

    assert isinstance(heartbeat_id, int)
    assert latest is not None
    assert latest["heartbeat_id"] == heartbeat_id
    assert latest["scheduler_state"] == "running"
    assert latest["last_action"] == "heartbeat"


def test_scheduler_heartbeat_is_not_stale_after_write():
    session_id = create_session(operator_id="scheduler-fresh")

    write_scheduler_heartbeat(session_id, scheduler_state="running")

    assert is_scheduler_heartbeat_stale(session_id, threshold_seconds=120) is False


def test_one_running_task_invariant_valid_with_zero_running_tasks():
    session_id = create_session(operator_id="zero-running")

    invariant = check_one_running_task_invariant(session_id)

    assert invariant.valid is True
    assert invariant.running_count == 0


def test_one_running_task_invariant_valid_with_one_running_task():
    session_id = create_session(operator_id="one-running")

    task_id = create_task(
        session_id=session_id,
        chain_id="chain-one-running",
        task_class="system_maintenance",
        task_type="invariant_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    transition_task_status(task_id, "running")

    invariant = check_one_running_task_invariant(session_id)

    assert invariant.valid is True
    assert invariant.running_count == 1


def test_one_running_task_invariant_detects_multiple_running_tasks():
    session_id = create_session(operator_id="multi-running")

    task_id_1 = create_task(
        session_id=session_id,
        chain_id="chain-multi-running",
        task_class="system_maintenance",
        task_type="invariant_test_1",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    task_id_2 = create_task(
        session_id=session_id,
        chain_id="chain-multi-running",
        task_class="system_maintenance",
        task_type="invariant_test_2",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    # Deliberately bypass TaskCommitter here. This test verifies that the
    # passive invariant detector catches corrupted/impossible runtime state.
    force_task_status(task_id_1, "running")
    force_task_status(task_id_2, "running")

    invariant = check_one_running_task_invariant(session_id)

    assert invariant.valid is False
    assert invariant.running_count == 2
    assert invariant.reason == "multiple_running_tasks_detected"
