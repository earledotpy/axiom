from __future__ import annotations

from axiom.core.noop_task_stager import (
    NoopTaskStagingError,
    stage_pending_noop_task,
)
from axiom.persistence.db import get_connection


def _create_session() -> int:
    with get_connection() as conn:
        return int(conn.execute("INSERT INTO sessions DEFAULT VALUES").lastrowid)


def _insert_active_role_manifest(manifest_id: str = "role.noop_test.v1") -> str:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, 'role', ?, ?, 'axiom.manifest.v1',
                    '1.0.0', 'noop_test', NULL, 'test', 1, 'test')
            """,
            (
                manifest_id,
                "policy/role_manifests/noop_test.json",
                "1" * 64,
            ),
        )
    return manifest_id


def test_stage_pending_noop_task_creates_manifest_bound_pending_task():
    session_id = _create_session()
    manifest_id = _insert_active_role_manifest()

    result = stage_pending_noop_task(
        session_id=session_id,
        manifest_id=manifest_id,
    )

    assert result.session_id == session_id
    assert result.manifest_id == manifest_id
    assert result.status == "pending"
    assert result.task_class == "system_maintenance"
    assert result.task_type == "manual_noop"

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, manifest_id, started_at, completed_at, result_json
            FROM tasks
            WHERE task_id = ?
            """,
            (result.task_id,),
        ).fetchone()

    assert row["status"] == "pending"
    assert row["manifest_id"] == manifest_id
    assert row["started_at"] is None
    assert row["completed_at"] is None
    assert row["result_json"] is None


def test_stage_pending_noop_task_refuses_without_active_role_manifest():
    session_id = _create_session()

    try:
        stage_pending_noop_task(session_id=session_id)
    except NoopTaskStagingError as exc:
        assert "No active role manifest" in str(exc)
    else:
        raise AssertionError("stager accepted missing role manifest")


def test_stage_pending_noop_task_refuses_tool_capability_map_manifest():
    session_id = _create_session()

    try:
        stage_pending_noop_task(
            session_id=session_id,
            manifest_id="security.tool_capability_map.v1",
        )
    except NoopTaskStagingError as exc:
        assert "Manifest must be type role" in str(exc)
    else:
        raise AssertionError("stager accepted non-role manifest")


def test_stage_pending_noop_task_refuses_when_running_task_exists():
    session_id = _create_session()
    manifest_id = _insert_active_role_manifest()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks
            (session_id, chain_id, task_class, task_type, status, manifest_id)
            VALUES (?, 'running-chain', 'system_maintenance', 'manual_noop', 'running', ?)
            """,
            (session_id, manifest_id),
        )

    try:
        stage_pending_noop_task(
            session_id=session_id,
            manifest_id=manifest_id,
        )
    except NoopTaskStagingError as exc:
        assert "running task" in str(exc)
    else:
        raise AssertionError("stager accepted session with running task")
