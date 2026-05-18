from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.persistence.db import get_connection, init_db
from axiom.core.scheduler import write_scheduler_heartbeat


TOOL_VERSION = "repair_session_state.v1"


def get_latest_session(conn) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT session_id, safe_pass_enabled, autonomous_operation_enabled,
               safe_pass_disabled_reason
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()

    return dict(row) if row is not None else None


def current_trusted_profile_exists(conn, profile_label: str) -> bool:
    row = conn.execute(
        """
        SELECT profile_id
        FROM model_profile_fingerprints
        WHERE profile_label = ?
          AND is_current = 1
          AND registration_status = 'current'
          AND thinking_mode != 'unknown'
        ORDER BY profile_id DESC
        LIMIT 1
        """,
        (profile_label,),
    ).fetchone()

    return row is not None


def latest_candidate_profile(conn, profile_label: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT profile_id, profile_label, model_name, thinking_mode,
               thinking_mode_rule_version, is_current, registration_status,
               calibration_run_id
        FROM model_profile_fingerprints
        WHERE profile_label = ?
        ORDER BY profile_id DESC
        LIMIT 1
        """,
        (profile_label,),
    ).fetchone()

    return dict(row) if row is not None else None


def create_session_if_missing(conn) -> int:
    cur = conn.execute(
        """
        INSERT INTO sessions
        (safe_pass_enabled, autonomous_operation_enabled,
         safe_pass_disabled_reason)
        VALUES (0, 0, 'no_stored_profile')
        """
    )
    return int(cur.lastrowid)


def write_security_event(
    conn,
    session_id: int,
    reason: str,
    details: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO security_events
        (session_id, event_type, reason, severity, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            "session_state_repaired",
            reason,
            "info",
            json.dumps(details, sort_keys=True, ensure_ascii=False),
        ),
    )


def refresh_ready_heartbeat_if_idle(session_id: int | None) -> int | None:
    """
    Write a fresh ready heartbeat for an idle repaired session.

    This is intentionally conservative:
    - Does nothing if there is no session_id.
    - Does nothing if the session still has a running task.
    - Writes a ready heartbeat only when the session is idle.
    """
    if session_id is None:
        return None

    with get_connection() as conn:
        running = conn.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE session_id = ? AND status = 'running'
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    if running is not None:
        return None

    return write_scheduler_heartbeat(
        session_id=session_id,
        scheduler_state="ready",
        last_action="session_repaired",
        active_task_id=None,
        active_chain_id=None,
        blocking_operation_type="session_repair",
        tick_completed=True,
        blocking_operation_completed=True,
    )


def repair_session_state(profile_label: str = "default") -> dict[str, Any]:
    init_db()

    changes: list[str] = []
    session_id: int | None = None

    with get_connection() as conn:
        latest_session = get_latest_session(conn)

        if latest_session is None:
            session_id = create_session_if_missing(conn)
            latest_session = get_latest_session(conn)
            changes.append("created_session")
        else:
            session_id = int(latest_session["session_id"])

        assert latest_session is not None

        has_current_profile = current_trusted_profile_exists(
            conn,
            profile_label=profile_label,
        )

        latest_profile = latest_candidate_profile(
            conn,
            profile_label=profile_label,
        )

        if not has_current_profile:
            update_needed = (
                int(latest_session["safe_pass_enabled"]) != 0
                or int(latest_session["autonomous_operation_enabled"]) != 0
                or latest_session["safe_pass_disabled_reason"] != "no_stored_profile"
            )

            if update_needed:
                conn.execute(
                    """
                    UPDATE sessions
                    SET safe_pass_enabled = 0,
                        autonomous_operation_enabled = 0,
                        safe_pass_disabled_reason = 'no_stored_profile',
                        safe_pass_disabled_at = COALESCE(
                            safe_pass_disabled_at,
                            strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                        )
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )
                changes.append("disabled_safe_pass_and_autonomous_operation")

                write_security_event(
                    conn,
                    session_id=session_id,
                    reason="no_stored_profile",
                    details={
                        "tool_version": TOOL_VERSION,
                        "profile_label": profile_label,
                        "current_trusted_profile_present": False,
                        "latest_profile": latest_profile,
                        "interpretation": (
                            "No current trusted model profile is stored. "
                            "Candidate profiles may exist but do not enable safe-pass."
                        ),
                    },
                )

        repaired_session = get_latest_session(conn)

    heartbeat_id = refresh_ready_heartbeat_if_idle(session_id)

    return {
        "tool_version": TOOL_VERSION,
        "profile_label": profile_label,
        "current_trusted_profile_present": has_current_profile,
        "latest_profile": latest_profile,
        "changes": changes,
        "session": repaired_session,
        "heartbeat_id": heartbeat_id,
    }

    return {
        "tool_version": TOOL_VERSION,
        "profile_label": profile_label,
        "current_trusted_profile_present": has_current_profile,
        "latest_profile": latest_profile,
        "changes": changes,
        "session": repaired_session,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair AXIOM latest session fail-closed state."
    )
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = repair_session_state(profile_label=args.profile_label)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print("AXIOM session-state repair")
    print("==========================")
    print(f"profile_label: {result['profile_label']}")
    print(
        "current_trusted_profile_present: "
        f"{result['current_trusted_profile_present']}"
    )

    print("")
    print("changes:")
    if result["changes"]:
        for change in result["changes"]:
            print(f"- {change}")
    else:
        print("- none")

    print("")
    print("session:")
    print(json.dumps(result["session"], indent=2, sort_keys=True, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())