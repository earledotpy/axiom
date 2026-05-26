from __future__ import annotations

import hashlib
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from axiom.core.operator_command_ledger import record_operator_command_intent
from axiom.core.operator_command_parser import OperatorCommandParser
from axiom.persistence.db import get_connection, init_db


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "config" / "axiom.yaml"


@dataclass(frozen=True)
class TelegramGatewayConfig:
    enabled: bool
    operator_whitelist: tuple[str, ...]
    allowed_chat_ids: tuple[str, ...]
    capability_token_sha256: tuple[str, ...]
    max_message_length: int
    per_sender_limit_per_minute: int
    per_chat_limit_per_minute: int
    global_limit_per_minute: int
    replay_window_seconds: int
    confirmation_expiry_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TelegramEnvelope:
    platform_message_id: str
    platform_sender_id: str
    platform_chat_id: str
    command_text: str
    capability_token: str
    received_at: str | None = None


@dataclass(frozen=True)
class TelegramGatewayResult:
    accepted: bool
    status: str
    denial_reason: str | None
    message_id: int | None
    confirmation_id: int | None
    command_id: int | None
    confirmation_token: str | None
    runtime_action_executed: bool
    ledger_written: bool
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_telegram_gateway_config(
    path: Path | str = DEFAULT_CONFIG_PATH,
) -> TelegramGatewayConfig:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    section = (data or {}).get("telegram_gateway", {}) or {}

    if "capability_tokens" in section:
        raise ValueError(
            "telegram_gateway.capability_tokens is not allowed; use capability_token_sha256"
        )

    def _tuple(name: str) -> tuple[str, ...]:
        values = section.get(name, [])
        if values is None:
            return ()
        if not isinstance(values, list):
            raise ValueError(f"telegram_gateway.{name} must be a list")
        return tuple(str(value) for value in values)

    hashes = tuple(value.lower() for value in _tuple("capability_token_sha256"))

    return TelegramGatewayConfig(
        enabled=bool(section.get("enabled", False)),
        operator_whitelist=_tuple("operator_whitelist"),
        allowed_chat_ids=_tuple("allowed_chat_ids"),
        capability_token_sha256=hashes,
        max_message_length=int(section.get("max_message_length", 128)),
        per_sender_limit_per_minute=int(section.get("per_sender_limit_per_minute", 6)),
        per_chat_limit_per_minute=int(section.get("per_chat_limit_per_minute", 12)),
        global_limit_per_minute=int(section.get("global_limit_per_minute", 30)),
        replay_window_seconds=int(section.get("replay_window_seconds", 86400)),
        confirmation_expiry_seconds=int(section.get("confirmation_expiry_seconds", 300)),
    )


class TelegramGateway:
    """
    Local Telegram adapter boundary.

    This class processes already-received Telegram-shaped envelopes. It does not
    open sockets, poll Telegram, register webhooks, or execute runtime actions.
    """

    def __init__(
        self,
        config: TelegramGatewayConfig | None = None,
        *,
        config_path: Path | str = DEFAULT_CONFIG_PATH,
    ) -> None:
        self.config = config or load_telegram_gateway_config(config_path)
        self.parser = OperatorCommandParser()
        init_db()

    def process_envelope(self, envelope: TelegramEnvelope) -> TelegramGatewayResult:
        if not self.config.enabled:
            return self._reject(
                "external_adapter_disabled",
                details={"adapter": "telegram"},
            )

        normalized = self._normalize_envelope(envelope)
        if isinstance(normalized, TelegramGatewayResult):
            return normalized

        replay = self._existing_message_id(envelope.platform_message_id)
        if replay is not None:
            return self._reject(
                "external_replay_detected",
                message_id=replay,
                details={"platform_message_id": envelope.platform_message_id},
            )

        rate_reason = self._rate_limit_reason(envelope)
        if rate_reason is not None:
            message_id = self._insert_message(
                envelope,
                decision_status="rejected",
                denial_reason=rate_reason,
                command_text=normalized["command_text"],
            )
            return self._reject(
                rate_reason,
                message_id=message_id,
                details={"platform_message_id": envelope.platform_message_id},
            )

        denial_reason = self._authorization_denial_reason(envelope)
        if denial_reason is not None:
            message_id = self._insert_message(
                envelope,
                decision_status="rejected",
                denial_reason=denial_reason,
                command_text=normalized["command_text"],
            )
            return self._reject(denial_reason, message_id=message_id)

        parse_result = self.parser.parse(normalized["command_text"])
        if not parse_result.accepted:
            message_id = self._insert_message(
                envelope,
                decision_status="rejected",
                denial_reason=parse_result.rejection_reason,
                command_text=normalized["command_text"],
            )
            return self._reject(
                parse_result.rejection_reason or "operator_command_rejected",
                message_id=message_id,
                details={"parser": parse_result.to_dict()},
            )

        message_id = self._insert_message(
            envelope,
            decision_status="confirmation_required",
            denial_reason=None,
            command_text=normalized["command_text"],
        )
        token = secrets.token_urlsafe(32)
        confirmation_id = self._insert_confirmation(
            message_id=message_id,
            command_name=parse_result.command_name or "",
            manifest_id=parse_result.manifest_id or "",
            confirmation_token=token,
        )

        return TelegramGatewayResult(
            accepted=True,
            status="confirmation_required",
            denial_reason=None,
            message_id=message_id,
            confirmation_id=confirmation_id,
            command_id=None,
            confirmation_token=token,
            runtime_action_executed=False,
            ledger_written=False,
            details={
                "parser": parse_result.to_dict(),
                "adapter": "telegram",
                "external_action_executed": False,
            },
        )

    def confirm_intent(
        self,
        confirmation_token: str,
        *,
        accept: bool = True,
        operator_id: str = "telegram_gateway",
    ) -> TelegramGatewayResult:
        token_sha256 = sha256_text(confirmation_token)
        now = _utc_now()

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    cr.confirmation_id,
                    cr.message_id,
                    cr.command_name,
                    cr.manifest_id,
                    cr.confirmation_status,
                    cr.expires_at,
                    em.command_text
                FROM external_confirmation_requests AS cr
                JOIN external_adapter_messages AS em
                  ON em.message_id = cr.message_id
                WHERE cr.confirmation_token_sha256 = ?
                """,
                (token_sha256,),
            ).fetchone()

            if row is None:
                return self._reject("confirmation_token_unknown")

            if row["confirmation_status"] != "pending":
                return self._reject(
                    "confirmation_not_pending",
                    message_id=int(row["message_id"]),
                    confirmation_id=int(row["confirmation_id"]),
                    details={"confirmation_status": row["confirmation_status"]},
                )

            if row["expires_at"] <= now:
                conn.execute(
                    """
                    UPDATE external_confirmation_requests
                    SET confirmation_status = 'expired',
                        completed_at = ?
                    WHERE confirmation_id = ?
                    """,
                    (now, row["confirmation_id"]),
                )
                return self._reject(
                    "confirmation_expired",
                    message_id=int(row["message_id"]),
                    confirmation_id=int(row["confirmation_id"]),
                )

            if not accept:
                conn.execute(
                    """
                    UPDATE external_confirmation_requests
                    SET confirmation_status = 'rejected',
                        completed_at = ?
                    WHERE confirmation_id = ?
                    """,
                    (now, row["confirmation_id"]),
                )
                conn.execute(
                    """
                    UPDATE external_adapter_messages
                    SET decision_status = 'rejected',
                        denial_reason = 'operator_confirmation_rejected'
                    WHERE message_id = ?
                    """,
                    (row["message_id"],),
                )
                return self._reject(
                    "operator_confirmation_rejected",
                    message_id=int(row["message_id"]),
                    confirmation_id=int(row["confirmation_id"]),
                )

        record = record_operator_command_intent(
            row["command_text"],
            operator_id=operator_id,
        )
        if not record.recorded:
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE external_confirmation_requests
                    SET confirmation_status = 'rejected',
                        completed_at = ?
                    WHERE confirmation_id = ?
                    """,
                    (now, row["confirmation_id"]),
                )
                conn.execute(
                    """
                    UPDATE external_adapter_messages
                    SET decision_status = 'rejected',
                        denial_reason = ?
                    WHERE message_id = ?
                    """,
                    (record.rejection_reason, row["message_id"]),
                )
            return self._reject(
                record.rejection_reason or "operator_command_ledger_rejected",
                message_id=int(row["message_id"]),
                confirmation_id=int(row["confirmation_id"]),
                details={"ledger": record.to_dict()},
            )

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE external_confirmation_requests
                SET confirmation_status = 'accepted',
                    command_id = ?,
                    completed_at = ?
                WHERE confirmation_id = ?
                """,
                (record.command_id, now, row["confirmation_id"]),
            )
            conn.execute(
                """
                UPDATE external_adapter_messages
                SET decision_status = 'accepted',
                    denial_reason = NULL
                WHERE message_id = ?
                """,
                (row["message_id"],),
            )

        return TelegramGatewayResult(
            accepted=True,
            status="accepted",
            denial_reason=None,
            message_id=int(row["message_id"]),
            confirmation_id=int(row["confirmation_id"]),
            command_id=record.command_id,
            confirmation_token=None,
            runtime_action_executed=False,
            ledger_written=True,
            details={"ledger": record.to_dict()},
        )

    def _normalize_envelope(
        self,
        envelope: TelegramEnvelope,
    ) -> dict[str, str] | TelegramGatewayResult:
        values = {
            "platform_message_id": envelope.platform_message_id,
            "platform_sender_id": envelope.platform_sender_id,
            "platform_chat_id": envelope.platform_chat_id,
            "command_text": envelope.command_text,
            "capability_token": envelope.capability_token,
        }
        for key, value in values.items():
            if not isinstance(value, str) or not value.strip():
                return self._reject(
                    "telegram_envelope_field_missing",
                    details={"field": key},
                )

        command_text = envelope.command_text.strip()
        if len(command_text) > self.config.max_message_length:
            return self._reject(
                "telegram_message_too_long",
                details={
                    "max_message_length": self.config.max_message_length,
                    "raw_text_length": len(command_text),
                },
            )

        return {"command_text": command_text}

    def _authorization_denial_reason(self, envelope: TelegramEnvelope) -> str | None:
        if self.config.operator_whitelist and (
            envelope.platform_sender_id not in self.config.operator_whitelist
        ):
            return "telegram_sender_not_whitelisted"

        if self.config.allowed_chat_ids and (
            envelope.platform_chat_id not in self.config.allowed_chat_ids
        ):
            return "telegram_chat_not_allowed"

        if not self.config.capability_token_sha256:
            return "telegram_capability_token_not_configured"

        if sha256_text(envelope.capability_token) not in self.config.capability_token_sha256:
            return "telegram_capability_token_invalid"

        return None

    def _existing_message_id(self, platform_message_id: str) -> int | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT message_id
                FROM external_adapter_messages
                WHERE adapter = 'telegram'
                  AND platform_message_id = ?
                """,
                (platform_message_id,),
            ).fetchone()
        return int(row["message_id"]) if row else None

    def _rate_limit_reason(self, envelope: TelegramEnvelope) -> str | None:
        checks = (
            (
                "telegram_sender_rate_limited",
                self.config.per_sender_limit_per_minute,
                "platform_sender_id = ?",
                (envelope.platform_sender_id,),
            ),
            (
                "telegram_chat_rate_limited",
                self.config.per_chat_limit_per_minute,
                "platform_chat_id = ?",
                (envelope.platform_chat_id,),
            ),
            (
                "telegram_global_rate_limited",
                self.config.global_limit_per_minute,
                "1 = 1",
                (),
            ),
        )

        with get_connection() as conn:
            for reason, limit, predicate, params in checks:
                if limit <= 0:
                    return reason
                row = conn.execute(
                    f"""
                    SELECT COUNT(*) AS count
                    FROM external_adapter_messages
                    WHERE adapter = 'telegram'
                      AND created_at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-60 seconds')
                      AND {predicate}
                    """,
                    params,
                ).fetchone()
                if int(row["count"]) >= limit:
                    return reason
        return None

    def _insert_message(
        self,
        envelope: TelegramEnvelope,
        *,
        decision_status: str,
        denial_reason: str | None,
        command_text: str,
    ) -> int:
        received_at = envelope.received_at or _utc_now()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO external_adapter_messages
                (adapter, platform_message_id, platform_sender_id, platform_chat_id,
                 raw_text_sha256, raw_text_length, command_text, received_at,
                 decision_status, denial_reason)
                VALUES
                ('telegram', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    envelope.platform_message_id,
                    envelope.platform_sender_id,
                    envelope.platform_chat_id,
                    sha256_text(command_text),
                    len(command_text),
                    command_text,
                    received_at,
                    decision_status,
                    denial_reason,
                ),
            )
            return int(cur.lastrowid)

    def _insert_confirmation(
        self,
        *,
        message_id: int,
        command_name: str,
        manifest_id: str,
        confirmation_token: str,
    ) -> int:
        expires_at = _utc_after(self.config.confirmation_expiry_seconds)
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO external_confirmation_requests
                (message_id, command_name, manifest_id, confirmation_token_sha256, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    command_name,
                    manifest_id,
                    sha256_text(confirmation_token),
                    expires_at,
                ),
            )
            return int(cur.lastrowid)

    @staticmethod
    def _reject(
        denial_reason: str | None,
        *,
        message_id: int | None = None,
        confirmation_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> TelegramGatewayResult:
        return TelegramGatewayResult(
            accepted=False,
            status="rejected",
            denial_reason=denial_reason,
            message_id=message_id,
            confirmation_id=confirmation_id,
            command_id=None,
            confirmation_token=None,
            runtime_action_executed=False,
            ledger_written=False,
            details=details or {},
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _utc_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
