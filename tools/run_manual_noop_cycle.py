from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.manual_noop_cycle import ManualNoopCycleError, run_manual_noop_cycle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one manual scheduler-dispatched no-op execution cycle."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--profile-label", default="default")
    parser.add_argument(
        "--allow-when-autonomous-blocked",
        action="store_true",
        help=(
            "Required manual/test override while AXIOM is fail-closed. "
            "Allows Scheduler.run_once() to dispatch a pending task."
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = run_manual_noop_cycle(
            session_id=args.session_id,
            profile_label=args.profile_label,
            allow_when_autonomous_blocked=args.allow_when_autonomous_blocked,
        )
    except ManualNoopCycleError as exc:
        payload = {
            "cycle_completed": False,
            "session_id": args.session_id,
            "error": str(exc),
            "manual_test_override_required": True,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"manual no-op cycle blocked: {exc}", file=sys.stderr)

        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM manual no-op cycle")
        print("========================")
        print(f"session_id: {result.session_id}")
        print(f"profile_label: {result.profile_label}")
        print(f"task_id: {result.task_id}")
        print(f"executed: {result.executed}")
        print(f"execution_audit_passed: {result.execution_audit.get('passed')}")

    return 0 if result.execution_audit.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())