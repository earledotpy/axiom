from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from axiom.core.decision import preview_decision, record_decision
from axiom.core.evaluation import build_evaluation_report
from axiom.core.governance_records import (
    DEFAULT_RECORD_ROOT,
    list_records,
    slug,
    unique,
    write_record,
)
from axiom.core.handoff import create_handoff
from axiom.core.operator_console import build_console_state

CYCLE_SUMMARY_SCHEMA = "axiom.governance_cycle_summary.v0.1"
ROADMAP_ARTIFACT_TYPE = "roadmap"
REVIEW_INGEST_SOURCE = "terminal_report"

RECORD_DIRS_FOR_CYCLES = (
    "tasks",
    "delegations",
    "handoffs",
    "evaluations",
    "evidence",
    "decisions",
)

ID_FIELD_BY_DIR = {
    "tasks": "task_card_id",
    "delegations": "delegation_id",
    "handoffs": "artifact_id",
    "evaluations": "evaluation_id",
    "evidence": "evidence_id",
    "decisions": "decision_id",
}

CLOSED_STATES = {"closed", "completed", "rejected", "revoked", "expired", "archived"}


@dataclass(frozen=True)
class GovernanceCycleResult:
    cycle: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoadmapCreateResult:
    created: bool
    path: str
    roadmap: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewIngestResult:
    created: bool
    path: str
    review: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuidedDecisionResult:
    created: bool
    path: str
    decision: dict[str, Any]
    cycle_summary: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False

    @property
    def authority_status(self) -> str:
        return str(self.decision.get("authority_status") or "advisory_only")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authority_status"] = self.authority_status
        return payload


def _record_id(directory: str, payload: dict[str, Any], fallback: str) -> str:
    field = ID_FIELD_BY_DIR.get(directory, "")
    value = payload.get(field)
    return value if isinstance(value, str) and value else fallback


def _record_scope(payload: dict[str, Any]) -> str:
    value = payload.get("scope")
    return value if isinstance(value, str) and value else "unspecified"


def _record_status(payload: dict[str, Any]) -> str:
    for field in ("status", "lifecycle_state", "decision_status"):
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value
    return "unknown"


def _record_title(directory: str, payload: dict[str, Any], record_id: str) -> str:
    for field in ("title", "operator_goal", "scope", "summary"):
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value
    if directory == "decisions":
        decision = payload.get("decision")
        target = payload.get("target_id")
        if isinstance(decision, str) and isinstance(target, str):
            return f"{decision}: {target}"
    return record_id


def _cycle_record(directory: str, path: Path, payload: dict[str, Any], record_root: Path) -> dict[str, Any]:
    record_id = _record_id(directory, payload, path.stem)
    status = _record_status(payload)
    try:
        relative_path = path.relative_to(record_root.parent.parent).as_posix()
    except ValueError:
        relative_path = path.as_posix()
    return {
        "record_id": record_id,
        "record_type": directory,
        "title": _record_title(directory, payload, record_id),
        "scope": _record_scope(payload),
        "status": status,
        "lifecycle_state": str(payload.get("lifecycle_state") or status),
        "authority_status": str(payload.get("authority_status") or "unknown"),
        "recommended_next_action": str(payload.get("recommended_next_action") or ""),
        "path": relative_path,
    }


def _records_by_scope(record_root: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for directory in RECORD_DIRS_FOR_CYCLES:
        for path, payload in list_records(record_root, directory):
            record = _cycle_record(directory, path, payload, record_root)
            grouped.setdefault(record["scope"], []).append(record)
    return grouped


def _scope_items(items: list[dict[str, Any]], record_type: str) -> list[dict[str, Any]]:
    return [item for item in items if item["record_type"] == record_type]


def _active_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item["status"] not in CLOSED_STATES]


def _scope_blockers(console_state: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    return [item for item in console_state["blockers"] if item.get("scope") == scope]


def _scope_decisions(console_state: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    return [item for item in console_state["decision_queue"] if item.get("scope") == scope]


def _next_actions(
    *,
    scope: str,
    records: list[dict[str, Any]],
    console_state: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    blockers = _scope_blockers(console_state, scope)
    decisions = _scope_decisions(console_state, scope)
    if blockers:
        actions.append("review_blockers")
    if any(item.get("decision_status") == "ready_for_operator_decision" for item in decisions):
        actions.append("preview_operator_decision")
    if not _scope_items(records, "evaluations"):
        actions.append("file_agent_review")
    if not _scope_items(records, "evidence"):
        actions.append("collect_or_file_evidence")
    if not decisions and _scope_items(records, "evaluations"):
        actions.append("prepare_decision_summary")
    if not actions:
        actions.append("no_operator_action_required")
    return actions


def build_cycle_state(*, root: Path, record_root: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    record_root = record_root or root / "governance" / "80_records"
    console_state = build_console_state(root=root)
    grouped = _records_by_scope(record_root)
    cycles: list[dict[str, Any]] = []

    for scope, records in sorted(grouped.items()):
        active = _active_items(records)
        if not active:
            continue
        cycles.append(
            {
                "scope": scope,
                "status": "blocked" if _scope_blockers(console_state, scope) else "active",
                "task_cards": _scope_items(records, "tasks"),
                "delegations": _scope_items(records, "delegations"),
                "handoffs": _scope_items(records, "handoffs"),
                "evaluations": _scope_items(records, "evaluations"),
                "evidence": _scope_items(records, "evidence"),
                "decisions": _scope_items(records, "decisions"),
                "blockers": _scope_blockers(console_state, scope),
                "decision_queue": _scope_decisions(console_state, scope),
                "next_valid_actions": _next_actions(
                    scope=scope,
                    records=records,
                    console_state=console_state,
                ),
            }
        )

    return {
        "schema": CYCLE_SUMMARY_SCHEMA,
        "generated_utc": console_state["generated_utc"],
        "authority_status": "advisory_only",
        "runtime_action_executed": False,
        "ledger_written": False,
        "cycles": cycles,
        "summary": {
            "active_cycle_count": len(cycles),
            "blocked_cycle_count": sum(1 for item in cycles if item["status"] == "blocked"),
            "pending_operator_decision_count": sum(
                len(item["decision_queue"]) for item in cycles
            ),
        },
        "failure_state": console_state["failure_state"],
        "recommended_next_actions": console_state["recommended_next_actions"],
    }


def format_cycle_summary(cycle_state: dict[str, Any]) -> str:
    lines = [
        "AXIOM GOVERNANCE CYCLE SUMMARY",
        f"authority_status: {cycle_state['authority_status']}",
        f"active_cycles: {cycle_state['summary']['active_cycle_count']}",
        f"blocked_cycles: {cycle_state['summary']['blocked_cycle_count']}",
        f"pending_operator_decisions: {cycle_state['summary']['pending_operator_decision_count']}",
    ]
    for cycle in cycle_state["cycles"]:
        lines.extend(
            [
                "",
                f"SCOPE: {cycle['scope']}",
                f"STATUS: {cycle['status']}",
                f"TASKS: {len(cycle['task_cards'])}",
                f"DELEGATIONS: {len(cycle['delegations'])}",
                f"REVIEWS FILED: {len(cycle['evaluations'])}",
                f"EVIDENCE: {len(cycle['evidence'])}",
                f"BLOCKERS: {len(cycle['blockers'])}",
                f"PENDING OPERATOR DECISIONS: {len(cycle['decision_queue'])}",
                f"NEXT VALID ACTIONS: {', '.join(cycle['next_valid_actions'])}",
            ]
        )
    return "\n".join(lines)


def create_roadmap(
    *,
    title: str,
    scope: str,
    items: Iterable[str],
    source_refs: Iterable[str] = (),
    record_root: Path = DEFAULT_RECORD_ROOT,
    summary: str = "",
) -> RoadmapCreateResult:
    roadmap_items = [
        {
            "sequence": index,
            "title": item,
            "status": "planned",
            "authority_status": "advisory_only",
        }
        for index, item in enumerate(unique(items), start=1)
    ]
    if not roadmap_items:
        raise ValueError("at least one roadmap item is required")

    result = create_handoff(
        record_root=record_root,
        title=title,
        scope=scope,
        artifact_type=ROADMAP_ARTIFACT_TYPE,
        actor_role="CURSOR",
        summary=summary or title,
        source_refs=source_refs,
        findings=(item["title"] for item in roadmap_items),
        recommended_operator_decision="defer",
        recommended_next_action="activate the next roadmap item with a task card or delegation packet",
    )
    payload = result.handoff
    payload["roadmap_items"] = roadmap_items
    payload["roadmap_status"] = "planned"
    payload["runtime_action_executed"] = False
    payload["ledger_written"] = False
    path = write_record(record_root, "handoffs", f"{payload['artifact_id']}.json", payload)
    return RoadmapCreateResult(created=True, path=str(path), roadmap=payload)


def ingest_terminal_review(
    *,
    target_artifact: str,
    scope: str,
    review_text: str,
    evaluating_actor: str = "Claude Code",
    actor_role: str = "AUD",
    evaluation_type: str = "governance_audit",
    verdict: str = "not_evaluated",
    inputs_reviewed: Iterable[str] = (),
    checks_performed: Iterable[str] = (),
    findings: Iterable[str] = (),
    blocking_objections: Iterable[str] = (),
    non_blocking_concerns: Iterable[str] = (),
    required_tests: Iterable[str] = (),
    required_implementation_changes: Iterable[str] = (),
    evidence_quality: str = "not_evaluated",
    recommended_operator_decision: str = "defer",
    recommended_next_action: str = "review ingested evaluation report",
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> ReviewIngestResult:
    if not review_text.strip() and not any(
        unique([*findings, *blocking_objections, *non_blocking_concerns])
    ):
        raise ValueError("review_text or structured review fields are required")

    report = build_evaluation_report(
        target_artifact=target_artifact,
        scope=scope,
        evaluating_actor=evaluating_actor,
        actor_role=actor_role,
        evaluation_type=evaluation_type,
        verdict=verdict,
        inputs_reviewed=inputs_reviewed,
        checks_performed=checks_performed,
        findings=findings,
        blocking_objections=blocking_objections,
        non_blocking_concerns=non_blocking_concerns,
        evidence_quality=evidence_quality,
        recommended_operator_decision=recommended_operator_decision,
        recommended_next_action=recommended_next_action,
    ).to_dict()
    report["ingest_source"] = REVIEW_INGEST_SOURCE
    report["terminal_report"] = review_text.strip()
    report["required_tests"] = unique(required_tests)
    report["required_implementation_changes"] = unique(required_implementation_changes)
    report["runtime_action_executed"] = False
    report["ledger_written"] = False
    path = write_record(record_root, "evaluations", f"{report['evaluation_id']}.json", report)
    return ReviewIngestResult(created=True, path=str(path), review=report)


def preview_guided_decision(
    *,
    root: Path,
    decision: str,
    target_id: str,
    scope: str,
    source_refs: Iterable[str] = (),
    rationale: str = "",
    recommended_next_action: str = "record or revise decision",
) -> GuidedDecisionResult:
    root = Path(root).resolve()
    record_root = root / "governance" / "80_records"
    cycle_state = build_cycle_state(root=root, record_root=record_root)
    result = preview_decision(
        record_root=record_root,
        decision=decision,
        target_id=target_id,
        scope=scope,
        source_refs=source_refs,
        rationale=rationale,
        recommended_next_action=recommended_next_action,
    )
    return GuidedDecisionResult(
        created=result.created,
        path=result.path,
        decision=result.decision,
        cycle_summary=cycle_state,
        runtime_action_executed=False,
        ledger_written=False,
    )


def record_guided_decision(
    *,
    root: Path,
    preview_id: str,
    operator: str,
    confirmation: str,
) -> GuidedDecisionResult:
    root = Path(root).resolve()
    record_root = root / "governance" / "80_records"
    result = record_decision(
        preview_id=preview_id,
        operator=operator,
        confirmation=confirmation,
        record_root=record_root,
    )
    return GuidedDecisionResult(
        created=result.created,
        path=result.path,
        decision=result.decision,
        cycle_summary=build_cycle_state(root=root, record_root=record_root),
        runtime_action_executed=False,
        ledger_written=False,
    )
