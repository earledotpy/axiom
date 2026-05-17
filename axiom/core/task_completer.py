from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


class TaskCompletionError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskCompletionResult:
    task_id: int
    session_id: int
    heartbeat_id: int
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_or_none(value: dict[str, Any] | list[Any] | str | None) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        return value

    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def complete_task(
    task_id: int,
    result_text: str | None = None,
    result_json: dict[str, Any] | list[Any] | str | None = None,
) -> TaskCompletionResult:
    """
    Complete a running task and clear scheduler active-task heartbeat state.

    This is the paired primitive for task_starter.start_task().
    """
    encoded_result_json = _json_or_none(result_json)

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
            raise TaskCompletionError(
                f"Task {task_id} may not complete: task_not_found"
            )

        if task["status"] != "running":
            raise TaskCompletionError(
                f"Task {task_id} may not complete: task_not_running"
            )

        session_id = int(task["session_id"])

        conn.execute(
            """
            UPDATE tasks
            SET status = 'completed',
                completed_at = COALESCE(
                    completed_at,
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                result_text = COALESCE(?, result_text),
                result_json = COALESCE(?, result_json)
            WHERE task_id = ?
            """,
            (result_text, encoded_result_json, task_id),
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
                'task_completed',
                1
            )
            """,
            (session_id,),
        )

        heartbeat_id = int(cur.lastrowid)

        return TaskCompletionResult(
            task_id=task_id,
            session_id=session_id,
            heartbeat_id=heartbeat_id,
            status="completed",
            details={
                "chain_id": task["chain_id"],
                "manifest_id": task["manifest_id"],
                "task_class": task["task_class"],
                "task_type": task["task_type"],
            },
        )