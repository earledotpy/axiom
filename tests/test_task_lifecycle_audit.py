from axiom.core.task_lifecycle_audit import audit_task_lifecycle
from axiom.persistence.db import get_connection, init_db


def _create_session() -> int:
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
    status: str,
    manifest_id: str | None = None,
    task_type: str = "test_task",
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
                    f"chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_task_lifecycle_audit_passes_for_empty_session():
    init_db()
    session_id = _create_session()

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is True
    assert result.violations == []


def test_task_lifecycle_audit_detects_running_task_missing_manifest():
    init_db()
    session_id = _create_session()
    _create_task(
        session_id=session_id,
        status="running",
        manifest_id=None,
        task_type="missing_manifest",
    )

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is False
    assert any(
        violation.code == "running_task_missing_manifest"
        for violation in result.violations
    )


def test_task_lifecycle_audit_detects_multiple_running_tasks():
    init_db()
    session_id = _create_session()

    manifest_id = "security.tool_capability_map.v1"
    _create_task(
        session_id=session_id,
        status="running",
        manifest_id=manifest_id,
        task_type="running_one",
    )
    _create_task(
        session_id=session_id,
        status="running",
        manifest_id=manifest_id,
        task_type="running_two",
    )

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is False
    assert any(
        violation.code == "multiple_running_tasks"
        for violation in result.violations
    )


def test_task_lifecycle_audit_detects_heartbeat_active_task_not_running():
    init_db()
    session_id = _create_session()
    task_id = _create_task(
        session_id=session_id,
        status="completed",
        manifest_id="security.tool_capability_map.v1",
        task_type="completed_active_task",
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, active_task_id,
             last_tick_started_at, last_tick_completed_at)
            VALUES (
                ?,
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                ?,
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            )
            """,
            (session_id, task_id),
        )

    result = audit_task_lifecycle(session_id=session_id)

    assert result.passed is False
    assert any(
        violation.code == "heartbeat_active_task_not_running"
        for violation in result.violations
    )