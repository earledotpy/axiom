import json
from pathlib import Path

from tools.validate_governance import (
    RECORD_SCHEMA_BY_DIR,
    REQUIRED_GOVERNANCE_FILES,
    REQUIRED_RECORD_DIRS,
    REQUIRED_ROOT_FILES,
    SCHEMA_FILE_BY_DIR,
    validate_governance,
)


MANDATE1_STATUS = "Status: Operator-accepted Mandate 1 scaffold"


def _write_minimal_scaffold(root: Path) -> None:
    for relative in REQUIRED_GOVERNANCE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "# Test Governance File",
                    "",
                    MANDATE1_STATUS,
                    "This file is part of the redesigned scaffold.",
                ]
            ),
            encoding="utf-8",
        )

    for relative, terms in REQUIRED_ROOT_FILES.items():
        path = root / relative
        path.write_text(
            "\n".join(
                [
                    f"# {terms[0]}",
                    "",
                    "## Required Reading",
                    "",
                    "- `governance/README_REDESIGN_DRAFT.md`",
                    "- `governance/00_doctrine/AXIOM_DOCTRINE.md`",
                    "",
                    f"Role marker: {terms[1]}",
                ]
            ),
            encoding="utf-8",
        )

    cursor_rule = root / ".cursor" / "rules" / "axiom-governance.mdc"
    cursor_rule.parent.mkdir(parents=True, exist_ok=True)
    cursor_rule.write_text(
        "\n".join(
            [
                "---",
                "alwaysApply: true",
                "---",
                "# AXIOM Cursor Entrypoint",
                "Cursor",
                "Process: `synthesize`",
                "Function: `summarize`",
            ]
        ),
        encoding="utf-8",
    )

    for directory in REQUIRED_RECORD_DIRS:
        (root / "governance" / "80_records" / directory).mkdir(parents=True, exist_ok=True)

    schema_root = root / "governance" / "80_records" / "schemas"
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


def _write_record(root: Path, directory: str, name: str, payload: dict) -> None:
    target = root / "governance" / "80_records" / directory
    target.mkdir(parents=True, exist_ok=True)
    target.joinpath(name).write_text(json.dumps(payload), encoding="utf-8")


def test_validate_governance_passes_minimal_mandate1_scaffold(tmp_path):
    _write_minimal_scaffold(tmp_path)

    result = validate_governance(tmp_path)

    assert result["passed"] is True
    assert result["tool_version"] == "governance_validation.v3"
    assert result["summary"] == {"error": 0, "warning": 0}


def test_validate_governance_fails_missing_root_entrypoint(tmp_path):
    _write_minimal_scaffold(tmp_path)
    (tmp_path / "AGENTS.md").unlink()

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "required_root_file_missing" in codes


def test_validate_governance_fails_missing_record_subdir(tmp_path):
    _write_minimal_scaffold(tmp_path)
    (tmp_path / "governance" / "80_records" / "handoffs").rmdir()

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "record_subdir_missing" in codes


def test_validate_governance_fails_missing_schema_file(tmp_path):
    _write_minimal_scaffold(tmp_path)
    (tmp_path / "governance" / "80_records" / "schemas" / "handoff.schema.json").unlink()

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "record_schema_file_missing" in codes


def test_validate_governance_fails_legacy_required_reading(tmp_path):
    _write_minimal_scaffold(tmp_path)
    (tmp_path / "CLAUDE.md").write_text(
        "\n".join(
            [
                "# Claude Code",
                "Governance Auditor",
                "## Required Reading",
                "- `governance/01_live_spine/AXIOM_Active_Bindings.md`",
            ]
        ),
        encoding="utf-8",
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "legacy_required_reading_path" in codes


def test_validate_governance_fails_invalid_record_json(tmp_path):
    _write_minimal_scaffold(tmp_path)
    target = tmp_path / "governance" / "80_records" / "handoffs"
    target.joinpath("bad.json").write_text("{not json", encoding="utf-8")

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "record_json_parse_error" in codes


def test_validate_governance_accepts_valid_task_card_record(tmp_path):
    _write_minimal_scaffold(tmp_path)
    _write_record(
        tmp_path,
        "tasks",
        "TC-001.json",
        {
            "schema": "axiom.task_card.v0.1",
            "task_card_id": "TC-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
        },
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is True


def test_validate_governance_applies_record_json_schema(tmp_path):
    _write_minimal_scaffold(tmp_path)
    schema_path = tmp_path / "governance" / "80_records" / "schemas" / "task_card.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "axiom.task_card.v0.1",
                "type": "object",
                "properties": {
                    "risk_class": {
                        "enum": ["low"]
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    _write_record(
        tmp_path,
        "tasks",
        "TC-001.json",
        {
            "schema": "axiom.task_card.v0.1",
            "task_card_id": "TC-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
            "risk_class": "authority_sensitive",
        },
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "record_schema_validation_failed" in codes


def test_validate_governance_rejects_operator_accepted_handoff(tmp_path):
    _write_minimal_scaffold(tmp_path)
    _write_record(
        tmp_path,
        "handoffs",
        "HND-001.json",
        {
            "schema": "axiom.handoff.v0.1",
            "artifact_id": "HND-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "operator_accepted",
        },
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "record_authority_status_not_advisory" in codes
    assert "operator_accepted_wrong_record_dir" in codes


def test_validate_governance_accepts_operator_decision_record(tmp_path):
    _write_minimal_scaffold(tmp_path)
    _write_record(
        tmp_path,
        "tasks",
        "TC-001.json",
        {
            "schema": "axiom.task_card.v0.1",
            "task_card_id": "TC-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "advisory_only",
        },
    )
    _write_record(
        tmp_path,
        "decisions",
        "D-001.json",
        {
            "schema": "axiom.operator_decision.v0.1",
            "decision_id": "D-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "operator_accepted",
            "decision": "approve",
            "source_refs": ["TC-001"],
        },
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is True


def test_validate_governance_rejects_accepted_autonomy_without_two_keys(tmp_path):
    _write_minimal_scaffold(tmp_path)
    _write_record(
        tmp_path,
        "autonomy",
        "A-001.json",
        {
            "schema": "axiom.autonomy_grant.v0.1",
            "grant_id": "A-001",
            "created_utc": "2026-06-08T12:00:00Z",
            "authority_status": "operator_accepted",
            "grant_state": "draft",
        },
    )

    result = validate_governance(tmp_path)

    assert result["passed"] is False
    codes = {finding["code"] for finding in result["findings"]}
    assert "accepted_autonomy_missing_gate_field" in codes
    assert "accepted_autonomy_state_invalid" in codes
