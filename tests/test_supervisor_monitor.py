from axiom.core.scheduler import write_scheduler_heartbeat
from axiom.core.supervisor_monitor import SupervisorMonitor
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session, create_task, transition_task_status

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def latest_security_event(event_type: str):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM security_events
            WHERE event_type = ?
            ORDER BY event_id DESC
            LIMIT 1
            """,
            (event_type,),
        ).fetchone()


def force_task_status(task_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id),
        )


def test_supervisor_monitor_reports_unhealthy_when_heartbeat_missing():
    session_id = create_session(operator_id="supervisor-missing-heartbeat")

    health = SupervisorMonitor(stale_threshold_seconds=120).check_session_health(session_id)

    assert health.healthy is False
    assert health.scheduler_stale is True
    assert health.reason == "scheduler_heartbeat_stale_or_missing"

    event = latest_security_event("supervisor_scheduler_stale")
    assert event is not None
    assert event["severity"] == "warning"


def test_supervisor_monitor_reports_healthy_with_fresh_heartbeat_and_zero_running_tasks():
    session_id = create_session(operator_id="supervisor-healthy-zero")

    write_scheduler_heartbeat(session_id, scheduler_state="running")

    health = SupervisorMonitor(stale_threshold_seconds=120).check_session_health(session_id)

    assert health.healthy is True
    assert health.scheduler_stale is False
    assert health.running_task_invariant_valid is True
    assert health.running_count == 0
    assert health.reason == "supervisor_health_ok"


def test_supervisor_monitor_reports_healthy_with_one_running_task():
    session_id = create_session(operator_id="supervisor-healthy-one")

    write_scheduler_heartbeat(session_id, scheduler_state="running")

    task_id = create_task(
        session_id=session_id,
        chain_id="chain-supervisor-one-running",
        task_class="system_maintenance",
        task_type="supervisor_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    transition_task_status(task_id, "running")

    health = SupervisorMonitor(stale_threshold_seconds=120).check_session_health(session_id)

    assert health.healthy is True
    assert health.running_task_invariant_valid is True
    assert health.running_count == 1


def test_supervisor_monitor_reports_critical_when_multiple_running_tasks():
    session_id = create_session(operator_id="supervisor-multiple-running")

    write_scheduler_heartbeat(session_id, scheduler_state="running")

    task_id_1 = create_task(
        session_id=session_id,
        chain_id="chain-supervisor-multiple-running",
        task_class="system_maintenance",
        task_type="supervisor_test_1",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    task_id_2 = create_task(
        session_id=session_id,
        chain_id="chain-supervisor-multiple-running",
        task_class="system_maintenance",
        task_type="supervisor_test_2",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    # Deliberately bypass TaskCommitter here. This test verifies that the
    # passive supervisor catches corrupted/impossible runtime state.
    force_task_status(task_id_1, "running")
    force_task_status(task_id_2, "running")

    health = SupervisorMonitor(stale_threshold_seconds=120).check_session_health(session_id)

    assert health.healthy is False
    assert health.scheduler_stale is False
    assert health.running_task_invariant_valid is False
    assert health.running_count == 2
    assert health.reason == "multiple_running_tasks_detected"

    event = latest_security_event("supervisor_running_task_invariant_failed")
    assert event is not None
    assert event["severity"] == "critical"


def test_supervisor_monitor_rejects_non_positive_threshold():
    try:
        SupervisorMonitor(stale_threshold_seconds=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("SupervisorMonitor accepted non-positive stale threshold")
