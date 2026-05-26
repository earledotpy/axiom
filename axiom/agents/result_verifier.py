from __future__ import annotations

import json
from typing import Any

from axiom.agents.base import AgentExecutionResult, ManifestBoundAgentExecutor
from axiom.core.task_completer import complete_task
from axiom.core.task_starter import start_task


class ResultVerifier(ManifestBoundAgentExecutor):
    agent_name = "result_verifier"
    required_task_class = "result_verification"
    required_role_name = "result_verifier"

    def execute(self, task_id: int) -> AgentExecutionResult:
        task = self._get_authorized_task(task_id)

        started = start_task(task_id)

        verification_summary = self._build_verification_summary(task)
        result_json = {
            "executor": self.agent_name,
            "task_id": task_id,
            "task_type": task["task_type"],
            "task_class": task["task_class"],
            "manifest_id": task["manifest_id"],
            "artifact_id": None,
            "artifact_type": None,
            "artifact_status": None,
            "executed": True,
            "side_effects": "result_verification_summary_only",
            "verification_summary": verification_summary,
            "tools_used": [],
            "model_calls": [],
            "cloud_cascade_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
            "autonomous_operation_enabled": False,
        }
        result_text = "ResultVerifier completed a deterministic verification summary."

        completed = complete_task(
            task_id=task_id,
            result_text=result_text,
            result_json=json.dumps(result_json, sort_keys=True),
        )

        return AgentExecutionResult(
            task_id=task_id,
            session_id=started.session_id,
            agent_name=self.agent_name,
            manifest_id=task["manifest_id"],
            started=True,
            completed=True,
            start_heartbeat_id=started.heartbeat_id,
            completion_heartbeat_id=completed.heartbeat_id,
            artifact_id=None,
            result_text=result_text,
            result_json=result_json,
        )

    def _build_verification_summary(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "axiom.result_verification_summary.v1",
            "verifier": self.agent_name,
            "task_id": task["task_id"],
            "session_id": task["session_id"],
            "chain_id": task["chain_id"],
            "manifest_id": task["manifest_id"],
            "goal_text": task.get("goal_text"),
            "input_json": task.get("input_json"),
            "verification_status": "summary_only",
            "artifact_created": False,
            "requires_human_or_future_executor_commit": True,
            "authority_expansion": "none",
            "tools_used": [],
            "model_calls": [],
            "cloud_cascade_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
        }


def execute_result_verification_task(task_id: int) -> AgentExecutionResult:
    return ResultVerifier().execute(task_id)
