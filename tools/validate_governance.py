from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, exceptions

ROOT = Path(__file__).resolve().parents[1]
TOOL_VERSION = "governance_validation.v3"
MANDATE1_STATUS = "Status: Operator-accepted Mandate 1 scaffold"

REQUIRED_ROOT_FILES = {
    "AGENTS.md": ("Codex", "Implementation Specialist"),
    "CLAUDE.md": ("Claude Code", "Governance Auditor"),
    ".antigravity.md": ("Antigravity", "Chief Architect"),
}

REQUIRED_CURSOR_RULES = {
    ".cursor/rules/axiom-governance.mdc": ("Cursor", "synthesize", "summarize"),
}

REQUIRED_GOVERNANCE_FILES = (
    "governance/README_REDESIGN_DRAFT.md",
    "governance/00_doctrine/AXIOM_DOCTRINE.md",
    "governance/10_workflow/AXIOM_GOVERNANCE_WORKFLOW.md",
    "governance/10_workflow/AXIOM_GOVERNANCE_CYCLE_SIMPLIFICATION.md",
    "governance/20_transport/AXIOM_GOVERNANCE_TRANSPORT.md",
    "governance/30_delegation/AXIOM_GOVERNANCE_DELEGATION.md",
    "governance/40_execution/AXIOM_GOVERNANCE_EXECUTION.md",
    "governance/50_evaluation/AXIOM_GOVERNANCE_EVALUATION.md",
    "governance/60_operator_console/AXIOM_OPERATOR_CONSOLE.md",
    "governance/60_operator_console/AXIOM_OPERATOR_CONSOLE_SCHEMA.md",
    "governance/60_operator_console/AXIOM_OPERATOR_CONSOLE_COMMANDS.md",
    "governance/70_autonomy_gate/AXIOM_AUTONOMY_GATE.md",
    "governance/80_records/README.md",
)

REQUIRED_RECORD_DIRS = {
    "tasks",
    "delegations",
    "handoffs",
    "evaluations",
    "evidence",
    "decisions",
    "bindings",
    "console",
    "autonomy",
    "command_manifests",
    "command_intents",
    "archive",
}

RECORD_SCHEMA_BY_DIR = {
    "tasks": "axiom.task_card.v0.1",
    "delegations": "axiom.delegation_packet.v0.1",
    "handoffs": "axiom.handoff.v0.1",
    "evaluations": "axiom.evaluation_report.v0.1",
    "evidence": "axiom.evidence.v0.1",
    "decisions": "axiom.operator_decision.v0.1",
    "bindings": "axiom.binding.v0.1",
    "console": "axiom.operator_console_state.v0.1",
    "autonomy": "axiom.autonomy_grant.v0.1",
    "command_manifests": "axiom.command_manifest.v0.1",
    "command_intents": "axiom.command_intent.v0.1",
    "archive": "axiom.archive_index.v0.1",
}

SCHEMA_FILE_BY_DIR = {
    "tasks": "task_card.schema.json",
    "delegations": "delegation_packet.schema.json",
    "handoffs": "handoff.schema.json",
    "evaluations": "evaluation_report.schema.json",
    "evidence": "evidence.schema.json",
    "decisions": "operator_decision.schema.json",
    "bindings": "binding.schema.json",
    "console": "operator_console_state.schema.json",
    "autonomy": "autonomy_grant.schema.json",
    "command_manifests": "command_manifest.schema.json",
    "command_intents": "command_intent.schema.json",
    "archive": "archive_index.schema.json",
}

ID_FIELDS_BY_DIR = {
    "tasks": "task_card_id",
    "delegations": "delegation_id",
    "handoffs": "artifact_id",
    "evaluations": "evaluation_id",
    "evidence": "evidence_id",
    "decisions": "decision_id",
    "bindings": "binding_id",
    "console": "console_state_id",
    "autonomy": "grant_id",
    "command_manifests": "manifest_id",
    "command_intents": "intent_id",
    "archive": "archive_id",
}

ALLOWED_AUTHORITY_STATUSES = {
    "advisory_only",
    "operator_accepted",
    "binding",
    "evidence_only",
    "historical_evidence",
}

ADVISORY_ONLY_DIRS = {"tasks", "delegations", "handoffs", "evaluations", "console", "command_intents"}

STALE_REQUIRED_READING_RE = re.compile(
    r"^\s*-\s+`?governance/(?:01_live_spine|02_cli_surfaces|03_advisory_council|05_handoffs)",
    re.IGNORECASE | re.MULTILINE,
)

LLM_ORCHESTRATOR_GRANT_RE = re.compile(
    r"\b(Codex|Cursor|Claude Code|Antigravity|ChatGPT|Claude|Gemini)\b.{0,80}"
    r"\b(is|serves as|acts as)\b.{0,80}\bauthority-bearing AXIOM Orchestrator\b",
    re.IGNORECASE | re.DOTALL,
)

RETIRED_ACTIVE_STATEMENTS = {
    "legacy_live_spine_active": re.compile(
        r"Current active governance remains under:\s*```text\s*governance/01_live_spine/",
        re.IGNORECASE,
    ),
    "legacy_handoff_primary_location": re.compile(
        r"Primary location:\s*```text\s*governance/05_handoffs/",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _json_files(record_root: Path) -> list[Path]:
    if not record_root.exists():
        return []
    files: list[Path] = []
    for directory in sorted(REQUIRED_RECORD_DIRS):
        candidate = record_root / directory
        if candidate.exists():
            files.extend(sorted(path for path in candidate.rglob("*.json") if path.is_file()))
    return files


def _record_dir(path: Path, record_root: Path) -> str | None:
    try:
        relative = path.relative_to(record_root)
    except ValueError:
        return None
    return relative.parts[0] if relative.parts else None


def validate_scaffold_files(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    for relative in REQUIRED_GOVERNANCE_FILES:
        path = root / relative
        if not path.exists():
            findings.append(
                Finding("error", "required_governance_file_missing", relative, "Required Mandate 1 governance file is missing.")
            )
            continue
        text = _read_text(path)
        if MANDATE1_STATUS not in text:
            findings.append(
                Finding(
                    "error",
                    "mandate1_status_missing",
                    relative,
                    f"Governance file must include '{MANDATE1_STATUS}'.",
                )
            )
        for code, pattern in RETIRED_ACTIVE_STATEMENTS.items():
            if pattern.search(text):
                findings.append(
                    Finding(
                        "error",
                        code,
                        relative,
                        "Governance file still describes a retired legacy path as active.",
                    )
                )

    for relative, expected_terms in REQUIRED_ROOT_FILES.items():
        path = root / relative
        if not path.exists():
            findings.append(
                Finding("error", "required_root_file_missing", relative, "Required CLI agent root entrypoint is missing.")
            )
            continue
        text = _read_text(path)
        for term in expected_terms:
            if term not in text:
                findings.append(
                    Finding(
                        "error",
                        "root_role_marker_missing",
                        relative,
                        f"Root entrypoint must include role marker: {term}.",
                    )
                )
        if STALE_REQUIRED_READING_RE.search(text):
            findings.append(
                Finding(
                    "error",
                    "legacy_required_reading_path",
                    relative,
                    "Root entrypoint required reading still points at retired legacy governance paths.",
                )
            )
        grant = LLM_ORCHESTRATOR_GRANT_RE.search(text)
        if grant:
            findings.append(
                Finding(
                    "error",
                    "llm_authority_orchestrator_grant",
                    relative,
                    "Root entrypoint appears to grant authority-bearing Orchestrator status to an LLM role.",
                )
            )

    for relative, expected_terms in REQUIRED_CURSOR_RULES.items():
        path = root / relative
        if not path.exists():
            findings.append(
                Finding("error", "required_cursor_rule_missing", relative, "Required Cursor project rule is missing.")
            )
            continue
        text = _read_text(path)
        for term in expected_terms:
            if term not in text:
                findings.append(
                    Finding(
                        "error",
                        "cursor_rule_marker_missing",
                        relative,
                        f"Cursor rule must include marker: {term}.",
                    )
                )
        grant = LLM_ORCHESTRATOR_GRANT_RE.search(text)
        if grant:
            findings.append(
                Finding(
                    "error",
                    "llm_authority_orchestrator_grant",
                    relative,
                    "Cursor rule appears to grant authority-bearing Orchestrator status to an LLM role.",
                )
            )

    return findings


def validate_record_root(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    record_root = root / "governance" / "80_records"

    if not record_root.exists():
        return [
            Finding(
                "error",
                "record_root_missing",
                _relative(record_root, root),
                "governance/80_records is the required JSON record root.",
            )
        ]

    for directory in sorted(REQUIRED_RECORD_DIRS):
        path = record_root / directory
        if not path.is_dir():
            findings.append(
                Finding(
                    "error",
                    "record_subdir_missing",
                    _relative(path, root),
                    "Required JSON record subdirectory is missing.",
                )
            )

    schema_root = record_root / "schemas"
    if not schema_root.is_dir():
        findings.append(
            Finding(
                "error",
                "schema_root_missing",
                _relative(schema_root, root),
                "Mandate 3 schema root is missing.",
            )
        )

    for filename in sorted(SCHEMA_FILE_BY_DIR.values()):
        path = schema_root / filename
        if not path.is_file():
            findings.append(
                Finding(
                    "error",
                    "record_schema_file_missing",
                    _relative(path, root),
                    "Required governance record JSON Schema file is missing.",
                )
            )

    return findings


def _load_record_schemas(root: Path, record_root: Path) -> tuple[dict[str, Draft202012Validator], list[Finding]]:
    schema_root = record_root / "schemas"
    validators: dict[str, Draft202012Validator] = {}
    findings: list[Finding] = []

    for directory, filename in sorted(SCHEMA_FILE_BY_DIR.items()):
        path = schema_root / filename
        relpath = _relative(path, root)
        if not path.exists():
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "record_schema_json_parse_error",
                    relpath,
                    f"Invalid schema JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}.",
                )
            )
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except exceptions.SchemaError as exc:
            findings.append(
                Finding(
                    "error",
                    "record_schema_invalid",
                    relpath,
                    f"JSON Schema is invalid: {exc.message}.",
                )
            )
            continue

        schema_id = schema.get("$id")
        expected_id = RECORD_SCHEMA_BY_DIR[directory]
        if schema_id != expected_id:
            findings.append(
                Finding(
                    "error",
                    "record_schema_id_mismatch",
                    relpath,
                    f"Schema $id must be {expected_id}.",
                )
            )
            continue

        validators[directory] = Draft202012Validator(schema)

    return validators, findings


def _format_schema_path(error: exceptions.ValidationError) -> str:
    if not error.path:
        return "<root>"
    return ".".join(str(part) for part in error.path)


def _validate_record_body(
    path: Path,
    payload: Any,
    root: Path,
    record_root: Path,
    validators: dict[str, Draft202012Validator],
) -> list[Finding]:
    relpath = _relative(path, root)
    directory = _record_dir(path, record_root)
    findings: list[Finding] = []

    if directory not in REQUIRED_RECORD_DIRS:
        return [
            Finding(
                "error",
                "record_unknown_subdir",
                relpath,
                "JSON record is outside an approved governance record subdirectory.",
            )
        ]

    if not isinstance(payload, dict):
        return [
            Finding("error", "record_not_object", relpath, "Governance JSON record root must be an object.")
        ]

    validator = validators.get(directory)
    if validator is None:
        findings.append(
            Finding(
                "error",
                "record_schema_validator_missing",
                relpath,
                f"No loaded JSON Schema validator for records under {directory}/.",
            )
        )
    else:
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
            findings.append(
                Finding(
                    "error",
                    "record_schema_validation_failed",
                    relpath,
                    f"{_format_schema_path(error)}: {error.message}",
                )
            )

    required_fields = {"schema", "created_utc", "authority_status", ID_FIELDS_BY_DIR[directory]}
    missing = sorted(field for field in required_fields if field not in payload)
    for field in missing:
        findings.append(
            Finding("error", "record_missing_required_field", relpath, f"Missing field: {field}.")
        )

    expected_schema = RECORD_SCHEMA_BY_DIR[directory]
    if payload.get("schema") != expected_schema:
        findings.append(
            Finding(
                "error",
                "record_schema_mismatch",
                relpath,
                f"schema must be {expected_schema} for records under {directory}/.",
            )
        )

    authority_status = payload.get("authority_status")
    if authority_status not in ALLOWED_AUTHORITY_STATUSES:
        findings.append(
            Finding(
                "error",
                "record_authority_status_invalid",
                relpath,
                "authority_status is missing or not approved.",
            )
        )
        return findings

    if directory in ADVISORY_ONLY_DIRS and authority_status != "advisory_only":
        findings.append(
            Finding(
                "error",
                "record_authority_status_not_advisory",
                relpath,
                f"Records under {directory}/ must remain advisory_only.",
            )
        )

    if directory == "evidence" and authority_status not in {"evidence_only", "advisory_only"}:
        findings.append(
            Finding(
                "error",
                "evidence_authority_status_invalid",
                relpath,
                "Evidence records must use evidence_only or advisory_only.",
            )
        )

    if directory == "bindings" and authority_status != "binding":
        findings.append(
            Finding(
                "error",
                "binding_authority_status_invalid",
                relpath,
                "Binding records must use authority_status binding.",
            )
        )

    if directory == "archive" and authority_status != "historical_evidence":
        findings.append(
            Finding(
                "error",
                "archive_authority_status_invalid",
                relpath,
                "Archive index records must use historical_evidence.",
            )
        )

    if authority_status == "operator_accepted" and directory not in {"decisions", "autonomy", "command_manifests"}:
        findings.append(
            Finding(
                "error",
                "operator_accepted_wrong_record_dir",
                relpath,
                "operator_accepted records are reserved for decisions/ and accepted autonomy records.",
            )
        )

    if directory == "autonomy" and authority_status == "operator_accepted":
        required = ("operator_decision_id", "technical_gate_result", "grant_state")
        for field in required:
            if field not in payload:
                findings.append(
                    Finding(
                        "error",
                        "accepted_autonomy_missing_gate_field",
                        relpath,
                        f"Accepted autonomy grant is missing field: {field}.",
                    )
                )
        if payload.get("grant_state") != "operator_accepted":
            findings.append(
                Finding(
                    "error",
                    "accepted_autonomy_state_invalid",
                    relpath,
                    "Accepted autonomy grant must have grant_state operator_accepted.",
                )
            )

    return findings


def _records_by_id(record_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in _json_files(record_root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        directory = _record_dir(path, record_root)
        if directory not in ID_FIELDS_BY_DIR:
            continue
        record_id = payload.get(ID_FIELDS_BY_DIR[directory])
        if isinstance(record_id, str) and record_id:
            records[record_id] = payload
    return records


def validate_cross_record_links(root: Path) -> list[Finding]:
    record_root = root / "governance" / "80_records"
    records = _records_by_id(record_root)
    findings: list[Finding] = []

    for path in _json_files(record_root):
        relpath = _relative(path, root)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        directory = _record_dir(path, record_root)

        if directory == "decisions" and payload.get("authority_status") == "operator_accepted":
            source_refs = payload.get("source_refs")
            if not isinstance(source_refs, list) or not source_refs:
                findings.append(
                    Finding(
                        "error",
                        "accepted_decision_missing_source_refs",
                        relpath,
                        "Accepted Operator decisions must cite at least one source record.",
                    )
                )
            else:
                for ref in source_refs:
                    if isinstance(ref, str) and ref not in records:
                        findings.append(
                            Finding(
                                "error",
                                "accepted_decision_source_ref_missing",
                                relpath,
                                f"Accepted decision source ref does not exist: {ref}.",
                            )
                        )

        if directory == "bindings":
            decision_id = payload.get("operator_decision_id")
            decision = records.get(decision_id) if isinstance(decision_id, str) else None
            if not decision or decision.get("authority_status") != "operator_accepted":
                findings.append(
                    Finding(
                        "error",
                        "binding_decision_not_operator_accepted",
                        relpath,
                        "Binding record must cite an operator_accepted decision.",
                    )
                )
            elif decision.get("decision") != "approve":
                findings.append(
                    Finding(
                        "error",
                        "binding_decision_not_approve",
                        relpath,
                        "Binding record must cite an approve decision.",
                    )
                )

        if directory == "command_intents" and payload.get("parse_status") == "accepted":
            manifest_id = payload.get("manifest_id")
            manifest = records.get(manifest_id) if isinstance(manifest_id, str) else None
            if not manifest or manifest.get("schema") != "axiom.command_manifest.v0.1":
                findings.append(
                    Finding(
                        "error",
                        "command_intent_manifest_missing",
                        relpath,
                        "Accepted command intent must cite an existing command manifest.",
                    )
                )
            if payload.get("runtime_action_executed") is not False or payload.get("ledger_written") is not False:
                findings.append(
                    Finding(
                        "error",
                        "command_intent_runtime_or_ledger_side_effect",
                        relpath,
                        "JSON-first command intents must not execute runtime actions or write legacy ledger rows.",
                    )
                )

        if directory == "autonomy" and payload.get("authority_status") == "operator_accepted":
            decision_id = payload.get("operator_decision_id")
            decision = records.get(decision_id) if isinstance(decision_id, str) else None
            if not decision or decision.get("authority_status") != "operator_accepted":
                findings.append(
                    Finding(
                        "error",
                        "accepted_autonomy_decision_not_operator_accepted",
                        relpath,
                        "Accepted autonomy grant must cite an operator_accepted decision.",
                    )
                )
            if payload.get("technical_gate_result") != "passed":
                findings.append(
                    Finding(
                        "error",
                        "accepted_autonomy_technical_gate_not_passed",
                        relpath,
                        "Accepted autonomy grant must cite a passed technical gate.",
                    )
                )

    return findings


def validate_records(root: Path) -> list[Finding]:
    record_root = root / "governance" / "80_records"
    validators, findings = _load_record_schemas(root, record_root)

    for path in _json_files(record_root):
        relpath = _relative(path, root)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "record_json_parse_error",
                    relpath,
                    f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}.",
                )
            )
            continue
        findings.extend(_validate_record_body(path, payload, root, record_root, validators))

    return findings


def validate_hygiene(root: Path) -> list[Finding]:
    governance = root / "governance"
    if not governance.exists():
        return [
            Finding("error", "governance_dir_missing", _relative(governance, root), "governance directory is missing.")
        ]

    findings: list[Finding] = []
    for path in sorted(governance.rglob("desktop.ini")):
        findings.append(
            Finding(
                "warning",
                "desktop_ini_present",
                _relative(path, root),
                "Windows desktop.ini file is present under governance.",
            )
        )

    return findings


def summarize_findings(findings: Iterable[Finding]) -> dict[str, int]:
    summary = {"error": 0, "warning": 0}
    for finding in findings:
        summary[finding.severity] = summary.get(finding.severity, 0) + 1
    return summary


def validate_governance(root: Path = ROOT, *, strict: bool = False) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    findings.extend(validate_scaffold_files(root))
    findings.extend(validate_record_root(root))
    findings.extend(validate_records(root))
    findings.extend(validate_cross_record_links(root))
    findings.extend(validate_hygiene(root))

    summary = summarize_findings(findings)
    passed = summary.get("error", 0) == 0
    if strict and summary.get("warning", 0) > 0:
        passed = False

    return {
        "tool_version": TOOL_VERSION,
        "root": str(root),
        "strict": strict,
        "passed": passed,
        "summary": summary,
        "findings": [asdict(finding) for finding in findings],
    }


def _print_text_report(result: dict[str, Any]) -> None:
    print("AXIOM governance validation")
    print("===========================")
    print(f"tool_version: {result['tool_version']}")
    print(f"passed: {result['passed']}")
    print(f"strict: {result['strict']}")
    print(f"errors: {result['summary'].get('error', 0)}")
    print(f"warnings: {result['summary'].get('warning', 0)}")
    for finding in result["findings"]:
        print("")
        print(f"[{finding['severity'].upper()}] {finding['code']}")
        print(f"path: {finding['path']}")
        print(f"message: {finding['message']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the AXIOM governance scaffold, Mandate 3 schemas, and JSON record root."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings as well as errors.",
    )
    args = parser.parse_args()

    result = validate_governance(args.root, strict=args.strict)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_text_report(result)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
