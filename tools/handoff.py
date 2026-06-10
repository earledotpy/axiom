from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.handoff import create_handoff, list_handoffs, load_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and inspect AXIOM handoff records.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--title", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--type", default="synthesis", dest="artifact_type")
    create.add_argument("--actor-role", default="CURSOR", choices=["CURSOR", "SYN", "ARCH", "IMPL", "AUD"])
    create.add_argument("--summary", default="")
    create.add_argument("--source-ref", action="append", default=[])
    create.add_argument("--finding", action="append", default=[])
    create.add_argument("--blocking", action="append", default=[])
    create.add_argument("--concern", action="append", default=[])
    create.add_argument("--recommended-decision", default="")
    create.add_argument("--recommended-next-action", default="review handoff")
    create.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("artifact_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = create_handoff(
            record_root=record_root,
            title=args.title,
            scope=args.scope,
            artifact_type=args.artifact_type,
            actor_role=args.actor_role,
            summary=args.summary,
            source_refs=args.source_ref,
            findings=args.finding,
            blocking_objections=args.blocking,
            non_blocking_concerns=args.concern,
            recommended_operator_decision=args.recommended_decision,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "list":
        payload = {"handoffs": list_handoffs(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["artifact_id"] for item in payload["handoffs"]))
        return 0

    if args.command == "show":
        payload = load_handoff(args.artifact_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("artifact_id", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
