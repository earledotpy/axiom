from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.agents.base import AgentExecutionResult  # noqa: E402
from axiom.agents.goal_planner import execute_goal_planning_task  # noqa: E402
from axiom.agents.result_verifier import execute_result_verification_task  # noqa: E402
from axiom.agents.task_planner import execute_task_planning_task  # noqa: E402
from axiom.agents.tool_executor import execute_tool_execution_task  # noqa: E402
from axiom.core.autonomous_gate import evaluate_autonomous_readiness  # noqa: E402
from axiom.persistence.repositories import (  # noqa: E402
    create_session,
    create_task,
    get_manifest_fingerprint,
)


AGENT_SEQUENCE: tuple[dict[str, object], ...] = (
    {
        "agent_name": "goal_planner",
        "manifest_id": "role.goal_planner.v1",
        "task_class": "goal_planning",
        "task_type": "phase5_manual_goal_planning_smoke",
        "goal_text": "Manual smoke: create a bounded draft goal plan.",
        "execute": execute_goal_planning_task,
    },
    {
        "agent_name": "task_planner",
        "manifest_id": "role.task_planner.v1",
        "task_class": "task_planning",
        "task_type": "phase5_manual_task_planning_smoke",
        "goal_text": "Manual smoke: create a bounded draft task plan.",
        "execute": execute_task_planning_task,
    },
    {
        "agent_name": "tool_executor",
        "manifest_id": "role.tool_executor.v1",
        "task_class": "tool_execution",
        "task_type": "phase5_manual_tool_execution_smoke",
        "goal_text": "Manual smoke: create a bounded draft tool plan.",
        "execute": execute_tool_execution_task,
    },
    {
        "agent_name": "result_verifier",
        "manifest_id": "role.result_verifier.v1",
        "task_class": "result_verification",
        "task_type": "phase5_manual_result_verification_smoke",
        "goal_text": "Manual smoke: create a deterministic verification summary.",
        "execute": execute_result_verification_task,
    },
)


def _require_active_agent_manifests() -> None:
    missing = []
    for item in AGENT_SEQUENCE:
        manifest_id = str(item["manifest_id"])
        row = get_manifest_fingerprint(manifest_id)
        if row is None:
            missing.append(manifest_id)

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Missing active Phase 5 agent manifests. Run "
            f"tools/register_manifests.py first. Missing: {joined}"
        )


def run_manual_agent_foundation_smoke(
    *,
    allow_when_autonomous_blocked: bool,
) -> dict[str, object]:
    decision = evaluate_autonomous_readiness()
    if not decision.allowed and not allow_when_autonomous_blocked:
        return {
            "smoke_completed": False,
            "error": "autonomous_readiness_not_available",
            "blocking_reasons": decision.blocking_reasons,
            "manual_test_override_required": True,
            "agents_executed": [],
        }

    _require_active_agent_manifests()
    session_id = create_session(operator_id="phase5_manual_agent_smoke")
    results: list[dict[str, object]] = []

    for item in AGENT_SEQUENCE:
        task_id = create_task(
            session_id=session_id,
            chain_id=f"phase5-manual-agent-smoke-{session_id}",
            task_class=str(item["task_class"]),
            task_type=str(item["task_type"]),
            priority=5,
            goal_text=str(item["goal_text"]),
            input_json={
                "source": "manual_agent_foundation_smoke",
                "agent_name": item["agent_name"],
            },
            manifest_id=str(item["manifest_id"]),
        )
        execute = item["execute"]
        result = execute(task_id)  # type: ignore[operator]
        if not isinstance(result, AgentExecutionResult):
            raise RuntimeError(f"Unexpected agent result for {item['agent_name']}")
        results.append(result.to_dict())

    return {
        "smoke_completed": True,
        "session_id": session_id,
        "agents_executed": [str(item["agent_name"]) for item in AGENT_SEQUENCE],
        "results": results,
        "runtime_calls": {
            "tools_used": [],
            "model_calls": [],
            "cloud_cascade_calls": [],
            "network_calls": [],
            "sandbox_calls": [],
        },
        "autonomous_operation_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the manual Phase 5 agent foundation smoke path."
    )
    parser.add_argument(
        "--allow-when-autonomous-blocked",
        action="store_true",
        help="Required manual/test override while AXIOM is fail-closed.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        payload = run_manual_agent_foundation_smoke(
            allow_when_autonomous_blocked=args.allow_when_autonomous_blocked,
        )
    except Exception as exc:
        payload = {
            "smoke_completed": False,
            "error": str(exc),
            "agents_executed": [],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"manual agent foundation smoke failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM manual agent foundation smoke")
        print("===================================")
        print(f"smoke_completed: {payload['smoke_completed']}")
        print(f"agents_executed: {', '.join(payload['agents_executed'])}")

    return 0 if payload.get("smoke_completed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
