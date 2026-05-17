from axiom.core.supervisor_monitor import SupervisorMonitor
from axiom.core.task_starter import start_task
from axiom.core.task_completer import complete_task
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
    task_type: str = "supervisor_active_task_test",
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
                    f"supervisor-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    MANIFEST_ID,
                ),
            ).lastrowid
        )


def test_supervisor_reports_healthy_with_fresh_no_active_task_heartbeat():
    session_id = _create_session()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, scheduler_state, last_action)
            VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'ready', 'heartbeat')
            """,
            (session_id,),
        )

    health = SupervisorMonitor().check_session_health(session_id)

    assert health.healthy is True
    assert health.reason == "supervisor_health_ok"
    assert health.active_task_present is False
    assert health.active_task_status is None


def test_supervisor_reports_healthy_with_active_running_task():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)

    health = SupervisorMonitor().check_session_health(session_id)

    assert health.healthy is True
    assert health.reason == "supervisor_health_ok_active_task_running"
    assert health.active_task_present is True
    assert health.active_task_status == "running"


def test_supervisor_reports_unhealthy_when_latest_active_task_completed():
    session_id = _create_session()
    task_id = _create_task(session_id=session_id)

    start_task(task_id)
    complete_task(task_id)

    # Deliberately create a bad latest heartbeat pointing to a completed task.
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, active_task_id, scheduler_state, last_action)
            VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), ?, 'running', 'bad_heartbeat')
            """,
            (session_id, task_id),
        )

    health = SupervisorMonitor().check_session_health(session_id)

    assert health.healthy is False
    assert health.reason == "heartbeat_active_task_not_running"
    assert health.active_task_present is True
    assert health.active_task_status == "completed"


def test_supervisor_reports_stale_when_no_heartbeat_exists():
    session_id = _create_session()

    health = SupervisorMonitor().check_session_health(session_id)

    assert health.healthy is False
    assert health.scheduler_stale is True
    assert health.reason == "scheduler_heartbeat_stale_or_missing"


def test_supervisor_health_to_dict_contains_active_task_fields():
    session_id = _create_session()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, scheduler_state, last_action)
            VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'ready', 'heartbeat')
            """,
            (session_id,),
        )

    payload = SupervisorMonitor().check_session_health(session_id).to_dict()

    assert "active_task_present" in payload
    assert "active_task_status" in payload
    assert "details" in payload