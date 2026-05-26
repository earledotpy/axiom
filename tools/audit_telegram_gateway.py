from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.telegram_gateway import load_telegram_gateway_config
from axiom.persistence.db import get_connection


CONFIG_PATH = ROOT / "config" / "axiom.yaml"
REQUIRED_TABLES = {
    "external_adapter_messages",
    "external_confirmation_requests",
}


@dataclass(frozen=True)
class TelegramGatewayAuditViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TelegramGatewayAuditResult:
    passed: bool
    checked: list[str]
    violations: list[TelegramGatewayAuditViolation]

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


def audit_telegram_gateway(config_path: Path = CONFIG_PATH) -> TelegramGatewayAuditResult:
    checked = [
        "telegram_gateway_config_shape",
        "telegram_gateway_secret_storage",
        "telegram_gateway_enabled_whitelist",
        "telegram_gateway_schema_tables",
        "telegram_gateway_confirmation_integrity",
        "telegram_gateway_no_implicit_execution",
    ]
    violations: list[TelegramGatewayAuditViolation] = []

    try:
        config = load_telegram_gateway_config(config_path)
    except Exception as exc:
        violations.append(
            TelegramGatewayAuditViolation(
                check="telegram_gateway_config_shape",
                reason="telegram_gateway_config_invalid",
                details={"error": str(exc)},
            )
        )
        config = None

    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    section = (raw_config or {}).get("telegram_gateway", {}) or {}

    if "capability_tokens" in section:
        violations.append(
            TelegramGatewayAuditViolation(
                check="telegram_gateway_secret_storage",
                reason="telegram_gateway_plaintext_capability_tokens_configured",
                details={"field": "telegram_gateway.capability_tokens"},
            )
        )

    if config is not None and config.enabled:
        if not config.operator_whitelist:
            violations.append(
                TelegramGatewayAuditViolation(
                    check="telegram_gateway_enabled_whitelist",
                    reason="telegram_gateway_enabled_without_operator_whitelist",
                    details={},
                )
            )
        if not config.allowed_chat_ids:
            violations.append(
                TelegramGatewayAuditViolation(
                    check="telegram_gateway_enabled_whitelist",
                    reason="telegram_gateway_enabled_without_allowed_chat_ids",
                    details={},
                )
            )
        if not config.capability_token_sha256:
            violations.append(
                TelegramGatewayAuditViolation(
                    check="telegram_gateway_enabled_whitelist",
                    reason="telegram_gateway_enabled_without_capability_hashes",
                    details={},
                )
            )

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (?, ?)
            """,
            tuple(sorted(REQUIRED_TABLES)),
        ).fetchall()
        present_tables = {row["name"] for row in rows}
        missing_tables = sorted(REQUIRED_TABLES - present_tables)
        if missing_tables:
            violations.append(
                TelegramGatewayAuditViolation(
                    check="telegram_gateway_schema_tables",
                    reason="telegram_gateway_schema_tables_missing",
                    details={"missing_tables": missing_tables},
                )
            )

        if not missing_tables:
            orphan_confirmations = conn.execute(
                """
                SELECT cr.confirmation_id
                FROM external_confirmation_requests AS cr
                LEFT JOIN external_adapter_messages AS em
                  ON em.message_id = cr.message_id
                WHERE em.message_id IS NULL
                LIMIT 10
                """
            ).fetchall()
            if orphan_confirmations:
                violations.append(
                    TelegramGatewayAuditViolation(
                        check="telegram_gateway_confirmation_integrity",
                        reason="telegram_gateway_confirmation_without_message",
                        details={
                            "confirmation_ids": [
                                int(row["confirmation_id"]) for row in orphan_confirmations
                            ]
                        },
                    )
                )

            accepted_without_command = conn.execute(
                """
                SELECT confirmation_id
                FROM external_confirmation_requests
                WHERE confirmation_status = 'accepted'
                  AND command_id IS NULL
                LIMIT 10
                """
            ).fetchall()
            if accepted_without_command:
                violations.append(
                    TelegramGatewayAuditViolation(
                        check="telegram_gateway_confirmation_integrity",
                        reason="telegram_gateway_accepted_confirmation_without_command",
                        details={
                            "confirmation_ids": [
                                int(row["confirmation_id"]) for row in accepted_without_command
                            ]
                        },
                    )
                )

            implicit_execution_rows = conn.execute(
                """
                SELECT em.message_id
                FROM external_adapter_messages AS em
                LEFT JOIN external_confirmation_requests AS cr
                  ON cr.message_id = em.message_id
                WHERE em.decision_status = 'accepted'
                  AND (
                    cr.confirmation_status IS NULL
                    OR cr.confirmation_status != 'accepted'
                    OR cr.command_id IS NULL
                  )
                LIMIT 10
                """
            ).fetchall()
            if implicit_execution_rows:
                violations.append(
                    TelegramGatewayAuditViolation(
                        check="telegram_gateway_no_implicit_execution",
                        reason="telegram_gateway_message_accepted_without_confirmation",
                        details={
                            "message_ids": [
                                int(row["message_id"]) for row in implicit_execution_rows
                            ]
                        },
                    )
                )

    return TelegramGatewayAuditResult(
        passed=not violations,
        checked=checked,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AXIOM Phase 6G Telegram gateway configuration and storage audit."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_telegram_gateway()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 6G Telegram gateway audit")
        print("=====================================")
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
