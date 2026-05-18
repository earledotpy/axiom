from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from axiom.persistence.db import get_connection


NOOP_EXECUTOR_NAME = "noop_task_executor"
FORBIDDEN_SIDE_EFFECT_KEYS = {
    "tools_used",
    "model_calls",
    "network_calls",
    "sandbox_calls",
}


@dataclass(frozen=True)
class TaskExecutionAuditViolation:
    task_id: int
    session_id: int
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass(frozen=True)
class TaskExecutionAuditResult:
    passed: bool
    scope: str
    session_id: int | None
    checked_task_count: int
    violations: list[TaskExecutionAuditViolation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "scope": self.scope,
            "session_id": self.session_id,
            "checked_task_count": self.checked_task_count,
            "violations": [violation.to_dict() for violation in self.violations],
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


def _load_noop_candidate_tasks(
    session_id: int | None,
    all_sessions: bool,
) -> list[dict[str, Any]]:
    where = """
    (
        task_type = 'noop_executor_test'
        OR result_json LIKE '%noop_task_executor%'
    )
    """

    params: tuple[Any, ...] = ()

    if not all_sessions:
        if session_id is None:
            return []
        where = f"session_id = ? AND {where}"
        params = (session_id,)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT task_id, session_id, task_class, task_type, status,
                   manifest_id, result_text, result_json, started_at,
                   completed_at
            FROM tasks
            WHERE {where}
            ORDER BY session_id, task_id
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]


def _parse_result_json(task: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    raw = task.get("result_json")
    if raw is None:
        return None, "missing_result_json"

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"invalid_result_json:{exc.msg}"

    if not isinstance(parsed, dict):
        return None, "result_json_not_object"

    return parsed, None


def _audit_task(task: dict[str, Any]) -> list[TaskExecutionAuditViolation]:
    violations: list[TaskExecutionAuditViolation] = []

    task_id = int(task["task_id"])
    session_id = int(task["session_id"])
    status = task["status"]

    if status == "running":
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason="noop_execution_task_still_running",
                details={"task_type": task["task_type"]},
            )
        )
        return violations

    if status != "completed":
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason="noop_execution_task_not_completed",
                details={"status": status},
            )
        )
        return violations

    if not task.get("result_text"):
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason="missing_result_text",
            )
        )

    parsed, error = _parse_result_json(task)
    if error is not None:
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason=error,
            )
        )
        return violations

    assert parsed is not None

    if parsed.get("executor") != NOOP_EXECUTOR_NAME:
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason="unexpected_executor",
                details={"executor": parsed.get("executor")},
            )
        )

    if parsed.get("side_effects") != "none":
        violations.append(
            TaskExecutionAuditViolation(
                task_id=task_id,
                session_id=session_id,
                reason="unexpected_side_effects",
                details={"side_effects": parsed.get("side_effects")},
            )
        )

    for key in FORBIDDEN_SIDE_EFFECT_KEYS:
        value = parsed.get(key)
        if value not in ([], None):
            violations.append(
                TaskExecutionAuditViolation(
                    task_id=task_id,
                    session_id=session_id,
                    reason=f"forbidden_{key}_claimed",
                    details={key: value},
                )
            )

    return violations


def audit_task_execution(all_sessions: bool = False) -> TaskExecutionAuditResult:
    session_id = None if all_sessions else _latest_session_id()
    tasks = _load_noop_candidate_tasks(session_id=session_id, all_sessions=all_sessions)

    violations: list[TaskExecutionAuditViolation] = []
    for task in tasks:
        violations.extend(_audit_task(task))

    return TaskExecutionAuditResult(
        passed=len(violations) == 0,
        scope="all_sessions" if all_sessions else "latest_session",
        session_id=session_id,
        checked_task_count=len(tasks),
        violations=violations,
    )