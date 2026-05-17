from axiom.persistence.db import get_connection, init_db
from tools.repair_session_state import repair_session_state


def test_repair_session_state_returns_fail_closed_state_without_current_profile():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (0, 0, 'no_stored_profile')
            """
        )

    result = repair_session_state(profile_label="repair_missing_current_profile_test")

    assert result["session"]["safe_pass_enabled"] == 0
    assert result["session"]["autonomous_operation_enabled"] == 0
    assert result["session"]["safe_pass_disabled_reason"] == "no_stored_profile"
    assert result["current_trusted_profile_present"] is False


def test_repair_session_state_disables_unsafe_latest_session_without_current_profile():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (1, 1, NULL)
            """
        )

    result = repair_session_state(profile_label="repair_no_current_profile_test")

    assert "disabled_safe_pass_and_autonomous_operation" in result["changes"]
    assert result["session"]["safe_pass_enabled"] == 0
    assert result["session"]["autonomous_operation_enabled"] == 0
    assert result["session"]["safe_pass_disabled_reason"] == "no_stored_profile"
    assert result["current_trusted_profile_present"] is False


def test_repair_session_state_is_idempotent_after_repair():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (0, 0, 'no_stored_profile')
            """
        )

    result = repair_session_state(profile_label="repair_idempotent_test")

    assert result["changes"] == []
    assert result["session"]["safe_pass_enabled"] == 0
    assert result["session"]["autonomous_operation_enabled"] == 0
    assert result["session"]["safe_pass_disabled_reason"] == "no_stored_profile"


def test_repair_session_state_writes_security_event_when_repairing():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (1, 1, NULL)
            """
        )

    result = repair_session_state(profile_label="repair_security_event_test")
    session_id = result["session"]["session_id"]

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT event_type, reason, severity
            FROM security_events
            WHERE session_id = ?
              AND event_type = 'session_state_repaired'
            ORDER BY event_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    assert row is not None
    assert row["event_type"] == "session_state_repaired"
    assert row["reason"] == "no_stored_profile"
    assert row["severity"] == "info"