from __future__ import annotations

import json
from typing import Any

from axiom.agents.base import AgentExecutionResult, ManifestBoundAgentExecutor
from axiom.core.task_completer import complete_task
from axiom.core.task_starter import start_task
from axiom.persistence.repositories import create_plan_artifact


class GoalPlanner(ManifestBoundAgentExecutor):
    agent_name = "goal_planner"
    required_task_class = "goal_planning"
    required_role_name = "goal_planner"

    def execute(self, task_id: int) -> AgentExecutionResult:
        task = self._get_authorized_task(task_id)

        started = start_task(task_id)

        goal_plan = self._build_goal_plan(task)
        artifact_id = create_plan_artifact(
            task_id=task_id,
            manifest_id=task["manifest_id"],
            artifact_json=goal_plan,
            artifact_type="goal_plan",
            risk_class="ordinary",
            artifact_status="draft",
            scanner_result="not_scanned",
        )

        result_json = {
            "executor": self.agent_name,
            "task_id": task_id,
            "task_type": task["task_type"],
            "task_class": task["task_class"],
            "manifest_id": task["manifest_id"],
            "artifact_id": artifact_id,
            "artifact_type": "goal_plan",
            "artifact_status": "draft",
            "executed": True,
            "side_effects": "draft_plan_artifact_only",
            "tools_used": [],
            "model_calls": [],
            "cloud_cascade_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
            "autonomous_operation_enabled": False,
        }
        result_text = "GoalPlanner created a draft goal plan artifact."

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
            artifact_id=artifact_id,
            result_text=result_text,
            result_json=result_json,
        )

    def _build_goal_plan(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "axiom.goal_plan.v1",
            "planner": self.agent_name,
            "task_id": task["task_id"],
            "session_id": task["session_id"],
            "chain_id": task["chain_id"],
            "manifest_id": task["manifest_id"],
            "goal_text": task.get("goal_text"),
            "input_json": task.get("input_json"),
            "planning_status": "draft",
            "bounded_first_slice": True,
            "requires_human_or_future_executor_commit": True,
            "child_tasks": [],
            "authority_expansion": "none",
            "tools_used": [],
            "model_calls": [],
            "cloud_cascade_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
        }


def execute_goal_planning_task(task_id: int) -> AgentExecutionResult:
    return GoalPlanner().execute(task_id)
