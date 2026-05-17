from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.task_canceller import TaskCancellationResult, cancel_task
from axiom.core.task_completer import TaskCompletionResult, complete_task
from axiom.core.task_failer import TaskFailureResult, fail_task
from axiom.core.task_lifecycle_audit import TaskLifecycleAuditResult, audit_task_lifecycle
from axiom.core.task_starter import TaskStartResult, start_task


@dataclass(frozen=True)
class TaskLifecycleServiceResult:
    operation: str
    task_id: int | None
    session_id: int | None
    status: str
    heartbeat_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskLifecycleService:
    """
    Stable facade for AXIOM task lifecycle operations.

    Scheduler, StateMachine, and TaskCommitter should depend on this service
    instead of importing individual lifecycle primitive modules directly.
    """

    def start(self, task_id: int) -> TaskLifecycleServiceResult:
        result: TaskStartResult = start_task(task_id)

        return TaskLifecycleServiceResult(
            operation="start",
            task_id=result.task_id,
            session_id=result.session_id,
            heartbeat_id=result.heartbeat_id,
            status=result.status,
            details=result.details,
        )

    def complete(
        self,
        task_id: int,
        result_text: str | None = None,
        result_json: dict[str, Any] | list[Any] | str | None = None,
    ) -> TaskLifecycleServiceResult:
        result: TaskCompletionResult = complete_task(
            task_id=task_id,
            result_text=result_text,
            result_json=result_json,
        )

        return TaskLifecycleServiceResult(
            operation="complete",
            task_id=result.task_id,
            session_id=result.session_id,
            heartbeat_id=result.heartbeat_id,
            status=result.status,
            details=result.details,
        )

    def fail(
        self,
        task_id: int,
        error_type: str = "execution_error",
        message: str = "Task execution failed.",
        details: dict[str, Any] | None = None,
    ) -> TaskLifecycleServiceResult:
        result: TaskFailureResult = fail_task(
            task_id=task_id,
            error_type=error_type,
            message=message,
            details=details,
        )

        return TaskLifecycleServiceResult(
            operation="fail",
            task_id=result.task_id,
            session_id=result.session_id,
            heartbeat_id=result.heartbeat_id,
            status=result.status,
            details=result.details,
        )

    def cancel(
        self,
        task_id: int,
        reason: str = "operator_cancelled",
        details: dict[str, Any] | None = None,
    ) -> TaskLifecycleServiceResult:
        result: TaskCancellationResult = cancel_task(
            task_id=task_id,
            reason=reason,
            details=details,
        )

        return TaskLifecycleServiceResult(
            operation="cancel",
            task_id=result.task_id,
            session_id=result.session_id,
            heartbeat_id=result.heartbeat_id,
            status=result.status,
            details=result.details,
        )

    def audit(
        self,
        session_id: int | None = None,
        latest_session: bool = False,
    ) -> TaskLifecycleAuditResult:
        return audit_task_lifecycle(
            session_id=session_id,
            latest_session=latest_session,
        )


_default_service = TaskLifecycleService()


def get_task_lifecycle_service() -> TaskLifecycleService:
    return _default_service