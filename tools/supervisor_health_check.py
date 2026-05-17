from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.supervisor_monitor import SupervisorMonitor


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check AXIOM supervisor health for a session."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--stale-threshold-seconds", type=int, default=120)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    monitor = SupervisorMonitor(
        stale_threshold_seconds=args.stale_threshold_seconds
    )
    health = monitor.check_session_health(args.session_id)
    payload = health.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM supervisor health")
        print("=======================")
        print(f"healthy: {health.healthy}")
        print(f"session_id: {health.session_id}")
        print(f"scheduler_stale: {health.scheduler_stale}")
        print(f"running_task_invariant_valid: {health.running_task_invariant_valid}")
        print(f"running_count: {health.running_count}")
        print(f"active_task_present: {health.active_task_present}")
        print(f"active_task_status: {health.active_task_status}")
        print(f"reason: {health.reason}")

    return 0 if health.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())