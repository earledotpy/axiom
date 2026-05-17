from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


class TaskLifecycleGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskRunningTransitionDecision:
    allowed: bool
    task_id: int
    session_id: int | None = None
    reason: str = "unknown"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_task_running_transition(task_id: int) -> TaskRunningTransitionDecision:
    with get_connection() as conn:
        task = conn.execute(
            """
            SELECT task_id, session_id, status, manifest_id
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if task is None:
            return TaskRunningTransitionDecision(
                allowed=False,
                task_id=task_id,
                reason="task_not_found",
            )

        session_id = int(task["session_id"])
        status = task["status"]
        manifest_id = task["manifest_id"]

        if status != "pending":
            return TaskRunningTransitionDecision(
                allowed=False,
                task_id=task_id,
                session_id=session_id,
                reason="task_not_pending",
                details={
                    "status": status,
                },
            )

        if manifest_id is None:
            return TaskRunningTransitionDecision(
                allowed=False,
                task_id=task_id,
                session_id=session_id,
                reason="manifest_id_required_before_running",
                details={
                    "status": status,
                    "manifest_id": manifest_id,
                },
            )

        running = conn.execute(
            """
            SELECT task_id, status, manifest_id
            FROM tasks
            WHERE session_id = ?
              AND status = 'running'
            ORDER BY task_id
            """,
            (session_id,),
        ).fetchall()

        if running:
            return TaskRunningTransitionDecision(
                allowed=False,
                task_id=task_id,
                session_id=session_id,
                reason="session_already_has_running_task",
                details={
                    "running_tasks": [dict(row) for row in running],
                },
            )

        return TaskRunningTransitionDecision(
            allowed=True,
            task_id=task_id,
            session_id=session_id,
            reason="task_may_transition_to_running",
            details={
                "manifest_id": manifest_id,
            },
        )


def require_task_running_transition_allowed(task_id: int) -> None:
    decision = evaluate_task_running_transition(task_id)

    if not decision.allowed:
        raise TaskLifecycleGuardError(
            f"Task {task_id} may not transition to running: {decision.reason}"
        )


def transition_task_to_running(task_id: int) -> TaskRunningTransitionDecision:
    """
    Atomically transition one pending, manifest-bound task to running.

    This is intentionally small and strict. It is the guard StateMachine/Scheduler
    code should call before any task is actually executed.
    """
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        task = conn.execute(
            """
            SELECT task_id, session_id, status, manifest_id
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if task is None:
            raise TaskLifecycleGuardError(
                f"Task {task_id} may not transition to running: task_not_found"
            )

        session_id = int(task["session_id"])
        status = task["status"]
        manifest_id = task["manifest_id"]

        if status != "pending":
            raise TaskLifecycleGuardError(
                f"Task {task_id} may not transition to running: task_not_pending"
            )

        if manifest_id is None:
            raise TaskLifecycleGuardError(
                "Task "
                f"{task_id} may not transition to running: "
                "manifest_id_required_before_running"
            )

        running = conn.execute(
            """
            SELECT task_id, status, manifest_id
            FROM tasks
            WHERE session_id = ?
              AND status = 'running'
            ORDER BY task_id
            """,
            (session_id,),
        ).fetchall()

        if running:
            raise TaskLifecycleGuardError(
                "Task "
                f"{task_id} may not transition to running: "
                "session_already_has_running_task"
            )

        conn.execute(
            """
            UPDATE tasks
            SET status = 'running',
                started_at = COALESCE(
                    started_at,
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            WHERE task_id = ?
            """,
            (task_id,),
        )

        return TaskRunningTransitionDecision(
            allowed=True,
            task_id=task_id,
            session_id=session_id,
            reason="task_transitioned_to_running",
            details={
                "manifest_id": manifest_id,
            },
        )