from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from axiom.persistence.db import get_connection


class NoopTaskStagingError(RuntimeError):
    pass


@dataclass(frozen=True)
class NoopTaskStagingResult:
    task_id: int
    session_id: int
    chain_id: str
    manifest_id: str
    status: str
    task_class: str
    task_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "chain_id": self.chain_id,
            "manifest_id": self.manifest_id,
            "status": self.status,
            "task_class": self.task_class,
            "task_type": self.task_type,
        }


def _latest_session_id() -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY session_id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        raise NoopTaskStagingError("No session exists; refusing to stage no-op task.")

    return int(row["session_id"])


def _resolve_active_role_manifest(manifest_id: str | None = None) -> str:
    with get_connection() as conn:
        if manifest_id:
            row = conn.execute(
                """
                SELECT manifest_id, manifest_type, active
                FROM manifest_fingerprints
                WHERE manifest_id = ?
                """,
                (manifest_id,),
            ).fetchone()

            if row is None:
                raise NoopTaskStagingError(f"Manifest not registered: {manifest_id}")

            if row["manifest_type"] != "role":
                raise NoopTaskStagingError(
                    f"Manifest must be type role, got {row['manifest_type']!r}"
                )

            if int(row["active"]) != 1:
                raise NoopTaskStagingError(f"Manifest is not active: {manifest_id}")

            return str(row["manifest_id"])

        row = conn.execute(
            """
            SELECT manifest_id
            FROM manifest_fingerprints
            WHERE manifest_type = 'role'
              AND active = 1
            ORDER BY registered_at DESC, fingerprint_id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        raise NoopTaskStagingError(
            "No active role manifest exists; refusing to stage a manifest-bound no-op task."
        )

    return str(row["manifest_id"])


def _assert_session_has_no_running_task(session_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS running_count
            FROM tasks
            WHERE session_id = ?
              AND status = 'running'
            """,
            (session_id,),
        ).fetchone()

    running_count = int(row["running_count"]) if row else 0
    if running_count != 0:
        raise NoopTaskStagingError(
            f"Session {session_id} already has {running_count} running task(s)."
        )


def stage_pending_noop_task(
    session_id: int | None = None,
    manifest_id: str | None = None,
    goal_text: str = "Manual staged no-op task for execution readiness verification.",
) -> NoopTaskStagingResult:
    resolved_session_id = int(session_id) if session_id is not None else _latest_session_id()
    resolved_manifest_id = _resolve_active_role_manifest(manifest_id)

    _assert_session_has_no_running_task(resolved_session_id)

    chain_id = f"manual-noop-{uuid.uuid4().hex}"
    input_json = {
        "staged_by": "noop_task_stager",
        "execution_expected": False,
        "manual_cycle_required": True,
        "safety_boundary": {
            "dispatches_scheduler": False,
            "executes_task_body": False,
            "calls_model": False,
            "calls_network": False,
            "calls_sandbox": False,
            "enables_autonomous_operation": False,
        },
    }

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks
            (session_id, parent_task_id, chain_id, task_class, task_type,
             status, priority, goal_text, input_json, manifest_id)
            VALUES (?, NULL, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (
                resolved_session_id,
                chain_id,
                "system_maintenance",
                "manual_noop",
                5,
                goal_text,
                json.dumps(input_json, sort_keys=True),
                resolved_manifest_id,
            ),
        )
        task_id = int(cur.lastrowid)

    return NoopTaskStagingResult(
        task_id=task_id,
        session_id=resolved_session_id,
        chain_id=chain_id,
        manifest_id=resolved_manifest_id,
        status="pending",
        task_class="system_maintenance",
        task_type="manual_noop",
    )
