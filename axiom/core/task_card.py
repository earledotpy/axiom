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

TASK_CARD_SCHEMA = "axiom.task_card.v0.1"
PROCESS_FUNCTION = {
    "scope": "scope",
    "architect": "plan",
    "implement": "build",
    "audit": "verify",
    "synthesize": "summarize",
}

DEFAULT_FORBIDDEN_ACTIONS = (
    "convert advisory output into binding governance",
    "approve mandate candidates",
    "write operator_accepted decision records",
    "update binding records without accepted decision",
    "enable runtime autonomy",
    "reactivate IPC execution",
    "mutate parser, command manifest, or ledger behavior without accepted mandate",
)


@dataclass(frozen=True)
class TaskCardCreateResult:
    created: bool
    path: str
    task_card: dict[str, Any]
    runtime_action_executed: bool = False
    ledger_written: bool = False
    authority_status: str = "advisory_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_task_card(
    *,
    operator_goal: str,
    scope: str,
    risk_class: str = "low",
    process: str = "scope",
    allowed_actions: Iterable[str] = (),
    forbidden_actions: Iterable[str] = (),
    required_outputs: Iterable[str] = (),
    stop_conditions: Iterable[str] = (),
    evidence_required: Iterable[str] = (),
    recommended_next_action: str = "perform scoped advisory work",
) -> dict[str, Any]:
    if not operator_goal.strip():
        raise ValueError("operator_goal is required")
    if not scope.strip():
        raise ValueError("scope is required")
    process = process.strip() or "scope"
    function = PROCESS_FUNCTION.get(process)
    if function is None:
        raise ValueError(f"unknown process: {process}")

    return {
        "schema": TASK_CARD_SCHEMA,
        "task_card_id": f"TC-{id_timestamp()}-{slug(scope)}",
        "created_utc": utc_now(),
        "operator_goal": operator_goal.strip(),
        "scope": scope.strip(),
        "authority_status": "advisory_only",
        "risk_class": risk_class.strip() or "low",
        "path": "lightweight_task_card",
        "process": process,
        "function": function,
        "allowed_actions": unique(allowed_actions),
        "forbidden_actions": unique([*DEFAULT_FORBIDDEN_ACTIONS, *forbidden_actions]),
        "required_outputs": unique(required_outputs),
        "stop_conditions": unique(stop_conditions),
        "evidence_required": unique(evidence_required),
        "recommended_next_action": recommended_next_action.strip() or "perform scoped advisory work",
        "status": "active",
        "lifecycle_state": "proposal",
    }


def create_task_card(*, record_root: Path = DEFAULT_RECORD_ROOT, **kwargs: Any) -> TaskCardCreateResult:
    payload = build_task_card(**kwargs)
    path = write_record(record_root, "tasks", f"{payload['task_card_id']}.json", payload)
    return TaskCardCreateResult(created=True, path=str(path), task_card=payload)


def list_task_cards(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path, payload in list_records(record_root, "tasks"):
        cards.append(
            {
                "path": str(path),
                "task_card_id": payload.get("task_card_id", path.stem),
                "created_utc": payload.get("created_utc", ""),
                "operator_goal": payload.get("operator_goal", ""),
                "scope": payload.get("scope", ""),
                "risk_class": payload.get("risk_class", ""),
                "process": payload.get("process", ""),
                "function": payload.get("function", ""),
                "status": payload.get("status", ""),
                "authority_status": payload.get("authority_status", "unknown"),
            }
        )
    return sorted(cards, key=lambda item: (item["created_utc"], item["task_card_id"]))


def load_task_card(task_card_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    return load_record_by_id(record_root, "tasks", task_card_id)


def close_task_card(task_card_id: str, *, reason: str, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    payload = load_task_card(task_card_id, record_root=record_root)
    payload["status"] = "closed"
    payload["lifecycle_state"] = "closed"
    payload["closed_reason"] = reason.strip() or "closed"
    payload["closed_utc"] = utc_now()
    write_record(record_root, "tasks", f"{task_card_id}.json", payload)
    return payload
