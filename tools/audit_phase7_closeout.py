from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.audit_phase7_acceptance_inventory import (  # noqa: E402
    audit_phase7_acceptance_inventory,
)
from tools.audit_phase7_e2e_gate import audit_phase7_e2e_gate  # noqa: E402
from tools.run_phase7_acceptance import (  # noqa: E402
    E2E_TEST_PATH,
    build_phase7_acceptance_plan,
)


@dataclass(frozen=True)
class Phase7CloseoutViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase7CloseoutAuditResult:
    passed: bool
    checked: list[str]
    inventory_passed: bool
    acceptance_report_passed: bool
    acceptance_report_executed: bool
    e2e_gate_passed: bool
    e2e_gate_status: str
    e2e_ready: bool
    e2e_test_present: bool
    e2e_blockers: list[str]
    violations: list[Phase7CloseoutViolation]

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "inventory_passed": self.inventory_passed,
            "acceptance_report_passed": self.acceptance_report_passed,
            "acceptance_report_executed": self.acceptance_report_executed,
            "e2e_gate_passed": self.e2e_gate_passed,
            "e2e_gate_status": self.e2e_gate_status,
            "e2e_ready": self.e2e_ready,
            "e2e_test_present": self.e2e_test_present,
            "e2e_blockers": self.e2e_blockers,
            "violation_count": self.violation_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


PHASE7_REQUIRED_ARTIFACTS = [
    "docs/phase7.md",
    "tools/audit_phase7_acceptance_inventory.py",
    "tools/run_phase7_acceptance.py",
    "tools/audit_phase7_e2e_gate.py",
    "tools/approve_phase7_e2e_readiness.py",
    "tools/audit_phase7_closeout.py",
    "tests/e2e/test_full_goal_flow_minimum.py",
    "ui/terminal/modules/60-phase7.ps1",
]

PHASE7_REQUIRED_COMMANDS = {
    "axiom-phase7-inventory": "tools/audit_phase7_acceptance_inventory.py",
    "axiom-phase7-acceptance": "tools/run_phase7_acceptance.py",
    "axiom-phase7-e2e-gate": "tools/audit_phase7_e2e_gate.py",
    "axiom-phase7-closeout": "tools/audit_phase7_closeout.py",
}

FORBIDDEN_DIRECT_SHORTCUTS = [
    "axiom-run-full-goal-e2e",
    "axiom-safe-pass-on",
    "axiom-enable-autonomous",
    "axiom-register-model",
    "axiom-promote-model",
    "axiom-calibrate-classifier",
]

REQUIRED_CLOSEOUT_DOC_PHRASES = [
    "Phase 7 is implemented through 7E",
    "108 canonical MVP acceptance rows",
    "runner executed: false",
    "gate_status: blocked",
    "explicit operator approval for full-goal E2E not supplied",
    "bounded local gate-selection artifact",
    "No state-changing enablement was performed",
    "python tools\\audit_phase7_closeout.py",
]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _violation(
    violations: list[Phase7CloseoutViolation],
    check: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> None:
    violations.append(
        Phase7CloseoutViolation(
            check=check,
            reason=reason,
            details=details or {},
        )
    )


def _json_registry() -> dict[str, Any]:
    return json.loads(_read("ui/terminal/registry/axiom-terminal-command-registry.json"))


def audit_phase7_closeout() -> Phase7CloseoutAuditResult:
    checked = [
        "phase7_inventory_audit",
        "phase7_acceptance_report_is_read_only",
        "phase7_e2e_gate_audit",
        "phase7_required_artifacts_exist",
        "phase7_terminal_commands_wired",
        "phase7_terminal_panel_is_report_only",
        "phase7_closeout_doc_current",
        "phase7_no_unsafe_shortcuts",
    ]
    violations: list[Phase7CloseoutViolation] = []

    inventory = audit_phase7_acceptance_inventory()
    acceptance_report = build_phase7_acceptance_plan(
        run=False,
        include_e2e=False,
        operator_approved_e2e=False,
    )
    blocked_e2e_request = build_phase7_acceptance_plan(
        run=True,
        include_e2e=True,
        operator_approved_e2e=False,
        use_stored_e2e_approval=False,
    )
    e2e_gate = audit_phase7_e2e_gate()

    if not inventory.passed:
        _violation(
            violations,
            "phase7_inventory_audit",
            "phase7_inventory_audit_failed",
            {"violations": inventory.violations},
        )

    if not acceptance_report.passed:
        _violation(
            violations,
            "phase7_acceptance_report_is_read_only",
            "phase7_acceptance_report_failed",
            {"violations": acceptance_report.violations},
        )
    if acceptance_report.executed:
        _violation(
            violations,
            "phase7_acceptance_report_is_read_only",
            "phase7_default_acceptance_report_executed_tests",
            {},
        )
    if E2E_TEST_PATH in acceptance_report.command:
        _violation(
            violations,
            "phase7_acceptance_report_is_read_only",
            "phase7_default_acceptance_report_selected_e2e",
            {"path": E2E_TEST_PATH},
        )

    if blocked_e2e_request.executed:
        _violation(
            violations,
            "phase7_e2e_gate_audit",
            "phase7_blocked_e2e_request_executed",
            {},
        )
    if E2E_TEST_PATH in blocked_e2e_request.command:
        _violation(
            violations,
            "phase7_e2e_gate_audit",
            "phase7_blocked_e2e_request_selected_e2e",
            {"path": E2E_TEST_PATH},
        )

    if not e2e_gate.passed:
        _violation(
            violations,
            "phase7_e2e_gate_audit",
            "phase7_e2e_gate_audit_failed",
            {"violations": e2e_gate.violations},
        )
    if not e2e_gate.e2e_ready and e2e_gate.gate_status != "blocked":
        _violation(
            violations,
            "phase7_e2e_gate_audit",
            "phase7_gate_status_not_blocked_when_not_ready",
            {"gate_status": e2e_gate.gate_status},
        )
    if not e2e_gate.e2e_blockers:
        _violation(
            violations,
            "phase7_e2e_gate_audit",
            "phase7_e2e_blockers_missing",
            {},
        )

    for artifact in PHASE7_REQUIRED_ARTIFACTS:
        if not (ROOT / artifact).exists():
            _violation(
                violations,
                "phase7_required_artifacts_exist",
                "phase7_artifact_missing",
                {"path": artifact},
            )

    registry = _json_registry()
    commands = {command["name"]: command for command in registry["commands"]}
    for name, tool in PHASE7_REQUIRED_COMMANDS.items():
        command = commands.get(name)
        if command is None:
            _violation(
                violations,
                "phase7_terminal_commands_wired",
                "phase7_terminal_command_missing",
                {"command": name},
            )
            continue
        if command.get("mutates_axiom_runtime") is not False:
            _violation(
                violations,
                "phase7_terminal_commands_wired",
                "phase7_terminal_command_mutates_runtime",
                {"command": name},
            )
        if command.get("risk") != "low":
            _violation(
                violations,
                "phase7_terminal_commands_wired",
                "phase7_terminal_command_not_low_risk",
                {"command": name, "risk": command.get("risk")},
            )
        if command.get("backing_tools") != [tool]:
            _violation(
                violations,
                "phase7_terminal_commands_wired",
                "phase7_terminal_command_backing_tool_mismatch",
                {"command": name, "expected": tool, "actual": command.get("backing_tools")},
            )

    preflight_tools = commands.get("axiom-preflight", {}).get("backing_tools", [])
    if "tools/audit_phase7_closeout.py" not in preflight_tools:
        _violation(
            violations,
            "phase7_terminal_commands_wired",
            "phase7_closeout_missing_from_preflight_registry",
            {},
        )

    terminal_tools = _read("ui/terminal/modules/20-axiom-tools.ps1")
    doctor = _read("ui/terminal/modules/49-doctor.ps1")
    docs = _read("ui/terminal/modules/52-docs.ps1")
    help_text = _read("ui/terminal/modules/90-safety-help.ps1")
    phase7_panel = _read("ui/terminal/modules/60-phase7.ps1")

    for phrase, source_name, source_text in [
        ("function axiom-phase7-closeout", "20-axiom-tools.ps1", terminal_tools),
        ("tools\\audit_phase7_closeout.py", "20-axiom-tools.ps1", terminal_tools),
        ("axiom-phase7-closeout", "49-doctor.ps1", doctor),
        ("tools\\audit_phase7_closeout.py", "49-doctor.ps1", doctor),
        ("phase7-closeout", "52-docs.ps1", docs),
        ("phase7-closeout-audit-tool", "52-docs.ps1", docs),
        ("axiom-phase7-closeout Phase 7E closeout and hardening audit", "90-safety-help.ps1", help_text),
    ]:
        if phrase not in source_text:
            _violation(
                violations,
                "phase7_terminal_commands_wired",
                "phase7_terminal_phrase_missing",
                {"phrase": phrase, "source": source_name},
            )

    for forbidden in [
        "--include-e2e",
        "--operator-approved-e2e",
        "--write-db",
        "register_model_fingerprint.py",
        "safe-pass enabled",
    ]:
        if forbidden in phase7_panel:
            _violation(
                violations,
                "phase7_terminal_panel_is_report_only",
                "phase7_terminal_panel_contains_state_changing_or_e2e_entrypoint",
                {"term": forbidden},
            )

    closeout_doc = _read("docs/phase7.md")
    for phrase in REQUIRED_CLOSEOUT_DOC_PHRASES:
        if phrase not in closeout_doc:
            _violation(
                violations,
                "phase7_closeout_doc_current",
                "phase7_closeout_doc_phrase_missing",
                {"phrase": phrase},
            )

    command_surface = "\n".join([terminal_tools, doctor, help_text, json.dumps(registry)])
    for name in FORBIDDEN_DIRECT_SHORTCUTS:
        if f"function {name}" in command_surface or f'"name": "{name}"' in command_surface:
            _violation(
                violations,
                "phase7_no_unsafe_shortcuts",
                "phase7_unsafe_shortcut_present",
                {"command": name},
            )

    return Phase7CloseoutAuditResult(
        passed=not violations,
        checked=checked,
        inventory_passed=inventory.passed,
        acceptance_report_passed=acceptance_report.passed,
        acceptance_report_executed=acceptance_report.executed,
        e2e_gate_passed=e2e_gate.passed,
        e2e_gate_status=e2e_gate.gate_status,
        e2e_ready=e2e_gate.e2e_ready,
        e2e_test_present=e2e_gate.e2e_test_present,
        e2e_blockers=e2e_gate.e2e_blockers,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM Phase 7 closeout and hardening audit."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_phase7_closeout()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 7 closeout and hardening audit")
        print("==========================================")
        print(f"passed: {payload['passed']}")
        print(f"violation_count: {payload['violation_count']}")
        print(f"acceptance_report_executed: {payload['acceptance_report_executed']}")
        print(f"e2e_gate_status: {payload['e2e_gate_status']}")
        print(f"e2e_ready: {payload['e2e_ready']}")
        print(f"e2e_test_present: {payload['e2e_test_present']}")
        print("")
        print("checks:")
        for check in payload["checked"]:
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
                if violation["details"]:
                    print(
                        f"  details: {json.dumps(violation['details'], sort_keys=True)}"
                    )
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

