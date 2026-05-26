from __future__ import annotations

import json

from axiom.agents.goal_planner import execute_goal_planning_task
from axiom.core.agent_boundary_audit import audit_agent_boundary
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import record_provider_usage
from tests.agent_test_helpers import (
    create_agent_session,
    create_agent_task,
    ensure_agent_manifest,
)


def ensure_all_agent_manifests() -> None:
    for agent_name in (
        "goal_planner",
        "task_planner",
        "tool_executor",
        "result_verifier",
    ):
        ensure_agent_manifest(agent_name)


def test_agent_boundary_audit_passes_with_registered_roles_and_no_agent_tasks():
    ensure_all_agent_manifests()

    result = audit_agent_boundary()

    assert result.passed is True
    assert result.checked_task_count == 0
    assert result.violations == []


def test_agent_boundary_audit_fails_when_required_role_manifest_missing():
    ensure_agent_manifest("task_planner")
    ensure_agent_manifest("tool_executor")
    ensure_agent_manifest("result_verifier")

    result = audit_agent_boundary()

    assert result.passed is False
    assert any(
        violation.check == "phase5_agent_role_manifests_active"
        and violation.reason == "missing_agent_role_manifest"
        and violation.details["role_name"] == "goal_planner"
        for violation in result.violations
    )


def test_agent_boundary_audit_validates_completed_agent_result_boundary():
    ensure_all_agent_manifests()
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)

    execute_goal_planning_task(task_id)

    result = audit_agent_boundary()

    assert result.passed is True
    assert result.checked_task_count == 1
    assert result.violations == []


def test_agent_boundary_audit_fails_on_runtime_call_drift():
    ensure_all_agent_manifests()
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)
    execute_goal_planning_task(task_id)

    with get_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        payload = json.loads(row["result_json"])
        payload["network_calls"] = [{"url": "https://example.invalid"}]
        conn.execute(
            "UPDATE tasks SET result_json = ? WHERE task_id = ?",
            (json.dumps(payload), task_id),
        )

    result = audit_agent_boundary()

    assert result.passed is False
    assert any(
        violation.check == "phase5_completed_agent_results_no_runtime_calls"
        and violation.reason == "agent_runtime_call_field_non_empty"
        and violation.details["field"] == "network_calls"
        for violation in result.violations
    )


def test_agent_boundary_audit_fails_on_provider_usage_for_agent_task():
    ensure_all_agent_manifests()
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)
    record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status="completed",
    )

    result = audit_agent_boundary()

    assert result.passed is False
    assert any(
        violation.check == "phase5_agent_tasks_do_not_record_provider_usage"
        and violation.reason == "agent_task_provider_usage_recorded"
        and violation.details["task_id"] == task_id
        for violation in result.violations
    )
