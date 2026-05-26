from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.noop_task_stager import (  # noqa: E402
    NoopTaskStagingError,
    stage_pending_noop_task,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage one pending manifest-bound no-op task without executing it."
    )
    parser.add_argument("--session-id", type=int, default=None)
    parser.add_argument("--manifest-id", default=None)
    parser.add_argument(
        "--goal-text",
        default="Manual staged no-op task for execution readiness verification.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = stage_pending_noop_task(
            session_id=args.session_id,
            manifest_id=args.manifest_id,
            goal_text=args.goal_text,
        )
    except NoopTaskStagingError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM staged pending no-op task")
        print("================================")
        print(f"task_id: {payload['task_id']}")
        print(f"session_id: {payload['session_id']}")
        print(f"chain_id: {payload['chain_id']}")
        print(f"manifest_id: {payload['manifest_id']}")
        print(f"status: {payload['status']}")
        print(f"task_class: {payload['task_class']}")
        print(f"task_type: {payload['task_type']}")
        print()
        print("No scheduler dispatch was run.")
        print("No task body was executed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
