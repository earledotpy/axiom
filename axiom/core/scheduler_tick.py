from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.core.scheduler_dispatcher import dispatch_next_task
from axiom.core.task_lifecycle_audit import audit_task_lifecycle
from tools.repair_session_state import repair_session_state


class SchedulerTickError(RuntimeError):
    pass


@dataclass(frozen=True)
class SchedulerTickResult:
    session_id: int
    tick_status: str
    reason: str
    dispatched_task_id: int | None = None
    heartbeat_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_scheduler_tick(
    session_id: int,
    profile_label: str = "default",
    allow_when_autonomous_blocked: bool = False,
) -> SchedulerTickResult:
    """
    Run one conservative scheduler tick.

    Default behavior is fail-closed:
    - repair latest session state if needed
    - evaluate autonomous readiness
    - audit task lifecycle for the target session
    - refuse dispatch while autonomous readiness is blocked

    allow_when_autonomous_blocked=True is for controlled tests/manual local
    lifecycle verification only. It must not be used for autonomous operation.
    """
    repair_result = repair_session_state(profile_label=profile_label)
    readiness = evaluate_autonomous_readiness(profile_label=profile_label)
    audit = audit_task_lifecycle(session_id=session_id)

    if not audit.passed:
        return SchedulerTickResult(
            session_id=session_id,
            tick_status="blocked",
            reason="task_lifecycle_audit_failed",
            details={
                "repair": repair_result,
                "readiness": readiness.to_dict(),
                "audit": audit.to_dict(),
            },
        )

    if not readiness.allowed and not allow_when_autonomous_blocked:
        return SchedulerTickResult(
            session_id=session_id,
            tick_status="blocked",
            reason="autonomous_not_ready",
            details={
                "repair": repair_result,
                "readiness": readiness.to_dict(),
                "audit": audit.to_dict(),
            },
        )

    dispatch = dispatch_next_task(session_id=session_id)

    if not dispatch.dispatched:
        return SchedulerTickResult(
            session_id=session_id,
            tick_status=dispatch.status,
            reason=dispatch.reason,
            details={
                "repair": repair_result,
                "readiness": readiness.to_dict(),
                "audit": audit.to_dict(),
                "dispatch": dispatch.to_dict(),
                "allow_when_autonomous_blocked": allow_when_autonomous_blocked,
            },
        )

    return SchedulerTickResult(
        session_id=session_id,
        tick_status="running",
        reason="task_dispatched",
        dispatched_task_id=dispatch.task_id,
        heartbeat_id=dispatch.heartbeat_id,
        details={
            "repair": repair_result,
            "readiness": readiness.to_dict(),
            "audit": audit.to_dict(),
            "dispatch": dispatch.to_dict(),
            "allow_when_autonomous_blocked": allow_when_autonomous_blocked,
        },
    )