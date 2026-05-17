from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.persistence.repositories import (
    get_task,
    record_resource_usage,
    transition_task_status,
)


class ResourceLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResourceLimitDecision:
    task_id: int
    resource_type: str
    amount: float
    limit_value: float | None
    status: str
    usage_id: int
    task_status_changed: bool


class ResourceLimitEvaluator:
    """
    Passive resource-limit evaluator.

    It records usage and may mark a task blocked_resource_limit when a measured
    amount exceeds a supplied limit. It does not execute tools or sandbox code.
    """

    def record_and_evaluate(
        self,
        task_id: int,
        resource_type: str,
        amount: int | float,
        limit_value: int | float | None = None,
        details: dict[str, Any] | None = None,
        block_task_on_exceeded: bool = True,
    ) -> ResourceLimitDecision:
        task = get_task(task_id)
        if task is None:
            raise ResourceLimitError(f"Unknown task_id: {task_id}")

        status = self.status_for_limit(amount, limit_value)

        usage_id = record_resource_usage(
            task_id=task_id,
            resource_type=resource_type,
            amount=amount,
            limit_value=limit_value,
            status=status,
            details=details,
        )

        task_status_changed = False

        if status == "exceeded" and block_task_on_exceeded:
            if task["status"] in {"pending", "running", "needs_human_input"}:
                transition_task_status(
                    task_id=task_id,
                    next_status="blocked_resource_limit",
                    error_info=f"Resource limit exceeded: {resource_type}",
                )
                task_status_changed = True

        return ResourceLimitDecision(
            task_id=task_id,
            resource_type=resource_type,
            amount=float(amount),
            limit_value=float(limit_value) if limit_value is not None else None,
            status=status,
            usage_id=usage_id,
            task_status_changed=task_status_changed,
        )

    @staticmethod
    def status_for_limit(
        amount: int | float,
        limit_value: int | float | None,
    ) -> str:
        if amount < 0:
            raise ValueError("amount must be non-negative")

        if limit_value is not None and limit_value < 0:
            raise ValueError("limit_value must be non-negative")

        if limit_value is None:
            return "unknown"

        if amount <= limit_value:
            return "within_limit"

        return "exceeded"
