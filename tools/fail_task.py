from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_failer import TaskFailureError, fail_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail an AXIOM running task and clear scheduler heartbeat."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--error-type", default="execution_error")
    parser.add_argument("--message", default="Task execution failed.")
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
        result = fail_task(
            task_id=args.task_id,
            error_type=args.error_type,
            message=args.message,
            details=details,
        )
    except TaskFailureError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "failed": False,
                        "task_id": args.task_id,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"task failure failed: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task failure")
        print("==================")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"heartbeat_id: {result.heartbeat_id}")
        print(f"status: {result.status}")
        print(f"error_type: {result.details.get('error_type')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())