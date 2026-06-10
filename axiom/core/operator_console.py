from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECORD_ROOT = ROOT / "governance" / "80_records"

CONSOLE_STATE_SCHEMA = "axiom.operator_console_state.v0.1"
COMMAND_OUTPUT_SCHEMA = "axiom.operator_console_command_output.v0.1"
ADVISORY_AUTHORITY = "advisory_only"

COMMAND_TO_VIEW = {
    "/axiom:show-active-state": "active_state",
    "show-active-state": "active_state",
    "active_state": "active_state",
    "/axiom:show-blockers": "blockers",
    "show-blockers": "blockers",
    "blockers": "blockers",
    "/axiom:show-decisions": "decision_queue",
    "show-decisions": "decision_queue",
    "decisions": "decision_queue",
    "decision_queue": "decision_queue",
    "/axiom:show-evidence": "evidence",
    "show-evidence": "evidence",
    "evidence": "evidence",
    "/axiom:show-autonomy-status": "autonomy_status",
    "show-autonomy-status": "autonomy_status",
    "autonomy_status": "autonomy_status",
}

SOURCE_TYPE_BY_DIR = {
    "tasks": "task_card",
    "delegations": "delegation_packet",
    "handoffs": "handoff_json",
    "evaluations": "evaluation_report",
    "evidence": "implementation_evidence",
    "decisions": "operator_decision",
    "bindings": "binding",
    "console": "console_view",
    "autonomy": "autonomy_grant",
    "command_manifests": "command_manifest",
    "command_intents": "command_intent",
    "archive": "archive_index",
}

ID_FIELD_BY_DIR = {
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

ADVISORY_ONLY_DIRS = {"tasks", "delegations", "handoffs", "evaluations", "console", "command_intents"}


@dataclass(frozen=True)
class GovernanceRecord:
    path: Path
    directory: str
    payload: dict[str, Any]

    @property
    def source_id(self) -> str:
        id_field = ID_FIELD_BY_DIR.get(self.directory, "")
        value = self.payload.get(id_field)
        return value if isinstance(value, str) and value else self.path.stem

    @property
    def authority_status(self) -> str:
        value = self.payload.get("authority_status")
        return value if isinstance(value, str) else "unknown"

    @property
    def lifecycle_state(self) -> str:
        for field_name in ("lifecycle_state", "target_lifecycle_state", "grant_state", "status"):
            value = self.payload.get(field_name)
            if isinstance(value, str) and value:
                return value
        return "unknown"


@dataclass(frozen=True)
class ConsoleFailureReason:
    reason: str
    affected_view: str
    source_refs: list[dict[str, Any]] = field(default_factory=list)
    recommended_next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsoleSource:
    source_id: str
    source_path: str
    source_type: str
    authority_status: str
    lifecycle_state: str
    read_status: str = "read"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _record_directory(path: Path, record_root: Path) -> str:
    try:
        relative = path.relative_to(record_root)
    except ValueError:
        return "unknown"
    return relative.parts[0] if relative.parts else "unknown"


def _source_ref(record: GovernanceRecord, root: Path) -> dict[str, Any]:
    return ConsoleSource(
        source_id=record.source_id,
        source_path=_relative(record.path, root),
        source_type=SOURCE_TYPE_BY_DIR.get(record.directory, "unknown"),
        authority_status=record.authority_status,
        lifecycle_state=record.lifecycle_state,
    ).to_dict()


def _failure_ref(path: Path, root: Path, reason: str) -> dict[str, Any]:
    return ConsoleSource(
        source_id=path.stem,
        source_path=_relative(path, root),
        source_type="unknown",
        authority_status="unknown",
        lifecycle_state="unknown",
        read_status="invalid",
        notes=[reason],
    ).to_dict()


def _load_records(root: Path, record_root: Path) -> tuple[list[GovernanceRecord], list[ConsoleFailureReason]]:
    records: list[GovernanceRecord] = []
    failures: list[ConsoleFailureReason] = []

    if not record_root.exists():
        failures.append(
            ConsoleFailureReason(
                reason="missing_source",
                affected_view="all",
                source_refs=[
                    ConsoleSource(
                        source_id="governance_records",
                        source_path=_relative(record_root, root),
                        source_type="unknown",
                        authority_status="unknown",
                        lifecycle_state="unknown",
                        read_status="missing",
                    ).to_dict()
                ],
                recommended_next_action="restore governance/80_records before generating console state",
            )
        )
        return records, failures

    record_dirs = set(ID_FIELD_BY_DIR)
    for path in sorted(record_root.rglob("*.json")):
        directory = _record_directory(path, record_root)
        if directory not in record_dirs:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            failures.append(
                ConsoleFailureReason(
                    reason="invalid_json",
                    affected_view="all",
                    source_refs=[_failure_ref(path, root, f"line {exc.lineno}, column {exc.colno}: {exc.msg}")],
                    recommended_next_action="repair or remove invalid governance JSON record",
                )
            )
            continue

        if not isinstance(payload, dict):
            failures.append(
                ConsoleFailureReason(
                    reason="unknown_schema",
                    affected_view="all",
                    source_refs=[_failure_ref(path, root, "record root is not an object")],
                    recommended_next_action="replace record with a JSON object",
                )
            )
            continue

        record = GovernanceRecord(path=path, directory=directory, payload=payload)
        failures.extend(_validate_record_for_console(record, root))
        records.append(record)

    return records, failures


def _validate_record_for_console(record: GovernanceRecord, root: Path) -> list[ConsoleFailureReason]:
    failures: list[ConsoleFailureReason] = []
    source_ref = _source_ref(record, root)

    if record.authority_status == "unknown":
        failures.append(
            ConsoleFailureReason(
                reason="missing_authority_status",
                affected_view="all",
                source_refs=[source_ref],
                recommended_next_action="add authority_status to the source record",
            )
        )

    if record.directory in ADVISORY_ONLY_DIRS and record.authority_status != ADVISORY_AUTHORITY:
        failures.append(
            ConsoleFailureReason(
                reason="conflicting_authority_status",
                affected_view="all",
                source_refs=[source_ref],
                recommended_next_action="keep agent-authored console sources advisory_only",
            )
        )

    if record.directory == "archive":
        failures.append(
            ConsoleFailureReason(
                reason="archive_used_as_active",
                affected_view="active_state",
                source_refs=[source_ref],
                recommended_next_action="treat archive records as historical evidence only",
            )
        )

    return failures


def _title(record: GovernanceRecord) -> str:
    for field_name in ("title", "operator_goal", "core_thesis", "summary", "scope"):
        value = record.payload.get(field_name)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            summary = value.get("summary")
            if isinstance(summary, str) and summary:
                return summary
    return record.source_id


def _scope(record: GovernanceRecord) -> str:
    value = record.payload.get("scope")
    return value if isinstance(value, str) and value else ""


def _list_field(payload: dict[str, Any], field_name: str) -> list[Any]:
    value = payload.get(field_name)
    return value if isinstance(value, list) else []


def _record_blockers(record: GovernanceRecord, root: Path) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    raw_items = _list_field(record.payload, "blocking_objections")
    evaluation = record.payload.get("evaluation")
    if isinstance(evaluation, dict):
        raw_items.extend(_list_field(evaluation, "blocking_objections"))
    if record.directory == "command_intents" and record.payload.get("parse_status") == "rejected":
        raw_items.append(
            {
                "title": str(record.payload.get("rejection_reason") or "command_intent_rejected"),
                "affected_layer": "Transport",
                "recommended_next_action": "repair command manifest or command payload before recording intent",
            }
        )

    for index, item in enumerate(raw_items, start=1):
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("reason") or item.get("summary") or "blocking_objection")
            affected_layer = str(item.get("affected_layer") or item.get("layer") or "Unknown")
            affected_boundary = str(item.get("affected_boundary") or item.get("boundary") or "")
            evidence = _list_field(item, "evidence")
            recommended = str(item.get("recommended_next_action") or item.get("recommended_resolution") or "")
        else:
            title = str(item)
            affected_layer = "Unknown"
            affected_boundary = ""
            evidence = []
            recommended = ""

        blockers.append(
            {
                "blocker_id": f"{record.source_id}:B{index}",
                "severity": "blocking",
                "title": title,
                "scope": _scope(record),
                "affected_layer": affected_layer,
                "affected_boundary": affected_boundary,
                "reported_by": str(record.payload.get("evaluating_actor") or record.payload.get("actor") or ""),
                "source_refs": [_source_ref(record, root)],
                "evidence": evidence,
                "recommended_resolution": recommended,
                "recommended_next_action": recommended,
            }
        )

    return blockers


def _failure_blockers(failures: list[ConsoleFailureReason]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for index, failure in enumerate(failures, start=1):
        blockers.append(
            {
                "blocker_id": f"failure:{index}",
                "severity": "blocking",
                "title": failure.reason,
                "scope": "operator_console",
                "affected_layer": "Operator Console",
                "affected_boundary": failure.affected_view,
                "reported_by": "operator_console",
                "source_refs": failure.source_refs,
                "evidence": failure.source_refs,
                "recommended_resolution": failure.recommended_next_action,
                "recommended_next_action": failure.recommended_next_action,
            }
        )
    return blockers


def _active_state(records: list[GovernanceRecord], root: Path) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    closed_states = {"closed", "completed", "rejected", "revoked", "expired", "archived"}
    active_dirs = {"tasks", "delegations", "handoffs", "evaluations", "decisions", "bindings", "autonomy", "command_manifests", "command_intents"}
    for record in records:
        if record.directory not in active_dirs:
            continue
        status = str(record.payload.get("status") or record.lifecycle_state or "unknown")
        if status in closed_states:
            continue
        active.append(
            {
                "item_id": record.source_id,
                "title": _title(record),
                "scope": _scope(record),
                "lifecycle_state": record.lifecycle_state,
                "authority_status": record.authority_status,
                "current_owner_role": str(record.payload.get("current_owner_role") or record.payload.get("actor_role") or record.payload.get("actor") or ""),
                "next_expected_role": str(record.payload.get("next_expected_role") or record.payload.get("recommended_owner") or record.payload.get("recommended_first_agent") or ""),
                "status": status,
                "source_refs": [_source_ref(record, root)],
                "recommended_next_action": str(record.payload.get("recommended_next_action") or ""),
            }
        )
    return active


def _decision_queue(records: list[GovernanceRecord], blockers: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    blocker_scopes = {blocker.get("scope") for blocker in blockers if blocker.get("scope")}
    decisions: list[dict[str, Any]] = []
    for record in records:
        payload = record.payload
        recommended = payload.get("recommended_operator_decision")
        next_step = payload.get("next_step")
        if isinstance(next_step, dict) and not recommended:
            recommended = next_step.get("binary_action")
        is_decision_source = record.directory in {"handoffs", "evaluations", "decisions"}
        if not is_decision_source or not recommended:
            continue
        scope = _scope(record)
        status = "blocked_pending_review" if scope in blocker_scopes else "ready_for_operator_decision"
        if record.directory == "decisions" and record.authority_status == "operator_accepted":
            status = "closed"
        decisions.append(
            {
                "decision_id": f"{record.source_id}:decision",
                "scope": scope,
                "title": _title(record),
                "decision_status": status,
                "decision_options": ["approve", "reject", "defer", "narrow_scope", "request_review", "request_remediation", "archive"],
                "authority_status": ADVISORY_AUTHORITY,
                "source_refs": [_source_ref(record, root)],
                "blocking_objections": [blocker for blocker in blockers if blocker.get("scope") == scope],
                "non_blocking_concerns": _list_field(payload, "non_blocking_concerns"),
                "evidence_refs": _list_field(payload, "evidence_refs"),
                "recommended_operator_decision": str(recommended),
                "recommended_next_action": str(payload.get("recommended_next_action") or ""),
            }
        )
    return decisions


def _evidence(records: list[GovernanceRecord], root: Path) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for record in records:
        if record.directory not in {"evidence", "evaluations"}:
            continue
        payload = record.payload
        evidence_quality = str(payload.get("evidence_quality") or "not_evaluated")
        evidence.append(
            {
                "evidence_id": record.source_id,
                "scope": _scope(record),
                "evidence_type": str(payload.get("evidence_type") or SOURCE_TYPE_BY_DIR.get(record.directory, "unknown")),
                "authority_status": ADVISORY_AUTHORITY,
                "source_refs": [_source_ref(record, root)],
                "files_changed": _list_field(payload, "files_changed"),
                "commands_run": _list_field(payload, "commands_run"),
                "verification_results": _list_field(payload, "verification_results") or _list_field(payload, "checks_performed"),
                "skipped_checks": _list_field(payload, "skipped_checks"),
                "assumptions": _list_field(payload, "assumptions"),
                "known_risks": _list_field(payload, "known_risks"),
                "evidence_quality": evidence_quality,
                "recommended_next_action": str(payload.get("recommended_next_action") or ""),
            }
        )
    return evidence


def _autonomy_status(records: list[GovernanceRecord], failures: list[ConsoleFailureReason], root: Path) -> dict[str, Any]:
    accepted: list[GovernanceRecord] = []
    invalid: list[GovernanceRecord] = []
    for record in records:
        if record.directory != "autonomy":
            continue
        if (
            record.authority_status == "operator_accepted"
            and record.payload.get("grant_state") == "operator_accepted"
            and record.payload.get("operator_decision_id")
            and record.payload.get("technical_gate_result") == "passed"
        ):
            accepted.append(record)
        elif record.authority_status == "operator_accepted":
            invalid.append(record)

    if invalid:
        return {
            "runtime_autonomy": "disabled",
            "authority_status": ADVISORY_AUTHORITY,
            "technical_gate_status": "conflicting",
            "active_grant_present": False,
            "active_grant_id": None,
            "grant_state": None,
            "scope": None,
            "missing_requirements": ["valid_operator_decision_id", "passed_technical_gate_result", "operator_accepted_grant_state"],
            "source_refs": [_source_ref(record, root) for record in invalid],
            "recommended_next_action": "repair accepted autonomy grant record or keep autonomy disabled",
        }

    if accepted:
        grant = accepted[-1]
        return {
            "runtime_autonomy": "disabled",
            "authority_status": ADVISORY_AUTHORITY,
            "technical_gate_status": "passed",
            "active_grant_present": True,
            "active_grant_id": grant.source_id,
            "grant_state": grant.payload.get("grant_state"),
            "scope": _scope(grant),
            "missing_requirements": [],
            "source_refs": [_source_ref(grant, root)],
            "recommended_next_action": "runtime execution remains disabled in governance-only implementation",
        }

    runtime = "unknown_failed_closed" if failures else "disabled"
    return {
        "runtime_autonomy": runtime,
        "authority_status": ADVISORY_AUTHORITY,
        "technical_gate_status": "not_evaluated",
        "active_grant_present": False,
        "active_grant_id": None,
        "grant_state": None,
        "scope": None,
        "missing_requirements": ["operator_accepted_autonomy_grant", "passed_technical_gate_result"],
        "source_refs": [],
        "recommended_next_action": "runtime autonomy remains disabled",
    }


def build_console_state(*, root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    record_root = root / "governance" / "80_records"
    records, failures = _load_records(root, record_root)

    source_state = [_source_ref(record, root) for record in records]
    blockers = [blocker for record in records for blocker in _record_blockers(record, root)]
    blockers.extend(_failure_blockers(failures))
    active_state = _active_state(records, root)
    decision_queue = _decision_queue(records, blockers, root)
    evidence = _evidence(records, root)
    autonomy_status = _autonomy_status(records, failures, root)

    recommended: list[str] = []
    if blockers:
        recommended.append("review_blockers")
    if decision_queue:
        recommended.append("review_decision_queue")
    if not recommended:
        recommended.append("no_operator_action_required")

    return {
        "schema": CONSOLE_STATE_SCHEMA,
        "generated_utc": _utc_now(),
        "authority_status": ADVISORY_AUTHORITY,
        "source_state": source_state,
        "active_state": active_state,
        "blockers": blockers,
        "decision_queue": decision_queue,
        "evidence": evidence,
        "autonomy_status": autonomy_status,
        "failure_state": {
            "failed_closed": bool(failures),
            "reasons": [failure.to_dict() for failure in failures],
        },
        "recommended_next_actions": recommended,
    }


def _view_data(view: str, state: dict[str, Any]) -> dict[str, Any]:
    if view == "active_state":
        active = state["active_state"]
        return {
            "active_state": active,
            "summary": {
                "active_count": len(active),
                "pending_operator_decision_count": sum(1 for item in active if item.get("status") == "pending_operator_decision"),
                "blocked_count": sum(1 for item in active if item.get("status") == "blocked"),
            },
        }
    if view == "blockers":
        blockers = state["blockers"]
        return {
            "blockers": blockers,
            "summary": {
                "blocking_count": len(blockers),
                "affected_layers": sorted({str(item.get("affected_layer")) for item in blockers if item.get("affected_layer")}),
            },
        }
    if view == "decision_queue":
        queue = state["decision_queue"]
        return {
            "decision_queue": queue,
            "summary": {
                "ready_for_operator_decision_count": sum(1 for item in queue if item.get("decision_status") == "ready_for_operator_decision"),
                "blocked_pending_review_count": sum(1 for item in queue if item.get("decision_status") == "blocked_pending_review"),
                "blocked_pending_evidence_count": sum(1 for item in queue if item.get("decision_status") == "blocked_pending_evidence"),
            },
        }
    if view == "evidence":
        evidence = state["evidence"]
        return {
            "evidence": evidence,
            "summary": {
                "strong_count": sum(1 for item in evidence if item.get("evidence_quality") == "strong"),
                "partial_count": sum(1 for item in evidence if item.get("evidence_quality") == "partial"),
                "weak_count": sum(1 for item in evidence if item.get("evidence_quality") == "weak"),
                "missing_count": sum(1 for item in evidence if item.get("evidence_quality") == "missing"),
            },
        }
    if view == "autonomy_status":
        return {"autonomy_status": state["autonomy_status"]}
    raise ValueError(f"unknown operator console view: {view}")


def build_command_output(command: str, *, root: Path = ROOT) -> dict[str, Any]:
    view = COMMAND_TO_VIEW.get(command)
    if view is None:
        raise ValueError(f"unknown read-only operator console command: {command}")

    state = build_console_state(root=root)
    return {
        "schema": COMMAND_OUTPUT_SCHEMA,
        "command": command,
        "generated_utc": state["generated_utc"],
        "authority_status": ADVISORY_AUTHORITY,
        "view": view,
        "source_refs": state["source_state"],
        "data": _view_data(view, state),
        "failure_state": state["failure_state"],
        "recommended_next_actions": state["recommended_next_actions"],
    }
