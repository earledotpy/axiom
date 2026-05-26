from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6_telegram_gateway_terminal_visibility.md"
ROADMAP = ROOT / "docs" / "phase6_roadmap.md"
PANEL = ROOT / "ui" / "terminal" / "modules" / "59-telegram-gateway.ps1"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TOOLS_MODULE = ROOT / "ui" / "terminal" / "modules" / "20-axiom-tools.ps1"
HELP_MODULE = ROOT / "ui" / "terminal" / "modules" / "90-safety-help.ps1"
DOCTOR_MODULE = ROOT / "ui" / "terminal" / "modules" / "49-doctor.ps1"
REPORT_MODULE = ROOT / "ui" / "terminal" / "modules" / "50-terminal-report.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def test_phase6h_telegram_gateway_terminal_panel_is_read_only():
    panel = PANEL.read_text(encoding="utf-8")

    assert "function axiom-telegram-gateway" in panel
    assert "mode=ro" in panel
    assert "config\\axiom.yaml" in panel
    assert "external_adapter_messages" in panel
    assert "external_confirmation_requests" in panel

    forbidden = [
        "process_envelope",
        "confirm_intent",
        "record_operator_command_intent.py",
        "Invoke-WebRequest",
        "Invoke-RestMethod",
        "Start-Process",
    ]
    for phrase in forbidden:
        assert phrase not in panel


def test_phase6h_terminal_surfaces_are_registered_and_non_mutating():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    commands = {command["name"]: command for command in registry["commands"]}

    assert "axiom-telegram-gateway" in commands
    assert "axiom-telegram-gateway-audit" in commands
    assert commands["axiom-telegram-gateway"]["mutates_axiom_runtime"] is False
    assert commands["axiom-telegram-gateway"]["category"] == "state_visibility"
    assert commands["axiom-telegram-gateway-audit"]["backing_tools"] == [
        "tools/audit_telegram_gateway.py"
    ]


def test_phase6h_help_doctor_report_docs_cover_gateway_visibility():
    docs = DOCS_MODULE.read_text(encoding="utf-8")
    tools = TOOLS_MODULE.read_text(encoding="utf-8")
    help_text = HELP_MODULE.read_text(encoding="utf-8")
    doctor = DOCTOR_MODULE.read_text(encoding="utf-8")
    report = REPORT_MODULE.read_text(encoding="utf-8")

    assert "phase6-telegram-gateway-terminal" in docs
    assert "telegram-gateway-terminal" in docs
    assert "axiom-telegram-gateway-audit" in tools
    assert "axiom-telegram-gateway" in help_text
    assert "Telegram gateway boundary state" in help_text
    assert "axiom-telegram-gateway" in doctor
    assert "tools\\audit_telegram_gateway.py" in doctor
    assert "axiom-telegram-gateway" in report
    assert "telegram_preflight_hook: tools\\audit_telegram_gateway.py" in report
    assert "runtime_mutation_shortcut: none" in report


def test_phase6h_doc_and_roadmap_are_current():
    doc = DOC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")

    required_doc_phrases = [
        "axiom-telegram-gateway",
        "read-only",
        "SQLite mode=ro",
        "pending confirmations",
        "recent external adapter decisions",
        "TelegramGateway.process_envelope",
        "TelegramGateway.confirm_intent",
    ]
    for phrase in required_doc_phrases:
        assert phrase in doc

    assert "Slices 6A through 6I are implemented" in roadmap
    assert "### 6H. Telegram Gateway Terminal Visibility" in roadmap
    assert "docs\\phase6_telegram_gateway_terminal_visibility.md" in roadmap
    assert "ui\\terminal\\modules\\59-telegram-gateway.ps1" in roadmap
