from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.app.status_report import build_status_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Report AXIOM operational status.")
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_status_report(profile_label=args.profile_label)

    if args.json:
        print(report.to_json())
    else:
        print("AXIOM operational status")
        print("========================")
        print(f"database_initialized: {report.database_initialized}")
        print(f"manifest_fingerprints_valid: {report.manifest_fingerprints_valid}")
        print(f"model_candidate_profile_present: {report.model_candidate_profile_present}")
        print(
            "current_trusted_model_profile_present: "
            f"{report.current_trusted_model_profile_present}"
        )
        print(f"safe_pass_enabled: {report.safe_pass_enabled}")
        print(f"autonomous_operation_enabled: {report.autonomous_operation_enabled}")
        print(f"autonomous_available: {report.autonomous_available}")

        if report.blocking_reasons:
            print("")
            print("blocking_reasons:")
            for reason in report.blocking_reasons:
                print(f"- {reason}")

    return 0 if report.database_initialized else 1


if __name__ == "__main__":
    raise SystemExit(main())