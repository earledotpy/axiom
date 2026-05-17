import json

import pytest

from axiom.persistence.repositories import (
    create_plan_artifact,
    create_session,
    create_task,
    get_plan_artifact,
    get_task,
)
from axiom.security.plan_artifact_scanner_service import (
    PlanArtifactScanServiceError,
    PlanArtifactScannerService,
)
from axiom.security.plan_injection_scanner import PlanInjectionScanner

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_artifact(artifact_json=None) -> tuple[int, int]:
    session_id = create_session(operator_id="plan-artifact-scanner-service")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-plan-artifact-scanner-service",
        task_class="task_planning",
        task_type="plan_artifact_scanner_service_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    artifact_id = create_plan_artifact(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        artifact_json=artifact_json or {"plan": "test"},
        artifact_type="task_plan",
    )
    return task_id, artifact_id


def test_scan_service_safe_pass_disabled_ordinary_checkpoint_blocks_artifact_and_task():
    task_id, artifact_id = make_artifact()

    service = PlanArtifactScannerService(
        scanner=PlanInjectionScanner(safe_pass_enabled=False)
    )
    result = service.scan_artifact(artifact_id, risk_class="ordinary")

    artifact = get_plan_artifact(artifact_id)
    task = get_task(task_id)

    assert result.scanner_result == "safe_pass_disabled"
    assert result.risk_class == "ordinary"
    assert result.artifact_status == "checkpoint_blocked"
    assert result.parent_task_status == "needs_human_input"

    assert artifact["scanner_result"] == "safe_pass_disabled"
    assert artifact["risk_class"] == "ordinary"
    assert artifact["artifact_status"] == "checkpoint_blocked"
    assert json.loads(artifact["scanner_details_json"])["scanner_result"] == "safe_pass_disabled"

    assert task["status"] == "needs_human_input"
    assert "Safe-pass is disabled" in task["error_info"]


def test_scan_service_safe_pass_disabled_high_risk_quarantines_artifact_and_task():
    task_id, artifact_id = make_artifact()

    service = PlanArtifactScannerService(
        scanner=PlanInjectionScanner(safe_pass_enabled=False)
    )
    result = service.scan_artifact(artifact_id, risk_class="high_risk")

    artifact = get_plan_artifact(artifact_id)
    task = get_task(task_id)

    assert result.scanner_result == "safe_pass_disabled"
    assert result.risk_class == "high_risk"
    assert result.artifact_status == "quarantined"
    assert result.parent_task_status == "quarantined"

    assert artifact["artifact_status"] == "quarantined"
    assert artifact["risk_class"] == "high_risk"
    assert task["status"] == "quarantined"
    assert "Safe-pass is disabled" in task["error_info"]


def test_scan_service_passed_artifact_moves_task_to_running():
    task_id, artifact_id = make_artifact()

    service = PlanArtifactScannerService(
        scanner=PlanInjectionScanner(safe_pass_enabled=True)
    )
    result = service.scan_artifact(artifact_id, risk_class="ordinary")

    artifact = get_plan_artifact(artifact_id)
    task = get_task(task_id)

    assert result.scanner_result == "passed"
    assert result.artifact_status == "scanner_passed"
    assert result.parent_task_status == "running"

    assert artifact["scanner_result"] == "passed"
    assert artifact["artifact_status"] == "scanner_passed"
    assert task["status"] == "running"


def test_scan_service_rejects_unknown_artifact_id():
    service = PlanArtifactScannerService()

    with pytest.raises(PlanArtifactScanServiceError):
        service.scan_artifact(999999999, risk_class="ordinary")
