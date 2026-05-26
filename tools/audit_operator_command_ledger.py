from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.operator_command_ledger import audit_operator_command_ledger


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM Phase 6 read-only operator command ledger audit."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_operator_command_ledger()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 6 operator command ledger audit")
        print("===========================================")
        print(f"passed: {payload['passed']}")
        print(f"checked_command_count: {payload['checked_command_count']}")
        print(f"violation_count: {payload['violation_count']}")
        print("")
        print("checks:")
        for check in payload["checked"]:
            print(f"- {check}")

        print("")
        print("violations:")
        if payload["violations"]:
            for violation in payload["violations"]:
                print(f"- {violation['check']}: {violation['reason']}")
                if violation["details"]:
                    print(
                        f"  details: {json.dumps(violation['details'], sort_keys=True)}"
                    )
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
