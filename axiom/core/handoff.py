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

HANDOFF_SCHEMA = "axiom.handoff.v0.1"
ROLE_TO_PROCESS_FUNCTION = {
    "ARCH": ("architect", "plan"),
    "IMPL": ("implement", "build"),
    "AUD": ("audit", "verify"),
    "CURSOR": ("synthesize", "summarize"),
    "SYN": ("synthesize", "summarize"),
}


@dataclass(frozen=True)
class HandoffCreateResult:
    created: bool
    path: str
    handoff: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_handoff(
    *,
    title: str,
    scope: str,
    artifact_type: str = "synthesis",
    actor_role: str = "CURSOR",
    summary: str = "",
    source_refs: Iterable[str] = (),
    findings: Iterable[str] = (),
    blocking_objections: Iterable[str] = (),
    non_blocking_concerns: Iterable[str] = (),
    recommended_operator_decision: str = "",
    recommended_next_action: str = "review handoff",
) -> dict[str, Any]:
    if not title.strip():
        raise ValueError("title is required")
    if not scope.strip():
        raise ValueError("scope is required")
    actor_role = actor_role.strip().upper() or "CURSOR"
    if actor_role == "SYN":
        actor_role = "CURSOR"
    process, function = ROLE_TO_PROCESS_FUNCTION.get(actor_role, ("synthesize", "summarize"))
    return {
        "schema": HANDOFF_SCHEMA,
        "artifact_id": f"HND-{id_timestamp()}-{slug(scope)}",
        "created_utc": utc_now(),
        "authority_status": "advisory_only",
        "title": title.strip(),
        "scope": scope.strip(),
        "artifact_type": artifact_type.strip() or "synthesis",
        "actor_role": actor_role,
        "process": process,
        "function": function,
        "summary": summary.strip(),
        "source_refs": unique(source_refs),
        "findings": unique(findings),
        "blocking_objections": unique(blocking_objections),
        "non_blocking_concerns": unique(non_blocking_concerns),
        "recommended_operator_decision": recommended_operator_decision.strip(),
        "recommended_next_action": recommended_next_action.strip() or "review handoff",
        "status": "active",
        "lifecycle_state": artifact_type.strip() or "handoff",
    }


def create_handoff(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> HandoffCreateResult:
    payload = build_handoff(**kwargs)
    path = write_record(record_root, "handoffs", f"{payload['artifact_id']}.json", payload)
    return HandoffCreateResult(created=True, path=str(path), handoff=payload)


def list_handoffs(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "handoffs"):
        rows.append(
            {
                "path": str(path),
                "artifact_id": payload.get("artifact_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "title": payload.get("title", ""),
                "scope": payload.get("scope", ""),
                "artifact_type": payload.get("artifact_type", ""),
                "process": payload.get("process", ""),
                "function": payload.get("function", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["artifact_id"]))


def load_handoff(artifact_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "handoffs", artifact_id)
