from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.app.bootstrap_validation import BootstrapValidator
from axiom.app.status_report import build_status_report
from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.core.supervisor_monitor import SupervisorMonitor
from axiom.persistence.db import get_connection
from tools.repair_session_state import repair_session_state


TOOL_VERSION = "verify_foundation.v2"


def _latest_session_id() -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY session_id DESC
            LIMIT 1
            """
        ).fetchone()

    return int(row["session_id"]) if row is not None else None


def _supervisor_health_payload(session_id: int | None) -> dict[str, Any]:
    if session_id is None:
        return {
            "checked": False,
            "reason": "no_session",
            "health": None,
        }

    health = SupervisorMonitor().check_session_health(session_id)

    return {
        "checked": True,
        "reason": health.reason,
        "health": health.to_dict(),
    }


def verify_foundation(profile_label: str = "default") -> dict[str, Any]:
    bootstrap_result = BootstrapValidator().run(raise_on_failure=False)
    repair_result = repair_session_state(profile_label=profile_label)
    status_report = build_status_report(profile_label=profile_label)
    readiness = evaluate_autonomous_readiness(profile_label=profile_label)

    latest_session_id = _latest_session_id()
    supervisor_health = _supervisor_health_payload(latest_session_id)

    foundation_passed = bootstrap_result.passed
    fail_closed_coherent = (
        not readiness.allowed
        and "no_current_trusted_model_profile" in readiness.blocking_reasons
        and "safe_pass_disabled" in readiness.blocking_reasons
    )

    return {
        "tool_version": TOOL_VERSION,
        "profile_label": profile_label,
        "foundation_passed": foundation_passed,
        "operational_mode": bootstrap_result.operational_mode,
        "session_repair_completed": True,
        "autonomous_allowed": readiness.allowed,
        "fail_closed_coherent": fail_closed_coherent,
        "blocking_reasons": readiness.blocking_reasons,
        "bootstrap": bootstrap_result.to_dict(),
        "session_repair": repair_result,
        "status": status_report.to_dict(),
        "autonomous_readiness": readiness.to_dict(),
        "supervisor_health": supervisor_health,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM foundation verification checks."
    )
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = verify_foundation(profile_label=args.profile_label)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print("AXIOM foundation verification")
        print("============================")
        print(f"foundation_passed: {result['foundation_passed']}")
        print(f"operational_mode: {result['operational_mode']}")
        print(f"session_repair_completed: {result['session_repair_completed']}")
        print(f"autonomous_allowed: {result['autonomous_allowed']}")
        print(f"fail_closed_coherent: {result['fail_closed_coherent']}")

        supervisor = result["supervisor_health"]
        print("")
        print("supervisor_health:")
        print(f"checked: {supervisor['checked']}")
        print(f"reason: {supervisor['reason']}")

        health = supervisor.get("health")
        if health is not None:
            print(f"healthy: {health['healthy']}")
            print(f"scheduler_stale: {health['scheduler_stale']}")
            print(f"running_count: {health['running_count']}")
            print(f"active_task_present: {health['active_task_present']}")
            print(f"active_task_status: {health['active_task_status']}")

        if result["blocking_reasons"]:
            print("")
            print("blocking_reasons:")
            for reason in result["blocking_reasons"]:
                print(f"- {reason}")

    return 0 if result["foundation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())