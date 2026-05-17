from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_completer import TaskCompletionError, complete_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Complete an AXIOM running task and clear scheduler heartbeat."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--result-text")
    parser.add_argument("--result-json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    parsed_result_json = None
    if args.result_json is not None:
        try:
            parsed_result_json = json.loads(args.result_json)
        except json.JSONDecodeError as exc:
            print(f"invalid --result-json: {exc}", file=sys.stderr)
            return 2

    try:
        result = complete_task(
            task_id=args.task_id,
            result_text=args.result_text,
            result_json=parsed_result_json,
        )
    except TaskCompletionError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "completed": False,
                        "task_id": args.task_id,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"task completion failed: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task completion")
        print("=====================")
        print(f"task_id: {result.task_id}")
        print(f"session_id: {result.session_id}")
        print(f"heartbeat_id: {result.heartbeat_id}")
        print(f"status: {result.status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())