from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.delegation import (
    create_delegation_packet,
    list_delegation_packets,
    load_delegation_packet,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create and inspect advisory AXIOM delegation packets."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--goal", required=True, help="Operator goal for the delegation.")
    create.add_argument("--scope", required=True, help="Delegation scope.")
    create.add_argument("--type", default="multi_agent_cycle", dest="delegation_type")
    create.add_argument("--first-agent", default="CURSOR", choices=["CURSOR", "SYN", "ARCH", "IMPL", "AUD"])
    create.add_argument("--out-of-scope", action="append", default=[])
    create.add_argument("--allowed-role", action="append", default=[])
    create.add_argument("--required-review", action="append", default=[])
    create.add_argument("--allowed-action", action="append", default=[])
    create.add_argument("--forbidden-action", action="append", default=[])
    create.add_argument("--success-criterion", action="append", default=[])
    create.add_argument("--evidence-required", action="append", default=[])
    create.add_argument("--decision-point", action="append", default=[])
    create.add_argument("--stop-condition", action="append", default=[])
    create.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("delegation_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = create_delegation_packet(
            operator_goal=args.goal,
            scope=args.scope,
            record_root=record_root,
            out_of_scope=args.out_of_scope,
            delegation_type=args.delegation_type,
            allowed_roles=args.allowed_role,
            required_reviews=args.required_review,
            allowed_actions=args.allowed_action,
            forbidden_actions=args.forbidden_action,
            success_criteria=args.success_criterion,
            evidence_required=args.evidence_required,
            decision_points=args.decision_point,
            stop_conditions=args.stop_condition,
            recommended_first_agent=args.first_agent,
        )
        payload = result.to_dict()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("AXIOM delegation packet created")
            print("===============================")
            print(f"path: {payload['path']}")
            print(f"delegation_id: {payload['packet']['delegation_id']}")
            print("authority_status: advisory_only")
            print("runtime_action_executed: False")
            print("ledger_written: False")
        return 0

    if args.command == "list":
        packets = list_delegation_packets(record_root=record_root)
        if args.json:
            print(json.dumps({"delegations": packets}, indent=2, sort_keys=True))
        else:
            print("AXIOM delegation packets")
            print("========================")
            for packet in packets:
                print(f"{packet['delegation_id']} | {packet['scope']} | {packet['status']}")
        return 0

    if args.command == "show":
        packet = load_delegation_packet(args.delegation_id, record_root=record_root)
        if args.json:
            print(json.dumps(packet, indent=2, sort_keys=True))
        else:
            print("AXIOM delegation packet")
            print("=======================")
            print(f"delegation_id: {packet.get('delegation_id')}")
            print(f"scope: {packet.get('scope')}")
            print(f"operator_goal: {packet.get('operator_goal')}")
            print(f"authority_status: {packet.get('authority_status')}")
            print(f"recommended_first_agent: {packet.get('recommended_first_agent')}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
