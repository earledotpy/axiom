import json

from axiom.persistence.repositories import (
    create_plan_artifact,
    create_session,
    create_task,
    get_plan_artifact,
    get_plan_artifacts_for_task,
    update_plan_artifact_scan_result,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="plan-artifact-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-plan-artifact-test",
        task_class="task_planning",
        task_type="plan_artifact_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def test_create_and_get_plan_artifact():
    task_id = make_task()

    artifact_id = create_plan_artifact(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        artifact_json={"steps": ["one", "two"]},
    )

    artifact = get_plan_artifact(artifact_id)

    assert artifact is not None
    assert artifact["artifact_id"] == artifact_id
    assert artifact["task_id"] == task_id
    assert artifact["manifest_id"] == TOOL_MAP_MANIFEST_ID
    assert artifact["artifact_type"] == "task_plan"
    assert artifact["artifact_status"] == "draft"
    assert artifact["scanner_result"] == "not_scanned"
    assert json.loads(artifact["artifact_json"]) == {"steps": ["one", "two"]}


def test_get_plan_artifacts_for_task_returns_all_rows():
    task_id = make_task()

    first_id = create_plan_artifact(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        artifact_json={"plan": 1},
    )
    second_id = create_plan_artifact(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        artifact_json={"plan": 2},
    )

    rows = get_plan_artifacts_for_task(task_id)
    ids = [row["artifact_id"] for row in rows]

    assert first_id in ids
    assert second_id in ids


def test_update_plan_artifact_scan_result():
    task_id = make_task()
    artifact_id = create_plan_artifact(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        artifact_json={"plan": "scan me"},
    )

    update_plan_artifact_scan_result(
        artifact_id=artifact_id,
        scanner_result="safe_pass_disabled",
        risk_class="ordinary",
        artifact_status="checkpoint_blocked",
        scanner_details={"reason": "safe-pass disabled"},
    )

    artifact = get_plan_artifact(artifact_id)

    assert artifact["scanner_result"] == "safe_pass_disabled"
    assert artifact["risk_class"] == "ordinary"
    assert artifact["artifact_status"] == "checkpoint_blocked"
    assert json.loads(artifact["scanner_details_json"]) == {"reason": "safe-pass disabled"}


def test_create_plan_artifact_rejects_unknown_task_id():
    try:
        create_plan_artifact(
            task_id=999999999,
            manifest_id=TOOL_MAP_MANIFEST_ID,
            artifact_json={"bad": True},
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown task_id was accepted")


def test_create_plan_artifact_rejects_unknown_manifest_id():
    task_id = make_task()

    try:
        create_plan_artifact(
            task_id=task_id,
            manifest_id="security.unknown_manifest.v1",
            artifact_json={"bad": True},
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown manifest_id was accepted")
