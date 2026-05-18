from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.core.noop_task_executor import complete_running_noop_task
from axiom.core.scheduler import Scheduler
from axiom.core.task_execution_audit import audit_task_execution
from axiom.persistence.db import get_connection


class ManualNoopCycleError(RuntimeError):
    pass


@dataclass(frozen=True)
class ManualNoopCycleResult:
    session_id: int
    profile_label: str
    scheduler_tick: dict[str, Any]
    task_id: int | None
    executed: bool
    execution_result: dict[str, Any] | None
    execution_audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "profile_label": self.profile_label,
            "scheduler_tick": self.scheduler_tick,
            "task_id": self.task_id,
            "executed": self.executed,
            "execution_result": self.execution_result,
            "execution_audit": self.execution_audit,
        }


def _latest_running_task_id(session_id: int) -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE session_id = ? AND status = 'running'
            ORDER BY task_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    return int(row["task_id"]) if row is not None else None


def _extract_task_id_from_tick(tick_payload: dict[str, Any]) -> int | None:
    for key in ("task_id", "dispatched_task_id", "started_task_id"):
        value = tick_payload.get(key)
        if value is not None:
            return int(value)

    dispatch_result = tick_payload.get("dispatch_result")
    if isinstance(dispatch_result, dict):
        value = dispatch_result.get("task_id")
        if value is not None:
            return int(value)

    return None


def run_manual_noop_cycle(
    session_id: int,
    profile_label: str = "default",
    allow_when_autonomous_blocked: bool = False,
) -> ManualNoopCycleResult:
    """
    Run one explicit manual/test no-op execution cycle.

    This function:
    1. Runs Scheduler.run_once().
    2. Finds the dispatched/running task.
    3. Completes it through execute_noop_task().
    4. Runs task execution audit.

    It does not call tools, models, network, sandbox, Telegram, or agents.
    """
    if not allow_when_autonomous_blocked:
        raise ManualNoopCycleError(
            "Manual no-op cycle requires explicit allow_when_autonomous_blocked=True "
            "while AXIOM remains fail-closed non-autonomous."
        )

    tick = Scheduler().run_once(
        session_id=session_id,
        profile_label=profile_label,
        allow_when_autonomous_blocked=allow_when_autonomous_blocked,
    )

    tick_payload = tick.to_dict()
    tick_status = tick_payload.get("tick_status") or tick_payload.get("status")

    if tick_status == "blocked":
        audit = audit_task_execution(all_sessions=False).to_dict()
        return ManualNoopCycleResult(
            session_id=session_id,
            profile_label=profile_label,
            scheduler_tick=tick_payload,
            task_id=None,
            executed=False,
            execution_result=None,
            execution_audit=audit,
        )

    task_id = _extract_task_id_from_tick(tick_payload)
    if task_id is None:
        task_id = _latest_running_task_id(session_id)

    if task_id is None:
        audit = audit_task_execution(all_sessions=False).to_dict()
        return ManualNoopCycleResult(
            session_id=session_id,
            profile_label=profile_label,
            scheduler_tick=tick_payload,
            task_id=None,
            executed=False,
            execution_result=None,
            execution_audit=audit,
        )

    execution = complete_running_noop_task(task_id)
    audit = audit_task_execution(all_sessions=False).to_dict()

    return ManualNoopCycleResult(
        session_id=session_id,
        profile_label=profile_label,
        scheduler_tick=tick_payload,
        task_id=task_id,
        executed=True,
        execution_result=execution.to_dict(),
        execution_audit=audit,
    )