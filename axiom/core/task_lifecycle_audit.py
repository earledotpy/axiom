from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


@dataclass(frozen=True)
class TaskLifecycleViolation:
    code: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskLifecycleAuditResult:
    passed: bool
    session_id: int | None
    violations: list[TaskLifecycleViolation]
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "session_id": self.session_id,
            "violations": [violation.to_dict() for violation in self.violations],
            "details": self.details,
        }


def _latest_session_id() -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY session_id DESC
            LIMIT 1
            """
        ).fetchone()

    return int(row["session_id"]) if row is not None else None


def _session_filter_sql(session_id: int | None) -> tuple[str, tuple[Any, ...]]:
    if session_id is None:
        return "", ()
    return "WHERE session_id = ?", (session_id,)


def audit_running_task_count(session_id: int | None) -> list[TaskLifecycleViolation]:
    where_sql, params = _session_filter_sql(session_id)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT session_id, COUNT(*) AS running_count
            FROM tasks
            {where_sql}
            GROUP BY session_id
            HAVING SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) > 1
            """,
            params,
        ).fetchall()

    violations: list[TaskLifecycleViolation] = []
    for row in rows:
        violations.append(
            TaskLifecycleViolation(
                code="multiple_running_tasks",
                reason="More than one task is running in the same session.",
                details={
                    "session_id": int(row["session_id"]),
                    "running_count": int(row["running_count"]),
                },
            )
        )

    return violations


def audit_running_tasks_have_manifest(session_id: int | None) -> list[TaskLifecycleViolation]:
    where_clause = "WHERE status = 'running' AND manifest_id IS NULL"
    params: tuple[Any, ...] = ()

    if session_id is not None:
        where_clause += " AND session_id = ?"
        params = (session_id,)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT task_id, session_id, chain_id, task_class, task_type, status
            FROM tasks
            {where_clause}
            ORDER BY task_id
            """,
            params,
        ).fetchall()

    return [
        TaskLifecycleViolation(
            code="running_task_missing_manifest",
            reason="Running task lacks required manifest_id binding.",
            details=dict(row),
        )
        for row in rows
    ]


def audit_heartbeat_active_task_coherence(
    session_id: int | None,
) -> list[TaskLifecycleViolation]:
    """
    Audit current scheduler heartbeat coherence.

    Historical heartbeat rows are an event trail. A past heartbeat may point to
    a task that was running at that time and later completed. Therefore this
    check evaluates only the latest heartbeat per session.
    """
    params: tuple[Any, ...] = ()

    if session_id is not None:
        session_filter = "WHERE h.session_id = ?"
        params = (session_id,)
    else:
        session_filter = ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT h.heartbeat_id, h.session_id, h.active_task_id,
                   t.status AS active_task_status,
                   h.last_freshness_at,
                   h.last_tick_started_at,
                   h.last_tick_completed_at
            FROM scheduler_heartbeat h
            LEFT JOIN tasks t
              ON h.active_task_id = t.task_id
            INNER JOIN (
                SELECT session_id, MAX(heartbeat_id) AS latest_heartbeat_id
                FROM scheduler_heartbeat
                GROUP BY session_id
            ) latest
              ON latest.session_id = h.session_id
             AND latest.latest_heartbeat_id = h.heartbeat_id
            {session_filter}
            ORDER BY h.heartbeat_id DESC
            """,
            params,
        ).fetchall()

    violations: list[TaskLifecycleViolation] = []

    for row in rows:
        active_task_id = row["active_task_id"]
        active_task_status = row["active_task_status"]

        if active_task_id is not None and active_task_status is None:
            violations.append(
                TaskLifecycleViolation(
                    code="heartbeat_active_task_missing",
                    reason="Latest scheduler heartbeat points to a missing active_task_id.",
                    details=dict(row),
                )
            )

        if active_task_id is not None and active_task_status != "running":
            violations.append(
                TaskLifecycleViolation(
                    code="heartbeat_active_task_not_running",
                    reason=(
                        "Latest scheduler heartbeat active_task_id does not "
                        "reference a running task."
                    ),
                    details=dict(row),
                )
            )

        started = row["last_tick_started_at"]
        completed = row["last_tick_completed_at"]

        if completed is not None and started is not None and completed < started:
            violations.append(
                TaskLifecycleViolation(
                    code="heartbeat_tick_completed_before_started",
                    reason="Latest scheduler heartbeat tick completion precedes tick start.",
                    details=dict(row),
                )
            )

    return violations


def audit_task_lifecycle(
    session_id: int | None = None,
    latest_session: bool = False,
) -> TaskLifecycleAuditResult:
    effective_session_id = _latest_session_id() if latest_session else session_id

    violations: list[TaskLifecycleViolation] = []
    violations.extend(audit_running_task_count(effective_session_id))
    violations.extend(audit_running_tasks_have_manifest(effective_session_id))
    violations.extend(audit_heartbeat_active_task_coherence(effective_session_id))

    return TaskLifecycleAuditResult(
        passed=len(violations) == 0,
        session_id=effective_session_id,
        violations=violations,
        details={
            "checks": [
                "multiple_running_tasks",
                "running_task_missing_manifest",
                "heartbeat_active_task_coherence",
            ],
        },
    )