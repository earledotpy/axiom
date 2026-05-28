from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axiom.core.operator_command_ledger import (
    audit_operator_command_ledger,
    record_operator_command_intent,
)
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase6.md"
ROADMAP = ROOT / "docs" / "phase6.md"
DOCS_MODULE = ROOT / "ui" / "terminal" / "modules" / "52-docs.ps1"
TERMINAL_MODULE = ROOT / "ui" / "terminal" / "modules" / "58-operator-commands.ps1"
REGISTRY = ROOT / "ui" / "terminal" / "registry" / "axiom-terminal-command-registry.json"


def register_manifests() -> None:
    result = subprocess.run(
        [sys.executable, "tools/register_manifests.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_record_operator_command_intent_writes_pending_task_and_ledger_row():
    register_manifests()
    session_id = create_session(operator_id="test_operator")

    record = record_operator_command_intent("status", operator_id="test_operator")

    assert record.recorded is True
    assert record.ledger_written is True
    assert record.runtime_action_executed is False
    assert record.command_name == "status"
    assert record.manifest_id == "operator.status.v1"
    assert record.authorization_status == "pending"
    assert record.command_status == "pending"

    with get_connection() as conn:
        task = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (record.task_id,),
        ).fetchone()
        command = conn.execute(
            "SELECT * FROM operator_commands WHERE command_id = ?",
            (record.command_id,),
        ).fetchone()

    assert task is not None
    assert task["session_id"] == session_id
    assert task["task_class"] == "operator_control"
    assert task["task_type"] == "operator_command_intent"
    assert task["status"] == "pending"
    assert task["manifest_id"] == "operator.status.v1"
    task_input = json.loads(task["input_json"])
    assert task_input["runtime_action_executed"] is False
    assert task_input["ledger_written"] is True

    assert command is not None
    assert command["task_id"] == record.task_id
    assert command["command_name"] == "status"
    assert command["authorization_status"] == "pending"
    assert command["command_status"] == "pending"
    assert json.loads(command["command_payload_json"]) == {}


def test_record_operator_command_intent_rejects_without_write_for_unknown_command():
    register_manifests()
    create_session(operator_id="test_operator")

    record = record_operator_command_intent("resume", operator_id="test_operator")

    assert record.recorded is False
    assert record.ledger_written is False
    assert record.runtime_action_executed is False
    assert record.rejection_reason == "unknown_operator_command"

    with get_connection() as conn:
        command_count = conn.execute("SELECT COUNT(*) FROM operator_commands").fetchone()[0]
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    assert command_count == 0
    assert task_count == 0


def test_record_operator_command_intent_requires_active_session():
    register_manifests()

    record = record_operator_command_intent("status", operator_id="test_operator")

    assert record.recorded is False
    assert record.ledger_written is False
    assert record.rejection_reason == "no_active_session"


def test_audit_operator_command_ledger_passes_for_valid_pending_record():
    register_manifests()
    create_session(operator_id="test_operator")
    record_operator_command_intent("status", operator_id="test_operator")

    result = audit_operator_command_ledger()

    assert result.passed is True
    assert result.checked_command_count == 1
    assert result.violation_count == 0


def test_audit_operator_command_ledger_flags_malformed_rows():
    register_manifests()
    create_session(operator_id="test_operator")
    record = record_operator_command_intent("status", operator_id="test_operator")

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET task_class = 'system_maintenance'
            WHERE task_id = ?
            """,
            (record.task_id,),
        )
        conn.execute(
            """
            UPDATE operator_commands
            SET command_status = 'completed',
                completed_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE command_id = ?
            """,
            (record.command_id,),
        )

    result = audit_operator_command_ledger()
    reasons = {violation.reason for violation in result.violations}

    assert result.passed is False
    assert "operator_command_task_identity_mismatch" in reasons
    assert "operator_command_status_not_phase6d_pending" in reasons


def test_record_operator_command_intent_cli_writes_without_execution():
    register_manifests()
    create_session(operator_id="test_operator")

    result = subprocess.run(
        [
            sys.executable,
            "tools/record_operator_command_intent.py",
            "status",
            "--operator-id",
            "test_operator",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recorded"] is True
    assert payload["ledger_written"] is True
    assert payload["runtime_action_executed"] is False
    assert payload["authorization_status"] == "pending"
    assert payload["command_status"] == "pending"


def test_audit_operator_command_ledger_cli_reports_read_only_pass():
    register_manifests()
    create_session(operator_id="test_operator")
    record_operator_command_intent("status", operator_id="test_operator")

    result = subprocess.run(
        [sys.executable, "tools/audit_operator_command_ledger.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["checked_command_count"] == 1


def test_phase6_operator_command_ledger_docs_terminal_and_index_are_current():
    text = DOC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    docs_module = DOCS_MODULE.read_text(encoding="utf-8")
    terminal_module = TERMINAL_MODULE.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    required_doc_phrases = [
        "authorization_status = pending",
        "command_status = pending",
        "runtime_action_executed = false",
        "python tools\\audit_operator_command_ledger.py",
        "axiom-operator-commands",
    ]

    for phrase in required_doc_phrases:
        assert phrase in text

    assert "docs\\phase6.md" in roadmap
    assert "phase6" in docs_module
    assert "operator-command-ledger-tool" in docs_module
    assert "operator-command-ledger-audit" in docs_module
    assert "mode=ro" in terminal_module
    assert "record_operator_command_intent.py" in terminal_module
    assert "axiom-operator-commands" in registry


