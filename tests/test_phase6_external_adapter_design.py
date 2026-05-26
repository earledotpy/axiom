from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6_external_adapter_design.md"
ROADMAP = ROOT / "docs" / "phase6_roadmap.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TOOLS = ROOT / "tools"
AXIOM = ROOT / "axiom"


def test_phase6f_design_packet_names_required_external_adapter_boundaries():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "This is a design packet only",
        "Telegram bot runtime",
        "external command ingestion",
        "ExternalAdapter.receive_message(envelope)",
        "ExternalAdapter.authenticate_sender(envelope)",
        "ExternalAdapter.request_operator_confirmation(intent_id)",
        "external_sender_not_whitelisted",
        "external_chat_not_allowed",
        "external_replay_detected",
        "external_rate_limited",
        "confirmation_required",
        "record_operator_command_intent(...)",
        "do not execute runtime action",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6f_design_packet_requires_whitelist_replay_rate_limit_and_confirmation():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "platform_sender_id is in local operator whitelist",
        "platform_chat_id is in local allowed chat whitelist",
        "message id has not been processed before",
        "per_sender_message_limit_per_minute",
        "dedupe table keyed by adapter + platform_message_id",
        "stage 2: require local operator confirmation",
        "confirmation must happen through a local approved surface",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6f_roadmap_and_terminal_docs_index_are_current():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs_module = DOCS_MODULE.read_text(encoding="utf-8")

    assert "Slices 6A through 6I are implemented" in roadmap
    assert "docs\\phase6_external_adapter_design.md" in roadmap
    assert "phase6-external-adapter-design" in docs_module
    assert "docs\\phase6_external_adapter_design.md" in docs_module


def test_phase6f_does_not_add_external_adapter_runtime_files():
    forbidden_paths = [
        TOOLS / "external_adapter_design_check.py",
        TOOLS / "telegram_adapter_smoke_test.py",
        TOOLS / "chat_adapter_smoke_test.py",
        AXIOM / "gateways" / "telegram_adapter.py",
        AXIOM / "gateways" / "chat_adapter.py",
        AXIOM / "core" / "external_adapter.py",
    ]

    for path in forbidden_paths:
        assert not path.exists(), f"6F is design-only; unexpected runtime file: {path}"
