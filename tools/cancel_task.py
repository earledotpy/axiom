from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_canceller import TaskCancellationError, cancel_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cancel an AXIOM pending or running task."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--reason", default="operator_cancelled")
    parser.add_argument("--details-json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    details = None
    if args.details_json is not None:
        try:
            details = json.loads(args.details_json)
        except json.JSONDecodeError as exc:
            print(f"invalid --details-json: {exc}", file=sys.stderr)
            return 2

    try:
        result = cancel_task(
            task_id=args.task_id,
            reason=args.reason,
            details=details,
        )
    except TaskCancellationError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "cancelled": False,
                        "task_id": args.task_id,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"task cancellation failed: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task cancellation")
        print("=======================")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"heartbeat_id: {result.heartbeat_id}")
        print(f"status: {result.status}")
        print(f"previous_status: {result.details.get('previous_status')}")
        print(f"reason: {result.details.get('reason')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())