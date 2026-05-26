from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from axiom.gateways.telegram_gateway import (
    TelegramEnvelope,
    TelegramGateway,
    TelegramGatewayConfig,
    sha256_text,
)


AXIOM_COMMAND_PREFIX = "/axiom"
AXIOM_CONFIRM_PREFIX = "/axiom-confirm"
AXIOM_REJECT_PREFIX = "/axiom-reject"


class TelegramBotApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedTelegramBotText:
    action: str
    capability_token: str | None
    command_text: str | None
    confirmation_token: str | None
    denial_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TelegramBotAdapterResult:
    accepted: bool
    action: str
    denial_reason: str | None
    update_id: int | None
    platform_message_id: str | None
    platform_sender_id: str | None
    platform_chat_id: str | None
    outbound_text: str | None
    outbound_sent: bool
    runtime_action_executed: bool
    ledger_written: bool
    gateway: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TelegramPollingBatchResult:
    offset: int | None
    update_count: int
    results: list[TelegramBotAdapterResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "offset": self.offset,
            "update_count": self.update_count,
            "results": [result.to_dict() for result in self.results],
        }


class TelegramBotApiClient:
    def __init__(
        self,
        bot_token: str,
        *,
        api_base: str = "https://api.telegram.org",
        timeout_seconds: int = 10,
    ) -> None:
        if not bot_token.strip():
            raise TelegramBotApiError("Telegram bot token is required")
        self.bot_token = bot_token
        self.api_base = api_base.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_updates(
        self,
        *,
        offset: int | None = None,
        timeout_seconds: int = 10,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout_seconds,
            "limit": limit,
            "allowed_updates": json.dumps(["message"]),
        }
        if offset is not None:
            payload["offset"] = offset
        response = self._request("getUpdates", payload)
        result = response.get("result", [])
        if not isinstance(result, list):
            raise TelegramBotApiError("Telegram getUpdates result was not a list")
        return [item for item in result if isinstance(item, dict)]

    def send_message(self, chat_id: str, text: str) -> dict[str, Any]:
        return self._request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )

    def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}/bot{self.bot_token}/{method}"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise TelegramBotApiError("Telegram Bot API request timed out") from exc
        except urllib.error.URLError as exc:
            raise TelegramBotApiError(f"Telegram Bot API request failed: {exc}") from exc

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TelegramBotApiError("Telegram Bot API returned invalid JSON") from exc

        if not decoded.get("ok"):
            raise TelegramBotApiError(
                f"Telegram Bot API rejected {method}: {decoded.get('description')}"
            )
        return decoded


class TelegramPollingAdapter:
    """
    Polling adapter for Telegram Bot API updates.

    This adapter is the network boundary. It converts Telegram updates into
    local gateway envelopes or confirmation calls. It never executes runtime
    actions directly.
    """

    def __init__(
        self,
        *,
        client: TelegramBotApiClient,
        gateway: TelegramGateway | None = None,
        config: TelegramGatewayConfig | None = None,
        send_responses: bool = True,
    ) -> None:
        self.client = client
        self.gateway = gateway or TelegramGateway(config=config)
        self.send_responses = send_responses

    @property
    def config(self) -> TelegramGatewayConfig:
        return self.gateway.config

    def poll_once(
        self,
        *,
        offset: int | None = None,
        timeout_seconds: int = 10,
        limit: int = 20,
    ) -> TelegramPollingBatchResult:
        updates = self.client.get_updates(
            offset=offset,
            timeout_seconds=timeout_seconds,
            limit=limit,
        )
        results = [self.process_update(update) for update in updates]
        next_offset = None
        if updates:
            next_offset = max(int(update.get("update_id", 0)) for update in updates) + 1
        return TelegramPollingBatchResult(
            offset=next_offset,
            update_count=len(updates),
            results=results,
        )

    def process_update(self, update: dict[str, Any]) -> TelegramBotAdapterResult:
        update_id = _optional_int(update.get("update_id"))
        message = update.get("message")
        if not isinstance(message, dict):
            return self._finalize(
                accepted=False,
                action="reject",
                denial_reason="telegram_update_message_missing",
                update_id=update_id,
                platform_message_id=None,
                platform_sender_id=None,
                platform_chat_id=None,
                outbound_text=None,
                gateway=None,
            )

        identity = _extract_identity(message)
        if identity["denial_reason"] is not None:
            return self._finalize(
                accepted=False,
                action="reject",
                denial_reason=identity["denial_reason"],
                update_id=update_id,
                platform_message_id=identity["platform_message_id"],
                platform_sender_id=identity["platform_sender_id"],
                platform_chat_id=identity["platform_chat_id"],
                outbound_text=_format_rejection(identity["denial_reason"]),
                gateway=None,
            )

        text = message.get("text")
        parsed = parse_bot_text(text if isinstance(text, str) else "")
        if parsed.denial_reason is not None:
            return self._finalize(
                accepted=False,
                action="reject",
                denial_reason=parsed.denial_reason,
                update_id=update_id,
                platform_message_id=identity["platform_message_id"],
                platform_sender_id=identity["platform_sender_id"],
                platform_chat_id=identity["platform_chat_id"],
                outbound_text=_format_rejection(parsed.denial_reason),
                gateway=None,
            )

        if parsed.action == "command":
            envelope = TelegramEnvelope(
                platform_message_id=identity["platform_message_id"] or "",
                platform_sender_id=identity["platform_sender_id"] or "",
                platform_chat_id=identity["platform_chat_id"] or "",
                command_text=parsed.command_text or "",
                capability_token=parsed.capability_token or "",
            )
            gateway_result = self.gateway.process_envelope(envelope)
            outbound_text = _format_gateway_result(gateway_result)
            return self._finalize(
                accepted=gateway_result.accepted,
                action="command",
                denial_reason=gateway_result.denial_reason,
                update_id=update_id,
                platform_message_id=identity["platform_message_id"],
                platform_sender_id=identity["platform_sender_id"],
                platform_chat_id=identity["platform_chat_id"],
                outbound_text=outbound_text,
                gateway=gateway_result.to_dict(),
            )

        denial_reason = self._confirmation_denial_reason(
            platform_sender_id=identity["platform_sender_id"] or "",
            platform_chat_id=identity["platform_chat_id"] or "",
            capability_token=parsed.capability_token or "",
        )
        if denial_reason is not None:
            return self._finalize(
                accepted=False,
                action=parsed.action,
                denial_reason=denial_reason,
                update_id=update_id,
                platform_message_id=identity["platform_message_id"],
                platform_sender_id=identity["platform_sender_id"],
                platform_chat_id=identity["platform_chat_id"],
                outbound_text=_format_rejection(denial_reason),
                gateway=None,
            )

        gateway_result = self.gateway.confirm_intent(
            parsed.confirmation_token or "",
            accept=parsed.action == "confirm",
            operator_id="telegram_bot_adapter",
        )
        outbound_text = _format_gateway_result(gateway_result)
        return self._finalize(
            accepted=gateway_result.accepted,
            action=parsed.action,
            denial_reason=gateway_result.denial_reason,
            update_id=update_id,
            platform_message_id=identity["platform_message_id"],
            platform_sender_id=identity["platform_sender_id"],
            platform_chat_id=identity["platform_chat_id"],
            outbound_text=outbound_text,
            gateway=gateway_result.to_dict(),
        )

    def _confirmation_denial_reason(
        self,
        *,
        platform_sender_id: str,
        platform_chat_id: str,
        capability_token: str,
    ) -> str | None:
        if not self.config.enabled:
            return "external_adapter_disabled"
        if self.config.operator_whitelist and platform_sender_id not in self.config.operator_whitelist:
            return "telegram_sender_not_whitelisted"
        if self.config.allowed_chat_ids and platform_chat_id not in self.config.allowed_chat_ids:
            return "telegram_chat_not_allowed"
        if not self.config.capability_token_sha256:
            return "telegram_capability_token_not_configured"
        if sha256_text(capability_token) not in self.config.capability_token_sha256:
            return "telegram_capability_token_invalid"
        return None

    def _finalize(
        self,
        *,
        accepted: bool,
        action: str,
        denial_reason: str | None,
        update_id: int | None,
        platform_message_id: str | None,
        platform_sender_id: str | None,
        platform_chat_id: str | None,
        outbound_text: str | None,
        gateway: dict[str, Any] | None,
    ) -> TelegramBotAdapterResult:
        outbound_sent = False
        if self.send_responses and outbound_text and platform_chat_id:
            self.client.send_message(platform_chat_id, outbound_text)
            outbound_sent = True

        return TelegramBotAdapterResult(
            accepted=accepted,
            action=action,
            denial_reason=denial_reason,
            update_id=update_id,
            platform_message_id=platform_message_id,
            platform_sender_id=platform_sender_id,
            platform_chat_id=platform_chat_id,
            outbound_text=outbound_text,
            outbound_sent=outbound_sent,
            runtime_action_executed=False,
            ledger_written=bool(gateway and gateway.get("ledger_written")),
            gateway=gateway,
        )


def parse_bot_text(text: str) -> ParsedTelegramBotText:
    if not text.strip():
        return ParsedTelegramBotText("reject", None, None, None, "telegram_message_text_missing")

    parts = text.strip().split(maxsplit=2)
    prefix = parts[0].lower()

    if prefix == AXIOM_COMMAND_PREFIX:
        if len(parts) != 3:
            return ParsedTelegramBotText("reject", None, None, None, "telegram_command_format_invalid")
        return ParsedTelegramBotText(
            action="command",
            capability_token=parts[1],
            command_text=parts[2],
            confirmation_token=None,
            denial_reason=None,
        )

    if prefix in {AXIOM_CONFIRM_PREFIX, AXIOM_REJECT_PREFIX}:
        if len(parts) != 3:
            return ParsedTelegramBotText("reject", None, None, None, "telegram_confirmation_format_invalid")
        return ParsedTelegramBotText(
            action="confirm" if prefix == AXIOM_CONFIRM_PREFIX else "reject_confirmation",
            capability_token=parts[1],
            command_text=None,
            confirmation_token=parts[2],
            denial_reason=None,
        )

    return ParsedTelegramBotText("reject", None, None, None, "telegram_command_prefix_unknown")


def _extract_identity(message: dict[str, Any]) -> dict[str, str | None]:
    chat = message.get("chat")
    sender = message.get("from")
    message_id = message.get("message_id")

    if not isinstance(chat, dict) or chat.get("id") is None:
        return _identity_denied("telegram_chat_id_missing")
    if not isinstance(sender, dict) or sender.get("id") is None:
        return _identity_denied("telegram_sender_id_missing", chat_id=str(chat.get("id")))
    if message_id is None:
        return _identity_denied(
            "telegram_message_id_missing",
            chat_id=str(chat.get("id")),
            sender_id=str(sender.get("id")),
        )

    chat_id = str(chat["id"])
    sender_id = str(sender["id"])
    return {
        "platform_message_id": f"{chat_id}:{message_id}",
        "platform_sender_id": sender_id,
        "platform_chat_id": chat_id,
        "denial_reason": None,
    }


def _identity_denied(
    reason: str,
    *,
    chat_id: str | None = None,
    sender_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "platform_message_id": None,
        "platform_sender_id": sender_id,
        "platform_chat_id": chat_id,
        "denial_reason": reason,
    }


def _format_gateway_result(result) -> str:
    if result.accepted and result.status == "confirmation_required":
        parser = result.details.get("parser", {})
        command_name = parser.get("command_name", "unknown")
        return "\n".join(
            [
                "AXIOM confirmation required",
                f"command: {command_name}",
                f"confirmation_id: {result.confirmation_id}",
                f"confirm: {AXIOM_CONFIRM_PREFIX} <capability-token> {result.confirmation_token}",
                f"reject: {AXIOM_REJECT_PREFIX} <capability-token> {result.confirmation_token}",
                "runtime_action_executed: false",
            ]
        )

    if result.accepted:
        return "\n".join(
            [
                "AXIOM intent recorded",
                f"command_id: {result.command_id}",
                "command_status: pending",
                "runtime_action_executed: false",
            ]
        )

    return _format_rejection(result.denial_reason or "telegram_gateway_rejected")


def _format_rejection(reason: str | None) -> str:
    return "\n".join(
        [
            "AXIOM rejected",
            f"reason: {reason or 'unknown'}",
            "runtime_action_executed: false",
        ]
    )


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
