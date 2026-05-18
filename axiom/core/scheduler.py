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


def write_scheduler_heartbeat(
    session_id: int,
    scheduler_state: str = "running",
    last_action: str = "heartbeat",
    active_task_id: int | None = None,
    active_chain_id: str | None = None,
    blocking_operation_type: str | None = None,
    tick_completed: bool = True,
    blocking_operation_completed: bool = True,
) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 'now') AS now
            """
        ).fetchone()
        now = row["now"]

        cursor = conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id,
             last_freshness_at,
             last_tick_started_at,
             last_tick_completed_at,
             last_blocking_operation_started_at,
             last_blocking_operation_completed_at,
             last_blocking_operation_type,
             active_task_id,
             active_chain_id,
             scheduler_state,
             last_action,
             tick_count,
             created_at,
             updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                session_id,
                now,
                now,
                now if tick_completed else None,
                now,
                now if blocking_operation_completed else None,
                blocking_operation_type,
                active_task_id,
                active_chain_id,
                scheduler_state,
                last_action,
                now,
                now,
            ),
        )

        return int(cursor.lastrowid)


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