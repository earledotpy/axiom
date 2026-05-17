from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.scheduler import (
    check_one_running_task_invariant,
    get_latest_scheduler_heartbeat,
    is_scheduler_heartbeat_stale,
)
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import log_security_event


@dataclass(frozen=True)
class SupervisorHealth:
    healthy: bool
    session_id: int
    scheduler_stale: bool
    running_task_invariant_valid: bool
    running_count: int
    reason: str
    latest_heartbeat: dict | None
    active_task_present: bool = False
    active_task_status: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupervisorMonitor:
    """
    Passive supervisor monitor.

    It observes scheduler freshness, task concurrency invariants, and latest
    heartbeat active-task coherence. It does not dispatch work, execute tools,
    or mutate task state.
    """

    def __init__(self, stale_threshold_seconds: int = 120):
        if stale_threshold_seconds <= 0:
            raise ValueError("stale_threshold_seconds must be positive")
        self.stale_threshold_seconds = stale_threshold_seconds

    def _active_task_status(self, active_task_id: int | None) -> str | None:
        if active_task_id is None:
            return None

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT status
                FROM tasks
                WHERE task_id = ?
                """,
                (active_task_id,),
            ).fetchone()

        return row["status"] if row is not None else None

    def check_session_health(self, session_id: int) -> SupervisorHealth:
        latest = get_latest_scheduler_heartbeat(session_id)
        stale = is_scheduler_heartbeat_stale(
            session_id,
            threshold_seconds=self.stale_threshold_seconds,
        )
        invariant = check_one_running_task_invariant(session_id)

        active_task_id = None
        active_task_status = None
        active_task_present = False

        if latest is not None:
            active_task_id = latest.get("active_task_id")
            active_task_present = active_task_id is not None
            active_task_status = self._active_task_status(active_task_id)

        if stale:
            log_security_event(
                session_id=session_id,
                event_type="supervisor_scheduler_stale",
                severity="warning",
                reason="scheduler_heartbeat_stale_or_missing",
                details={
                    "stale_threshold_seconds": self.stale_threshold_seconds,
                    "latest_heartbeat": latest,
                },
            )

            return SupervisorHealth(
                healthy=False,
                session_id=session_id,
                scheduler_stale=True,
                running_task_invariant_valid=invariant.valid,
                running_count=invariant.running_count,
                reason="scheduler_heartbeat_stale_or_missing",
                latest_heartbeat=latest,
                active_task_present=active_task_present,
                active_task_status=active_task_status,
                details={
                    "stale_threshold_seconds": self.stale_threshold_seconds,
                },
            )

        if not invariant.valid:
            log_security_event(
                session_id=session_id,
                event_type="supervisor_running_task_invariant_failed",
                severity="critical",
                reason=invariant.reason,
                details={
                    "running_count": invariant.running_count,
                },
            )

            return SupervisorHealth(
                healthy=False,
                session_id=session_id,
                scheduler_stale=False,
                running_task_invariant_valid=False,
                running_count=invariant.running_count,
                reason=invariant.reason,
                latest_heartbeat=latest,
                active_task_present=active_task_present,
                active_task_status=active_task_status,
            )

        if active_task_present and active_task_status is None:
            log_security_event(
                session_id=session_id,
                event_type="supervisor_active_task_missing",
                severity="critical",
                reason="heartbeat_active_task_missing",
                details={
                    "active_task_id": active_task_id,
                    "latest_heartbeat": latest,
                },
            )

            return SupervisorHealth(
                healthy=False,
                session_id=session_id,
                scheduler_stale=False,
                running_task_invariant_valid=True,
                running_count=invariant.running_count,
                reason="heartbeat_active_task_missing",
                latest_heartbeat=latest,
                active_task_present=True,
                active_task_status=None,
                details={
                    "active_task_id": active_task_id,
                },
            )

        if active_task_present and active_task_status != "running":
            log_security_event(
                session_id=session_id,
                event_type="supervisor_active_task_not_running",
                severity="critical",
                reason="heartbeat_active_task_not_running",
                details={
                    "active_task_id": active_task_id,
                    "active_task_status": active_task_status,
                    "latest_heartbeat": latest,
                },
            )

            return SupervisorHealth(
                healthy=False,
                session_id=session_id,
                scheduler_stale=False,
                running_task_invariant_valid=True,
                running_count=invariant.running_count,
                reason="heartbeat_active_task_not_running",
                latest_heartbeat=latest,
                active_task_present=True,
                active_task_status=active_task_status,
                details={
                    "active_task_id": active_task_id,
                },
            )

        if active_task_present and active_task_status == "running":
            return SupervisorHealth(
                healthy=True,
                session_id=session_id,
                scheduler_stale=False,
                running_task_invariant_valid=True,
                running_count=invariant.running_count,
                reason="supervisor_health_ok_active_task_running",
                latest_heartbeat=latest,
                active_task_present=True,
                active_task_status="running",
                details={
                    "active_task_id": active_task_id,
                },
            )

        return SupervisorHealth(
            healthy=True,
            session_id=session_id,
            scheduler_stale=False,
            running_task_invariant_valid=True,
            running_count=invariant.running_count,
            reason="supervisor_health_ok",
            latest_heartbeat=latest,
            active_task_present=False,
            active_task_status=None,
        )