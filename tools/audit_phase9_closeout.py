from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_ARTIFACTS = [
    "docs/phase9.md",
    "tools/audit_phase9_closeout.py",
    "tests/test_phase9_closeout.py",
    "tests/test_scheduler_loop.py",
    "axiom/core/scheduler_loop.py",
    "axiom/core/scheduler.py",
    "axiom/core/scheduler_tick.py",
    "axiom/core/noop_task_executor.py",
    "tools/run_scheduler_loop.py",
]

REQUIRED_DOC_PHRASES = [
    "Phase 9 is closed",
    "automatic scheduler-to-executor integration for manual_noop tasks",
    "fail_closed_non_autonomous",
    "one-running-task invariant remains enforced",
    "verification commands: pytest tests",
    "no real model, cloud, network, sandbox, memory, Telegram, agent, or general task scheduler authority is enabled",
]

REQUIRED_RUNTIME_GUARDS = [
    "if task[\"task_type\"] != \"manual_noop\"",
    "Automatic execution only authorized for manual_noop tasks",
    "This is not a background service.",
    "max_ticks must be >= 1",
    "allow_when_autonomous_blocked",
    "complete_running_noop_task",
]

FORBIDDEN_RUNTIME_TERMS = [
    "ModelGateway(",
    "NetworkGateway(",
    "SandboxGateway(",
    "MemoryGateway(",
    "TelegramGateway(",
    "execute_goal_planning_task",
    "execute_task_planning_task",
    "execute_tool_execution_task",
    "execute_result_verification_task",
    "run_manual_agent_foundation_smoke",
]

FORBIDDEN_DIRECT_SHORTCUTS = [
    "axiom-enable-autonomous",
    "axiom-safe-pass-on",
    "axiom-promote-model",
    "axiom-register-model",
    "axiom-run-scheduler",
    "axiom-run-noop-cycle",
    "axiom-execute-noop",
    "axiom-dispatch",
    "axiom-start-task",
]

TERMINAL_HOOKS = [
    (
        "ui/terminal/modules/utilities/20-axiom-tools.ps1",
        [
            "function axiom-phase9-closeout",
            "tools\\audit_phase9_closeout.py",
            "Phase 9 closeout audit",
        ],
    ),
    (
        "ui/terminal/modules/diagnostics/49-doctor.ps1",
        [
            "axiom-phase9-closeout",
            "tools\\audit_phase9_closeout.py",
        ],
    ),
    (
        "ui/terminal/modules/diagnostics/52-docs.ps1",
        [
            "phase9-closeout",
            "docs\\phase9.md",
            "phase9-closeout-audit-tool",
            "tools\\audit_phase9_closeout.py",
        ],
    ),
    (
        "ui/terminal/modules/safety/90-safety-help.ps1",
        [
            "axiom-phase9-closeout Phase 9 closeout audit",
            "Phase 9 bounded manual_noop scheduler-to-executor closeout audit",
        ],
    ),
]


@dataclass(frozen=True)
class Phase9CloseoutViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase9CloseoutAuditResult:
    passed: bool
    checked: list[str]
    violation_count: int
    command_registered: bool
    preflight_registered: bool
    runtime_guard_count: int
    violations: list[Phase9CloseoutViolation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "violation_count": self.violation_count,
            "command_registered": self.command_registered,
            "preflight_registered": self.preflight_registered,
            "runtime_guard_count": self.runtime_guard_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _violation(
    violations: list[Phase9CloseoutViolation],
    check: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> None:
    violations.append(
        Phase9CloseoutViolation(
            check=check,
            reason=reason,
            details=details or {},
        )
    )


def _registry() -> dict[str, Any]:
    return json.loads(_read("ui/terminal/registry/axiom-terminal-command-registry.json"))


def audit_phase9_closeout() -> Phase9CloseoutAuditResult:
    checked = [
        "phase9_required_artifacts_exist",
        "phase9_doc_records_boundary",
        "phase9_terminal_command_registered",
        "phase9_terminal_hooks_present",
        "phase9_runtime_guards_present",
        "phase9_runtime_avoids_forbidden_gateways",
        "phase9_no_unsafe_direct_shortcuts",
    ]
    violations: list[Phase9CloseoutViolation] = []

    for artifact in REQUIRED_ARTIFACTS:
        if not (ROOT / artifact).exists():
            _violation(
                violations,
                "phase9_required_artifacts_exist",
                "phase9_artifact_missing",
                {"path": artifact},
            )

    doc_text = _read("docs/phase9.md") if (ROOT / "docs/phase9.md").exists() else ""
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in doc_text:
            _violation(
                violations,
                "phase9_doc_records_boundary",
                "phase9_doc_phrase_missing",
                {"phrase": phrase},
            )

    registry = _registry()
    commands = {command["name"]: command for command in registry["commands"]}
    command = commands.get("axiom-phase9-closeout")
    command_registered = command is not None
    preflight_tools = commands.get("axiom-preflight", {}).get("backing_tools", [])
    preflight_registered = "tools/audit_phase9_closeout.py" in preflight_tools

    if command is None:
        _violation(
            violations,
            "phase9_terminal_command_registered",
            "phase9_command_missing",
            {"command": "axiom-phase9-closeout"},
        )
    else:
        expected = {
            "category": "verification",
            "primary": True,
            "mutates_axiom_runtime": False,
            "risk": "low",
            "status": "implemented",
            "backing_tools": ["tools/audit_phase9_closeout.py"],
        }
        for key, expected_value in expected.items():
            if command.get(key) != expected_value:
                _violation(
                    violations,
                    "phase9_terminal_command_registered",
                    "phase9_command_metadata_mismatch",
                    {
                        "command": "axiom-phase9-closeout",
                        "field": key,
                        "expected": expected_value,
                        "actual": command.get(key),
                    },
                )

    if not preflight_registered:
        _violation(
            violations,
            "phase9_terminal_command_registered",
            "phase9_audit_missing_from_preflight_registry",
            {},
        )

    for relative_path, phrases in TERMINAL_HOOKS:
        text = _read(relative_path)
        for phrase in phrases:
            if phrase not in text:
                _violation(
                    violations,
                    "phase9_terminal_hooks_present",
                    "phase9_terminal_hook_missing",
                    {"path": relative_path, "phrase": phrase},
                )

    scheduler_loop = (
        _read("axiom/core/scheduler_loop.py")
        if (ROOT / "axiom/core/scheduler_loop.py").exists()
        else ""
    )
    runtime_guard_count = 0
    for phrase in REQUIRED_RUNTIME_GUARDS:
        if phrase in scheduler_loop:
            runtime_guard_count += 1
        else:
            _violation(
                violations,
                "phase9_runtime_guards_present",
                "phase9_runtime_guard_missing",
                {"phrase": phrase},
            )

    runtime_text = "\n".join(
        [
            scheduler_loop,
            _read("axiom/core/noop_task_executor.py")
            if (ROOT / "axiom/core/noop_task_executor.py").exists()
            else "",
            _read("tools/run_scheduler_loop.py")
            if (ROOT / "tools/run_scheduler_loop.py").exists()
            else "",
        ]
    )
    for term in FORBIDDEN_RUNTIME_TERMS:
        if term in runtime_text:
            _violation(
                violations,
                "phase9_runtime_avoids_forbidden_gateways",
                "phase9_forbidden_runtime_term_present",
                {"term": term},
            )

    terminal_text = "\n".join(
        [
            _read("ui/terminal/modules/utilities/20-axiom-tools.ps1"),
            _read("ui/terminal/modules/diagnostics/49-doctor.ps1"),
            _read("ui/terminal/modules/safety/90-safety-help.ps1"),
        ]
    )
    command_names = {command["name"] for command in registry["commands"]}
    for shortcut in FORBIDDEN_DIRECT_SHORTCUTS:
        if f"function {shortcut}" in terminal_text or shortcut in command_names:
            _violation(
                violations,
                "phase9_no_unsafe_direct_shortcuts",
                "phase9_unsafe_direct_shortcut_present",
                {"command": shortcut},
            )

    return Phase9CloseoutAuditResult(
        passed=not violations,
        checked=checked,
        violation_count=len(violations),
        command_registered=command_registered,
        preflight_registered=preflight_registered,
        runtime_guard_count=runtime_guard_count,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM Phase 9 closeout and boundary audit."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_phase9_closeout()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 9 closeout audit")
        print("============================")
        print(f"passed: {payload['passed']}")
        print(f"violation_count: {payload['violation_count']}")
        print(f"command_registered: {payload['command_registered']}")
        print(f"preflight_registered: {payload['preflight_registered']}")
        print(f"runtime_guard_count: {payload['runtime_guard_count']}")
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
