import json
import subprocess
import sys
from pathlib import Path

import pytest

from axiom.core.delegation import create_delegation_packet
from axiom.core.evidence import create_evidence
from axiom.core.governance_cycle import (
    build_cycle_state,
    create_roadmap,
    ingest_terminal_review,
    preview_guided_decision,
    record_guided_decision,
)
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


def test_roadmap_is_durable_advisory_handoff(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)

    result = create_roadmap(
        record_root=record_root,
        title="Level 2A governance roadmap",
        scope="Mandates 8-12",
        items=[
            "Mandate 8: Governance cycle coordinator",
            "Mandate 9: Typed relay intake",
        ],
    )

    assert result.roadmap["authority_status"] == "advisory_only"
    assert result.roadmap["artifact_type"] == "roadmap"
    assert result.roadmap["roadmap_items"][0]["status"] == "planned"
    assert result.roadmap["runtime_action_executed"] is False
    assert validate_governance(tmp_path)["passed"] is True


def test_cycle_state_derives_records_blockers_and_next_actions(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    scope = "Test cleanup planning"
    task = create_task_card(operator_goal="Clean up tests", scope=scope, record_root=record_root).task_card
    create_delegation_packet(operator_goal="Clean up tests", scope=scope, record_root=record_root)
    review = ingest_terminal_review(
        record_root=record_root,
        target_artifact=task["task_card_id"],
        scope=scope,
        review_text="Claude found one blocking evidence issue.",
        verdict="blocked",
        blocking_objections=["missing command evidence"],
        recommended_operator_decision="request_remediation",
    ).review
    create_evidence(scope=scope, commands_run=["python -m pytest tests/test_example.py -q"], record_root=record_root)

    state = build_cycle_state(root=tmp_path, record_root=record_root)
    cycle = next(item for item in state["cycles"] if item["scope"] == scope)

    assert state["authority_status"] == "advisory_only"
    assert cycle["status"] == "blocked"
    assert cycle["task_cards"][0]["record_id"] == task["task_card_id"]
    assert cycle["evaluations"][0]["record_id"] == review["evaluation_id"]
    assert cycle["blockers"][0]["title"] == "missing command evidence"
    assert "review_blockers" in cycle["next_valid_actions"]


def test_review_ingest_preserves_terminal_report_as_advisory_evaluation(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    task = create_task_card(operator_goal="Review target", scope="Review ingest", record_root=record_root).task_card

    result = ingest_terminal_review(
        record_root=record_root,
        target_artifact=task["task_card_id"],
        scope="Review ingest",
        review_text="Terminal-only report body",
        findings=["review filed"],
        required_tests=["python -m pytest tests/test_governance_cycle.py -q"],
        required_implementation_changes=["add review ingestion command"],
    )

    assert result.review["ingest_source"] == "terminal_report"
    assert result.review["terminal_report"] == "Terminal-only report body"
    assert result.review["authority_status"] == "advisory_only"
    assert result.review["runtime_action_executed"] is False
    assert validate_governance(tmp_path)["passed"] is True


def test_guided_decision_still_requires_exact_confirmation(tmp_path):
    record_root = _write_minimal_scaffold(tmp_path)
    task = create_task_card(operator_goal="Accept reviewed item", scope="Decision guide", record_root=record_root).task_card
    review = ingest_terminal_review(
        record_root=record_root,
        target_artifact=task["task_card_id"],
        scope="Decision guide",
        review_text="No blockers.",
        verdict="pass",
        recommended_operator_decision="approve",
    ).review

    preview = preview_guided_decision(
        root=tmp_path,
        decision="approve",
        target_id=task["task_card_id"],
        scope="Decision guide",
        source_refs=[review["evaluation_id"]],
        rationale="Jeremy accepts the reviewed item.",
    ).decision

    with pytest.raises(ValueError, match="confirmation token mismatch"):
        record_guided_decision(
            root=tmp_path,
            preview_id=preview["decision_id"],
            operator="Jeremy",
            confirmation="wrong",
        )

    accepted = record_guided_decision(
        root=tmp_path,
        preview_id=preview["decision_id"],
        operator="Jeremy",
        confirmation=preview["confirmation_token"],
    ).decision

    assert accepted["authority_status"] == "operator_accepted"
    assert validate_governance(tmp_path)["passed"] is True


def test_governance_cycle_cli_files_roadmap(tmp_path):
    _write_minimal_scaffold(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/governance_cycle.py",
            "--root",
            str(tmp_path),
            "file-roadmap",
            "--title",
            "CLI roadmap",
            "--scope",
            "CLI Mandates",
            "--item",
            "Mandate 8: Governance cycle coordinator",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["roadmap"]["artifact_type"] == "roadmap"
    assert payload["runtime_action_executed"] is False
