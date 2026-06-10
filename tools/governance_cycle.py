from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.governance_cycle import (
    build_cycle_state,
    create_roadmap,
    format_cycle_summary,
    preview_guided_decision,
    record_guided_decision,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coordinate AXIOM governance cycles from JSON records without executing work."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show")
    show.add_argument("--json", action="store_true")

    summary = subparsers.add_parser("summary")
    summary.add_argument("--json", action="store_true")

    next_actions = subparsers.add_parser("next-actions")
    next_actions.add_argument("--json", action="store_true")

    roadmap = subparsers.add_parser("file-roadmap")
    roadmap.add_argument("--title", required=True)
    roadmap.add_argument("--scope", required=True)
    roadmap.add_argument("--item", action="append", required=True)
    roadmap.add_argument("--source-ref", action="append", default=[])
    roadmap.add_argument("--summary", default="")
    roadmap.add_argument("--json", action="store_true")

    preview = subparsers.add_parser("decision-preview")
    preview.add_argument("--decision", required=True, choices=["approve", "reject", "defer", "narrow_scope", "request_review", "request_remediation", "archive"])
    preview.add_argument("--target-id", required=True)
    preview.add_argument("--scope", required=True)
    preview.add_argument("--source-ref", action="append", default=[])
    preview.add_argument("--rationale", default="")
    preview.add_argument("--recommended-next-action", default="record or revise decision")
    preview.add_argument("--json", action="store_true")

    record = subparsers.add_parser("decision-record")
    record.add_argument("--preview-id", required=True)
    record.add_argument("--operator", default="Jeremy")
    record.add_argument("--confirm", required=True)
    record.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command in {"show", "summary", "next-actions"}:
        payload = build_cycle_state(root=args.root, record_root=record_root)
        if args.command == "next-actions":
            payload = {
                "schema": "axiom.governance_cycle_next_actions.v0.1",
                "authority_status": "advisory_only",
                "runtime_action_executed": False,
                "ledger_written": False,
                "cycles": [
                    {
                        "scope": cycle["scope"],
                        "status": cycle["status"],
                        "next_valid_actions": cycle["next_valid_actions"],
                    }
                    for cycle in payload["cycles"]
                ],
                "summary": payload["summary"],
                "failure_state": payload["failure_state"],
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(format_cycle_summary(payload if args.command != "next-actions" else build_cycle_state(root=args.root, record_root=record_root)))
        return 0

    if args.command == "file-roadmap":
        result = create_roadmap(
            record_root=record_root,
            title=args.title,
            scope=args.scope,
            items=args.item,
            source_refs=args.source_ref,
            summary=args.summary,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "decision-preview":
        result = preview_guided_decision(
            root=args.root,
            decision=args.decision,
            target_id=args.target_id,
            scope=args.scope,
            source_refs=args.source_ref,
            rationale=args.rationale,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("AXIOM guided decision preview")
            print("=============================")
            print(f"decision_id: {result['decision']['decision_id']}")
            print(f"confirmation_token: {result['decision']['confirmation_token']}")
            print("authority_status: advisory_only")
            print("runtime_action_executed: False")
            print("ledger_written: False")
        return 0

    if args.command == "decision-record":
        result = record_guided_decision(
            root=args.root,
            preview_id=args.preview_id,
            operator=args.operator,
            confirmation=args.confirm,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["decision"]["authority_status"])
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
