from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.evaluation import (
    build_blocker_summary,
    create_evaluation_report,
    list_evaluation_reports,
    load_evaluation_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create and inspect advisory AXIOM evaluation reports."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--target-artifact", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--actor", default="Claude Code", dest="evaluating_actor")
    create.add_argument("--actor-role", default="AUD", choices=["AUD", "ARCH", "IMPL", "CURSOR", "SYN"])
    create.add_argument("--target-lifecycle-state", default="unknown")
    create.add_argument("--type", default="governance_audit", dest="evaluation_type")
    create.add_argument("--verdict", default="not_evaluated")
    create.add_argument("--input-reviewed", action="append", default=[])
    create.add_argument("--check-performed", action="append", default=[])
    create.add_argument("--finding", action="append", default=[])
    create.add_argument("--blocking", action="append", default=[])
    create.add_argument("--concern", action="append", default=[])
    create.add_argument("--affected-layer", default="Evaluation")
    create.add_argument("--evidence-quality", default="not_evaluated")
    create.add_argument("--scope-compliance", default="not_evaluated")
    create.add_argument("--doctrine-compliance", default="not_evaluated")
    create.add_argument("--workflow-compliance", default="not_evaluated")
    create.add_argument("--transport-compliance", default="not_evaluated")
    create.add_argument("--delegation-compliance", default="not_evaluated")
    create.add_argument("--execution-compliance", default="not_evaluated")
    create.add_argument("--recommended-decision", default="defer")
    create.add_argument("--recommended-next-action", default="review evaluation report")
    create.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("evaluation_id")
    show.add_argument("--json", action="store_true")

    blockers = subparsers.add_parser("blockers")
    blockers.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = create_evaluation_report(
            target_artifact=args.target_artifact,
            scope=args.scope,
            record_root=record_root,
            evaluating_actor=args.evaluating_actor,
            actor_role=args.actor_role,
            target_lifecycle_state=args.target_lifecycle_state,
            evaluation_type=args.evaluation_type,
            verdict=args.verdict,
            inputs_reviewed=args.input_reviewed,
            checks_performed=args.check_performed,
            findings=args.finding,
            blocking_objections=args.blocking,
            non_blocking_concerns=args.concern,
            evidence_quality=args.evidence_quality,
            scope_compliance=args.scope_compliance,
            doctrine_compliance=args.doctrine_compliance,
            workflow_compliance=args.workflow_compliance,
            transport_compliance=args.transport_compliance,
            delegation_compliance=args.delegation_compliance,
            execution_compliance=args.execution_compliance,
            recommended_operator_decision=args.recommended_decision,
            recommended_next_action=args.recommended_next_action,
            affected_layer=args.affected_layer,
        )
        payload = result.to_dict()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("AXIOM evaluation report created")
            print("==============================")
            print(f"path: {payload['path']}")
            print(f"evaluation_id: {payload['report']['evaluation_id']}")
            print("authority_status: advisory_only")
            print("runtime_action_executed: False")
            print("ledger_written: False")
        return 0

    if args.command == "list":
        reports = list_evaluation_reports(record_root=record_root)
        if args.json:
            print(json.dumps({"evaluations": reports}, indent=2, sort_keys=True))
        else:
            print("AXIOM evaluation reports")
            print("========================")
            for report in reports:
                print(
                    f"{report['evaluation_id']} | {report['scope']} | "
                    f"{report['verdict']} | blockers={report['blocking_count']}"
                )
        return 0

    if args.command == "show":
        report = load_evaluation_report(args.evaluation_id, record_root=record_root)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("AXIOM evaluation report")
            print("=======================")
            print(f"evaluation_id: {report.get('evaluation_id')}")
            print(f"scope: {report.get('scope')}")
            print(f"target_artifact: {report.get('target_artifact')}")
            print(f"verdict: {report.get('verdict')}")
            print(f"authority_status: {report.get('authority_status')}")
        return 0

    if args.command == "blockers":
        summary = build_blocker_summary(record_root=record_root)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print("AXIOM blocker summary")
            print("=====================")
            print(f"blocking_count: {summary['blocking_count']}")
            for blocker in summary["blockers"]:
                print(f"{blocker['blocker_id']} | {blocker['scope']} | {blocker['title']}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
