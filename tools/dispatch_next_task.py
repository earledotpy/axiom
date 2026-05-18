from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.core.scheduler_dispatcher import dispatch_next_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dispatch the next eligible pending AXIOM task."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--manual-test-override",
        action="store_true",
        help=(
            "Allow this direct dispatch CLI to dispatch while autonomous readiness "
            "is blocked. Intended only for controlled manual/test use."
        ),
    )
    args = parser.parse_args()

    decision = evaluate_autonomous_readiness()

    if not decision.allowed and not args.manual_test_override:
        reasons = ", ".join(decision.blocking_reasons) or "unknown"
        payload = {
            "dispatched": False,
            "session_id": args.session_id,
            "task_id": None,
            "reason": "autonomous_readiness_not_available",
            "blocking_reasons": decision.blocking_reasons,
            "manual_test_override_required": True,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                "dispatch_next_task blocked: autonomous readiness is not available "
                f"({reasons}). Use tools\\scheduler_tick.py for normal operation, "
                "or pass --manual-test-override for controlled manual/test use.",
                file=sys.stderr,
            )

        return 1

    result = dispatch_next_task(session_id=args.session_id)
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM scheduler dispatch")
        print("========================")
        print(f"session_id: {result.session_id}")
        print(f"dispatched: {result.dispatched}")
        print(f"task_id: {result.task_id}")
        print(f"reason: {result.reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())