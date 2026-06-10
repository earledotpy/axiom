from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from axiom.core.governance_records import (
    DEFAULT_RECORD_ROOT,
    id_timestamp,
    list_records,
    load_record_by_id,
    slug,
    unique,
    utc_now,
    write_record,
)

AUTONOMY_GRANT_SCHEMA = "axiom.autonomy_grant.v0.1"


@dataclass(frozen=True)
class AutonomyGrantResult:
    created: bool
    path: str
    grant: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_autonomy_grant(
    *,
    scope: str,
    autonomy_level: str = "A0",
    allowed_roles: Iterable[str] = (),
    allowed_actions: Iterable[str] = (),
    forbidden_actions: Iterable[str] = (),
    protected_surfaces: Iterable[str] = (),
    required_evidence: Iterable[str] = (),
    stop_conditions: Iterable[str] = (),
    max_cycles: int = 1,
    expires_utc: str = "",
) -> dict[str, Any]:
    if not scope.strip():
        raise ValueError("scope is required")
    return {
        "schema": AUTONOMY_GRANT_SCHEMA,
        "grant_id": f"AGT-{id_timestamp()}-{slug(scope)}",
        "created_utc": utc_now(),
        "operator_decision_id": "",
        "technical_gate_result": "not_evaluated",
        "grant_state": "draft",
        "autonomy_level": autonomy_level.strip() or "A0",
        "scope": scope.strip(),
        "out_of_scope": [],
        "allowed_roles": unique(allowed_roles),
        "allowed_actions": unique(allowed_actions),
        "forbidden_actions": unique(["enable runtime autonomy", "start scheduler or executor", *forbidden_actions]),
        "protected_surfaces": unique(protected_surfaces),
        "required_evidence": unique(required_evidence),
        "stop_conditions": unique(stop_conditions),
        "revocation_conditions": ["Operator revokes grant", "grant expires", "stop condition triggers"],
        "expires_utc": expires_utc,
        "max_cycles": max_cycles,
        "authority_status": "advisory_only",
        "runtime_action_executed": False,
        "ledger_written": False,
        "status": "draft",
        "lifecycle_state": "draft",
    }


def draft_autonomy_grant(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> AutonomyGrantResult:
    payload = build_autonomy_grant(**kwargs)
    path = write_record(record_root, "autonomy", f"{payload['grant_id']}.json", payload)
    return AutonomyGrantResult(created=True, path=str(path), grant=payload)


def accept_autonomy_grant(
    *,
    grant_id: str,
    operator_decision_id: str,
    technical_gate_result: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> AutonomyGrantResult:
    payload = load_record_by_id(record_root, "autonomy", grant_id)
    decision = load_record_by_id(record_root, "decisions", operator_decision_id)
    if decision.get("authority_status") != "operator_accepted":
        raise ValueError("accepted autonomy grant requires operator_accepted decision")
    if technical_gate_result != "passed":
        raise ValueError("accepted autonomy grant requires passed technical gate")
    payload["operator_decision_id"] = operator_decision_id
    payload["technical_gate_result"] = "passed"
    payload["grant_state"] = "operator_accepted"
    payload["authority_status"] = "operator_accepted"
    payload["status"] = "operator_accepted"
    payload["lifecycle_state"] = "operator_accepted"
    payload["accepted_utc"] = utc_now()
    payload["runtime_action_executed"] = False
    path = write_record(record_root, "autonomy", f"{grant_id}.json", payload)
    return AutonomyGrantResult(created=True, path=str(path), grant=payload, authority_status="operator_accepted")


def revoke_autonomy_grant(
    *,
    grant_id: str,
    reason: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> AutonomyGrantResult:
    payload = load_record_by_id(record_root, "autonomy", grant_id)
    payload["grant_state"] = "revoked"
    payload["status"] = "revoked"
    payload["lifecycle_state"] = "revoked"
    payload["revoked_reason"] = reason.strip() or "revoked"
    payload["revoked_utc"] = utc_now()
    payload["runtime_action_executed"] = False
    path = write_record(record_root, "autonomy", f"{grant_id}.json", payload)
    return AutonomyGrantResult(created=True, path=str(path), grant=payload, authority_status=str(payload.get("authority_status", "advisory_only")))


def list_autonomy_grants(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "autonomy"):
        rows.append(
            {
                "path": str(path),
                "grant_id": payload.get("grant_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "scope": payload.get("scope", ""),
                "autonomy_level": payload.get("autonomy_level", ""),
                "grant_state": payload.get("grant_state", ""),
                "technical_gate_result": payload.get("technical_gate_result", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["grant_id"]))


def load_autonomy_grant(grant_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "autonomy", grant_id)
