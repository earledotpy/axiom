from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from axiom.core.operator_command_parser import OperatorCommandParser
from axiom.persistence.db import get_connection


@dataclass(frozen=True)
class OperatorCommandIntentRecord:
    recorded: bool
    command_id: int | None
    task_id: int | None
    command_name: str | None
    manifest_id: str | None
    authorization_status: str | None
    command_status: str | None
    rejection_reason: str | None
    runtime_action_executed: bool
    ledger_written: bool
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorCommandLedgerViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorCommandLedgerAuditResult:
    passed: bool
    checked: list[str]
    checked_command_count: int
    violations: list[OperatorCommandLedgerViolation]

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "checked_command_count": self.checked_command_count,
            "violation_count": self.violation_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _latest_active_session_id(conn) -> int | None:
    row = conn.execute(
        """
        SELECT session_id
        FROM sessions
        WHERE ended_at IS NULL
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()
    return int(row["session_id"]) if row else None


def record_operator_command_intent(
    raw: str | dict[str, Any],
    *,
    operator_id: str = "local_operator",
) -> OperatorCommandIntentRecord:
    """
    Record accepted local operator command intent without executing it.

    Rejected parser results are returned without ledger writes because unknown
    commands have no approved manifest_id for the operator_commands foreign key.
    """
    parse_result = OperatorCommandParser().parse(raw)

    if not parse_result.accepted:
        return OperatorCommandIntentRecord(
            recorded=False,
            command_id=None,
            task_id=None,
            command_name=parse_result.command_name,
            manifest_id=parse_result.manifest_id,
            authorization_status=None,
            command_status=None,
            rejection_reason=parse_result.rejection_reason,
            runtime_action_executed=False,
            ledger_written=False,
            details={"parser": parse_result.to_dict()},
        )

    with get_connection() as conn:
        manifest = conn.execute(
            """
            SELECT manifest_id, manifest_type, command_name, active
            FROM manifest_fingerprints
            WHERE manifest_id = ?
              AND active = 1
            """,
            (parse_result.manifest_id,),
        ).fetchone()

        if manifest is None:
            return OperatorCommandIntentRecord(
                recorded=False,
                command_id=None,
                task_id=None,
                command_name=parse_result.command_name,
                manifest_id=parse_result.manifest_id,
                authorization_status=None,
                command_status=None,
                rejection_reason="operator_command_manifest_not_registered",
                runtime_action_executed=False,
                ledger_written=False,
                details={"parser": parse_result.to_dict()},
            )

        if (
            manifest["manifest_type"] != "operator_control"
            or manifest["command_name"] != parse_result.command_name
        ):
            return OperatorCommandIntentRecord(
                recorded=False,
                command_id=None,
                task_id=None,
                command_name=parse_result.command_name,
                manifest_id=parse_result.manifest_id,
                authorization_status=None,
                command_status=None,
                rejection_reason="operator_command_manifest_identity_mismatch",
                runtime_action_executed=False,
                ledger_written=False,
                details={
                    "parser": parse_result.to_dict(),
                    "manifest_type": manifest["manifest_type"],
                    "manifest_command_name": manifest["command_name"],
                },
            )

        session_id = _latest_active_session_id(conn)
        if session_id is None:
            return OperatorCommandIntentRecord(
                recorded=False,
                command_id=None,
                task_id=None,
                command_name=parse_result.command_name,
                manifest_id=parse_result.manifest_id,
                authorization_status=None,
                command_status=None,
                rejection_reason="no_active_session",
                runtime_action_executed=False,
                ledger_written=False,
                details={"operator_id": operator_id, "parser": parse_result.to_dict()},
            )

        task_input = {
            "source": "operator_command_ledger",
            "operator_id": operator_id,
            "command_name": parse_result.command_name,
            "manifest_id": parse_result.manifest_id,
            "payload": parse_result.payload,
            "source_text": parse_result.source_text,
            "runtime_action_executed": False,
            "ledger_written": True,
        }

        task_cur = conn.execute(
            """
            INSERT INTO tasks
            (session_id, chain_id, task_class, task_type, priority,
             goal_text, input_json, manifest_id)
            VALUES (?, ?, 'operator_control', 'operator_command_intent', 5, ?, ?, ?)
            """,
            (
                session_id,
                f"operator-command-{parse_result.command_name}",
                f"Operator command intent: {parse_result.command_name}",
                _json_dumps(task_input),
                parse_result.manifest_id,
            ),
        )
        task_id = int(task_cur.lastrowid)

        command_cur = conn.execute(
            """
            INSERT INTO operator_commands
            (task_id, command_name, command_payload_json, manifest_id,
             authorization_status, command_status)
            VALUES (?, ?, ?, ?, 'pending', 'pending')
            """,
            (
                task_id,
                parse_result.command_name,
                _json_dumps(parse_result.payload),
                parse_result.manifest_id,
            ),
        )
        command_id = int(command_cur.lastrowid)

    return OperatorCommandIntentRecord(
        recorded=True,
        command_id=command_id,
        task_id=task_id,
        command_name=parse_result.command_name,
        manifest_id=parse_result.manifest_id,
        authorization_status="pending",
        command_status="pending",
        rejection_reason=None,
        runtime_action_executed=False,
        ledger_written=True,
        details={
            "operator_id": operator_id,
            "parser": parse_result.to_dict(),
            "session_id": session_id,
        },
    )


def audit_operator_command_ledger() -> OperatorCommandLedgerAuditResult:
    checked = [
        "operator_command_task_link",
        "operator_command_manifest_link",
        "operator_command_phase6d_status_bounds",
        "operator_command_payload_json",
        "operator_command_pending_task_alignment",
    ]
    violations: list[OperatorCommandLedgerViolation] = []

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                oc.command_id,
                oc.task_id,
                oc.command_name,
                oc.command_payload_json,
                oc.manifest_id,
                oc.authorization_status,
                oc.command_status,
                oc.rejection_reason,
                oc.completed_at,
                t.task_class,
                t.task_type,
                t.status AS task_status,
                t.manifest_id AS task_manifest_id,
                mf.manifest_type,
                mf.command_name AS manifest_command_name,
                mf.active AS manifest_active
            FROM operator_commands AS oc
            LEFT JOIN tasks AS t
              ON t.task_id = oc.task_id
            LEFT JOIN manifest_fingerprints AS mf
              ON mf.manifest_id = oc.manifest_id
            ORDER BY oc.command_id
            """
        ).fetchall()

    for row in rows:
        data = dict(row)
        command_id = int(data["command_id"])

        if data["task_class"] != "operator_control" or data["task_type"] != "operator_command_intent":
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_task_link",
                    reason="operator_command_task_identity_mismatch",
                    details={
                        "command_id": command_id,
                        "task_id": data["task_id"],
                        "task_class": data["task_class"],
                        "task_type": data["task_type"],
                    },
                )
            )

        if data["task_manifest_id"] != data["manifest_id"]:
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_manifest_link",
                    reason="operator_command_task_manifest_mismatch",
                    details={
                        "command_id": command_id,
                        "task_manifest_id": data["task_manifest_id"],
                        "command_manifest_id": data["manifest_id"],
                    },
                )
            )

        if (
            data["manifest_type"] != "operator_control"
            or data["manifest_command_name"] != data["command_name"]
            or data["manifest_active"] != 1
        ):
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_manifest_link",
                    reason="operator_command_manifest_identity_mismatch",
                    details={
                        "command_id": command_id,
                        "manifest_id": data["manifest_id"],
                        "manifest_type": data["manifest_type"],
                        "manifest_command_name": data["manifest_command_name"],
                        "command_name": data["command_name"],
                        "manifest_active": data["manifest_active"],
                    },
                )
            )

        if data["authorization_status"] != "pending" or data["command_status"] != "pending":
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_phase6d_status_bounds",
                    reason="operator_command_status_not_phase6d_pending",
                    details={
                        "command_id": command_id,
                        "authorization_status": data["authorization_status"],
                        "command_status": data["command_status"],
                        "completed_at": data["completed_at"],
                    },
                )
            )

        try:
            payload = json.loads(data["command_payload_json"] or "{}")
        except json.JSONDecodeError as exc:
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_payload_json",
                    reason="operator_command_payload_json_invalid",
                    details={"command_id": command_id, "error": str(exc)},
                )
            )
        else:
            if not isinstance(payload, dict):
                violations.append(
                    OperatorCommandLedgerViolation(
                        check="operator_command_payload_json",
                        reason="operator_command_payload_not_object",
                        details={
                            "command_id": command_id,
                            "payload_type": type(payload).__name__,
                        },
                    )
                )

        if data["command_status"] == "pending" and data["task_status"] != "pending":
            violations.append(
                OperatorCommandLedgerViolation(
                    check="operator_command_pending_task_alignment",
                    reason="operator_command_pending_task_not_pending",
                    details={
                        "command_id": command_id,
                        "task_id": data["task_id"],
                        "task_status": data["task_status"],
                    },
                )
            )

    return OperatorCommandLedgerAuditResult(
        passed=not violations,
        checked=checked,
        checked_command_count=len(rows),
        violations=violations,
    )
