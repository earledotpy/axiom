from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.core.noop_task_executor import (
    NoopTaskExecutionError,
    _get_task,
    complete_running_noop_task,
)
from axiom.core.scheduler import Scheduler


TERMINAL_TICK_STATUSES = {
    "blocked",
    "idle",
    "running",
    "error",
}


@dataclass(frozen=True)
class SchedulerLoopResult:
    session_id: int
    profile_label: str
    ticks_requested: int
    ticks_run: int
    stopped_reason: str
    final_tick_status: str | None
    tick_results: list[dict[str, Any]]
    execution_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "profile_label": self.profile_label,
            "ticks_requested": self.ticks_requested,
            "ticks_run": self.ticks_run,
            "stopped_reason": self.stopped_reason,
            "final_tick_status": self.final_tick_status,
            "tick_results": self.tick_results,
            "execution_result": self.execution_result,
        }


def _complete_manual_noop_task(task_id: int) -> dict[str, Any]:
    task = _get_task(task_id)

    if task["task_type"] != "manual_noop":
        raise NoopTaskExecutionError(
            "Automatic execution only authorized for manual_noop tasks"
        )

    return complete_running_noop_task(task_id).to_dict()


def run_scheduler_loop(
    session_id: int,
    profile_label: str = "default",
    max_ticks: int = 1,
    allow_when_autonomous_blocked: bool = False,
) -> SchedulerLoopResult:
    """
    Run a bounded, foreground-only scheduler loop.

    This is not a background service. It delegates one tick at a time to
    Scheduler.run_once(), completes dispatched manual_noop tasks in-process,
    and stops as soon as the scheduler reports an unhandled terminal condition.
    """
    if max_ticks < 1:
        raise ValueError("max_ticks must be >= 1")

    scheduler = Scheduler()
    tick_results: list[dict[str, Any]] = []
    execution_result: dict[str, Any] | None = None
    final_tick_status: str | None = None
    stopped_reason = "max_ticks_reached"

    for _ in range(max_ticks):
        result = scheduler.run_once(
            session_id=session_id,
            profile_label=profile_label,
            allow_when_autonomous_blocked=allow_when_autonomous_blocked,
        )

        payload = result.to_dict()
        if result.dispatched_task_id is not None:
            execution_result = _complete_manual_noop_task(result.dispatched_task_id)
            payload["execution_result"] = execution_result

        tick_results.append(payload)

        final_tick_status = payload.get("tick_status") or payload.get("status")

        if final_tick_status in TERMINAL_TICK_STATUSES and not (
            final_tick_status == "running" and "execution_result" in payload
        ):
            stopped_reason = final_tick_status
            break

    return SchedulerLoopResult(
        session_id=session_id,
        profile_label=profile_label,
        ticks_requested=max_ticks,
        ticks_run=len(tick_results),
        stopped_reason=stopped_reason,
        final_tick_status=final_tick_status,
        tick_results=tick_results,
        execution_result=execution_result,
    )
