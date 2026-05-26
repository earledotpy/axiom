from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from axiom.persistence.db import get_connection

ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = ROOT / "tools"


@dataclass(frozen=True)
class ToolCheck:
    name: str
    passed: bool
    reason: str
    returncode: int
    command: list[str]
    output: str


@dataclass(frozen=True)
class ExecutionReadinessResult:
    ready: bool
    session_id: int | None
    lifecycle_audit: ToolCheck
    execution_audit: ToolCheck
    supervisor_health: ToolCheck
    pending_manifest_bound_task_count: int
    running_task_count: int
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


CheckRunner = Callable[[str, list[str]], ToolCheck]


def _combined_output(stdout: str, stderr: str) -> str:
    output = "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)
    return output.strip()


def _output_has_true(output: str, key: str) -> bool:
    normalized = output.replace("`", "")
    return f"{key}: True" in normalized or f"{key}=True" in normalized


def _output_has_false(output: str, key: str) -> bool:
    normalized = output.replace("`", "")
    return f"{key}: False" in normalized or f"{key}=False" in normalized


def _default_runner(script_name: str, args: list[str]) -> ToolCheck:
    script_path = TOOLS_DIR / script_name
    command = [sys.executable, str(script_path), *args]

    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    output = _combined_output(completed.stdout, completed.stderr)
    passed = completed.returncode == 0

    if script_name == "audit_task_lifecycle.py":
        passed = passed and _output_has_true(output, "passed") and not _output_has_false(output, "passed")
    elif script_name == "audit_task_execution.py":
        passed = passed and _output_has_true(output, "passed") and not _output_has_false(output, "passed")
    elif script_name == "supervisor_health_check.py":
        passed = (
            passed
            and _output_has_true(output, "healthy")
            and "supervisor_health_ok" in output
            and not _output_has_false(output, "healthy")
        )

    reason = "passed" if passed else "tool_check_failed"

    return ToolCheck(
        name=script_name,
        passed=passed,
        reason=reason,
        returncode=completed.returncode,
        command=command,
        output=output,
    )


def get_latest_session_id() -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY session_id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None

    return int(row["session_id"])


def count_running_tasks(session_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE session_id = ?
              AND status = 'running'
            """,
            (session_id,),
        ).fetchone()

    return int(row["count"])


def count_pending_manifest_bound_tasks(session_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE session_id = ?
              AND status = 'pending'
              AND manifest_id IS NOT NULL
            """,
            (session_id,),
        ).fetchone()

    return int(row["count"])


def skipped_check(name: str, reason: str) -> ToolCheck:
    return ToolCheck(
        name=name,
        passed=False,
        reason=reason,
        returncode=0,
        command=[],
        output="",
    )


def evaluate_execution_readiness(
    session_id: int | None = None,
    check_runner: CheckRunner | None = None,
) -> ExecutionReadinessResult:
    runner = check_runner or _default_runner
    resolved_session_id = session_id if session_id is not None else get_latest_session_id()

    if resolved_session_id is None:
        reasons = ["no_latest_session"]
        return ExecutionReadinessResult(
            ready=False,
            session_id=None,
            lifecycle_audit=skipped_check("audit_task_lifecycle.py", "no_latest_session"),
            execution_audit=skipped_check("audit_task_execution.py", "no_latest_session"),
            supervisor_health=skipped_check("supervisor_health_check.py", "no_latest_session"),
            pending_manifest_bound_task_count=0,
            running_task_count=0,
            reasons=reasons,
        )

    lifecycle_audit = runner("audit_task_lifecycle.py", [])
    execution_audit = runner("audit_task_execution.py", [])
    supervisor_health = runner("supervisor_health_check.py", [str(resolved_session_id)])

    pending_manifest_bound_task_count = count_pending_manifest_bound_tasks(resolved_session_id)
    running_task_count = count_running_tasks(resolved_session_id)

    reasons: list[str] = []

    if not lifecycle_audit.passed:
        reasons.append("lifecycle_audit_not_clean")

    if not execution_audit.passed:
        reasons.append("execution_audit_not_clean")

    if not supervisor_health.passed:
        reasons.append("supervisor_health_not_clean")

    if running_task_count != 0:
        reasons.append("running_tasks_present")

    if pending_manifest_bound_task_count < 1:
        reasons.append("no_pending_manifest_bound_task")

    ready = len(reasons) == 0

    return ExecutionReadinessResult(
        ready=ready,
        session_id=resolved_session_id,
        lifecycle_audit=lifecycle_audit,
        execution_audit=execution_audit,
        supervisor_health=supervisor_health,
        pending_manifest_bound_task_count=pending_manifest_bound_task_count,
        running_task_count=running_task_count,
        reasons=reasons,
    )