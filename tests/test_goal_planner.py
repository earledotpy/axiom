import json

import pytest

from axiom.agents.base import AgentExecutionError
from axiom.agents.goal_planner import execute_goal_planning_task
from axiom.persistence.db import get_connection
from tests.agent_test_helpers import (
    create_agent_session,
    create_agent_task,
    ensure_agent_manifest,
)


GOAL_PLANNER_MANIFEST_ID = "role.goal_planner.v1"


def test_goal_planner_creates_draft_goal_plan_without_runtime_calls():
    ensure_agent_manifest("goal_planner")
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)

    result = execute_goal_planning_task(task_id)

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.agent_name == "goal_planner"
    assert result.manifest_id == GOAL_PLANNER_MANIFEST_ID
    assert result.started is True
    assert result.completed is True
    assert result.start_heartbeat_id > 0
    assert result.completion_heartbeat_id > 0
    assert result.artifact_id is not None
    assert result.result_json["side_effects"] == "draft_plan_artifact_only"
    assert result.result_json["tools_used"] == []
    assert result.result_json["model_calls"] == []
    assert result.result_json["cloud_cascade_calls"] == []
    assert result.result_json["network_calls"] == []
    assert result.result_json["sandbox_calls"] == []
    assert result.result_json["autonomous_operation_enabled"] is False

    with get_connection() as conn:
        task = conn.execute(
            "SELECT status, result_text, result_json FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        artifact = conn.execute(
            """
            SELECT artifact_type, artifact_status, risk_class, scanner_result,
                   artifact_json, manifest_id
            FROM plan_artifacts
            WHERE artifact_id = ?
            """,
            (result.artifact_id,),
        ).fetchone()

    assert task["status"] == "completed"
    assert task["result_text"] == "GoalPlanner created a draft goal plan artifact."
    stored_result = json.loads(task["result_json"])
    assert stored_result["executor"] == "goal_planner"

    assert artifact["artifact_type"] == "goal_plan"
    assert artifact["artifact_status"] == "draft"
    assert artifact["risk_class"] == "ordinary"
    assert artifact["scanner_result"] == "not_scanned"
    assert artifact["manifest_id"] == GOAL_PLANNER_MANIFEST_ID

    plan = json.loads(artifact["artifact_json"])
    assert plan["schema_version"] == "axiom.goal_plan.v1"
    assert plan["requires_human_or_future_executor_commit"] is True
    assert plan["authority_expansion"] == "none"
    assert plan["child_tasks"] == []


def test_goal_planner_rejects_task_without_manifest():
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id, manifest_id=None)

    with pytest.raises(AgentExecutionError, match="requires manifest-bound task"):
        execute_goal_planning_task(task_id)


def test_goal_planner_rejects_non_goal_planning_task():
    ensure_agent_manifest("goal_planner")
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id, task_class="task_planning")

    with pytest.raises(AgentExecutionError, match="requires goal_planning task"):
        execute_goal_planning_task(task_id)


def test_goal_planner_rejects_inactive_manifest():
    ensure_agent_manifest("goal_planner", active=0)
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)

    with pytest.raises(AgentExecutionError, match="requires active manifest"):
        execute_goal_planning_task(task_id)


def test_goal_planner_rejects_non_pending_task():
    ensure_agent_manifest("goal_planner")
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id, status="completed")

    with pytest.raises(AgentExecutionError, match="requires pending task"):
        execute_goal_planning_task(task_id)
