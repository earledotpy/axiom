from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.task_lifecycle_service import get_task_lifecycle_service
from axiom.persistence.db import get_connection


class SchedulerDispatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class SchedulerDispatchResult:
    dispatched: bool
    session_id: int
    task_id: int | None
    status: str
    reason: str
    heartbeat_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _running_task_exists(session_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE session_id = ?
              AND status = 'running'
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    return row is not None


def _select_next_pending_task(session_id: int) -> dict[str, Any] | None:
    """
    Select the next scheduler-eligible pending task.

    Eligibility:
    - same session
    - status pending
    - cancel_requested = 0
    - manifest_id present
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id, session_id, chain_id, task_class, task_type,
                   priority, created_at, manifest_id
            FROM tasks
            WHERE session_id = ?
              AND status = 'pending'
              AND cancel_requested = 0
              AND manifest_id IS NOT NULL
              AND trim(manifest_id) != ''
            ORDER BY priority DESC, created_at ASC, task_id ASC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    return dict(row) if row is not None else None


def dispatch_next_task(session_id: int) -> SchedulerDispatchResult:
    """
    Start exactly one eligible pending task for a session.

    This is the scheduler-facing dispatch primitive. It delegates actual task
    transition and heartbeat active_task_id writing to TaskLifecycleService.
    """
    if _running_task_exists(session_id):
        return SchedulerDispatchResult(
            dispatched=False,
            session_id=session_id,
            task_id=None,
            status="blocked",
            reason="session_already_has_running_task",
        )

    task = _select_next_pending_task(session_id)

    if task is None:
        return SchedulerDispatchResult(
            dispatched=False,
            session_id=session_id,
            task_id=None,
            status="idle",
            reason="no_eligible_pending_task",
        )

    service = get_task_lifecycle_service()
    started = service.start(int(task["task_id"]))

    return SchedulerDispatchResult(
        dispatched=True,
        session_id=session_id,
        task_id=started.task_id,
        heartbeat_id=started.heartbeat_id,
        status=started.status,
        reason="task_dispatched",
        details={
            "selected_task": task,
            "lifecycle_result": started.to_dict(),
        },
    )