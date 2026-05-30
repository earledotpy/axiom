from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from axiom.persistence.db import get_connection


@dataclass(frozen=True)
class AxiomStatusReport:
    database_initialized: bool
    manifest_fingerprints_valid: bool
    model_candidate_profile_present: bool
    current_trusted_model_profile_present: bool
    safe_pass_enabled: bool
    autonomous_operation_enabled: bool
    scheduler_heartbeat_fresh: bool
    no_blocking_tasks: bool
    autonomous_available: bool
    blocking_reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _schema_initialized(conn) -> bool:
    if not _table_exists(conn, "schema_migrations"):
        return False

    row = conn.execute(
        """
        SELECT schema_version
        FROM schema_migrations
        WHERE schema_version = 'v1.11.4'
        """
    ).fetchone()

    return row is not None


def _active_manifest_count(conn) -> int:
    if not _table_exists(conn, "manifest_fingerprints"):
        return 0

    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM manifest_fingerprints
        WHERE active = 1
        """
    ).fetchone()

    return int(row["count"])


def _tool_capability_map_registered(conn) -> bool:
    if not _table_exists(conn, "manifest_fingerprints"):
        return False

    row = conn.execute(
        """
        SELECT manifest_id
        FROM manifest_fingerprints
        WHERE manifest_id = 'security.tool_capability_map.v1'
          AND manifest_type = 'tool_capability_map'
          AND active = 1
        """
    ).fetchone()

    return row is not None


def _latest_session_state(conn) -> tuple[bool, bool, int | None, str | None]:
    if not _table_exists(conn, "sessions"):
        return False, False, None, "sessions_table_missing"

    row = conn.execute(
        """
        SELECT session_id, safe_pass_enabled, autonomous_operation_enabled,
               safe_pass_disabled_reason
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return False, False, None, "no_session"

    return (
        bool(row["safe_pass_enabled"]),
        bool(row["autonomous_operation_enabled"]),
        int(row["session_id"]),
        row["safe_pass_disabled_reason"],
    )


def _model_profile_state(conn, profile_label: str) -> dict[str, Any]:
    if not _table_exists(conn, "model_profile_fingerprints"):
        return {
            "candidate_present": False,
            "current_present": False,
            "latest_profile": None,
            "current_profile": None,
        }

    latest = conn.execute(
        """
        SELECT profile_id, profile_label, model_name, quantization,
               thinking_mode, thinking_mode_rule_version,
               calibration_run_id, is_current, registration_status
        FROM model_profile_fingerprints
        WHERE profile_label = ?
        ORDER BY profile_id DESC
        LIMIT 1
        """,
        (profile_label,),
    ).fetchone()

    current = conn.execute(
        """
        SELECT profile_id, profile_label, model_name, quantization,
               thinking_mode, thinking_mode_rule_version,
               calibration_run_id, is_current, registration_status
        FROM model_profile_fingerprints
        WHERE profile_label = ?
          AND is_current = 1
          AND registration_status = 'current'
        ORDER BY profile_id DESC
        LIMIT 1
        """,
        (profile_label,),
    ).fetchone()

    candidate_present = False
    if latest is not None:
        candidate_present = latest["registration_status"] == "candidate"

    return {
        "candidate_present": candidate_present,
        "current_present": current is not None,
        "latest_profile": dict(latest) if latest is not None else None,
        "current_profile": dict(current) if current is not None else None,
    }


def _scheduler_heartbeat_fresh(conn, threshold_seconds: int = 120) -> tuple[bool, str | None]:
    """Check if scheduler heartbeat is fresh (within threshold). Returns (is_fresh, last_freshness_at)."""
    if not _table_exists(conn, "scheduler_heartbeat"):
        return False, None

    row = conn.execute(
        """
        SELECT last_freshness_at
        FROM scheduler_heartbeat
        ORDER BY heartbeat_id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return False, None

    last_freshness_at = row["last_freshness_at"]
    try:
        last_tick = datetime.fromisoformat(last_freshness_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed = (now - last_tick).total_seconds()
        is_fresh = elapsed <= threshold_seconds
        return is_fresh, last_freshness_at
    except (ValueError, AttributeError):
        return False, last_freshness_at


def _no_blocking_tasks(conn, session_id: int | None) -> tuple[bool, int]:
    """Check if there are no blocking tasks (needs_human_input or quarantined). Returns (no_blocking, count)."""
    if not session_id or not _table_exists(conn, "tasks"):
        return True, 0

    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM tasks
        WHERE session_id = ?
          AND status IN ('needs_human_input', 'quarantined')
        """,
        (session_id,),
    ).fetchone()

    count = int(row["count"]) if row else 0
    return count == 0, count


def build_status_report(profile_label: str = "default") -> AxiomStatusReport:
    blocking_reasons: list[str] = []

    with get_connection() as conn:
        database_initialized = _schema_initialized(conn)

        active_manifest_count = _active_manifest_count(conn)
        tool_map_registered = _tool_capability_map_registered(conn)
        manifest_fingerprints_valid = active_manifest_count > 0 and tool_map_registered

        model_state = _model_profile_state(conn, profile_label=profile_label)
        model_candidate_profile_present = bool(model_state["candidate_present"])
        current_trusted_model_profile_present = bool(model_state["current_present"])

        safe_pass_enabled, autonomous_operation_enabled, session_id, safe_pass_reason = (
            _latest_session_state(conn)
        )

        scheduler_heartbeat_fresh, last_freshness_at = _scheduler_heartbeat_fresh(conn)
        no_blocking_tasks, blocking_task_count = _no_blocking_tasks(conn, session_id)

    if not database_initialized:
        blocking_reasons.append("database_not_initialized")

    if not manifest_fingerprints_valid:
        blocking_reasons.append("manifest_fingerprints_not_valid")

    if not current_trusted_model_profile_present:
        blocking_reasons.append("no_current_trusted_model_profile")

    if not safe_pass_enabled:
        blocking_reasons.append("safe_pass_disabled")

    if not autonomous_operation_enabled:
        blocking_reasons.append("autonomous_operation_disabled")

    if not scheduler_heartbeat_fresh:
        blocking_reasons.append("scheduler_heartbeat_stale")

    if not no_blocking_tasks:
        blocking_reasons.append("blocking_tasks_present")

    autonomous_available = (
        database_initialized
        and manifest_fingerprints_valid
        and current_trusted_model_profile_present
        and safe_pass_enabled
        and autonomous_operation_enabled
        and scheduler_heartbeat_fresh
        and no_blocking_tasks
    )

    return AxiomStatusReport(
        database_initialized=database_initialized,
        manifest_fingerprints_valid=manifest_fingerprints_valid,
        model_candidate_profile_present=model_candidate_profile_present,
        current_trusted_model_profile_present=current_trusted_model_profile_present,
        safe_pass_enabled=safe_pass_enabled,
        autonomous_operation_enabled=autonomous_operation_enabled,
        scheduler_heartbeat_fresh=scheduler_heartbeat_fresh,
        no_blocking_tasks=no_blocking_tasks,
        autonomous_available=autonomous_available,
        blocking_reasons=blocking_reasons,
        details={
            "profile_label": profile_label,
            "active_manifest_count": active_manifest_count,
            "tool_capability_map_registered": tool_map_registered,
            "session_id": session_id,
            "safe_pass_disabled_reason": safe_pass_reason,
            "latest_model_profile": model_state["latest_profile"],
            "current_model_profile": model_state["current_profile"],
            "scheduler_heartbeat_last_freshness": last_freshness_at,
            "blocking_task_count": blocking_task_count,
        },
    )