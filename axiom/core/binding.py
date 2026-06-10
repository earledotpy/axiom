from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from axiom.core.governance_records import (
    DEFAULT_RECORD_ROOT,
    id_timestamp,
    list_records,
    load_record_by_id,
    slug,
    utc_now,
    write_record,
)

BINDING_SCHEMA = "axiom.binding.v0.1"


@dataclass(frozen=True)
class BindingResult:
    created: bool
    path: str
    binding: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "binding"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_binding(
    *,
    operator_decision_id: str,
    binding_type: str,
    target: str,
    scope: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
    summary: str = "",
) -> dict[str, Any]:
    decision = load_record_by_id(record_root, "decisions", operator_decision_id)
    if decision.get("authority_status") != "operator_accepted":
        raise ValueError("binding requires operator_accepted decision")
    if decision.get("decision") != "approve":
        raise ValueError("binding requires approve decision")
    if not binding_type.strip():
        raise ValueError("binding_type is required")
    if not target.strip():
        raise ValueError("target is required")
    if not scope.strip():
        raise ValueError("scope is required")

    binding_id = f"BND-{id_timestamp()}-{slug(scope)}"
    return {
        "schema": BINDING_SCHEMA,
        "binding_id": binding_id,
        "created_utc": utc_now(),
        "authority_status": "binding",
        "operator_decision_id": operator_decision_id,
        "binding_type": binding_type.strip(),
        "target": target.strip(),
        "scope": scope.strip(),
        "summary": summary.strip(),
        "binding_state": "active",
        "source_refs": [operator_decision_id],
        "runtime_action_executed": False,
        "ledger_written": False,
        "status": "active",
        "lifecycle_state": "binding_update",
    }


def apply_binding(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> BindingResult:
    payload = build_binding(record_root=record_root, **kwargs)
    path = write_record(record_root, "bindings", f"{payload['binding_id']}.json", payload)
    return BindingResult(created=True, path=str(path), binding=payload)


def list_bindings(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "bindings"):
        rows.append(
            {
                "path": str(path),
                "binding_id": payload.get("binding_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "scope": payload.get("scope", ""),
                "binding_type": payload.get("binding_type", ""),
                "binding_state": payload.get("binding_state", ""),
                "operator_decision_id": payload.get("operator_decision_id", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(rows, key=lambda item: (item["created_utc"], item["binding_id"]))


def load_binding(binding_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "bindings", binding_id)
