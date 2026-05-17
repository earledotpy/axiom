from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.autonomous_gate import evaluate_autonomous_readiness


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether AXIOM may enter autonomous operation."
    )
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    decision = evaluate_autonomous_readiness(profile_label=args.profile_label)

    if args.json:
        print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
    else:
        print("AXIOM autonomous readiness")
        print("==========================")
        print(f"allowed: {decision.allowed}")

        if decision.blocking_reasons:
            print("")
            print("blocking_reasons:")
            for reason in decision.blocking_reasons:
                print(f"- {reason}")

    return 0 if decision.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())