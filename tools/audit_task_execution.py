from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_execution_audit import audit_task_execution


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit AXIOM no-op task execution records."
    )
    parser.add_argument("--all-sessions", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_task_execution(all_sessions=args.all_sessions)
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task execution audit")
        print("==========================")
        print(f"passed: {result.passed}")
        print(f"scope: {result.scope}")
        print(f"session_id: {result.session_id}")
        print(f"checked_task_count: {result.checked_task_count}")
        print("")
        print("violations:")
        if result.violations:
            for violation in result.violations:
                print(
                    f"- task_id={violation.task_id} "
                    f"session_id={violation.session_id} "
                    f"reason={violation.reason}"
                )
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())