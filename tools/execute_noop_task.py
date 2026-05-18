from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.noop_task_executor import (
    NoopTaskExecutionError,
    execute_noop_task,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute a manifest-bound AXIOM task using the no-op executor."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = execute_noop_task(task_id=args.task_id)
    except NoopTaskExecutionError as exc:
        payload = {
            "executed": False,
            "task_id": args.task_id,
            "error": str(exc),
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"execute_noop_task failed: {exc}", file=sys.stderr)

        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM no-op task execution")
        print("==========================")
        print(f"executed: True")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"started: {result.started}")
        print(f"completed: {result.completed}")
        print(f"start_heartbeat_id: {result.start_heartbeat_id}")
        print(f"completion_heartbeat_id: {result.completion_heartbeat_id}")
        print(f"result_text: {result.result_text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())