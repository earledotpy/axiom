import json

import pytest

from axiom.agents.base import AgentExecutionError
from axiom.agents.result_verifier import execute_result_verification_task
from axiom.persistence.db import get_connection
from tests.agent_test_helpers import (
    create_agent_session,
    create_agent_task,
    ensure_agent_manifest,
)


RESULT_VERIFIER_MANIFEST_ID = "role.result_verifier.v1"

def test_result_verifier_completes_summary_without_runtime_calls_or_artifacts():
    ensure_agent_manifest("result_verifier")
    session_id = create_agent_session()
    task_id = create_agent_task("result_verifier", session_id)

    result = execute_result_verification_task(task_id)

    assert result.task_id == task_id
    assert result.session_id == session_id
    assert result.agent_name == "result_verifier"
    assert result.manifest_id == RESULT_VERIFIER_MANIFEST_ID
    assert result.started is True
    assert result.completed is True
    assert result.start_heartbeat_id > 0
    assert result.completion_heartbeat_id > 0
    assert result.artifact_id is None
    assert result.result_json["side_effects"] == "result_verification_summary_only"
    assert result.result_json["artifact_id"] is None
    assert result.result_json["artifact_type"] is None
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
        artifact_count = conn.execute(
            "SELECT COUNT(*) AS count FROM plan_artifacts WHERE task_id = ?",
            (task_id,),
        ).fetchone()["count"]

    assert task["status"] == "completed"
    assert task["result_text"] == (
        "ResultVerifier completed a deterministic verification summary."
    )
    assert artifact_count == 0

    stored_result = json.loads(task["result_json"])
    assert stored_result["executor"] == "result_verifier"
    summary = stored_result["verification_summary"]
    assert summary["schema_version"] == "axiom.result_verification_summary.v1"
    assert summary["artifact_created"] is False
    assert summary["requires_human_or_future_executor_commit"] is True
    assert summary["authority_expansion"] == "none"


def test_result_verifier_rejects_task_without_manifest():
    session_id = create_agent_session()
    task_id = create_agent_task("result_verifier", session_id, manifest_id=None)

    with pytest.raises(AgentExecutionError, match="requires manifest-bound task"):
        execute_result_verification_task(task_id)


def test_result_verifier_rejects_non_result_verification_task():
    ensure_agent_manifest("result_verifier")
    session_id = create_agent_session()
    task_id = create_agent_task("result_verifier", session_id, task_class="tool_execution")

    with pytest.raises(AgentExecutionError, match="requires result_verification task"):
        execute_result_verification_task(task_id)


def test_result_verifier_rejects_inactive_manifest():
    ensure_agent_manifest("result_verifier", active=0)
    session_id = create_agent_session()
    task_id = create_agent_task("result_verifier", session_id)

    with pytest.raises(AgentExecutionError, match="requires active manifest"):
        execute_result_verification_task(task_id)


def test_result_verifier_rejects_non_pending_task():
    ensure_agent_manifest("result_verifier")
    session_id = create_agent_session()
    task_id = create_agent_task("result_verifier", session_id, status="completed")

    with pytest.raises(AgentExecutionError, match="requires pending task"):
        execute_result_verification_task(task_id)
