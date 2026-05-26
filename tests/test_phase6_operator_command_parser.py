from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axiom.core.operator_command_parser import OperatorCommandParser


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6_operator_command_parser.md"
ROADMAP = ROOT / "docs" / "phase6_roadmap.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"


def test_operator_command_parser_accepts_status_text_and_alias():
    parser = OperatorCommandParser()

    for raw in ("status", "/status"):
        result = parser.parse(raw)

        assert result.accepted is True
        assert result.command_name == "status"
        assert result.manifest_id == "operator.status.v1"
        assert result.rejection_reason is None
        assert result.details["runtime_action_executed"] is False
        assert result.details["ledger_written"] is False


def test_operator_command_parser_accepts_structured_status_payload():
    result = OperatorCommandParser().parse({"command": "status", "payload": {}})

    assert result.accepted is True
    assert result.command_name == "status"
    assert result.payload == {}


def test_operator_command_parser_rejects_unknown_and_unsafe_commands():
    parser = OperatorCommandParser()

    for raw in ("resume", "enable_autonomous", "/resume"):
        result = parser.parse(raw)

        assert result.accepted is False
        assert result.command_name is None
        assert result.rejection_reason == "unknown_operator_command"


def test_operator_command_parser_rejects_payloads_for_status():
    parser = OperatorCommandParser()

    text_result = parser.parse("status now")
    object_result = parser.parse({"command": "status", "payload": {"verbose": True}})

    assert text_result.accepted is False
    assert text_result.rejection_reason == "command_payload_not_allowed"
    assert object_result.accepted is False
    assert object_result.rejection_reason == "command_payload_not_allowed"


def test_operator_command_parser_rejects_malformed_structured_input():
    parser = OperatorCommandParser()

    missing = parser.parse({"payload": {}})
    bad_payload = parser.parse({"command": "status", "payload": []})

    assert missing.accepted is False
    assert missing.rejection_reason == "command_field_missing_or_invalid"
    assert bad_payload.accepted is False
    assert bad_payload.rejection_reason == "command_payload_must_be_object"


def test_parse_operator_command_cli_reports_no_execution_or_ledger_write():
    result = subprocess.run(
        [
            sys.executable,
            "tools/parse_operator_command.py",
            "status",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["accepted"] is True
    assert payload["details"]["runtime_action_executed"] is False
    assert payload["details"]["ledger_written"] is False


def test_parse_operator_command_cli_fails_closed_for_unknown_command():
    result = subprocess.run(
        [
            sys.executable,
            "tools/parse_operator_command.py",
            "resume",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["accepted"] is False
    assert payload["rejection_reason"] == "unknown_operator_command"


def test_phase6_operator_command_parser_docs_and_index_are_current():
    text = DOC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs_module = DOCS_MODULE.read_text(encoding="utf-8")

    required = [
        "The parser does not execute commands",
        "does not write the command ledger",
        "unknown_operator_command",
        "command_payload_not_allowed",
        "python tools\\parse_operator_command.py status --json",
    ]

    for phrase in required:
        assert phrase in text

    assert "docs\\phase6_operator_command_parser.md" in roadmap
    assert "phase6-command-parser" in docs_module
    assert "operator-command-parser-tool" in docs_module
