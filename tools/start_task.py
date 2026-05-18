from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.core.task_starter import TaskStartError, start_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start an AXIOM task using lifecycle guard and heartbeat write."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--manual-test-override",
        action="store_true",
        help=(
            "Allow this direct lifecycle CLI to start a task while autonomous "
            "readiness is blocked. Intended only for controlled manual/test use."
        ),
    )
    args = parser.parse_args()

    decision = evaluate_autonomous_readiness()

    if not decision.allowed and not args.manual_test_override:
        reasons = ", ".join(decision.blocking_reasons) or "unknown"
        payload = {
            "started": False,
            "task_id": args.task_id,
            "error": "autonomous_readiness_not_available",
            "blocking_reasons": decision.blocking_reasons,
            "manual_test_override_required": True,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                "start_task blocked: autonomous readiness is not available "
                f"({reasons}). Use tools\\scheduler_tick.py for normal operation, "
                "or pass --manual-test-override for controlled manual/test use.",
                file=sys.stderr,
            )

        return 1

    try:
        result = start_task(args.task_id)
    except TaskStartError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "started": False,
                        "task_id": args.task_id,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"start_task failed: {exc}", file=sys.stderr)
        return 1

    payload = {
        "started": True,
        "task_id": result.task_id,
        "session_id": result.session_id,
        "heartbeat_id": result.heartbeat_id,
        "status": result.status,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task start")
        print("================")
        print(f"started: True")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"heartbeat_id: {result.heartbeat_id}")
        print(f"status: {result.status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())