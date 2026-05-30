from __future__ import annotations

from datetime import datetime, timedelta, timezone

from axiom.app.status_report import build_status_report
from axiom.persistence.db import get_connection, init_db
from axiom.security.autonomous_gate_panel import get_autonomous_gate_status


def test_7step_gate_all_passed():
    """Test when all 7 gate steps pass."""
    init_db()
    # Create minimal passing state
    with get_connection() as conn:
        # Create session with autonomous enabled and safe pass enabled
        cur = conn.execute(
            """
            INSERT INTO sessions (autonomous_operation_enabled, safe_pass_enabled)
            VALUES (1, 1)
            """
        )
        session_id = cur.lastrowid

        # Create heartbeat (fresh)
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, scheduler_state)
            VALUES (?, ?, 'ready')
            """,
            (session_id, now),
        )

        # Create current model profile
        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, calibration_set_id, calibration_set_sha256,
             model_name, ollama_host, threshold, passed,
             approved_by_panel_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "calib.default.v1",
                "test_set_1",
                "abc123",
                "qwen3:4b",
                "http://localhost:11434",
                0.8,
                1,
                "v1.0",
            ),
        )

        conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, ollama_model_tag,
             ollama_model_digest, quantization, thinking_mode,
             selected_profile_sha256, calibration_run_id, is_current,
             registration_status, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "default",
                "qwen3:4b",
                "http://localhost:11434",
                "qwen3:4b",
                "abc123xyz",
                "q4",
                "disabled",
                "profile_sha_123",
                "calib.default.v1",
                1,
                "current",
                "test",
            ),
        )

        # Tool capability map is auto-seeded by conftest, so no need to insert it
        conn.commit()

    report = build_status_report()
    assert report.database_initialized
    assert report.manifest_fingerprints_valid
    assert report.current_trusted_model_profile_present
    assert report.safe_pass_enabled
    assert report.autonomous_operation_enabled
    assert report.scheduler_heartbeat_fresh
    assert report.no_blocking_tasks
    assert report.autonomous_available
    assert len(report.blocking_reasons) == 0


def test_7step_gate_heartbeat_stale():
    """Test gate fails when heartbeat is stale."""
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions (autonomous_operation_enabled, safe_pass_enabled)
            VALUES (1, 1)
            """
        )
        session_id = cur.lastrowid

        # Create stale heartbeat (> 120 seconds old)
        old_time = (
            datetime.now(timezone.utc) - timedelta(seconds=150)
        ).isoformat().replace('+00:00', 'Z')
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, scheduler_state)
            VALUES (?, ?, 'ready')
            """,
            (session_id, old_time),
        )
        conn.commit()

    report = build_status_report()
    assert not report.scheduler_heartbeat_fresh
    assert "scheduler_heartbeat_stale" in report.blocking_reasons
    assert not report.autonomous_available


def test_7step_gate_blocking_tasks_present():
    """Test gate fails when blocking tasks exist."""
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions (autonomous_operation_enabled, safe_pass_enabled)
            VALUES (1, 1)
            """
        )
        session_id = cur.lastrowid

        # Create fresh heartbeat
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        conn.execute(
            """
            INSERT INTO scheduler_heartbeat
            (session_id, last_freshness_at, scheduler_state)
            VALUES (?, ?, 'ready')
            """,
            (session_id, now),
        )

        # Create task needing human input
        conn.execute(
            """
            INSERT INTO tasks
            (session_id, chain_id, task_class, task_type, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, "chain_1", "goal_planning", "plan", "needs_human_input"),
        )
        conn.commit()

    report = build_status_report()
    assert not report.no_blocking_tasks
    assert "blocking_tasks_present" in report.blocking_reasons
    assert report.details["blocking_task_count"] == 1
    assert not report.autonomous_available


def test_autonomous_gate_panel_structure():
    """Test the panel data structure returns all 7 steps."""
    init_db()
    panel_data = get_autonomous_gate_status()
    assert len(panel_data.steps) == 7
    for i, step in enumerate(panel_data.steps, 1):
        assert step.step_number == i
        assert step.name is not None
        assert isinstance(step.passed, bool)

    # Verify step names match the specification
    expected_names = [
        "Database Initialized",
        "Manifest Fingerprints Valid",
        "Current Trusted Model Profile",
        "Safe Pass Enabled",
        "Autonomous Operation Enabled",
        "Scheduler Heartbeat Fresh",
        "No Blocking Tasks",
    ]
    assert [s.name for s in panel_data.steps] == expected_names
