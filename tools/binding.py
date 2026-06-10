from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.binding import apply_binding, list_bindings, load_binding


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply and inspect AXIOM binding records.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_cmd = subparsers.add_parser("apply")
    apply_cmd.add_argument("--decision-id", required=True)
    apply_cmd.add_argument("--binding-type", required=True)
    apply_cmd.add_argument("--target", required=True)
    apply_cmd.add_argument("--scope", required=True)
    apply_cmd.add_argument("--summary", default="")
    apply_cmd.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("binding_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "apply":
        result = apply_binding(
            record_root=record_root,
            operator_decision_id=args.decision_id,
            binding_type=args.binding_type,
            target=args.target,
            scope=args.scope,
            summary=args.summary,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "list":
        payload = {"bindings": list_bindings(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["binding_id"] for item in payload["bindings"]))
        return 0

    if args.command == "show":
        payload = load_binding(args.binding_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("binding_id", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
