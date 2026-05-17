from __future__ import annotations

from dataclasses import dataclass

from axiom.persistence.db import get_connection


@dataclass(frozen=True)
class RunningTaskInvariant:
    valid: bool
    running_count: int
    reason: str


def count_running_tasks(session_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS running_count
            FROM tasks
            WHERE session_id = ? AND status = 'running'
            """,
            (session_id,),
        ).fetchone()

        return int(row["running_count"])


def check_one_running_task_invariant(session_id: int) -> RunningTaskInvariant:
    running_count = count_running_tasks(session_id)

    if running_count <= 1:
        return RunningTaskInvariant(
            valid=True,
            running_count=running_count,
            reason="one_running_task_invariant_satisfied",
        )

    return RunningTaskInvariant(
        valid=False,
        running_count=running_count,
        reason="multiple_running_tasks_detected",
    )


def write_scheduler_heartbeat(session_id: int, scheduler_state: str = "running") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, scheduler_state, last_freshness_at, last_action)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), ?)
            """,
            (session_id, scheduler_state, "heartbeat"),
        )
        return int(cur.lastrowid)


def get_latest_scheduler_heartbeat(session_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM scheduler_heartbeat
            WHERE session_id = ?
            ORDER BY last_freshness_at DESC, heartbeat_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

        return dict(row) if row else None


def is_scheduler_heartbeat_stale(session_id: int, threshold_seconds: int = 120) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN 1
                    WHEN (
                        julianday('now') - julianday(MAX(last_freshness_at))
                    ) * 86400.0 > ? THEN 1
                    ELSE 0
                END AS stale
            FROM scheduler_heartbeat
            WHERE session_id = ?
            """,
            (threshold_seconds, session_id),
        ).fetchone()

        return bool(row["stale"])


class Scheduler:
    """
    Conservative single-step scheduler facade.

    This class intentionally does not start a loop or thread. It exposes one
    run_once() method that delegates to scheduler_tick, preserving fail-closed
    autonomous-readiness behavior by default.
    """

    def run_once(
        self,
        session_id: int,
        profile_label: str = "default",
        allow_when_autonomous_blocked: bool = False,
    ):
        from axiom.core.scheduler_tick import run_scheduler_tick

        return run_scheduler_tick(
            session_id=session_id,
            profile_label=profile_label,
            allow_when_autonomous_blocked=allow_when_autonomous_blocked,
        )