from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from axiom.core.task_completer import complete_task
from axiom.core.task_starter import start_task
from axiom.persistence.db import get_connection


class NoopTaskExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class NoopTaskExecutionResult:
    task_id: int
    session_id: int
    started: bool
    completed: bool
    start_heartbeat_id: int
    completion_heartbeat_id: int
    result_text: str
    result_json: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "started": self.started,
            "completed": self.completed,
            "start_heartbeat_id": self.start_heartbeat_id,
            "completion_heartbeat_id": self.completion_heartbeat_id,
            "result_text": self.result_text,
            "result_json": self.result_json,
        }


def _get_task(task_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id, session_id, chain_id, task_class, task_type,
                   status, manifest_id
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    if row is None:
        raise NoopTaskExecutionError(f"Task not found: {task_id}")

    return dict(row)


def execute_noop_task(task_id: int) -> NoopTaskExecutionResult:
    """
    Execute a manifest-bound task through a deterministic no-op harness.

    This does not call tools, models, network, sandbox, agents, or planners.
    It only validates the lifecycle path:
        pending -> running -> completed
    """
    task = _get_task(task_id)

    if task["status"] != "pending":
        raise NoopTaskExecutionError(
            f"No-op executor requires pending task; got {task['status']}"
        )

    if not task["manifest_id"]:
        raise NoopTaskExecutionError(
            "No-op executor requires manifest-bound task"
        )

    started = start_task(task_id)

    result_json = {
        "executor": "noop_task_executor",
        "task_id": task_id,
        "task_type": task["task_type"],
        "task_class": task["task_class"],
        "executed": True,
        "side_effects": "none",
        "tools_used": [],
        "model_calls": [],
        "network_calls": [],
        "sandbox_calls": [],
    }
    result_text = "No-op task execution completed."

    completed = complete_task(
        task_id=task_id,
        result_text=result_text,
        result_json=json.dumps(result_json, sort_keys=True),
    )

    return NoopTaskExecutionResult(
        task_id=task_id,
        session_id=started.session_id,
        started=True,
        completed=True,
        start_heartbeat_id=started.heartbeat_id,
        completion_heartbeat_id=completed.heartbeat_id,
        result_text=result_text,
        result_json=result_json,
    )
    
    
def complete_running_noop_task(task_id: int) -> NoopTaskExecutionResult:
    """
    Complete a task that has already been moved to running by the scheduler.

    This is for scheduler-dispatched manual/test cycles only. It does not
    call tools, models, network, sandbox, agents, or planners.
    """
    task = _get_task(task_id)

    if task["status"] != "running":
        raise NoopTaskExecutionError(
            f"Running no-op completion requires running task; got {task['status']}"
        )

    if not task["manifest_id"]:
        raise NoopTaskExecutionError(
            "Running no-op completion requires manifest-bound task"
        )

    result_json = {
        "executor": "noop_task_executor",
        "task_id": task_id,
        "task_type": task["task_type"],
        "task_class": task["task_class"],
        "executed": True,
        "side_effects": "none",
        "tools_used": [],
        "model_calls": [],
        "network_calls": [],
        "sandbox_calls": [],
    }
    result_text = "No-op task execution completed."

    completed = complete_task(
        task_id=task_id,
        result_text=result_text,
        result_json=json.dumps(result_json, sort_keys=True),
    )

    return NoopTaskExecutionResult(
        task_id=task_id,
        session_id=task["session_id"],
        started=True,
        completed=True,
        start_heartbeat_id=0,
        completion_heartbeat_id=completed.heartbeat_id,
        result_text=result_text,
        result_json=result_json,
    )