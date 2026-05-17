import json
import subprocess
import sys
from pathlib import Path

from axiom.persistence.db import get_connection, init_db


ROOT = Path(__file__).resolve().parents[1]


def _create_clean_latest_session() -> int:
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


def test_audit_task_lifecycle_default_audits_latest_session_json():
    session_id = _create_clean_latest_session()

    result = subprocess.run(
        [sys.executable, "tools/audit_task_lifecycle.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["scope"] == "latest_session"
    assert payload["session_id"] == session_id
    assert payload["passed"] is True


def test_audit_task_lifecycle_latest_session_explicit_matches_default():
    session_id = _create_clean_latest_session()

    result = subprocess.run(
        [
            sys.executable,
            "tools/audit_task_lifecycle.py",
            "--latest-session",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["scope"] == "latest_session"
    assert payload["session_id"] == session_id
    assert payload["passed"] is True


def test_audit_task_lifecycle_rejects_conflicting_scope_flags():
    result = subprocess.run(
        [
            sys.executable,
            "tools/audit_task_lifecycle.py",
            "--latest-session",
            "--all-sessions",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "cannot be combined" in result.stderr