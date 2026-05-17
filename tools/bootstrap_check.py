from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.app.bootstrap_validation import BootstrapValidator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM passive bootstrap validation checks."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    args = parser.parse_args()

    result = BootstrapValidator().run(raise_on_failure=False)
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASSED" if result.passed else "FAILED"
        readiness = result.autonomous_readiness
        autonomous_allowed = readiness.get("allowed", False)
        blocking_reasons = readiness.get("blocking_reasons", [])

        print(f"AXIOM bootstrap validation: {status}")
        print(f"foundation_passed: {result.passed}")
        print(f"operational_mode: {result.operational_mode}")
        print(f"autonomous_allowed: {autonomous_allowed}")

        if blocking_reasons:
            print("")
            print("blocking_reasons:")
            for reason in blocking_reasons:
                print(f"- {reason}")

        print("")
        print("foundation_checks:")
        for check in result.checks:
            check_status = "PASS" if check.passed else "FAIL"
            print(f"[{check_status}] {check.name}: {check.reason}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
