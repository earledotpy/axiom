from axiom.core.task_lifecycle_service import TaskLifecycleService
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
    task_type: str = "service_test_task",
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
                    f"service-chain-{session_id}-{task_type}",
                    "system_maintenance",
                    task_type,
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_task_lifecycle_service_start_then_complete_keeps_audit_clean():
    service = TaskLifecycleService()
    session_id = _create_session()
    task_id = _create_task(session_id=session_id, task_type="service_complete")

    started = service.start(task_id)
    completed = service.complete(
        task_id,
        result_text="service completed",
        result_json={"ok": True},
    )
    audit = service.audit(session_id=session_id)

    assert started.operation == "start"
    assert started.status == "running"
    assert completed.operation == "complete"
    assert completed.status == "completed"
    assert audit.passed is True
    assert audit.violations == []


def test_task_lifecycle_service_start_then_fail_keeps_audit_clean():
    service = TaskLifecycleService()
    session_id = _create_session()
    task_id = _create_task(session_id=session_id, task_type="service_fail")

    started = service.start(task_id)
    failed = service.fail(
        task_id,
        error_type="service_test_error",
        message="service failure verified",
        details={"ok": False},
    )
    audit = service.audit(session_id=session_id)

    assert started.status == "running"
    assert failed.operation == "fail"
    assert failed.status == "failed"
    assert audit.passed is True
    assert audit.violations == []


def test_task_lifecycle_service_start_then_cancel_keeps_audit_clean():
    service = TaskLifecycleService()
    session_id = _create_session()
    task_id = _create_task(session_id=session_id, task_type="service_cancel_running")

    started = service.start(task_id)
    cancelled = service.cancel(
        task_id,
        reason="service_running_cancel_verified",
    )
    audit = service.audit(session_id=session_id)

    assert started.status == "running"
    assert cancelled.operation == "cancel"
    assert cancelled.status == "cancelled"
    assert cancelled.details["previous_status"] == "running"
    assert audit.passed is True
    assert audit.violations == []


def test_task_lifecycle_service_cancel_pending_keeps_audit_clean():
    service = TaskLifecycleService()
    session_id = _create_session()
    task_id = _create_task(session_id=session_id, task_type="service_cancel_pending")

    cancelled = service.cancel(
        task_id,
        reason="service_pending_cancel_verified",
    )
    audit = service.audit(session_id=session_id)

    assert cancelled.operation == "cancel"
    assert cancelled.status == "cancelled"
    assert cancelled.heartbeat_id is None
    assert cancelled.details["previous_status"] == "pending"
    assert audit.passed is True
    assert audit.violations == []