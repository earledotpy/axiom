import json
from pathlib import Path

import pytest

from axiom.core.operator_console import build_command_output, build_console_state


RECORD_DIRS = {
    "tasks",
    "delegations",
    "handoffs",
    "evaluations",
    "evidence",
    "decisions",
    "console",
    "autonomy",
    "archive",
}


def _record_root(root: Path) -> Path:
    record_root = root / "governance" / "80_records"
    for directory in RECORD_DIRS:
        (record_root / directory).mkdir(parents=True, exist_ok=True)
    return record_root


def _write_record(root: Path, directory: str, name: str, payload: dict) -> None:
    target = _record_root(root) / directory
    target.joinpath(name).write_text(json.dumps(payload), encoding="utf-8")


def test_operator_console_empty_records_default_to_disabled_autonomy(tmp_path):
    _record_root(tmp_path)

    state = build_console_state(root=tmp_path)
    output = build_command_output("/axiom:show-autonomy-status", root=tmp_path)

    assert state["schema"] == "axiom.operator_console_state.v0.1"
    assert state["authority_status"] == "advisory_only"
    assert state["failure_state"]["failed_closed"] is False
    assert output["authority_status"] == "advisory_only"
    assert output["data"]["autonomy_status"]["runtime_autonomy"] == "disabled"
    assert output["data"]["autonomy_status"]["active_grant_present"] is False


def test_operator_console_active_state_reads_task_cards(tmp_path):
    _write_record(
        tmp_path,
        "tasks",
        "TC-001.json",
        {
            "schema": "axiom.task_card.v0.1",
            "task_card_id": "TC-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
            "operator_goal": "Implement read-only console",
            "scope": "MND-2",
            "lifecycle_state": "proposal",
            "status": "active",
            "recommended_next_action": "audit",
        },
    )

    output = build_command_output("/axiom:show-active-state", root=tmp_path)

    assert output["view"] == "active_state"
    assert output["data"]["summary"]["active_count"] == 1
    item = output["data"]["active_state"][0]
    assert item["item_id"] == "TC-001"
    assert item["title"] == "Implement read-only console"
    assert item["authority_status"] == "advisory_only"


def test_operator_console_extracts_blocking_objections(tmp_path):
    _write_record(
        tmp_path,
        "evaluations",
        "EV-001.json",
        {
            "schema": "axiom.evaluation_report.v0.1",
            "evaluation_id": "EV-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
            "scope": "MND-2",
            "blocking_objections": [
                {
                    "title": "missing evidence",
                    "affected_layer": "Evaluation",
                    "recommended_next_action": "collect evidence",
                }
            ],
        },
    )

    output = build_command_output("/axiom:show-blockers", root=tmp_path)

    assert output["data"]["summary"]["blocking_count"] == 1
    blocker = output["data"]["blockers"][0]
    assert blocker["title"] == "missing evidence"
    assert blocker["affected_layer"] == "Evaluation"


def test_operator_console_decision_queue_uses_recommendations(tmp_path):
    _write_record(
        tmp_path,
        "handoffs",
        "HND-001.json",
        {
            "schema": "axiom.handoff.v0.1",
            "artifact_id": "HND-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
            "scope": "MND-2",
            "recommended_operator_decision": "approve",
        },
    )

    output = build_command_output("/axiom:show-decisions", root=tmp_path)

    assert output["view"] == "decision_queue"
    assert output["data"]["summary"]["ready_for_operator_decision_count"] == 1
    assert output["data"]["decision_queue"][0]["recommended_operator_decision"] == "approve"
    assert output["data"]["decision_queue"][0]["authority_status"] == "advisory_only"


def test_operator_console_evidence_view_reads_evidence_records(tmp_path):
    _write_record(
        tmp_path,
        "evidence",
        "EVI-001.json",
        {
            "schema": "axiom.evidence.v0.1",
            "evidence_id": "EVI-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "evidence_only",
            "scope": "MND-2",
            "evidence_quality": "strong",
            "commands_run": ["python tools/operator_console.py --state --json"],
        },
    )

    output = build_command_output("/axiom:show-evidence", root=tmp_path)

    assert output["data"]["summary"]["strong_count"] == 1
    assert output["data"]["evidence"][0]["commands_run"] == [
        "python tools/operator_console.py --state --json"
    ]
    assert output["data"]["evidence"][0]["authority_status"] == "advisory_only"


def test_operator_console_invalid_json_fails_closed(tmp_path):
    record_root = _record_root(tmp_path)
    (record_root / "handoffs" / "bad.json").write_text("{not json", encoding="utf-8")

    output = build_command_output("/axiom:show-blockers", root=tmp_path)

    assert output["failure_state"]["failed_closed"] is True
    assert output["failure_state"]["reasons"][0]["reason"] == "invalid_json"
    assert output["data"]["summary"]["blocking_count"] == 1


def test_operator_console_rejects_unknown_command(tmp_path):
    _record_root(tmp_path)

    with pytest.raises(ValueError, match="unknown read-only operator console command"):
        build_command_output("/axiom:approve", root=tmp_path)


def test_operator_console_valid_accepted_autonomy_is_visible_not_authority(tmp_path):
    _write_record(
        tmp_path,
        "autonomy",
        "A-001.json",
        {
            "schema": "axiom.autonomy_grant.v0.1",
            "grant_id": "A-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "operator_accepted",
            "grant_state": "operator_accepted",
            "operator_decision_id": "D-001",
            "technical_gate_result": "passed",
            "scope": "bounded-doc-review",
        },
    )

    output = build_command_output("/axiom:show-autonomy-status", root=tmp_path)

    status = output["data"]["autonomy_status"]
    assert status["runtime_autonomy"] == "disabled"
    assert status["active_grant_present"] is True
    assert status["scope"] == "bounded-doc-review"
    assert output["authority_status"] == "advisory_only"
