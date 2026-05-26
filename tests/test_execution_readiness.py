from __future__ import annotations

from axiom.core.execution_readiness import ToolCheck, evaluate_execution_readiness
from axiom.persistence.db import get_connection


def _passing_runner(script_name: str, args: list[str]) -> ToolCheck:
    if script_name == "supervisor_health_check.py":
        output = "healthy: True\nreason: supervisor_health_ok"
    else:
        output = "passed: True"

    return ToolCheck(
        name=script_name,
        passed=True,
        reason="passed",
        returncode=0,
        command=[script_name, *args],
        output=output,
    )


def _failing_execution_runner(script_name: str, args: list[str]) -> ToolCheck:
    if script_name == "audit_task_execution.py":
        return ToolCheck(
            name=script_name,
            passed=False,
            reason="tool_check_failed",
            returncode=1,
            command=[script_name, *args],
            output="passed: False",
        )

    return _passing_runner(script_name, args)


def _insert_role_manifest(manifest_id: str = "role.execution_readiness_test.v1") -> str:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, 1, ?)
            """,
            (
                manifest_id,
                "role",
                f"policy/role_manifests/{manifest_id}.json",
                "1" * 64,
                "axiom.manifest.v1",
                "1.0.0",
                "execution_readiness_test",
                "test",
                "test",
            ),
        )

    return manifest_id


def _insert_session() -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO sessions (scheduler_status)
                VALUES ('ready')
                """
            ).lastrowid
        )


def _insert_task(session_id: int, status: str, manifest_id: str | None) -> int:
    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status, manifest_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    f"chain-{session_id}-{status}",
                    "system_maintenance",
                    "noop",
                    status,
                    manifest_id,
                ),
            ).lastrowid
        )


def test_execution_readiness_true_when_audits_health_clean_pending_bound_and_no_running():
    session_id = _insert_session()
    manifest_id = _insert_role_manifest()
    _insert_task(session_id=session_id, status="pending", manifest_id=manifest_id)

    result = evaluate_execution_readiness(
        session_id=session_id,
        check_runner=_passing_runner,
    )

    assert result.ready is True
    assert result.reasons == []
    assert result.pending_manifest_bound_task_count == 1
    assert result.running_task_count == 0


def test_execution_readiness_false_when_no_pending_manifest_bound_task():
    session_id = _insert_session()

    result = evaluate_execution_readiness(
        session_id=session_id,
        check_runner=_passing_runner,
    )

    assert result.ready is False
    assert "no_pending_manifest_bound_task" in result.reasons
    assert result.pending_manifest_bound_task_count == 0


def test_execution_readiness_false_when_running_task_present():
    session_id = _insert_session()
    manifest_id = _insert_role_manifest("role.execution_readiness_running_test.v1")
    _insert_task(session_id=session_id, status="pending", manifest_id=manifest_id)
    _insert_task(session_id=session_id, status="running", manifest_id=manifest_id)

    result = evaluate_execution_readiness(
        session_id=session_id,
        check_runner=_passing_runner,
    )

    assert result.ready is False
    assert "running_tasks_present" in result.reasons
    assert result.running_task_count == 1


def test_execution_readiness_false_when_execution_audit_fails():
    session_id = _insert_session()
    manifest_id = _insert_role_manifest("role.execution_readiness_audit_test.v1")
    _insert_task(session_id=session_id, status="pending", manifest_id=manifest_id)

    result = evaluate_execution_readiness(
        session_id=session_id,
        check_runner=_failing_execution_runner,
    )

    assert result.ready is False
    assert "execution_audit_not_clean" in result.reasons