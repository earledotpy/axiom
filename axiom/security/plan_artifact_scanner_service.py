from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from axiom.persistence.repositories import (
    get_plan_artifact,
    get_task,
    transition_task_status,
    update_plan_artifact_scan_result,
)
from axiom.security.plan_injection_scanner import PlanInjectionScanner


class PlanArtifactScanServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlanArtifactScanServiceResult:
    artifact_id: int
    task_id: int
    scanner_result: str
    risk_class: str
    artifact_status: str
    parent_task_status: str


class PlanArtifactScannerService:
    """
    Applies PlanInjectionScanner output to persisted plan_artifacts and parent tasks.

    This service does not execute the plan.
    It only records scanner disposition and updates task state according to
    the scanner contract.
    """

    def __init__(self, scanner: PlanInjectionScanner | None = None):
        self.scanner = scanner or PlanInjectionScanner(safe_pass_enabled=False)

    def scan_artifact(
        self,
        artifact_id: int,
        risk_class: str = "ordinary",
    ) -> PlanArtifactScanServiceResult:
        artifact = get_plan_artifact(artifact_id)

        if artifact is None:
            raise PlanArtifactScanServiceError(f"Unknown artifact_id: {artifact_id}")

        task_id = int(artifact["task_id"])
        task = get_task(task_id)

        if task is None:
            raise PlanArtifactScanServiceError(f"Plan artifact has unknown task_id: {task_id}")

        artifact_payload = json.loads(artifact["artifact_json"])

        scanner_output = self.scanner.scan(
            artifact_payload,
            risk_class=risk_class,
            parent_task_status=task["status"],
        )

        update_plan_artifact_scan_result(
            artifact_id=artifact_id,
            scanner_result=scanner_output["scanner_result"],
            risk_class=scanner_output["risk_class"],
            artifact_status=scanner_output["artifact_status"],
            scanner_details=scanner_output,
        )

        parent_task_status = scanner_output["parent_task_status"]

        if task["status"] != parent_task_status:
            transition_task_status(
                task_id=task_id,
                next_status=parent_task_status,
                error_info=scanner_output["reason"]
                if parent_task_status in {"failed", "quarantined", "needs_human_input"}
                else None,
            )

        return PlanArtifactScanServiceResult(
            artifact_id=artifact_id,
            task_id=task_id,
            scanner_result=scanner_output["scanner_result"],
            risk_class=scanner_output["risk_class"],
            artifact_status=scanner_output["artifact_status"],
            parent_task_status=parent_task_status,
        )
