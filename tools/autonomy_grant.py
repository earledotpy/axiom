from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.autonomy_grant import (
    accept_autonomy_grant,
    draft_autonomy_grant,
    list_autonomy_grants,
    load_autonomy_grant,
    revoke_autonomy_grant,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and inspect AXIOM autonomy grant records without enabling runtime autonomy.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft = subparsers.add_parser("draft")
    draft.add_argument("--scope", required=True)
    draft.add_argument("--level", default="A0", dest="autonomy_level")
    draft.add_argument("--allowed-role", action="append", default=[])
    draft.add_argument("--allowed-action", action="append", default=[])
    draft.add_argument("--forbidden-action", action="append", default=[])
    draft.add_argument("--protected-surface", action="append", default=[])
    draft.add_argument("--required-evidence", action="append", default=[])
    draft.add_argument("--stop-condition", action="append", default=[])
    draft.add_argument("--max-cycles", type=int, default=1)
    draft.add_argument("--expires-utc", default="")
    draft.add_argument("--json", action="store_true")

    accept = subparsers.add_parser("accept")
    accept.add_argument("grant_id")
    accept.add_argument("--decision-id", required=True)
    accept.add_argument("--technical-gate-result", required=True)
    accept.add_argument("--json", action="store_true")

    revoke = subparsers.add_parser("revoke")
    revoke.add_argument("grant_id")
    revoke.add_argument("--reason", required=True)
    revoke.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("grant_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "draft":
        result = draft_autonomy_grant(
            record_root=record_root,
            scope=args.scope,
            autonomy_level=args.autonomy_level,
            allowed_roles=args.allowed_role,
            allowed_actions=args.allowed_action,
            forbidden_actions=args.forbidden_action,
            protected_surfaces=args.protected_surface,
            required_evidence=args.required_evidence,
            stop_conditions=args.stop_condition,
            max_cycles=args.max_cycles,
            expires_utc=args.expires_utc,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "accept":
        result = accept_autonomy_grant(
            grant_id=args.grant_id,
            operator_decision_id=args.decision_id,
            technical_gate_result=args.technical_gate_result,
            record_root=record_root,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["grant"]["grant_state"])
        return 0

    if args.command == "revoke":
        result = revoke_autonomy_grant(grant_id=args.grant_id, reason=args.reason, record_root=record_root).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["grant"]["grant_state"])
        return 0

    if args.command == "list":
        payload = {"autonomy_grants": list_autonomy_grants(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["grant_id"] for item in payload["autonomy_grants"]))
        return 0

    if args.command == "show":
        payload = load_autonomy_grant(args.grant_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("grant_id", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
