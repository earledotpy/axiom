from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.evidence import create_evidence, list_evidence, load_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and inspect AXIOM evidence records.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--scope", required=True)
    create.add_argument("--type", default="implementation_evidence", dest="evidence_type")
    create.add_argument("--file-changed", action="append", default=[])
    create.add_argument("--command-run", action="append", default=[])
    create.add_argument("--verification-result", action="append", default=[])
    create.add_argument("--skipped-check", action="append", default=[])
    create.add_argument("--assumption", action="append", default=[])
    create.add_argument("--known-risk", action="append", default=[])
    create.add_argument("--evidence-quality", default="not_evaluated")
    create.add_argument("--recommended-next-action", default="review evidence")
    create.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show")
    show.add_argument("evidence_id")
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create":
        result = create_evidence(
            record_root=record_root,
            scope=args.scope,
            evidence_type=args.evidence_type,
            files_changed=args.file_changed,
            commands_run=args.command_run,
            verification_results=args.verification_result,
            skipped_checks=args.skipped_check,
            assumptions=args.assumption,
            known_risks=args.known_risk,
            evidence_quality=args.evidence_quality,
            recommended_next_action=args.recommended_next_action,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "list":
        payload = {"evidence": list_evidence(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["evidence_id"] for item in payload["evidence"]))
        return 0

    if args.command == "show":
        payload = load_evidence(args.evidence_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("evidence_id", ""))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
