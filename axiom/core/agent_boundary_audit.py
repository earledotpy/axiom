from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from axiom.persistence.db import get_connection


PHASE5_AGENT_ROLES: dict[str, dict[str, str]] = {
    "goal_planner": {
        "manifest_id": "role.goal_planner.v1",
        "task_class": "goal_planning",
    },
    "task_planner": {
        "manifest_id": "role.task_planner.v1",
        "task_class": "task_planning",
    },
    "tool_executor": {
        "manifest_id": "role.tool_executor.v1",
        "task_class": "tool_execution",
    },
    "result_verifier": {
        "manifest_id": "role.result_verifier.v1",
        "task_class": "result_verification",
    },
}

RUNTIME_CALL_FIELDS = (
    "tools_used",
    "model_calls",
    "cloud_cascade_calls",
    "network_calls",
    "sandbox_calls",
)


@dataclass(frozen=True)
class AgentBoundaryViolation:
    check: str
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentBoundaryAuditResult:
    passed: bool
    checked: list[str]
    violations: list[AgentBoundaryViolation]
    checked_task_count: int

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "checked_task_count": self.checked_task_count,
            "violation_count": self.violation_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


def _decode_result_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}

    decoded: Any = value
    for _ in range(2):
        if isinstance(decoded, str):
            decoded = json.loads(decoded)

    if not isinstance(decoded, dict):
        raise ValueError("task result_json did not decode to an object")

    return decoded


def _audit_active_agent_role_manifests() -> list[AgentBoundaryViolation]:
    violations: list[AgentBoundaryViolation] = []

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT manifest_id, manifest_type, role_name, active
            FROM manifest_fingerprints
            WHERE manifest_id IN (?, ?, ?, ?)
            """,
            tuple(item["manifest_id"] for item in PHASE5_AGENT_ROLES.values()),
        ).fetchall()

    by_manifest_id = {row["manifest_id"]: dict(row) for row in rows}
    for role_name, config in PHASE5_AGENT_ROLES.items():
        manifest_id = config["manifest_id"]
        row = by_manifest_id.get(manifest_id)
        if row is None:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_agent_role_manifests_active",
                    reason="missing_agent_role_manifest",
                    details={"role_name": role_name, "manifest_id": manifest_id},
                )
            )
            continue

        if row["manifest_type"] != "role" or row["role_name"] != role_name:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_agent_role_manifests_active",
                    reason="agent_manifest_identity_mismatch",
                    details={
                        "role_name": role_name,
                        "manifest_id": manifest_id,
                        "manifest_type": row["manifest_type"],
                        "row_role_name": row["role_name"],
                    },
                )
            )

        if row["active"] != 1:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_agent_role_manifests_active",
                    reason="agent_role_manifest_inactive",
                    details={"role_name": role_name, "manifest_id": manifest_id},
                )
            )

    return violations


def _audit_completed_agent_tasks() -> tuple[int, list[AgentBoundaryViolation]]:
    violations: list[AgentBoundaryViolation] = []
    task_classes = tuple(item["task_class"] for item in PHASE5_AGENT_ROLES.values())
    expected_by_class = {
        item["task_class"]: {
            "agent_name": role_name,
            "manifest_id": item["manifest_id"],
        }
        for role_name, item in PHASE5_AGENT_ROLES.items()
    }

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT task_id, session_id, task_class, status, manifest_id, result_json
            FROM tasks
            WHERE task_class IN (?, ?, ?, ?)
            ORDER BY task_id
            """,
            task_classes,
        ).fetchall()

        provider_rows = conn.execute(
            """
            SELECT task_id, COUNT(*) AS usage_count
            FROM provider_usage
            WHERE task_id IN (
                SELECT task_id FROM tasks WHERE task_class IN (?, ?, ?, ?)
            )
            GROUP BY task_id
            """,
            task_classes,
        ).fetchall()

    provider_usage_by_task = {
        int(row["task_id"]): int(row["usage_count"]) for row in provider_rows
    }

    for row in rows:
        task = dict(row)
        task_id = int(task["task_id"])
        if provider_usage_by_task.get(task_id, 0):
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_agent_tasks_do_not_record_provider_usage",
                    reason="agent_task_provider_usage_recorded",
                    details={
                        "task_id": task_id,
                        "usage_count": provider_usage_by_task[task_id],
                    },
                )
            )

        if task["status"] != "completed":
            continue

        expected = expected_by_class[str(task["task_class"])]
        try:
            result_json = _decode_result_json(task["result_json"])
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_completed_agent_results_parse",
                    reason="agent_result_json_invalid",
                    details={"task_id": task_id, "error": str(exc)},
                )
            )
            continue

        if result_json.get("executor") != expected["agent_name"]:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_completed_agent_results_identity",
                    reason="agent_executor_mismatch",
                    details={
                        "task_id": task_id,
                        "expected": expected["agent_name"],
                        "actual": result_json.get("executor"),
                    },
                )
            )

        if result_json.get("manifest_id") != expected["manifest_id"]:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_completed_agent_results_identity",
                    reason="agent_manifest_mismatch",
                    details={
                        "task_id": task_id,
                        "expected": expected["manifest_id"],
                        "actual": result_json.get("manifest_id"),
                    },
                )
            )

        for field in RUNTIME_CALL_FIELDS:
            if result_json.get(field) not in ([], None):
                violations.append(
                    AgentBoundaryViolation(
                        check="phase5_completed_agent_results_no_runtime_calls",
                        reason="agent_runtime_call_field_non_empty",
                        details={
                            "task_id": task_id,
                            "field": field,
                            "value": result_json.get(field),
                        },
                    )
                )

        if result_json.get("autonomous_operation_enabled") is not False:
            violations.append(
                AgentBoundaryViolation(
                    check="phase5_completed_agent_results_manual_only",
                    reason="agent_result_does_not_report_manual_only_boundary",
                    details={
                        "task_id": task_id,
                        "autonomous_operation_enabled": result_json.get(
                            "autonomous_operation_enabled"
                        ),
                    },
                )
            )

    return len(rows), violations


def audit_agent_boundary() -> AgentBoundaryAuditResult:
    checked = [
        "phase5_agent_role_manifests_active",
        "phase5_agent_tasks_do_not_record_provider_usage",
        "phase5_completed_agent_results_parse",
        "phase5_completed_agent_results_identity",
        "phase5_completed_agent_results_no_runtime_calls",
        "phase5_completed_agent_results_manual_only",
    ]
    violations = _audit_active_agent_role_manifests()
    checked_task_count, task_violations = _audit_completed_agent_tasks()
    violations.extend(task_violations)

    return AgentBoundaryAuditResult(
        passed=not violations,
        checked=checked,
        violations=violations,
        checked_task_count=checked_task_count,
    )
