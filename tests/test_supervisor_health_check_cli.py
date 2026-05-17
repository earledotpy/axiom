import json
import subprocess
import sys
from pathlib import Path

from axiom.core.task_starter import start_task
from axiom.persistence.db import get_connection, init_db


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ID = "security.tool_capability_map.v1"


def _create_session() -> int:
    init_db()
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO sessions
                (safe_pass_enabled, autonomous_operation_enabled,
                 safe_pass_disabled_reason)
                VALUES (0, 0, 'no_stored_profile')
                """
            ).lastrowid
        )


def _create_pending_task(session_id: int) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 manifest_id)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (
                    session_id,
                    f"supervisor-cli-chain-{session_id}",
                    "system_maintenance",
                    "supervisor_cli_test",
                    MANIFEST_ID,
                ),
            ).lastrowid
        )


def test_supervisor_health_check_cli_json_reports_healthy_active_task():
    session_id = _create_session()
    task_id = _create_pending_task(session_id)

    start_task(task_id)

    result = subprocess.run(
        [
            sys.executable,
            "tools/supervisor_health_check.py",
            str(session_id),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["healthy"] is True
    assert payload["session_id"] == session_id
    assert payload["active_task_present"] is True
    assert payload["active_task_status"] == "running"
    assert payload["reason"] == "supervisor_health_ok_active_task_running"


def test_supervisor_health_check_cli_text_reports_no_heartbeat_unhealthy():
    session_id = _create_session()

    result = subprocess.run(
        [
            sys.executable,
            "tools/supervisor_health_check.py",
            str(session_id),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "AXIOM supervisor health" in result.stdout
    assert "healthy: False" in result.stdout
    assert "scheduler_stale: True" in result.stdout
    assert "reason: scheduler_heartbeat_stale_or_missing" in result.stdout