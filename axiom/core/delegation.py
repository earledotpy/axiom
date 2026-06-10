from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DELEGATION_SCHEMA = "axiom.delegation_packet.v0.1"
DEFAULT_RECORD_ROOT = ROOT / "governance" / "80_records"

DEFAULT_FORBIDDEN_ACTIONS = (
    "convert advisory output into binding governance",
    "approve mandate candidates",
    "update binding records without accepted decision",
    "change Doctrine without accepted decision",
    "enable runtime autonomy",
    "reactivate IPC execution",
    "alter security gates without accepted mandate",
    "promote models",
    "expand network or tool permissions",
    "bypass parser or manifest validation for /axiom:*",
    "treat native CLI approval as Axiom approval",
)

DEFAULT_STOP_CONDITIONS = (
    "scope ambiguity appears",
    "authority boundary is unclear",
    "required evidence is unavailable",
    "required review is missing",
    "protected surface would be touched without accepted mandate",
    "command or artifact schema is invalid",
    "Doctrine conflict is detected",
    "Workflow transition is not permitted",
    "Transport meaning is ambiguous",
    "runtime, autonomy, IPC, scheduler, executor, model, network, or security posture would change",
)

AGENT_ROLE_TO_PROCESS_FUNCTION = {
    "ARCH": ("architect", "plan"),
    "IMPL": ("implement", "build"),
    "AUD": ("audit", "verify"),
    "CURSOR": ("synthesize", "summarize"),
    "SYN": ("synthesize", "summarize"),
}


@dataclass(frozen=True)
class DelegationPacket:
    schema: str
    delegation_id: str
    created_utc: str
    operator_goal: str
    scope: str
    out_of_scope: list[str]
    authority_status: str
    delegation_context: str
    delegation_type: str
    process: str
    function: str
    allowed_roles: list[str]
    required_reviews: list[str]
    allowed_actions: list[str]
    forbidden_actions: list[str]
    success_criteria: list[str]
    evidence_required: list[str]
    decision_points: list[str]
    stop_conditions: list[str]
    recommended_first_agent: str
    status: str = "active"
    lifecycle_state: str = "delegated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DelegationCreateResult:
    created: bool
    path: str
    packet: dict[str, Any]
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


def _delegation_dir(record_root: Path) -> Path:
    return record_root / "delegations"


def _normalize_agent_role(agent_role: str) -> str:
    role = agent_role.strip().upper() or "CURSOR"
    if role == "SYN":
        return "CURSOR"
    return role


def _resolve_process_function(recommended_first_agent: str) -> tuple[str, str]:
    return AGENT_ROLE_TO_PROCESS_FUNCTION.get(recommended_first_agent, ("route", "route"))


def build_delegation_packet(
    *,
    operator_goal: str,
    scope: str,
    out_of_scope: Iterable[str] = (),
    delegation_type: str = "multi_agent_cycle",
    allowed_roles: Iterable[str] = (),
    required_reviews: Iterable[str] = (),
    allowed_actions: Iterable[str] = (),
    forbidden_actions: Iterable[str] = (),
    success_criteria: Iterable[str] = (),
    evidence_required: Iterable[str] = (),
    decision_points: Iterable[str] = (),
    stop_conditions: Iterable[str] = (),
    recommended_first_agent: str = "CURSOR",
) -> DelegationPacket:
    if not operator_goal.strip():
        raise ValueError("operator_goal is required")
    if not scope.strip():
        raise ValueError("scope is required")

    recommended_first_agent = _normalize_agent_role(recommended_first_agent)
    process, function = _resolve_process_function(recommended_first_agent)
    roles = _unique([*allowed_roles, recommended_first_agent])

    return DelegationPacket(
        schema=DELEGATION_SCHEMA,
        delegation_id=f"DLG-{_id_timestamp()}-{_slug(scope)}",
        created_utc=_utc_now(),
        operator_goal=operator_goal.strip(),
        scope=scope.strip(),
        out_of_scope=_unique(out_of_scope),
        authority_status="advisory_only",
        delegation_context="operator_directed",
        delegation_type=delegation_type.strip() or "multi_agent_cycle",
        process=process,
        function=function,
        allowed_roles=roles,
        required_reviews=_unique(required_reviews),
        allowed_actions=_unique(allowed_actions),
        forbidden_actions=_unique([*DEFAULT_FORBIDDEN_ACTIONS, *forbidden_actions]),
        success_criteria=_unique(success_criteria),
        evidence_required=_unique(evidence_required),
        decision_points=_unique(decision_points),
        stop_conditions=_unique([*DEFAULT_STOP_CONDITIONS, *stop_conditions]),
        recommended_first_agent=recommended_first_agent,
    )


def create_delegation_packet(
    *,
    operator_goal: str,
    scope: str,
    record_root: Path = DEFAULT_RECORD_ROOT,
    out_of_scope: Iterable[str] = (),
    delegation_type: str = "multi_agent_cycle",
    allowed_roles: Iterable[str] = (),
    required_reviews: Iterable[str] = (),
    allowed_actions: Iterable[str] = (),
    forbidden_actions: Iterable[str] = (),
    success_criteria: Iterable[str] = (),
    evidence_required: Iterable[str] = (),
    decision_points: Iterable[str] = (),
    stop_conditions: Iterable[str] = (),
    recommended_first_agent: str = "CURSOR",
) -> DelegationCreateResult:
    packet = build_delegation_packet(
        operator_goal=operator_goal,
        scope=scope,
        out_of_scope=out_of_scope,
        delegation_type=delegation_type,
        allowed_roles=allowed_roles,
        required_reviews=required_reviews,
        allowed_actions=allowed_actions,
        forbidden_actions=forbidden_actions,
        success_criteria=success_criteria,
        evidence_required=evidence_required,
        decision_points=decision_points,
        stop_conditions=stop_conditions,
        recommended_first_agent=recommended_first_agent,
    )
    directory = _delegation_dir(record_root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{packet.delegation_id}.json"
    payload = packet.to_dict()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return DelegationCreateResult(created=True, path=str(path), packet=payload)


def list_delegation_packets(*, record_root: Path = DEFAULT_RECORD_ROOT) -> list[dict[str, Any]]:
    directory = _delegation_dir(record_root)
    if not directory.exists():
        return []

    packets: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            packets.append(
                {
                    "path": str(path),
                    "delegation_id": payload.get("delegation_id", path.stem),
                    "created_utc": payload.get("created_utc", ""),
                    "operator_goal": payload.get("operator_goal", ""),
                    "scope": payload.get("scope", ""),
                    "authority_status": payload.get("authority_status", "unknown"),
                    "delegation_type": payload.get("delegation_type", ""),
                    "process": payload.get("process", ""),
                    "function": payload.get("function", ""),
                    "recommended_first_agent": payload.get("recommended_first_agent", ""),
                    "status": payload.get("status", ""),
                }
            )
    return sorted(packets, key=lambda item: (item["created_utc"], item["delegation_id"]))


def load_delegation_packet(delegation_id: str, *, record_root: Path = DEFAULT_RECORD_ROOT) -> dict[str, Any]:
    directory = _delegation_dir(record_root)
    path = directory / f"{delegation_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"delegation packet not found: {delegation_id}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"delegation packet root is not an object: {delegation_id}")
    return payload
