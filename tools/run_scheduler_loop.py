from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.scheduler_loop import run_scheduler_loop


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a bounded foreground AXIOM scheduler loop."
    )
    parser.add_argument("session_id", type=int)
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--max-ticks", type=int, default=1)
    parser.add_argument(
        "--allow-when-autonomous-blocked",
        action="store_true",
        help=(
            "Manual/test override. Allows the loop to dispatch even when "
            "autonomous readiness is blocked."
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = run_scheduler_loop(
            session_id=args.session_id,
            profile_label=args.profile_label,
            max_ticks=args.max_ticks,
            allow_when_autonomous_blocked=args.allow_when_autonomous_blocked,
        )
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "loop_completed": False,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"scheduler loop failed: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM scheduler loop")
        print("====================")
        print(f"session_id: {result.session_id}")
        print(f"profile_label: {result.profile_label}")
        print(f"ticks_requested: {result.ticks_requested}")
        print(f"ticks_run: {result.ticks_run}")
        print(f"stopped_reason: {result.stopped_reason}")
        print(f"final_tick_status: {result.final_tick_status}")
        print(f"execution_result: {result.execution_result}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
