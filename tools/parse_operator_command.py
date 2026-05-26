from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.operator_command_parser import OperatorCommandParser


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a local AXIOM operator command without executing it."
    )
    parser.add_argument("command", nargs="?", help="Command text, for example: status")
    parser.add_argument("--json-input", help="Structured command object as JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    if args.json_input and args.command:
        print("Use either command text or --json-input, not both.", file=sys.stderr)
        return 2

    if args.json_input:
        try:
            raw = json.loads(args.json_input)
        except json.JSONDecodeError as exc:
            print(f"Invalid --json-input: {exc}", file=sys.stderr)
            return 2
    elif args.command:
        raw = args.command
    else:
        raw = sys.stdin.read()

    result = OperatorCommandParser().parse(raw)
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM operator command parse")
        print("============================")
        print(f"accepted: {payload['accepted']}")
        print(f"command_name: {payload['command_name']}")
        print(f"manifest_id: {payload['manifest_id']}")
        print(f"rejection_reason: {payload['rejection_reason']}")
        print("runtime_action_executed: False")
        print("ledger_written: False")

    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
