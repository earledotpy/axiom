from __future__ import annotations

import json

from axiom.persistence.db import get_connection, init_db


AGENT_MANIFESTS = {
    "goal_planner": {
        "manifest_id": "role.goal_planner.v1",
        "task_class": "goal_planning",
        "task_type": "phase5_goal_planning_slice",
        "relative_path": "policy/role_manifests/goal_planner.v1.json",
        "sha": "1" * 64,
        "goal_text": "Create a bounded first Phase 5 goal plan.",
        "input": {"slice": "goal_planner_foundation"},
    },
    "task_planner": {
        "manifest_id": "role.task_planner.v1",
        "task_class": "task_planning",
        "task_type": "phase5_task_planning_slice",
        "relative_path": "policy/role_manifests/task_planner.v1.json",
        "sha": "2" * 64,
        "goal_text": "Break the approved goal plan into bounded tasks.",
        "input": {"slice": "task_planner_foundation"},
    },
    "tool_executor": {
        "manifest_id": "role.tool_executor.v1",
        "task_class": "tool_execution",
        "task_type": "phase5_tool_execution_slice",
        "relative_path": "policy/role_manifests/tool_executor.v1.json",
        "sha": "3" * 64,
        "goal_text": "Prepare a bounded tool execution plan.",
        "input": {"slice": "tool_executor_foundation"},
    },
    "result_verifier": {
        "manifest_id": "role.result_verifier.v1",
        "task_class": "result_verification",
        "task_type": "phase5_result_verification_slice",
        "relative_path": "policy/role_manifests/result_verifier.v1.json",
        "sha": "4" * 64,
        "goal_text": "Summarize verification boundaries for a completed result.",
        "input": {"slice": "result_verifier_foundation"},
    },
}

DEFAULT_MANIFEST = object()


def ensure_agent_manifest(agent_name: str, active: int = 1) -> str:
    config = AGENT_MANIFESTS[agent_name]
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, 'role', ?, ?, 'axiom.manifest.v1', '1.0.0',
                    ?, NULL, 'phase5-test', ?, 'test')
            """,
            (
                config["manifest_id"],
                config["relative_path"],
                config["sha"],
                agent_name,
                active,
            ),
        )
    return str(config["manifest_id"])


def create_agent_session() -> int:
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


def create_agent_task(
    agent_name: str,
    session_id: int,
    status: str = "pending",
    manifest_id: str | None | object = DEFAULT_MANIFEST,
    task_class: str | None = None,
) -> int:
    config = AGENT_MANIFESTS[agent_name]
    if manifest_id is DEFAULT_MANIFEST:
        manifest_id = str(config["manifest_id"])
    if task_class is None:
        task_class = str(config["task_class"])

    with get_connection() as conn:
        return int(
            conn.execute(
                """
                INSERT INTO tasks
                (session_id, chain_id, task_class, task_type, status,
                 goal_text, input_json, manifest_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    f"chain-{agent_name}-{session_id}",
                    task_class,
                    config["task_type"],
                    status,
                    config["goal_text"],
                    json.dumps(config["input"]),
                    manifest_id,
                ),
            ).lastrowid
        )
