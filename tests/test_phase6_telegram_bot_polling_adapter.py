from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from axiom.gateways.telegram_bot_adapter import (
    AXIOM_COMMAND_PREFIX,
    AXIOM_CONFIRM_PREFIX,
    TelegramBotApiClient,
    TelegramBotApiError,
    TelegramPollingAdapter,
    parse_bot_text,
)
from axiom.gateways.telegram_gateway import TelegramGateway, TelegramGatewayConfig, sha256_text
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6.md"


class FakeTelegramClient:
    def __init__(self, updates=None):
        self.updates = list(updates or [])
        self.sent_messages = []

    def get_updates(self, *, offset=None, timeout_seconds=10, limit=20):
        return self.updates[:limit]

    def send_message(self, chat_id: str, text: str):
        self.sent_messages.append({"chat_id": chat_id, "text": text})
        return {"ok": True, "result": {"chat": {"id": chat_id}, "text": text}}


def register_manifests() -> None:
    result = subprocess.run(
        [sys.executable, "tools/register_manifests.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def enabled_config() -> TelegramGatewayConfig:
    return TelegramGatewayConfig(
        enabled=True,
        operator_whitelist=("1001",),
        allowed_chat_ids=("2002",),
        capability_token_sha256=(sha256_text("test-token"),),
        max_message_length=128,
        per_sender_limit_per_minute=6,
        per_chat_limit_per_minute=12,
        global_limit_per_minute=30,
        replay_window_seconds=86400,
        confirmation_expiry_seconds=300,
    )


def update(text: str, *, update_id: int = 10, message_id: int = 20, sender_id: int = 1001, chat_id: int = 2002):
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "from": {"id": sender_id},
            "chat": {"id": chat_id},
            "text": text,
        },
    }


def test_parse_bot_text_accepts_command_and_confirmation_formats():
    command = parse_bot_text(f"{AXIOM_COMMAND_PREFIX} test-token /status")
    confirmation = parse_bot_text(f"{AXIOM_CONFIRM_PREFIX} test-token abc123")
    unknown = parse_bot_text("/status")

    assert command.action == "command"
    assert command.capability_token == "test-token"
    assert command.command_text == "/status"
    assert confirmation.action == "confirm"
    assert confirmation.confirmation_token == "abc123"
    assert unknown.denial_reason == "telegram_command_prefix_unknown"


def test_polling_adapter_processes_command_without_runtime_execution():
    register_manifests()
    fake = FakeTelegramClient()
    gateway = TelegramGateway(config=enabled_config())
    adapter = TelegramPollingAdapter(client=fake, gateway=gateway)

    result = adapter.process_update(update("/axiom test-token /status"))

    assert result.accepted is True
    assert result.action == "command"
    assert result.runtime_action_executed is False
    assert result.ledger_written is False
    assert result.gateway is not None
    assert result.gateway["status"] == "confirmation_required"
    assert fake.sent_messages
    assert "AXIOM confirmation required" in fake.sent_messages[0]["text"]

    with get_connection() as conn:
        command_count = conn.execute("SELECT COUNT(*) FROM operator_commands").fetchone()[0]
        confirmation_count = conn.execute(
            "SELECT COUNT(*) FROM external_confirmation_requests"
        ).fetchone()[0]

    assert command_count == 0
    assert confirmation_count == 1


def test_polling_adapter_confirmation_records_pending_intent_only():
    register_manifests()
    create_session(operator_id="telegram_adapter_test")
    fake = FakeTelegramClient()
    gateway = TelegramGateway(config=enabled_config())
    adapter = TelegramPollingAdapter(client=fake, gateway=gateway)
    pending = adapter.process_update(update("/axiom test-token /status", message_id=20))
    token = pending.gateway["confirmation_token"]

    confirmed = adapter.process_update(
        update(f"/axiom-confirm test-token {token}", update_id=11, message_id=21)
    )

    assert confirmed.accepted is True
    assert confirmed.action == "confirm"
    assert confirmed.runtime_action_executed is False
    assert confirmed.ledger_written is True
    assert confirmed.gateway["command_id"] is not None
    assert "AXIOM intent recorded" in fake.sent_messages[-1]["text"]

    with get_connection() as conn:
        command = conn.execute(
            "SELECT authorization_status, command_status FROM operator_commands"
        ).fetchone()

    assert command["authorization_status"] == "pending"
    assert command["command_status"] == "pending"


def test_polling_adapter_rejects_unwhitelisted_confirmation_before_ledger_write():
    register_manifests()
    create_session(operator_id="telegram_adapter_test")
    fake = FakeTelegramClient()
    gateway = TelegramGateway(config=enabled_config())
    adapter = TelegramPollingAdapter(client=fake, gateway=gateway)
    pending = adapter.process_update(update("/axiom test-token /status", message_id=20))
    token = pending.gateway["confirmation_token"]

    rejected = adapter.process_update(
        update(
            f"/axiom-confirm test-token {token}",
            update_id=11,
            message_id=21,
            sender_id=9999,
        )
    )

    assert rejected.accepted is False
    assert rejected.denial_reason == "telegram_sender_not_whitelisted"
    assert rejected.runtime_action_executed is False
    with get_connection() as conn:
        command_count = conn.execute("SELECT COUNT(*) FROM operator_commands").fetchone()[0]
    assert command_count == 0


def test_polling_tool_requires_bot_token_without_network_call():
    env = os.environ.copy()
    env.pop("TELEGRAM_BOT_TOKEN", None)
    result = subprocess.run(
        [sys.executable, "tools/run_telegram_polling_adapter.py", "--once", "--json"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "TELEGRAM_BOT_TOKEN is not set" in result.stderr


def test_bot_api_client_converts_read_timeout_to_api_error(monkeypatch):
    def raise_timeout(request, timeout):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(
        "axiom.gateways.telegram_bot_adapter.urllib.request.urlopen",
        raise_timeout,
    )

    client = TelegramBotApiClient("test-token", timeout_seconds=1)

    with pytest.raises(TelegramBotApiError) as excinfo:
        client.get_updates(timeout_seconds=1)

    assert "Telegram Bot API request timed out" in str(excinfo.value)


def test_polling_adapter_doc_records_live_boundary():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "tools\\run_telegram_polling_adapter.py",
        "TELEGRAM_BOT_TOKEN",
        "/axiom <capability-token> /status",
        "/axiom-confirm <capability-token> <confirmation-token>",
        "does not execute runtime actions",
        "not wired into the terminal command registry",
    ]
    for phrase in required:
        assert phrase in text


