from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.execution_readiness import evaluate_execution_readiness


def print_text_report(result) -> None:
    print("AXIOM execution readiness")
    print("=========================")
    print(f"ready: {result.ready}")
    print(f"session_id: {result.session_id}")
    print(f"lifecycle_audit_passed: {result.lifecycle_audit.passed}")
    print(f"execution_audit_passed: {result.execution_audit.passed}")
    print(f"supervisor_health_passed: {result.supervisor_health.passed}")
    print(f"pending_manifest_bound_task_count: {result.pending_manifest_bound_task_count}")
    print(f"running_task_count: {result.running_task_count}")

    print()
    print("reasons:")
    if result.reasons:
        for reason in result.reasons:
            print(f"- {reason}")
    else:
        print("- none")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only AXIOM execution readiness check."
    )
    parser.add_argument("--session-id", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 when execution readiness is false.",
    )
    args = parser.parse_args()

    result = evaluate_execution_readiness(session_id=args.session_id)

    if args.json:
        print(result.to_json())
    else:
        print_text_report(result)

    if args.strict and not result.ready:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())