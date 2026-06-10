from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from axiom.core.governance_records import (
    DEFAULT_RECORD_ROOT,
    find_record_by_id,
    id_timestamp,
    list_records,
    load_record_by_id,
    slug,
    unique,
    utc_now,
    write_record,
)

DECISION_SCHEMA = "axiom.operator_decision.v0.1"
ALLOWED_DECISIONS = {
    "approve",
    "reject",
    "defer",
    "narrow_scope",
    "request_review",
    "request_remediation",
    "archive",
}


@dataclass(frozen=True)
class DecisionResult:
    created: bool
    path: str
    decision: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ensure_sources_exist(record_root: Path, refs: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for ref in unique(refs):
        found = False
        for directory, id_field in (
            ("tasks", "task_card_id"),
            ("delegations", "delegation_id"),
            ("handoffs", "artifact_id"),
            ("evaluations", "evaluation_id"),
            ("evidence", "evidence_id"),
            ("decisions", "decision_id"),
            ("autonomy", "grant_id"),
            ("bindings", "binding_id"),
        ):
            if find_record_by_id(record_root, directory, id_field, ref) is not None:
                found = True
                break
        if not found:
            missing.append(ref)
    return missing


def build_decision_preview(
    *,
    decision: str,
    target_id: str,
    scope: str,
    source_refs: Iterable[str] = (),
    rationale: str = "",
    recommended_next_action: str = "record or revise decision",
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> dict[str, Any]:
    decision = decision.strip()
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"unknown decision: {decision}")
    if not target_id.strip():
        raise ValueError("target_id is required")
    if not scope.strip():
        raise ValueError("scope is required")

    refs = unique([target_id, *source_refs])
    missing = _ensure_sources_exist(record_root, refs)
    if missing:
        raise ValueError(f"source record not found: {', '.join(missing)}")

    decision_id = f"DEC-{id_timestamp()}-{slug(scope)}"
    return {
        "schema": DECISION_SCHEMA,
        "decision_id": decision_id,
        "created_utc": utc_now(),
        "operator": "",
        "scope": scope.strip(),
        "authority_status": "advisory_only",
        "decision": decision,
        "target_id": target_id.strip(),
        "source_refs": refs,
        "rationale": rationale.strip(),
        "decision_status": "preview",
        "confirmation_token": f"I_ACCEPT_AXIOM_DECISION:{decision_id}",
        "recommended_next_action": recommended_next_action.strip() or "record or revise decision",
        "runtime_action_executed": False,
        "ledger_written": False,
        "status": "pending_operator_confirmation",
        "lifecycle_state": "operator_decision",
    }


def preview_decision(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> DecisionResult:
    payload = build_decision_preview(record_root=record_root, **kwargs)
    path = write_record(record_root, "decisions", f"{payload['decision_id']}.json", payload)
    return DecisionResult(created=True, path=str(path), decision=payload)


def record_decision(
    *,
    preview_id: str,
    operator: str,
    confirmation: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> DecisionResult:
    payload = load_record_by_id(record_root, "decisions", preview_id)
    expected = payload.get("confirmation_token")
    if confirmation != expected:
        raise ValueError("decision confirmation token mismatch")
    if payload.get("authority_status") == "operator_accepted":
        raise ValueError("decision is already operator_accepted")
    if not operator.strip():
        raise ValueError("operator is required")

    payload["operator"] = operator.strip()
    payload["authority_status"] = "operator_accepted"
    payload["decision_status"] = "recorded"
    payload["accepted_utc"] = utc_now()
    payload["status"] = "closed"
    path = write_record(record_root, "decisions", f"{preview_id}.json", payload)
    return DecisionResult(
        created=True,
        path=str(path),
        decision=payload,
        authority_status="operator_accepted",
    )


def list_decisions(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "decisions"):
        rows.append(
            {
                "path": str(path),
                "decision_id": payload.get("decision_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "scope": payload.get("scope", ""),
                "decision": payload.get("decision", ""),
                "decision_status": payload.get("decision_status", ""),
                "authority_status": payload.get("authority_status", "unknown"),
                "target_id": payload.get("target_id", ""),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["decision_id"]))


def load_decision(decision_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "decisions", decision_id)
