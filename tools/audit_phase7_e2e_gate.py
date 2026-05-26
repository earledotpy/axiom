from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.run_phase7_acceptance import (  # noqa: E402
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
)


@dataclass(frozen=True)
class Phase7E2EGateAuditResult:
    passed: bool
    gate_status: str
    e2e_ready: bool
    e2e_test_path: str
    e2e_test_present: bool
    e2e_blockers: list[str]
    checks: list[str]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_phase7_e2e_gate() -> Phase7E2EGateAuditResult:
    violations: list[dict[str, Any]] = []
    checks: list[str] = []

    default_plan = build_phase7_acceptance_plan(
        run=False,
        include_e2e=False,
        operator_approved_e2e=False,
        use_stored_e2e_approval=False,
    )
    blocked_e2e_plan = build_phase7_acceptance_plan(
        run=True,
        include_e2e=True,
        operator_approved_e2e=False,
        use_stored_e2e_approval=False,
    )

    checks.append("default_phase7_acceptance_report_is_non_executing")
    if default_plan.executed:
        violations.append(
            {
                "check": "default_phase7_acceptance_report_is_non_executing",
                "reason": "default_report_executed_tests",
            }
        )

    checks.append("default_phase7_acceptance_report_excludes_e2e")
    if E2E_TEST_PATH in default_plan.command:
        violations.append(
            {
                "check": "default_phase7_acceptance_report_excludes_e2e",
                "reason": "default_command_selected_e2e_test",
                "path": E2E_TEST_PATH,
            }
        )

    checks.append("include_e2e_without_operator_approval_is_blocked")
    if blocked_e2e_plan.executed:
        violations.append(
            {
                "check": "include_e2e_without_operator_approval_is_blocked",
                "reason": "blocked_e2e_request_executed",
            }
        )

    checks.append("blocked_e2e_request_records_violation")
    if not any(
        item.get("reason") == "e2e_requested_but_blocked"
        for item in blocked_e2e_plan.violations
    ):
        violations.append(
            {
                "check": "blocked_e2e_request_records_violation",
                "reason": "missing_e2e_requested_but_blocked_violation",
            }
        )

    checks.append("blocked_e2e_request_excludes_e2e_path")
    if E2E_TEST_PATH in blocked_e2e_plan.command:
        violations.append(
            {
                "check": "blocked_e2e_request_excludes_e2e_path",
                "reason": "blocked_command_selected_e2e_test",
                "path": E2E_TEST_PATH,
            }
        )

    checks.append("explicit_operator_approval_is_required")
    if "explicit operator approval for full-goal E2E not supplied" not in blocked_e2e_plan.e2e_blockers:
        violations.append(
            {
                "check": "explicit_operator_approval_is_required",
                "reason": "operator_approval_blocker_missing",
            }
        )

    checks.append("e2e_blockers_are_reported")
    if not blocked_e2e_plan.e2e_blockers:
        violations.append(
            {
                "check": "e2e_blockers_are_reported",
                "reason": "blocked_e2e_request_has_no_blockers",
            }
        )

    gate_status = "ready" if default_plan.e2e_ready else "blocked"

    return Phase7E2EGateAuditResult(
        passed=not violations,
        gate_status=gate_status,
        e2e_ready=default_plan.e2e_ready,
        e2e_test_path=E2E_TEST_PATH,
        e2e_test_present=default_plan.e2e_test_present,
        e2e_blockers=default_plan.e2e_blockers,
        checks=checks,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the AXIOM Phase 7C full-goal E2E gate."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_phase7_e2e_gate()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 7C full-goal E2E gate audit")
        print("=======================================")
        print(f"passed: {payload['passed']}")
        print(f"gate_status: {payload['gate_status']}")
        print(f"e2e_ready: {payload['e2e_ready']}")
        print(f"e2e_test_present: {payload['e2e_test_present']}")
        print("")
        print("checks:")
        for check in payload["checks"]:
            print(f"- {check}")
        print("")
        print("e2e blockers:")
        if payload["e2e_blockers"]:
            for blocker in payload["e2e_blockers"]:
                print(f"- {blocker}")
        else:
            print("- none")
        print("")
        print("violations:")
        if payload["violations"]:
            for violation in payload["violations"]:
                print(f"- {violation['check']}: {violation['reason']}")
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
