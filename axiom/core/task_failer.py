from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


class TaskFailureError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskFailureResult:
    task_id: int
    session_id: int
    heartbeat_id: int
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _encode_error_info(
    error_type: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> str:
    return json.dumps(
        {
            "error_type": error_type,
            "message": message,
            "details": details or {},
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def fail_task(
    task_id: int,
    error_type: str = "execution_error",
    message: str = "Task execution failed.",
    details: dict[str, Any] | None = None,
) -> TaskFailureResult:
    """
    Mark a running task failed and clear scheduler active-task heartbeat state.

    This is the failure-path pair for task_starter.start_task().
    """
    error_info = _encode_error_info(
        error_type=error_type,
        message=message,
        details=details,
    )

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
            raise TaskFailureError(
                f"Task {task_id} may not fail: task_not_found"
            )

        if task["status"] != "running":
            raise TaskFailureError(
                f"Task {task_id} may not fail: task_not_running"
            )

        session_id = int(task["session_id"])

        conn.execute(
            """
            UPDATE tasks
            SET status = 'failed',
                completed_at = COALESCE(
                    completed_at,
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                error_info = ?
            WHERE task_id = ?
            """,
            (error_info, task_id),
        )

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
                'task_failed',
                1
            )
            """,
            (session_id,),
        )

        heartbeat_id = int(cur.lastrowid)

        return TaskFailureResult(
            task_id=task_id,
            session_id=session_id,
            heartbeat_id=heartbeat_id,
            status="failed",
            details={
                "chain_id": task["chain_id"],
                "manifest_id": task["manifest_id"],
                "task_class": task["task_class"],
                "task_type": task["task_type"],
                "error_type": error_type,
            },
        )