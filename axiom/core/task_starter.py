from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.task_lifecycle_guard import (
    TaskLifecycleGuardError,
    transition_task_to_running,
)
from axiom.persistence.db import get_connection


class TaskStartError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskStartResult:
    task_id: int
    session_id: int
    heartbeat_id: int
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get_running_task(task_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id, session_id, chain_id, task_class, task_type,
                   status, manifest_id, started_at
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    if row is None:
        raise TaskStartError(f"Task not found after transition: {task_id}")

    return dict(row)


def write_task_start_heartbeat(task: dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, last_tick_started_at,
             last_blocking_operation_started_at, last_blocking_operation_type,
             active_task_id, active_chain_id, scheduler_state, last_action,
             tick_count)
            VALUES (
                ?,
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                'task_execution',
                ?,
                ?,
                'running',
                'task_started',
                1
            )
            """,
            (
                task["session_id"],
                task["task_id"],
                task["chain_id"],
            ),
        )

        return int(cur.lastrowid)


def start_task(task_id: int) -> TaskStartResult:
    """
    Guarded task start.

    This function is the narrow integration point that Scheduler/StateMachine
    should use before any task execution begins.
    """
    try:
        transition_decision = transition_task_to_running(task_id)
    except TaskLifecycleGuardError as exc:
        raise TaskStartError(str(exc)) from exc

    task = _get_running_task(task_id)

    if task["status"] != "running":
        raise TaskStartError(f"Task did not transition to running: {task_id}")

    heartbeat_id = write_task_start_heartbeat(task)

    return TaskStartResult(
        task_id=task_id,
        session_id=int(task["session_id"]),
        heartbeat_id=heartbeat_id,
        status="running",
        details={
            "transition": transition_decision.to_dict(),
            "manifest_id": task["manifest_id"],
            "chain_id": task["chain_id"],
            "task_class": task["task_class"],
            "task_type": task["task_type"],
        },
    )