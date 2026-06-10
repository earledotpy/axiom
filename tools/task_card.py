from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_card import close_task_card, create_task_card, list_task_cards, load_task_card


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and inspect AXIOM task cards.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--goal", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--risk", default="low", dest="risk_class")
    create.add_argument("--process", default="scope", choices=["scope", "architect", "implement", "audit", "synthesize"])
    create.add_argument("--allowed-action", action="append", default=[])
    create.add_argument("--forbidden-action", action="append", default=[])
    create.add_argument("--required-output", action="append", default=[])
    create.add_argument("--stop-condition", action="append", default=[])
    create.add_argument("--evidence-required", action="append", default=[])
    create.add_argument("--recommended-next-action", default="perform scoped advisory work")
    create.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("task_card_id")
    show.add_argument("--json", action="store_true")

    close = subparsers.add_parser("close")
    close.add_argument("task_card_id")
    close.add_argument("--reason", required=True)
    close.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = create_task_card(
            record_root=record_root,
            operator_goal=args.goal,
            scope=args.scope,
            risk_class=args.risk_class,
            process=args.process,
            allowed_actions=args.allowed_action,
            forbidden_actions=args.forbidden_action,
            required_outputs=args.required_output,
            stop_conditions=args.stop_condition,
            evidence_required=args.evidence_required,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "list":
        payload = {"task_cards": list_task_cards(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["task_card_id"] for item in payload["task_cards"]))
        return 0

    if args.command == "show":
        payload = load_task_card(args.task_card_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("task_card_id", ""))
        return 0

    if args.command == "close":
        payload = close_task_card(args.task_card_id, reason=args.reason, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("status", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
