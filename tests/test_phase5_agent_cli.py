from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.agent_test_helpers import (
    create_agent_session,
    create_agent_task,
    ensure_agent_manifest,
)


ROOT = Path(__file__).resolve().parents[1]

CLI_CASES = {
    "goal_planner": {
        "script": "tools/execute_goal_planning_task.py",
        "executor": "goal_planner",
    },
    "task_planner": {
        "script": "tools/execute_task_planning_task.py",
        "executor": "task_planner",
    },
    "tool_executor": {
        "script": "tools/execute_tool_execution_task.py",
        "executor": "tool_executor",
    },
    "result_verifier": {
        "script": "tools/execute_result_verification_task.py",
        "executor": "result_verifier",
    },
}


def _run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_phase5_agent_cli_blocks_without_manual_override():
    ensure_agent_manifest("goal_planner")
    session_id = create_agent_session()
    task_id = create_agent_task("goal_planner", session_id)

    result = _run_script(
        [
            "tools/execute_goal_planning_task.py",
            str(task_id),
            "--json",
        ]
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["executed"] is False
    assert payload["agent_name"] == "goal_planner"
    assert payload["error"] == "autonomous_readiness_not_available"
    assert payload["manual_test_override_required"] is True


def test_phase5_agent_cli_wrappers_execute_with_manual_override():
    for agent_name, case in CLI_CASES.items():
        ensure_agent_manifest(agent_name)
        session_id = create_agent_session()
        task_id = create_agent_task(agent_name, session_id)

        result = _run_script(
            [
                case["script"],
                str(task_id),
                "--manual-test-override",
                "--json",
            ]
        )

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["agent_name"] == case["executor"]
        assert payload["task_id"] == task_id
        assert payload["started"] is True
        assert payload["completed"] is True
        assert payload["result_json"]["tools_used"] == []
        assert payload["result_json"]["model_calls"] == []
        assert payload["result_json"]["cloud_cascade_calls"] == []
        assert payload["result_json"]["network_calls"] == []
        assert payload["result_json"]["sandbox_calls"] == []


def test_register_manifests_registers_phase5_agent_roles():
    result = _run_script(["tools/register_manifests.py"])

    assert result.returncode == 0
    assert "registered" in result.stdout

    from axiom.persistence.repositories import get_manifest_fingerprint

    for manifest_id in (
        "role.goal_planner.v1",
        "role.task_planner.v1",
        "role.tool_executor.v1",
        "role.result_verifier.v1",
    ):
        row = get_manifest_fingerprint(manifest_id)
        assert row is not None
        assert row["manifest_type"] == "role"
        assert row["active"] == 1


def test_manual_agent_foundation_smoke_runs_only_with_override():
    register = _run_script(["tools/register_manifests.py"])
    assert register.returncode == 0

    blocked = _run_script(["tools/run_manual_agent_foundation_smoke.py", "--json"])
    assert blocked.returncode == 1
    blocked_payload = json.loads(blocked.stdout)
    assert blocked_payload["smoke_completed"] is False
    assert blocked_payload["manual_test_override_required"] is True

    result = _run_script(
        [
            "tools/run_manual_agent_foundation_smoke.py",
            "--allow-when-autonomous-blocked",
            "--json",
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["smoke_completed"] is True
    assert payload["agents_executed"] == [
        "goal_planner",
        "task_planner",
        "tool_executor",
        "result_verifier",
    ]
    assert payload["runtime_calls"]["tools_used"] == []
    assert payload["runtime_calls"]["model_calls"] == []
    assert payload["runtime_calls"]["cloud_cascade_calls"] == []
    assert payload["runtime_calls"]["network_calls"] == []
    assert payload["runtime_calls"]["sandbox_calls"] == []
    assert payload["autonomous_operation_enabled"] is False
