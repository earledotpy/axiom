from __future__ import annotations

import json
from typing import Any

from axiom.persistence.db import get_connection, init_db
from axiom.core.state_machine import StateMachine


def _json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def create_session(operator_id: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (operator_id) VALUES (?)",
            (operator_id,),
        )
        return int(cur.lastrowid)


def get_session(session_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None


def log_session_event(
    session_id: int,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO session_events (session_id, event_type, details_json)
            VALUES (?, ?, ?)
            """,
            (session_id, event_type, _json_dumps(details)),
        )
        return int(cur.lastrowid)


def log_security_event(
    event_type: str,
    severity: str,
    reason: str | None = None,
    details: dict[str, Any] | None = None,
    session_id: int | None = None,
    task_id: int | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO security_events
            (session_id, task_id, event_type, reason, severity, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, task_id, event_type, reason, severity, _json_dumps(details)),
        )
        return int(cur.lastrowid)


def get_active_manifest_fingerprints() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM manifest_fingerprints
            WHERE active = 1
            ORDER BY manifest_id
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_manifest_fingerprint(manifest_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM manifest_fingerprints
            WHERE manifest_id = ? AND active = 1
            """,
            (manifest_id,),
        ).fetchone()
        return dict(row) if row else None


def create_task(
    session_id: int,
    chain_id: str,
    task_class: str,
    task_type: str,
    priority: int = 5,
    goal_text: str | None = None,
    input_json: dict[str, Any] | None = None,
    manifest_id: str | None = None,
    parent_task_id: int | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks
            (session_id, parent_task_id, chain_id, task_class, task_type, priority,
             goal_text, input_json, manifest_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                parent_task_id,
                chain_id,
                task_class,
                task_type,
                priority,
                goal_text,
                _json_dumps(input_json),
                manifest_id,
            ),
        )
        return int(cur.lastrowid)


def get_task(task_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        return dict(row) if row else None


def update_task_status(
    task_id: int,
    status: str,
    result_text: str | None = None,
    result_json: dict[str, Any] | None = None,
    error_info: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = ?,
                result_text = COALESCE(?, result_text),
                result_json = COALESCE(?, result_json),
                error_info = COALESCE(?, error_info),
                completed_at = CASE
                    WHEN ? IN ('completed', 'failed', 'quarantined', 'cancelled')
                    THEN strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ELSE completed_at
                END
            WHERE task_id = ?
            """,
            (
                status,
                result_text,
                _json_dumps(result_json),
                error_info,
                status,
                task_id,
            ),
        )

def transition_task_status(
    task_id: int,
    next_status: str,
    result_text: str | None = None,
    result_json: dict[str, Any] | None = None,
    error_info: str | None = None,
) -> None:
    task = get_task(task_id)
    if task is None:
        raise ValueError(f"Unknown task_id: {task_id}")

    if next_status == "running":
        from axiom.core.task_committer import TaskCommitter

        TaskCommitter().commit_status(
            task_id=task_id,
            next_status=next_status,
            result_text=result_text,
            result_json=result_json,
            error_info=error_info,
        )
        return

    StateMachine().require_transition(task["status"], next_status)

    update_task_status(
        task_id=task_id,
        status=next_status,
        result_text=result_text,
        result_json=result_json,
        error_info=error_info,
    )
    
    
def record_provider_usage(
    session_id: int,
    provider: str,
    status: str,
    task_id: int | None = None,
    model: str | None = None,
    estimated_input_tokens: int | None = None,
    estimated_output_tokens: int | None = None,
    actual_input_tokens: int | None = None,
    actual_output_tokens: int | None = None,
    actuals_unavailable: int = 0,
    charged_input_estimate: int | None = None,
    charged_output_estimate: int | None = None,
    error_info: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO provider_usage
            (session_id, task_id, provider, model, status,
             estimated_input_tokens, estimated_output_tokens,
             actual_input_tokens, actual_output_tokens, actuals_unavailable,
             charged_input_estimate, charged_output_estimate, error_info,
             completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CASE
                    WHEN ? IN ('completed', 'failed', 'rate_limited', 'quota_exhausted', 'abandoned_session_crash')
                    THEN strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ELSE NULL
                END
            )
            """,
            (
                session_id,
                task_id,
                provider,
                model,
                status,
                estimated_input_tokens,
                estimated_output_tokens,
                actual_input_tokens,
                actual_output_tokens,
                actuals_unavailable,
                charged_input_estimate,
                charged_output_estimate,
                error_info,
                status,
            ),
        )
        return int(cur.lastrowid)
        

def get_provider_usage(usage_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM provider_usage
            WHERE usage_id = ?
            """,
            (usage_id,),
        ).fetchone()

        return dict(row) if row else None


def get_provider_usage_for_task(task_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM provider_usage
            WHERE task_id = ?
            ORDER BY usage_id
            """,
            (task_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_provider_usage_for_session(session_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM provider_usage
            WHERE session_id = ?
            ORDER BY usage_id
            """,
            (session_id,),
        ).fetchall()

        return [dict(row) for row in rows]
        
    
def update_provider_usage_status(
    usage_id: int,
    status: str,
    estimated_input_tokens: int | None = None,
    estimated_output_tokens: int | None = None,
    actual_input_tokens: int | None = None,
    actual_output_tokens: int | None = None,
    actuals_unavailable: int | None = None,
    charged_input_estimate: int | None = None,
    charged_output_estimate: int | None = None,
    error_info: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE provider_usage
            SET status = ?,
                estimated_input_tokens = COALESCE(?, estimated_input_tokens),
                estimated_output_tokens = COALESCE(?, estimated_output_tokens),
                actual_input_tokens = COALESCE(?, actual_input_tokens),
                actual_output_tokens = COALESCE(?, actual_output_tokens),
                actuals_unavailable = COALESCE(?, actuals_unavailable),
                charged_input_estimate = COALESCE(?, charged_input_estimate),
                charged_output_estimate = COALESCE(?, charged_output_estimate),
                error_info = COALESCE(?, error_info),
                completed_at = CASE
                    WHEN ? IN ('completed', 'failed', 'rate_limited', 'quota_exhausted', 'abandoned_session_crash')
                    THEN strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ELSE completed_at
                END
            WHERE usage_id = ?
            """,
            (
                status,
                estimated_input_tokens,
                estimated_output_tokens,
                actual_input_tokens,
                actual_output_tokens,
                actuals_unavailable,
                charged_input_estimate,
                charged_output_estimate,
                error_info,
                status,
                usage_id,
            ),
        )

        
def get_current_model_profile(profile_label: str = "default") -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM model_profile_fingerprints
            WHERE profile_label = ? AND is_current = 1
            """,
            (profile_label,),
        ).fetchone()
        return dict(row) if row else None


def get_passing_calibration_run(calibration_run_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM classifier_calibration_runs
            WHERE calibration_run_id = ?
            """,
            (calibration_run_id,),
        ).fetchone()

        if row is None:
            return None

        data = dict(row)
        status = str(data.get("status", "")).lower()
        passed = data.get("passed")

        if status == "passed" or passed in (1, True, "1", "true", "True"):
            return data

        return None

def bind_task_permissions(
    task_id: int,
    manifest_id: str,
    granted_capabilities: dict[str, Any],
    granted_tools: list[str],
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO task_permissions
            (task_id, manifest_id, granted_capabilities_json, granted_tools_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                task_id,
                manifest_id,
                _json_dumps(granted_capabilities),
                _json_dumps(granted_tools),
            ),
        )
        return int(cur.lastrowid)


def get_task_permissions(task_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM task_permissions
            WHERE task_id = ?
            ORDER BY permission_id
            """,
            (task_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_task_permission(permission_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM task_permissions
            WHERE permission_id = ?
            """,
            (permission_id,),
        ).fetchone()

        return dict(row) if row else None
        
def create_plan_artifact(
    task_id: int,
    manifest_id: str,
    artifact_json: dict[str, Any],
    artifact_type: str = "task_plan",
    risk_class: str = "ordinary",
    artifact_status: str = "draft",
    scanner_result: str = "not_scanned",
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO plan_artifacts
            (task_id, manifest_id, artifact_type, artifact_json, risk_class, artifact_status, scanner_result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                manifest_id,
                artifact_type,
                _json_dumps(artifact_json),
                risk_class,
                artifact_status,
                scanner_result,
            ),
        )
        return int(cur.lastrowid)


def get_plan_artifact(artifact_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM plan_artifacts
            WHERE artifact_id = ?
            """,
            (artifact_id,),
        ).fetchone()

        return dict(row) if row else None


def get_plan_artifacts_for_task(task_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM plan_artifacts
            WHERE task_id = ?
            ORDER BY artifact_id
            """,
            (task_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def update_plan_artifact_scan_result(
    artifact_id: int,
    scanner_result: str,
    risk_class: str,
    artifact_status: str,
    scanner_details: dict[str, Any] | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE plan_artifacts
            SET scanner_result = ?,
                risk_class = ?,
                artifact_status = ?,
                scanner_details_json = COALESCE(?, scanner_details_json),
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE artifact_id = ?
            """,
            (
                scanner_result,
                risk_class,
                artifact_status,
                _json_dumps(scanner_details),
                artifact_id,
            ),
        )


def record_resource_usage(
    task_id: int,
    resource_type: str,
    amount: int | float,
    status: str,
    limit_value: int | float | None = None,
    details: dict[str, Any] | None = None,
) -> int:
    if amount < 0:
        raise ValueError("resource usage amount must be non-negative")

    if limit_value is not None and limit_value < 0:
        raise ValueError("resource usage limit_value must be non-negative")

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO resource_usage
            (task_id, resource_type, amount, limit_value, status, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                resource_type,
                amount,
                limit_value,
                status,
                _json_dumps(details),
            ),
        )
        return int(cur.lastrowid)


def get_resource_usage_for_task(task_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM resource_usage
            WHERE task_id = ?
            ORDER BY usage_id
            """,
            (task_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_resource_usage(usage_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM resource_usage
            WHERE usage_id = ?
            """,
            (usage_id,),
        ).fetchone()

        return dict(row) if row else None
        
        
__all__ = [
    "init_db",
    "get_connection",
    "create_session",
    "get_session",
    "log_session_event",
    "log_security_event",
    "get_active_manifest_fingerprints",
    "get_manifest_fingerprint",
    "create_task",
    "get_task",
    "update_task_status",
    "record_provider_usage",
    "get_current_model_profile",
    "get_passing_calibration_run",
    "transition_task_status",
    "bind_task_permissions",
    "get_task_permissions",
    "get_task_permission",
    "create_plan_artifact",
    "get_plan_artifact",
    "get_plan_artifacts_for_task",
    "update_plan_artifact_scan_result",
    "record_resource_usage",
    "get_resource_usage_for_task",
    "get_resource_usage",
    "get_provider_usage",
    "get_provider_usage_for_task",
    "get_provider_usage_for_session",
    "update_provider_usage_status",
]
