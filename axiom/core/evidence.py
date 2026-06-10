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

EVIDENCE_SCHEMA = "axiom.evidence.v0.1"


@dataclass(frozen=True)
class EvidenceCreateResult:
    created: bool
    path: str
    evidence: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "evidence_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evidence(
    *,
    scope: str,
    evidence_type: str = "implementation_evidence",
    files_changed: Iterable[str] = (),
    commands_run: Iterable[str] = (),
    verification_results: Iterable[str] = (),
    skipped_checks: Iterable[str] = (),
    assumptions: Iterable[str] = (),
    known_risks: Iterable[str] = (),
    evidence_quality: str = "not_evaluated",
    recommended_next_action: str = "review evidence",
) -> dict[str, Any]:
    if not scope.strip():
        raise ValueError("scope is required")
    return {
        "schema": EVIDENCE_SCHEMA,
        "evidence_id": f"EVI-{id_timestamp()}-{slug(scope)}",
        "created_utc": utc_now(),
        "authority_status": "evidence_only",
        "scope": scope.strip(),
        "evidence_type": evidence_type.strip() or "implementation_evidence",
        "files_changed": unique(files_changed),
        "commands_run": unique(commands_run),
        "verification_results": unique(verification_results),
        "skipped_checks": unique(skipped_checks),
        "assumptions": unique(assumptions),
        "known_risks": unique(known_risks),
        "evidence_quality": evidence_quality.strip() or "not_evaluated",
        "recommended_next_action": recommended_next_action.strip() or "review evidence",
        "status": "active",
        "lifecycle_state": "implementation_evidence",
    }


def create_evidence(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> EvidenceCreateResult:
    payload = build_evidence(**kwargs)
    path = write_record(record_root, "evidence", f"{payload['evidence_id']}.json", payload)
    return EvidenceCreateResult(created=True, path=str(path), evidence=payload)


def list_evidence(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "evidence"):
        rows.append(
            {
                "path": str(path),
                "evidence_id": payload.get("evidence_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "scope": payload.get("scope", ""),
                "evidence_type": payload.get("evidence_type", ""),
                "evidence_quality": payload.get("evidence_quality", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["evidence_id"]))


def load_evidence(evidence_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "evidence", evidence_id)
