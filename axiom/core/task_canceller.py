from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


class TaskCancellationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskCancellationResult:
    task_id: int
    session_id: int
    heartbeat_id: int | None
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _encode_cancellation_info(
    reason: str,
    details: dict[str, Any] | None = None,
) -> str:
    return json.dumps(
        {
            "event_type": "task_cancelled",
            "reason": reason,
            "details": details or {},
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def cancel_task(
    task_id: int,
    reason: str = "operator_cancelled",
    details: dict[str, Any] | None = None,
) -> TaskCancellationResult:
    """
    Cancel a pending or running task.

    Pending cancellation does not need heartbeat cleanup.
    Running cancellation clears scheduler active-task heartbeat state.
    """
    error_info = _encode_cancellation_info(reason=reason, details=details)

    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        task = conn.execute(
            """
            SELECT task_id, session_id, chain_id, task_class, task_type,
                   status, manifest_id
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if task is None:
            raise TaskCancellationError(
                f"Task {task_id} may not cancel: task_not_found"
            )

        status = task["status"]

        if status not in {"pending", "running"}:
            raise TaskCancellationError(
                f"Task {task_id} may not cancel: task_not_cancellable"
            )

        session_id = int(task["session_id"])
        was_running = status == "running"

        conn.execute(
            """
            UPDATE tasks
            SET status = 'cancelled',
                cancel_requested = 1,
                completed_at = COALESCE(
                    completed_at,
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                error_info = ?
            WHERE task_id = ?
            """,
            (error_info, task_id),
        )

        heartbeat_id: int | None = None

        if was_running:
            cur = conn.execute(
                """
                INSERT INTO scheduler_heartbeat
                (session_id, last_freshness_at, last_tick_started_at,
                 last_tick_completed_at, last_blocking_operation_started_at,
                 last_blocking_operation_completed_at, last_blocking_operation_type,
                 active_task_id, active_chain_id, scheduler_state, last_action,
                 tick_count)
                VALUES (
                    ?,
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    'task_execution',
                    NULL,
                    NULL,
                    'ready',
                    'task_cancelled',
                    1
                )
                """,
                (session_id,),
            )
            heartbeat_id = int(cur.lastrowid)

        return TaskCancellationResult(
            task_id=task_id,
            session_id=session_id,
            heartbeat_id=heartbeat_id,
            status="cancelled",
            details={
                "chain_id": task["chain_id"],
                "manifest_id": task["manifest_id"],
                "task_class": task["task_class"],
                "task_type": task["task_type"],
                "previous_status": status,
                "reason": reason,
            },
        )