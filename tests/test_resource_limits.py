import pytest

from axiom.core.resource_limits import ResourceLimitError, ResourceLimitEvaluator
from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_resource_usage,
    get_task,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="resource-limit-evaluator")
    return create_task(
        session_id=session_id,
        chain_id="chain-resource-limit-evaluator",
        task_class="system_maintenance",
        task_type="resource_limit_evaluator_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def test_resource_limit_status_within_limit():
    assert ResourceLimitEvaluator.status_for_limit(10, 60) == "within_limit"


def test_resource_limit_status_exceeded():
    assert ResourceLimitEvaluator.status_for_limit(61, 60) == "exceeded"


def test_resource_limit_status_unknown_without_limit():
    assert ResourceLimitEvaluator.status_for_limit(10, None) == "unknown"


def test_resource_limit_status_rejects_negative_amount():
    with pytest.raises(ValueError):
        ResourceLimitEvaluator.status_for_limit(-1, 60)


def test_resource_limit_status_rejects_negative_limit():
    with pytest.raises(ValueError):
        ResourceLimitEvaluator.status_for_limit(1, -60)


def test_record_and_evaluate_within_limit_records_usage_without_task_block():
    task_id = make_task()

    decision = ResourceLimitEvaluator().record_and_evaluate(
        task_id=task_id,
        resource_type="sandbox_wall_clock_seconds",
        amount=10,
        limit_value=60,
        details={"phase": "test"},
    )

    usage = get_resource_usage(decision.usage_id)
    task = get_task(task_id)

    assert decision.status == "within_limit"
    assert decision.task_status_changed is False
    assert usage["status"] == "within_limit"
    assert usage["resource_type"] == "sandbox_wall_clock_seconds"
    assert task["status"] == "pending"


def test_record_and_evaluate_exceeded_blocks_pending_task():
    task_id = make_task()

    decision = ResourceLimitEvaluator().record_and_evaluate(
        task_id=task_id,
        resource_type="sandbox_wall_clock_seconds",
        amount=61,
        limit_value=60,
        details={"phase": "test"},
    )

    usage = get_resource_usage(decision.usage_id)
    task = get_task(task_id)

    assert decision.status == "exceeded"
    assert decision.task_status_changed is True
    assert usage["status"] == "exceeded"
    assert task["status"] == "blocked_resource_limit"
    assert "Resource limit exceeded" in task["error_info"]


def test_record_and_evaluate_exceeded_can_record_without_blocking_task():
    task_id = make_task()

    decision = ResourceLimitEvaluator().record_and_evaluate(
        task_id=task_id,
        resource_type="context_bundle_kb",
        amount=501,
        limit_value=500,
        block_task_on_exceeded=False,
    )

    task = get_task(task_id)

    assert decision.status == "exceeded"
    assert decision.task_status_changed is False
    assert task["status"] == "pending"


def test_record_and_evaluate_unknown_task_rejected():
    with pytest.raises(ResourceLimitError):
        ResourceLimitEvaluator().record_and_evaluate(
            task_id=999999999,
            resource_type="context_bundle_kb",
            amount=1,
            limit_value=500,
        )
