from __future__ import annotations

import json
import sys
from collections.abc import Callable

from axiom.agents.base import AgentExecutionError, AgentExecutionResult
from axiom.core.autonomous_gate import evaluate_autonomous_readiness


def run_manual_agent_cli(
    *,
    agent_name: str,
    task_id: int,
    execute: Callable[[int], AgentExecutionResult],
    json_output: bool,
    manual_test_override: bool,
) -> int:
    decision = evaluate_autonomous_readiness()

    if not decision.allowed and not manual_test_override:
        reasons = ", ".join(decision.blocking_reasons) or "unknown"
        payload = {
            "executed": False,
            "agent_name": agent_name,
            "task_id": task_id,
            "error": "autonomous_readiness_not_available",
            "blocking_reasons": decision.blocking_reasons,
            "manual_test_override_required": True,
        }

        if json_output:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"{agent_name} blocked: autonomous readiness is not available "
                f"({reasons}). Pass --manual-test-override for controlled "
                "manual/test use.",
                file=sys.stderr,
            )

        return 1

    try:
        result = execute(task_id)
    except AgentExecutionError as exc:
        payload = {
            "executed": False,
            "agent_name": agent_name,
            "task_id": task_id,
            "error": str(exc),
        }

        if json_output:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"{agent_name} failed: {exc}", file=sys.stderr)

        return 1

    payload = result.to_dict()

    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"AXIOM manual {agent_name}")
        print("=" * (14 + len(agent_name)))
        print("executed: True")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"manifest_id: {result.manifest_id}")
        print(f"started: {result.started}")
        print(f"completed: {result.completed}")
        print(f"artifact_id: {result.artifact_id}")
        print(f"result_text: {result.result_text}")

    return 0

