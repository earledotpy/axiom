from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.scheduler_dispatcher import dispatch_next_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dispatch the next eligible pending AXIOM task."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

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
        print(f"status: {result.status}")
        print(f"reason: {result.reason}")
        print(f"heartbeat_id: {result.heartbeat_id}")

    return 0 if result.status in {"running", "idle", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())