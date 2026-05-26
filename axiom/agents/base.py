from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from axiom.persistence.db import get_connection


class AgentExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentExecutionResult:
    task_id: int
    session_id: int
    agent_name: str
    manifest_id: str
    started: bool
    completed: bool
    start_heartbeat_id: int
    completion_heartbeat_id: int
    artifact_id: int | None
    result_text: str
    result_json: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ManifestBoundAgentExecutor:
    agent_name: str
    required_task_class: str
    required_role_name: str

    def _get_authorized_task(self, task_id: int) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT t.task_id, t.session_id, t.chain_id, t.task_class,
                       t.task_type, t.status, t.goal_text, t.input_json,
                       t.manifest_id, mf.manifest_type, mf.role_name,
                       mf.active
                FROM tasks AS t
                LEFT JOIN manifest_fingerprints AS mf
                  ON mf.manifest_id = t.manifest_id
                WHERE t.task_id = ?
                """,
                (task_id,),
            ).fetchone()

        if row is None:
            raise AgentExecutionError(f"Task not found: {task_id}")

        task = dict(row)

        if task["status"] != "pending":
            raise AgentExecutionError(
                f"{self.agent_name} requires pending task; got {task['status']}"
            )

        if not task["manifest_id"]:
            raise AgentExecutionError(
                f"{self.agent_name} requires manifest-bound task"
            )

        if task["task_class"] != self.required_task_class:
            raise AgentExecutionError(
                f"{self.agent_name} requires {self.required_task_class} task; "
                f"got {task['task_class']}"
            )

        if task["active"] != 1:
            raise AgentExecutionError(
                f"{self.agent_name} requires active manifest fingerprint"
            )

        if task["manifest_type"] != "role":
            raise AgentExecutionError(
                f"{self.agent_name} requires role manifest; "
                f"got {task['manifest_type']}"
            )

        if task["role_name"] != self.required_role_name:
            raise AgentExecutionError(
                f"{self.agent_name} requires role_name "
                f"{self.required_role_name}; got {task['role_name']}"
            )

        return task

