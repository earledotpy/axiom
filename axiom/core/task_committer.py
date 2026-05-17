from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.core.scheduler import write_scheduler_heartbeat
from axiom.core.task_lifecycle_guard import evaluate_task_running_transition
from axiom.core.task_lifecycle_service import get_task_lifecycle_service
from axiom.persistence.repositories import get_task


class TaskCommitError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommitResult:
    task_id: int
    previous_status: str
    next_status: str
    heartbeat_before_id: int | None
    heartbeat_after_id: int | None


class TaskCommitter:
    """
    Compatibility wrapper for task status commits.

    Lifecycle-sensitive transitions are delegated to TaskLifecycleService so
    Scheduler/StateMachine behavior uses the same guarded primitives as the
    CLI tools and lifecycle tests.

    The public CommitResult still preserves heartbeat_before_id and
    heartbeat_after_id for older callers/tests.
    """

    def __init__(self) -> None:
        self.lifecycle = get_task_lifecycle_service()

    def _prevalidate_transition(
        self,
        task_id: int,
        previous_status: str,
        next_status: str,
    ) -> None:
        if next_status == "running":
            decision = evaluate_task_running_transition(task_id)

            if decision.allowed:
                return

            if decision.reason == "manifest_id_required_before_running":
                raise TaskCommitError(
                    f"Cannot start task {task_id}: manifest_id is required before transition to running"
                )

            if decision.reason == "session_already_has_running_task":
                raise TaskCommitError(
                    f"Cannot start task {task_id}: another task is already running"
                )

            raise TaskCommitError(
                f"Cannot start task {task_id}: {decision.reason}"
            )

        if next_status == "completed" and previous_status != "running":
            raise TaskCommitError(
                f"Cannot complete task {task_id}: task_not_running"
            )

        if next_status == "failed" and previous_status != "running":
            raise TaskCommitError(
                f"Cannot fail task {task_id}: task_not_running"
            )

        if next_status == "cancelled" and previous_status not in {"pending", "running"}:
            raise TaskCommitError(
                f"Cannot cancel task {task_id}: task_not_cancellable"
            )

    def commit_status(
        self,
        task_id: int,
        next_status: str,
        result_text: str | None = None,
        result_json: dict[str, Any] | list[Any] | str | None = None,
        error_info: str | None = None,
    ) -> CommitResult:
        task = get_task(task_id)
        if task is None:
            raise TaskCommitError(f"Unknown task_id: {task_id}")

        previous_status = task["status"]
        session_id = int(task["session_id"])

        if next_status not in {"running", "completed", "failed", "cancelled"}:
            raise TaskCommitError(
                f"Unsupported TaskCommitter lifecycle target: {next_status}"
            )

        self._prevalidate_transition(
            task_id=task_id,
            previous_status=previous_status,
            next_status=next_status,
        )

        heartbeat_before_id = write_scheduler_heartbeat(
            session_id=session_id,
            scheduler_state="running",
        )

        try:
            if next_status == "running":
                result = self.lifecycle.start(task_id)

            elif next_status == "completed":
                result = self.lifecycle.complete(
                    task_id=task_id,
                    result_text=result_text,
                    result_json=result_json,
                )

            elif next_status == "failed":
                result = self.lifecycle.fail(
                    task_id=task_id,
                    error_type="task_commit_failed",
                    message=error_info or "Task marked failed by TaskCommitter.",
                    details={
                        "previous_status": previous_status,
                    },
                )

            elif next_status == "cancelled":
                result = self.lifecycle.cancel(
                    task_id=task_id,
                    reason="task_commit_cancelled",
                    details={
                        "previous_status": previous_status,
                    },
                )

            else:
                raise TaskCommitError(
                    f"Unsupported TaskCommitter lifecycle target: {next_status}"
                )

        except Exception as exc:
            if isinstance(exc, TaskCommitError):
                raise
            raise TaskCommitError(str(exc)) from exc

        heartbeat_after_id = result.heartbeat_id

        if heartbeat_after_id is None:
            heartbeat_after_id = write_scheduler_heartbeat(
                session_id=session_id,
                scheduler_state="running",
            )

        return CommitResult(
            task_id=task_id,
            previous_status=previous_status,
            next_status=next_status,
            heartbeat_before_id=heartbeat_before_id,
            heartbeat_after_id=heartbeat_after_id,
        )