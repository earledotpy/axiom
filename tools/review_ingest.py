from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.governance_cycle import ingest_terminal_review


def _read_review_text(args: argparse.Namespace) -> str:
    if args.review_text:
        return args.review_text
    if args.review_file:
        return Path(args.review_file).read_text(encoding="utf-8-sig")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest terminal review output as an advisory AXIOM evaluation record."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--target-artifact", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--actor", default="Claude Code", dest="evaluating_actor")
    create.add_argument("--actor-role", default="AUD", choices=["AUD", "ARCH", "IMPL", "CURSOR", "SYN"])
    create.add_argument("--type", default="governance_audit", dest="evaluation_type")
    create.add_argument("--verdict", default="not_evaluated")
    create.add_argument("--review-text", default="")
    create.add_argument("--review-file", default="")
    create.add_argument("--input-reviewed", action="append", default=[])
    create.add_argument("--check-performed", action="append", default=[])
    create.add_argument("--finding", action="append", default=[])
    create.add_argument("--blocking", action="append", default=[])
    create.add_argument("--concern", action="append", default=[])
    create.add_argument("--required-test", action="append", default=[])
    create.add_argument("--required-change", action="append", default=[])
    create.add_argument("--evidence-quality", default="not_evaluated")
    create.add_argument("--recommended-decision", default="defer")
    create.add_argument("--recommended-next-action", default="review ingested evaluation report")
    create.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = ingest_terminal_review(
            record_root=record_root,
            target_artifact=args.target_artifact,
            scope=args.scope,
            review_text=_read_review_text(args),
            evaluating_actor=args.evaluating_actor,
            actor_role=args.actor_role,
            evaluation_type=args.evaluation_type,
            verdict=args.verdict,
            inputs_reviewed=args.input_reviewed,
            checks_performed=args.check_performed,
            findings=args.finding,
            blocking_objections=args.blocking,
            non_blocking_concerns=args.concern,
            required_tests=args.required_test,
            required_implementation_changes=args.required_change,
            evidence_quality=args.evidence_quality,
            recommended_operator_decision=args.recommended_decision,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("AXIOM review ingested")
            print("====================")
            print(f"path: {result['path']}")
            print(f"evaluation_id: {result['review']['evaluation_id']}")
            print("authority_status: advisory_only")
            print("runtime_action_executed: False")
            print("ledger_written: False")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
