from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.scheduler_tick import run_scheduler_tick


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one conservative AXIOM scheduler tick."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--profile-label", default="default")
    parser.add_argument(
        "--allow-when-autonomous-blocked",
        action="store_true",
        help="Manual/test override. Do not use for autonomous operation.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_scheduler_tick(
        session_id=args.session_id,
        profile_label=args.profile_label,
        allow_when_autonomous_blocked=args.allow_when_autonomous_blocked,
    )

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM scheduler tick")
        print("====================")
        print(f"session_id: {result.session_id}")
        print(f"tick_status: {result.tick_status}")
        print(f"reason: {result.reason}")
        print(f"dispatched_task_id: {result.dispatched_task_id}")
        print(f"heartbeat_id: {result.heartbeat_id}")

    return 0 if result.tick_status in {"blocked", "idle", "running"} else 1


if __name__ == "__main__":
    raise SystemExit(main())