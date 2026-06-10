import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from axiom.core.evaluation import (
    build_blocker_summary,
    build_evaluation_report,
    create_evaluation_report,
    list_evaluation_reports,
    load_evaluation_report,
)
from axiom.core.operator_console import build_command_output


ROOT = Path(__file__).resolve().parents[1]


def _record_root(tmp_path: Path) -> Path:
    root = tmp_path / "governance" / "80_records"
    for directory in (
        "tasks",
        "delegations",
        "handoffs",
        "evaluations",
        "evidence",
        "decisions",
        "console",
        "autonomy",
        "archive",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def test_build_evaluation_report_is_advisory_audit_verify():
    report = build_evaluation_report(
        target_artifact="tools/evaluation.py",
        scope="MND-5",
        blocking_objections=["missing validation"],
        recommended_next_action="add tests",
    )
    payload = report.to_dict()

    assert payload["schema"] == "axiom.evaluation_report.v0.1"
    assert payload["authority_status"] == "advisory_only"
    assert payload["actor_role"] == "AUD"
    assert payload["process"] == "audit"
    assert payload["function"] == "verify"
    assert payload["blocking_objections"][0]["title"] == "missing validation"
    assert payload["blocking_objections"][0]["recommended_next_action"] == "add tests"


def test_created_evaluation_report_validates_against_schema(tmp_path):
    record_root = _record_root(tmp_path)
    result = create_evaluation_report(
        target_artifact="governance/50_evaluation/AXIOM_GOVERNANCE_EVALUATION.md",
        scope="MND-5",
        record_root=record_root,
        verdict="pass_with_concerns",
        evidence_quality="partial",
        checks_performed=["schema validation"],
        findings=["evaluation report created"],
    )

    path = Path(result.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "governance" / "80_records" / "schemas" / "evaluation_report.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(payload)

    assert path.exists()
    assert payload["evaluation_id"].startswith("EVL-")
    assert payload["authority_status"] == "advisory_only"
    assert payload["evidence_quality"] == "partial"


def test_list_load_and_blocker_summary(tmp_path):
    record_root = _record_root(tmp_path)
    created = create_evaluation_report(
        target_artifact="tools/evaluation.py",
        scope="MND-5",
        record_root=record_root,
        verdict="blocked",
        blocking_objections=["operator decision missing"],
        affected_layer="Governance",
    )

    reports = list_evaluation_reports(record_root=record_root)
    loaded = load_evaluation_report(created.report["evaluation_id"], record_root=record_root)
    summary = build_blocker_summary(record_root=record_root)

    assert len(reports) == 1
    assert reports[0]["blocking_count"] == 1
    assert loaded["scope"] == "MND-5"
    assert summary["schema"] == "axiom.blocker_summary.v0.1"
    assert summary["blocking_count"] == 1
    assert summary["blockers"][0]["affected_layer"] == "Governance"
    assert summary["blockers"][0]["authority_status"] == "advisory_only"


def test_evaluation_cli_create_list_and_blockers(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluation.py",
            "--root",
            str(tmp_path),
            "create",
            "--target-artifact",
            "tools/evaluation.py",
            "--scope",
            "MND-5",
            "--verdict",
            "blocked",
            "--blocking",
            "missing evidence",
            "--affected-layer",
            "Evaluation",
            "--recommended-next-action",
            "collect evidence",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["created"] is True
    assert payload["runtime_action_executed"] is False
    assert payload["ledger_written"] is False
    assert payload["report"]["process"] == "audit"
    assert payload["report"]["function"] == "verify"

    list_result = subprocess.run(
        [sys.executable, "tools/evaluation.py", "--root", str(tmp_path), "list", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    blockers_result = subprocess.run(
        [sys.executable, "tools/evaluation.py", "--root", str(tmp_path), "blockers", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert list_result.returncode == 0
    assert blockers_result.returncode == 0
    listed = json.loads(list_result.stdout)
    blockers = json.loads(blockers_result.stdout)
    assert len(listed["evaluations"]) == 1
    assert blockers["blocking_count"] == 1
    assert blockers["blockers"][0]["recommended_next_action"] == "collect evidence"


def test_operator_console_reads_evaluation_blockers_and_decisions(tmp_path):
    record_root = _record_root(tmp_path)
    create_evaluation_report(
        target_artifact="tools/evaluation.py",
        scope="MND-5",
        record_root=record_root,
        verdict="blocked",
        blocking_objections=["authority boundary needs review"],
        recommended_operator_decision="request_review",
        recommended_next_action="review blocker",
    )

    blockers = build_command_output("/axiom:show-blockers", root=tmp_path)
    decisions = build_command_output("/axiom:show-decisions", root=tmp_path)

    assert blockers["data"]["summary"]["blocking_count"] == 1
    assert blockers["data"]["blockers"][0]["scope"] == "MND-5"
    assert decisions["data"]["summary"]["blocked_pending_review_count"] == 1
    assert decisions["data"]["decision_queue"][0]["recommended_operator_decision"] == "request_review"
