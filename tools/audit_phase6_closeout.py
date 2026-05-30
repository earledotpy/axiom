from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Phase6CloseoutViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase6CloseoutAuditResult:
    passed: bool
    checked: list[str]
    violations: list[Phase6CloseoutViolation]

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "violation_count": self.violation_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


PHASE6_REQUIRED_ARTIFACTS = [
    "docs/phase6.md",
    "axiom/policy/operator_control_manifests/status.v1.json",
    "axiom/core/operator_command_parser.py",
    "axiom/core/operator_command_ledger.py",
    "axiom/gateways/telegram_gateway.py",
    "tools/audit_operator_command_ledger.py",
    "tools/audit_telegram_gateway.py",
    "tools/audit_phase6_closeout.py",
    "ui/terminal/modules/operators/58-operator-commands.ps1",
    "ui/terminal/modules/operators/59-telegram-gateway.ps1",
]

V113_PHASE6_PHRASES = [
    "Implement Telegram Gateway after operator whitelist mechanism is specified.",
    "Implement CommandParser and OperatorControlInserter.",
    "Enforce operator-control manifests and capability-token boundaries.",
]

DEFERRED_RUNTIME_PHRASES = [
    "live Telegram polling",
    "webhook registration",
    "outbound Telegram replies",
    "terminal confirmation shortcut",
    "automatic execution after confirmation",
]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _violation(
    violations: list[Phase6CloseoutViolation],
    check: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> None:
    violations.append(
        Phase6CloseoutViolation(
            check=check,
            reason=reason,
            details=details or {},
        )
    )


def audit_phase6_closeout() -> Phase6CloseoutAuditResult:
    checked = [
        "phase6_v113_alignment",
        "phase6_required_artifacts_exist",
        "phase6_roadmap_current",
        "phase6_telegram_disabled_by_default",
        "phase6_live_telegram_runtime_absent",
        "phase6_terminal_surfaces_read_only",
        "phase6_operator_cognitive_load",
        "phase6_deferred_runtime_work_named",
    ]
    violations: list[Phase6CloseoutViolation] = []

    implementation = _read("AXIOM_Implementation_v1.13.md")
    for phrase in V113_PHASE6_PHRASES:
        if phrase not in implementation:
            _violation(
                violations,
                "phase6_v113_alignment",
                "phase6_v113_source_phrase_missing",
                {"phrase": phrase},
            )

    for artifact in PHASE6_REQUIRED_ARTIFACTS:
        if not (ROOT / artifact).exists():
            _violation(
                violations,
                "phase6_required_artifacts_exist",
                "phase6_artifact_missing",
                {"path": artifact},
            )

    roadmap = _read("docs/phase6.md")
    if "Slices 6A through 6I are implemented" not in roadmap:
        _violation(
            violations,
            "phase6_roadmap_current",
            "phase6_roadmap_status_not_current",
            {"expected": "Slices 6A through 6I are implemented"},
        )
    if "### 6I. Closeout And Hardening Audit" not in roadmap:
        _violation(
            violations,
            "phase6_roadmap_current",
            "phase6_roadmap_missing_6i_section",
            {},
        )

    config = yaml.safe_load(_read("config/axiom.yaml")) or {}
    telegram_config = config.get("telegram_gateway", {}) or {}
    if telegram_config.get("enabled", False) is not False:
        _violation(
            violations,
            "phase6_telegram_disabled_by_default",
            "telegram_gateway_not_disabled_by_default",
            {"enabled": telegram_config.get("enabled")},
        )
    if "capability_tokens" in telegram_config:
        _violation(
            violations,
            "phase6_telegram_disabled_by_default",
            "telegram_gateway_plaintext_token_field_present",
            {},
        )

    gateway_source = _read("axiom/gateways/telegram_gateway.py")
    forbidden_gateway_terms = [
        "run_polling",
        "run_webhook",
        "set_webhook",
        "send_message",
        "Application.builder",
        "import requests",
        "import httpx",
        "from telegram",
    ]
    for term in forbidden_gateway_terms:
        if term in gateway_source:
            _violation(
                violations,
                "phase6_live_telegram_runtime_absent",
                "phase6_live_telegram_runtime_term_present",
                {"term": term},
            )

    terminal_panel = _read("ui/terminal/modules/operators/59-telegram-gateway.ps1")
    if "mode=ro" not in terminal_panel:
        _violation(
            violations,
            "phase6_terminal_surfaces_read_only",
            "telegram_terminal_panel_not_sqlite_read_only",
            {},
        )
    for term in ("process_envelope", "confirm_intent", "record_operator_command_intent.py"):
        if term in terminal_panel:
            _violation(
                violations,
                "phase6_terminal_surfaces_read_only",
                "telegram_terminal_panel_contains_mutation_entrypoint",
                {"term": term},
            )

    registry = json.loads(_read("ui/terminal/registry/axiom-terminal-command-registry.json"))
    commands = {command["name"]: command for command in registry["commands"]}
    for name in (
        "axiom-operator-commands",
        "axiom-operator-command-audit",
        "axiom-telegram-gateway",
        "axiom-telegram-gateway-audit",
    ):
        command = commands.get(name)
        if command is None:
            _violation(
                violations,
                "phase6_terminal_surfaces_read_only",
                "phase6_terminal_command_missing",
                {"command": name},
            )
        elif command.get("mutates_axiom_runtime") is not False:
            _violation(
                violations,
                "phase6_terminal_surfaces_read_only",
                "phase6_terminal_command_mutates_runtime",
                {"command": name},
            )

    section_count = terminal_panel.count("Write-AxiomUiSection")
    if section_count > 5:
        _violation(
            violations,
            "phase6_operator_cognitive_load",
            "telegram_terminal_panel_has_too_many_sections",
            {"section_count": section_count, "max_allowed": 5},
        )

    help_text = _read("ui/terminal/modules/safety/90-safety-help.ps1")
    phase6_terms = (
        "axiom-operator-commands",
        "axiom-operator-command-audit",
        "axiom-telegram-gateway",
        "axiom-telegram-gateway-audit",
        "axiom-phase6",
    )
    phase6_mentions = sum(help_text.count(term) for term in phase6_terms)
    if phase6_mentions > 18:
        _violation(
            violations,
            "phase6_operator_cognitive_load",
            "terminal_help_phase6_surface_too_repetitive",
            {"phase6_mentions": phase6_mentions, "max_allowed": 18},
        )

    closeout = _read("docs/phase6.md")
    for phrase in DEFERRED_RUNTIME_PHRASES:
        if phrase not in closeout:
            _violation(
                violations,
                "phase6_deferred_runtime_work_named",
                "phase6_deferred_runtime_phrase_missing",
                {"phrase": phrase},
            )

    return Phase6CloseoutAuditResult(
        passed=not violations,
        checked=checked,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM Phase 6 closeout and hardening audit."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_phase6_closeout()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 6 closeout and hardening audit")
        print("==========================================")
        print(f"passed: {payload['passed']}")
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

