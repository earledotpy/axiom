from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.operator_command_ledger import record_operator_command_intent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record approved AXIOM operator command intent without executing it."
    )
    parser.add_argument("command", nargs="?", help="Command text, for example: status")
    parser.add_argument("--json-input", help="Structured command object as JSON.")
    parser.add_argument(
        "--operator-id",
        default="local_operator",
        help="Local operator identity label for task input_json.",
    )
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

    result = record_operator_command_intent(raw, operator_id=args.operator_id)
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM operator command intent record")
        print("====================================")
        print(f"recorded: {payload['recorded']}")
        print(f"command_id: {payload['command_id']}")
        print(f"task_id: {payload['task_id']}")
        print(f"command_name: {payload['command_name']}")
        print(f"manifest_id: {payload['manifest_id']}")
        print(f"authorization_status: {payload['authorization_status']}")
        print(f"command_status: {payload['command_status']}")
        print(f"rejection_reason: {payload['rejection_reason']}")
        print("runtime_action_executed: False")
        print(f"ledger_written: {payload['ledger_written']}")

    return 0 if result.recorded else 1


if __name__ == "__main__":
    raise SystemExit(main())
