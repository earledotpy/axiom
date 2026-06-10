from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.decision import list_decisions, load_decision, preview_decision, record_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview and record AXIOM Operator decisions.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--decision", required=True, choices=["approve", "reject", "defer", "narrow_scope", "request_review", "request_remediation", "archive"])
    preview.add_argument("--target-id", required=True)
    preview.add_argument("--scope", required=True)
    preview.add_argument("--source-ref", action="append", default=[])
    preview.add_argument("--rationale", default="")
    preview.add_argument("--recommended-next-action", default="record or revise decision")
    preview.add_argument("--json", action="store_true")

    record = subparsers.add_parser("record")
    record.add_argument("--preview-id", required=True)
    record.add_argument("--operator", default="Jeremy")
    record.add_argument("--confirm", required=True)
    record.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("decision_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "preview":
        result = preview_decision(
            record_root=record_root,
            decision=args.decision,
            target_id=args.target_id,
            scope=args.scope,
            source_refs=args.source_ref,
            rationale=args.rationale,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["decision"]["confirmation_token"])
        return 0

    if args.command == "record":
        result = record_decision(
            preview_id=args.preview_id,
            operator=args.operator,
            confirmation=args.confirm,
            record_root=record_root,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["decision"]["authority_status"])
        return 0

    if args.command == "list":
        payload = {"decisions": list_decisions(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["decision_id"] for item in payload["decisions"]))
        return 0

    if args.command == "show":
        payload = load_decision(args.decision_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("decision_id", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
