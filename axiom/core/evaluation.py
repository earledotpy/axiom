from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
EVALUATION_SCHEMA = "axiom.evaluation_report.v0.1"
BLOCKER_SUMMARY_SCHEMA = "axiom.blocker_summary.v0.1"
DEFAULT_RECORD_ROOT = ROOT / "governance" / "80_records"

AGENT_ROLE_TO_PROCESS_FUNCTION = {
    "ARCH": ("architect", "plan"),
    "IMPL": ("implement", "build"),
    "AUD": ("audit", "verify"),
    "CURSOR": ("synthesize", "summarize"),
    "SYN": ("synthesize", "summarize"),
}


@dataclass(frozen=True)
class EvaluationReport:
    schema: str
    evaluation_id: str
    created_utc: str
    evaluating_actor: str
    actor_role: str
    process: str
    function: str
    target_artifact: str
    target_lifecycle_state: str
    authority_status: str
    evaluation_type: str
    scope: str
    verdict: str
    inputs_reviewed: list[str]
    checks_performed: list[str]
    findings: list[str]
    blocking_objections: list[dict[str, Any]]
    non_blocking_concerns: list[str]
    evidence_quality: str
    scope_compliance: str
    doctrine_compliance: str
    workflow_compliance: str
    transport_compliance: str
    delegation_compliance: str
    execution_compliance: str
    recommended_operator_decision: str
    recommended_next_action: str
    status: str = "active"
    lifecycle_state: str = "evaluated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationCreateResult:
    created: bool
    path: str
    report: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _id_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper()).strip("-")
    return cleaned[:32] or "AXIOM"


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip() if isinstance(item, str) else ""
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _evaluation_dir(record_root: Path) -> Path:
    return record_root / "evaluations"


def _resolve_process_function(actor_role: str) -> tuple[str, str]:
    return AGENT_ROLE_TO_PROCESS_FUNCTION.get(actor_role, ("audit", "verify"))


def _normalize_actor_role(actor_role: str) -> str:
    role = actor_role.strip().upper() or "AUD"
    if role == "SYN":
        return "CURSOR"
    return role


def _blocker(title: str, *, affected_layer: str, recommended_next_action: str) -> dict[str, Any]:
    return {
        "title": title.strip(),
        "affected_layer": affected_layer.strip() or "Evaluation",
        "recommended_next_action": recommended_next_action.strip(),
    }


def build_evaluation_report(
    *,
    target_artifact: str,
    scope: str,
    evaluating_actor: str = "Claude Code",
    actor_role: str = "AUD",
    target_lifecycle_state: str = "unknown",
    evaluation_type: str = "governance_audit",
    verdict: str = "not_evaluated",
    inputs_reviewed: Iterable[str] = (),
    checks_performed: Iterable[str] = (),
    findings: Iterable[str] = (),
    blocking_objections: Iterable[str] = (),
    non_blocking_concerns: Iterable[str] = (),
    evidence_quality: str = "not_evaluated",
    scope_compliance: str = "not_evaluated",
    doctrine_compliance: str = "not_evaluated",
    workflow_compliance: str = "not_evaluated",
    transport_compliance: str = "not_evaluated",
    delegation_compliance: str = "not_evaluated",
    execution_compliance: str = "not_evaluated",
    recommended_operator_decision: str = "defer",
    recommended_next_action: str = "review evaluation report",
    affected_layer: str = "Evaluation",
) -> EvaluationReport:
    if not target_artifact.strip():
        raise ValueError("target_artifact is required")
    if not scope.strip():
        raise ValueError("scope is required")

    actor_role = _normalize_actor_role(actor_role)
    process, function = _resolve_process_function(actor_role)
    blocker_items = [
        _blocker(item, affected_layer=affected_layer, recommended_next_action=recommended_next_action)
        for item in _unique(blocking_objections)
    ]

    return EvaluationReport(
        schema=EVALUATION_SCHEMA,
        evaluation_id=f"EVL-{_id_timestamp()}-{_slug(scope)}",
        created_utc=_utc_now(),
        evaluating_actor=evaluating_actor.strip() or "Claude Code",
        actor_role=actor_role,
        process=process,
        function=function,
        target_artifact=target_artifact.strip(),
        target_lifecycle_state=target_lifecycle_state.strip() or "unknown",
        authority_status="advisory_only",
        evaluation_type=evaluation_type.strip() or "governance_audit",
        scope=scope.strip(),
        verdict=verdict.strip() or "not_evaluated",
        inputs_reviewed=_unique(inputs_reviewed),
        checks_performed=_unique(checks_performed),
        findings=_unique(findings),
        blocking_objections=blocker_items,
        non_blocking_concerns=_unique(non_blocking_concerns),
        evidence_quality=evidence_quality.strip() or "not_evaluated",
        scope_compliance=scope_compliance.strip() or "not_evaluated",
        doctrine_compliance=doctrine_compliance.strip() or "not_evaluated",
        workflow_compliance=workflow_compliance.strip() or "not_evaluated",
        transport_compliance=transport_compliance.strip() or "not_evaluated",
        delegation_compliance=delegation_compliance.strip() or "not_evaluated",
        execution_compliance=execution_compliance.strip() or "not_evaluated",
        recommended_operator_decision=recommended_operator_decision.strip() or "defer",
        recommended_next_action=recommended_next_action.strip() or "review evaluation report",
    )


def create_evaluation_report(
    *,
    target_artifact: str,
    scope: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
    evaluating_actor: str = "Claude Code",
    actor_role: str = "AUD",
    target_lifecycle_state: str = "unknown",
    evaluation_type: str = "governance_audit",
    verdict: str = "not_evaluated",
    inputs_reviewed: Iterable[str] = (),
    checks_performed: Iterable[str] = (),
    findings: Iterable[str] = (),
    blocking_objections: Iterable[str] = (),
    non_blocking_concerns: Iterable[str] = (),
    evidence_quality: str = "not_evaluated",
    scope_compliance: str = "not_evaluated",
    doctrine_compliance: str = "not_evaluated",
    workflow_compliance: str = "not_evaluated",
    transport_compliance: str = "not_evaluated",
    delegation_compliance: str = "not_evaluated",
    execution_compliance: str = "not_evaluated",
    recommended_operator_decision: str = "defer",
    recommended_next_action: str = "review evaluation report",
    affected_layer: str = "Evaluation",
) -> EvaluationCreateResult:
    report = build_evaluation_report(
        target_artifact=target_artifact,
        scope=scope,
        evaluating_actor=evaluating_actor,
        actor_role=actor_role,
        target_lifecycle_state=target_lifecycle_state,
        evaluation_type=evaluation_type,
        verdict=verdict,
        inputs_reviewed=inputs_reviewed,
        checks_performed=checks_performed,
        findings=findings,
        blocking_objections=blocking_objections,
        non_blocking_concerns=non_blocking_concerns,
        evidence_quality=evidence_quality,
        scope_compliance=scope_compliance,
        doctrine_compliance=doctrine_compliance,
        workflow_compliance=workflow_compliance,
        transport_compliance=transport_compliance,
        delegation_compliance=delegation_compliance,
        execution_compliance=execution_compliance,
        recommended_operator_decision=recommended_operator_decision,
        recommended_next_action=recommended_next_action,
        affected_layer=affected_layer,
    )
    directory = _evaluation_dir(record_root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{report.evaluation_id}.json"
    payload = report.to_dict()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return EvaluationCreateResult(created=True, path=str(path), report=payload)


def list_evaluation_reports(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    directory = _evaluation_dir(record_root)
    if not directory.exists():
        return []

    reports: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            reports.append(
                {
                    "path": str(path),
                    "evaluation_id": payload.get("evaluation_id", path.stem),
                    "created_utc": payload.get("created_utc", ""),
                    "scope": payload.get("scope", ""),
                    "target_artifact": payload.get("target_artifact", ""),
                    "authority_status": payload.get("authority_status", "unknown"),
                    "evaluation_type": payload.get("evaluation_type", ""),
                    "verdict": payload.get("verdict", ""),
                    "process": payload.get("process", ""),
                    "function": payload.get("function", ""),
                    "blocking_count": len(payload.get("blocking_objections", []))
                    if isinstance(payload.get("blocking_objections"), list)
                    else 0,
                    "status": payload.get("status", ""),
                }
            )
    return sorted(reports, key=lambda item: (item["created_utc"], item["evaluation_id"]))


def load_evaluation_report(evaluation_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    path = _evaluation_dir(record_root) / f"{evaluation_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"evaluation report not found: {evaluation_id}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"evaluation report root is not an object: {evaluation_id}")
    return payload


def build_blocker_summary(*, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    for report in list_evaluation_reports(record_root=record_root):
        payload = load_evaluation_report(str(report["evaluation_id"]), record_root=record_root)
        raw_blockers = payload.get("blocking_objections", [])
        if not isinstance(raw_blockers, list):
            continue
        for index, item in enumerate(raw_blockers, start=1):
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("reason") or "blocking_objection")
                affected_layer = str(item.get("affected_layer") or item.get("layer") or "Evaluation")
                recommended = str(item.get("recommended_next_action") or item.get("recommended_resolution") or "")
            else:
                title = str(item)
                affected_layer = "Evaluation"
                recommended = ""
            blockers.append(
                {
                    "blocker_id": f"{payload.get('evaluation_id', report['evaluation_id'])}:B{index}",
                    "scope": str(payload.get("scope") or ""),
                    "title": title,
                    "affected_layer": affected_layer,
                    "source_evaluation_id": str(payload.get("evaluation_id") or report["evaluation_id"]),
                    "target_artifact": str(payload.get("target_artifact") or ""),
                    "reported_by": str(payload.get("evaluating_actor") or ""),
                    "recommended_next_action": recommended,
                    "authority_status": "advisory_only",
                }
            )

    return {
        "schema": BLOCKER_SUMMARY_SCHEMA,
        "generated_utc": _utc_now(),
        "authority_status": "advisory_only",
        "blocking_count": len(blockers),
        "affected_layers": sorted({item["affected_layer"] for item in blockers if item.get("affected_layer")}),
        "blockers": blockers,
    }
