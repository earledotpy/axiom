from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.operator_console import COMMAND_TO_VIEW, build_command_output, build_console_state


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render read-only AXIOM Operator Console views from governance JSON records."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(COMMAND_TO_VIEW),
        help="Read-only console command, for example /axiom:show-active-state.",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", action="store_true", help="Print the full console state object.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text mode is a compact summary.")
    args = parser.parse_args()

    if args.state:
        payload = build_console_state(root=args.root)
    else:
        command = args.command or "/axiom:show-active-state"
        payload = build_command_output(command, root=args.root)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_summary(payload)

    return 0


def _print_summary(payload: dict) -> None:
    print("AXIOM Operator Console")
    print("======================")
    print(f"schema: {payload['schema']}")
    print(f"authority_status: {payload['authority_status']}")
    if "view" in payload:
        print(f"command: {payload['command']}")
        print(f"view: {payload['view']}")
    print(f"failed_closed: {payload['failure_state']['failed_closed']}")
    print(f"recommended_next_actions: {', '.join(payload['recommended_next_actions'])}")

    data = payload.get("data", payload)
    summary = data.get("summary")
    if isinstance(summary, dict):
        print("")
        print("summary:")
        for key, value in summary.items():
            print(f"- {key}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
