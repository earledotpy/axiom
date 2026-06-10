import json
import subprocess
import sys
from pathlib import Path

import pytest

from axiom.core.autonomy_grant import accept_autonomy_grant, draft_autonomy_grant
from axiom.core.binding import apply_binding
from axiom.core.decision import preview_decision, record_decision
from axiom.core.evidence import create_evidence
from axiom.core.governance_command import create_command_manifest, parse_governance_command, record_command_intent
from axiom.core.handoff import create_handoff
from axiom.core.operator_console import build_command_output
from axiom.core.task_card import create_task_card
from tools.validate_governance import (
    RECORD_SCHEMA_BY_DIR,
    REQUIRED_CURSOR_RULES,
    REQUIRED_GOVERNANCE_FILES,
    REQUIRED_RECORD_DIRS,
    REQUIRED_ROOT_FILES,
    SCHEMA_FILE_BY_DIR,
    validate_governance,
)

ROOT = Path(__file__).resolve().parents[1]
MANDATE1_STATUS = "Status: Operator-accepted Mandate 1 scaffold"


def _write_minimal_scaffold(root: Path) -> Path:
    for relative in REQUIRED_GOVERNANCE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Test\n\n{MANDATE1_STATUS}\n", encoding="utf-8")

    for relative, terms in REQUIRED_ROOT_FILES.items():
        path = root / relative
        path.write_text(f"# {terms[0]}\n\n{terms[1]}\n", encoding="utf-8")

    for relative, terms in REQUIRED_CURSOR_RULES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(terms), encoding="utf-8")

    record_root = root / "governance" / "80_records"
    for directory in REQUIRED_RECORD_DIRS:
        (record_root / directory).mkdir(parents=True, exist_ok=True)

    schema_root = record_root / "schemas"
    schema_root.mkdir(parents=True, exist_ok=True)
    for directory, filename in SCHEMA_FILE_BY_DIR.items():
        schema_root.joinpath(filename).write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": RECORD_SCHEMA_BY_DIR[directory],
                    "type": "object",
                }
            ),
            encoding="utf-8",
        )
    return record_root


def test_decision_confirmation_and_binding_flow_validates(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    task = create_task_card(operator_goal="Govern operating records", scope="MND-6", record_root=record_root).task_card
    evidence = create_evidence(scope="MND-6", commands_run=["pytest"], record_root=record_root).evidence
    create_handoff(
        title="Ready for decision",
        scope="MND-6",
        source_refs=[task["task_card_id"], evidence["evidence_id"]],
        recommended_operator_decision="approve",
        record_root=record_root,
    )

    preview = preview_decision(
        decision="approve",
        target_id=task["task_card_id"],
        scope="MND-6",
        source_refs=[evidence["evidence_id"]],
        record_root=record_root,
    ).decision

    with pytest.raises(ValueError, match="confirmation token mismatch"):
        record_decision(
            preview_id=preview["decision_id"],
            operator="Jeremy",
            confirmation="wrong",
            record_root=record_root,
        )

    accepted = record_decision(
        preview_id=preview["decision_id"],
        operator="Jeremy",
        confirmation=preview["confirmation_token"],
        record_root=record_root,
    ).decision
    binding = apply_binding(
        operator_decision_id=accepted["decision_id"],
        binding_type="active_governance",
        target="governance/80_records",
        scope="MND-6",
        record_root=record_root,
    ).binding

    result = validate_governance(tmp_path)

    assert accepted["authority_status"] == "operator_accepted"
    assert binding["authority_status"] == "binding"
    assert result["passed"] is True


def test_default_handoff_names_cursor_as_synthesis_actor(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    handoff = create_handoff(
        title="Cursor synthesis",
        scope="MND-CURSOR",
        summary="Cursor owns synthesis and summarization.",
        record_root=record_root,
    ).handoff

    assert handoff["actor_role"] == "CURSOR"
    assert handoff["process"] == "synthesize"
    assert handoff["function"] == "summarize"
    assert validate_governance(tmp_path)["passed"] is True


def test_binding_requires_accepted_approve_decision(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    task = create_task_card(operator_goal="Reject binding", scope="MND-6", record_root=record_root).task_card
    preview = preview_decision(
        decision="defer",
        target_id=task["task_card_id"],
        scope="MND-6",
        record_root=record_root,
    ).decision
    accepted = record_decision(
        preview_id=preview["decision_id"],
        operator="Jeremy",
        confirmation=preview["confirmation_token"],
        record_root=record_root,
    ).decision

    with pytest.raises(ValueError, match="approve decision"):
        apply_binding(
            operator_decision_id=accepted["decision_id"],
            binding_type="active_governance",
            target="governance/80_records",
            scope="MND-6",
            record_root=record_root,
        )


def test_governance_command_manifest_and_intent_records(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    manifest = create_command_manifest(
        command="/axiom:show-active-state",
        effect_class="read_only",
        record_root=record_root,
    ).intent

    parsed = parse_governance_command("/axiom:show-active-state", record_root=record_root)
    recorded = record_command_intent("/axiom:show-active-state", record_root=record_root)
    rejected = record_command_intent("/approve", record_root=record_root)

    assert manifest["runtime_action_allowed"] is False
    assert parsed.accepted is True
    assert recorded.recorded is True
    assert recorded.intent["ledger_written"] is False
    assert rejected.recorded is False
    assert rejected.intent["rejection_reason"] == "native_cli_command_not_axiom_authority"
    assert validate_governance(tmp_path)["passed"] is True


def test_autonomy_grant_record_is_visible_but_runtime_disabled(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    task = create_task_card(operator_goal="Autonomy record", scope="A0 visibility", record_root=record_root).task_card
    preview = preview_decision(
        decision="approve",
        target_id=task["task_card_id"],
        scope="A0 visibility",
        record_root=record_root,
    ).decision
    accepted = record_decision(
        preview_id=preview["decision_id"],
        operator="Jeremy",
        confirmation=preview["confirmation_token"],
        record_root=record_root,
    ).decision
    grant = draft_autonomy_grant(scope="A0 visibility", autonomy_level="A1", record_root=record_root).grant
    accepted_grant = accept_autonomy_grant(
        grant_id=grant["grant_id"],
        operator_decision_id=accepted["decision_id"],
        technical_gate_result="passed",
        record_root=record_root,
    ).grant

    output = build_command_output("/axiom:show-autonomy-status", root=tmp_path)

    assert accepted_grant["authority_status"] == "operator_accepted"
    assert output["data"]["autonomy_status"]["active_grant_present"] is True
    assert output["data"]["autonomy_status"]["runtime_autonomy"] == "disabled"
    assert validate_governance(tmp_path)["passed"] is True


def test_decision_cli_preview_and_record(tmp_path):
    _write_minimal_scaffold(tmp_path)
    task_result = subprocess.run(
        [
            sys.executable,
            "tools/task_card.py",
            "--root",
            str(tmp_path),
            "create",
            "--goal",
            "CLI decision",
            "--scope",
            "MND-6",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    task = json.loads(task_result.stdout)["task_card"]
    preview_result = subprocess.run(
        [
            sys.executable,
            "tools/decision.py",
            "--root",
            str(tmp_path),
            "preview",
            "--decision",
            "approve",
            "--target-id",
            task["task_card_id"],
            "--scope",
            "MND-6",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    preview = json.loads(preview_result.stdout)["decision"]
    record_result = subprocess.run(
        [
            sys.executable,
            "tools/decision.py",
            "--root",
            str(tmp_path),
            "record",
            "--preview-id",
            preview["decision_id"],
            "--operator",
            "Jeremy",
            "--confirm",
            preview["confirmation_token"],
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert task_result.returncode == 0
    assert preview_result.returncode == 0
    assert record_result.returncode == 0
    assert json.loads(record_result.stdout)["decision"]["authority_status"] == "operator_accepted"
