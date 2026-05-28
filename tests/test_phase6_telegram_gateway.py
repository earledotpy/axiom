from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axiom.gateways.telegram_gateway import (
    TelegramEnvelope,
    TelegramGateway,
    TelegramGatewayConfig,
    load_telegram_gateway_config,
    sha256_text,
)
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session
from tools.audit_telegram_gateway import audit_telegram_gateway


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6.md"
ROADMAP = ROOT / "docs" / "phase6.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"
CONFIG = ROOT / "config" / "axiom.yaml"


def register_manifests() -> None:
    result = subprocess.run(
        [sys.executable, "tools/register_manifests.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def enabled_config(*, token: str = "test-token", per_sender_limit: int = 6) -> TelegramGatewayConfig:
    return TelegramGatewayConfig(
        enabled=True,
        operator_whitelist=("1001",),
        allowed_chat_ids=("2002",),
        capability_token_sha256=(sha256_text(token),),
        max_message_length=128,
        per_sender_limit_per_minute=per_sender_limit,
        per_chat_limit_per_minute=12,
        global_limit_per_minute=30,
        replay_window_seconds=86400,
        confirmation_expiry_seconds=300,
    )


def envelope(
    message_id: str = "m-1",
    *,
    sender_id: str = "1001",
    chat_id: str = "2002",
    command_text: str = "/status",
    token: str = "test-token",
) -> TelegramEnvelope:
    return TelegramEnvelope(
        platform_message_id=message_id,
        platform_sender_id=sender_id,
        platform_chat_id=chat_id,
        command_text=command_text,
        capability_token=token,
    )


def test_default_telegram_gateway_config_is_disabled_and_hash_only():
    config = load_telegram_gateway_config(CONFIG)

    assert config.enabled is False
    assert config.operator_whitelist == ()
    assert config.allowed_chat_ids == ()
    assert config.capability_token_sha256 == ()
    assert "capability_tokens" not in CONFIG.read_text(encoding="utf-8")


def test_disabled_gateway_rejects_without_persisting_external_message():
    gateway = TelegramGateway(config=TelegramGatewayConfig(
        enabled=False,
        operator_whitelist=(),
        allowed_chat_ids=(),
        capability_token_sha256=(),
        max_message_length=128,
        per_sender_limit_per_minute=6,
        per_chat_limit_per_minute=12,
        global_limit_per_minute=30,
        replay_window_seconds=86400,
        confirmation_expiry_seconds=300,
    ))

    result = gateway.process_envelope(envelope())

    assert result.accepted is False
    assert result.denial_reason == "external_adapter_disabled"
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM external_adapter_messages").fetchone()[0]
    assert count == 0


def test_valid_telegram_envelope_creates_pending_confirmation_without_ledger_write():
    register_manifests()
    gateway = TelegramGateway(config=enabled_config())

    result = gateway.process_envelope(envelope())

    assert result.accepted is True
    assert result.status == "confirmation_required"
    assert result.confirmation_token
    assert result.ledger_written is False
    assert result.runtime_action_executed is False

    with get_connection() as conn:
        message = conn.execute(
            "SELECT * FROM external_adapter_messages WHERE message_id = ?",
            (result.message_id,),
        ).fetchone()
        confirmation = conn.execute(
            "SELECT * FROM external_confirmation_requests WHERE confirmation_id = ?",
            (result.confirmation_id,),
        ).fetchone()
        command_count = conn.execute("SELECT COUNT(*) FROM operator_commands").fetchone()[0]

    assert message["decision_status"] == "confirmation_required"
    assert message["raw_text_sha256"] == sha256_text("/status")
    assert message["raw_text_length"] == len("/status")
    assert confirmation["confirmation_status"] == "pending"
    assert confirmation["confirmation_token_sha256"] == sha256_text(result.confirmation_token)
    assert command_count == 0


def test_confirming_telegram_intent_writes_pending_operator_command_without_execution():
    register_manifests()
    create_session(operator_id="test_operator")
    gateway = TelegramGateway(config=enabled_config())
    pending = gateway.process_envelope(envelope())

    result = gateway.confirm_intent(
        pending.confirmation_token or "",
        operator_id="telegram_test_operator",
    )

    assert result.accepted is True
    assert result.status == "accepted"
    assert result.ledger_written is True
    assert result.runtime_action_executed is False
    assert result.command_id is not None

    with get_connection() as conn:
        command = conn.execute(
            "SELECT * FROM operator_commands WHERE command_id = ?",
            (result.command_id,),
        ).fetchone()
        confirmation = conn.execute(
            "SELECT * FROM external_confirmation_requests WHERE confirmation_id = ?",
            (result.confirmation_id,),
        ).fetchone()

    assert command["command_name"] == "status"
    assert command["authorization_status"] == "pending"
    assert command["command_status"] == "pending"
    assert confirmation["confirmation_status"] == "accepted"
    assert confirmation["command_id"] == result.command_id


def test_telegram_gateway_rejects_replay_invalid_token_and_sender_rate_limit():
    register_manifests()
    gateway = TelegramGateway(config=enabled_config(per_sender_limit=1))

    first = gateway.process_envelope(envelope("m-1"))
    replay = gateway.process_envelope(envelope("m-1"))
    invalid_token = gateway.process_envelope(envelope("m-2", token="wrong-token"))
    limited = gateway.process_envelope(envelope("m-3"))

    assert first.status == "confirmation_required"
    assert replay.accepted is False
    assert replay.denial_reason == "external_replay_detected"
    assert invalid_token.accepted is False
    assert invalid_token.denial_reason == "telegram_sender_rate_limited"
    assert limited.accepted is False
    assert limited.denial_reason == "telegram_sender_rate_limited"


def test_telegram_gateway_rejects_invalid_token_when_under_rate_limit():
    register_manifests()
    gateway = TelegramGateway(config=enabled_config())

    result = gateway.process_envelope(envelope("m-1", token="wrong-token"))

    assert result.accepted is False
    assert result.denial_reason == "telegram_capability_token_invalid"
    with get_connection() as conn:
        confirmation_count = conn.execute(
            "SELECT COUNT(*) FROM external_confirmation_requests"
        ).fetchone()[0]
    assert confirmation_count == 0


def test_telegram_gateway_audit_and_cli_pass_for_default_disabled_config():
    result = audit_telegram_gateway()

    assert result.passed is True
    assert result.violation_count == 0

    cli = subprocess.run(
        [sys.executable, "tools/audit_telegram_gateway.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    payload = json.loads(cli.stdout)
    assert payload["passed"] is True
    assert payload["violation_count"] == 0


def test_phase6_telegram_gateway_docs_terminal_and_registry_are_current():
    doc = DOC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs_module = DOCS_MODULE.read_text(encoding="utf-8")
    tools_module = TOOLS_MODULE.read_text(encoding="utf-8")
    help_module = HELP_MODULE.read_text(encoding="utf-8")
    registry_text = REGISTRY.read_text(encoding="utf-8")
    registry = json.loads(registry_text)

    required_doc_phrases = [
        "does not start a Telegram bot",
        "capability_token_sha256",
        "external_adapter_messages",
        "external_confirmation_requests",
        "runtime_action_executed = false",
        "python tools\\audit_telegram_gateway.py",
    ]
    for phrase in required_doc_phrases:
        assert phrase in doc

    assert "### 6G. Telegram Gateway Runtime Foundation" in roadmap
    assert "phase6" in docs_module
    assert "telegram-gateway-audit" in docs_module
    assert "axiom-telegram-gateway-audit" in tools_module
    assert "axiom-telegram-gateway-audit" in help_module
    assert "tools/audit_telegram_gateway.py" in registry_text
    assert any(
        command["name"] == "axiom-telegram-gateway-audit"
        for command in registry["commands"]
    )


def test_telegram_gateway_module_has_no_live_telegram_network_runtime():
    source = (ROOT / "axiom" / "gateways" / "telegram_gateway.py").read_text(
        encoding="utf-8"
    )

    forbidden_imports = [
        "import requests",
        "import httpx",
        "from telegram",
        "import telegram",
    ]
    for forbidden in forbidden_imports:
        assert forbidden not in source


