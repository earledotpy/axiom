import json

from axiom.core.context_builder import ContextBuilder
from axiom.core.token_estimator import TokenEstimator
from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_resource_usage,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="resource-accounting-integration")
    return create_task(
        session_id=session_id,
        chain_id="chain-resource-accounting-integration",
        task_class="system_maintenance",
        task_type="resource_accounting_integration_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def test_token_estimator_records_estimated_input_tokens():
    task_id = make_task()

    usage_id = TokenEstimator().record_estimated_input_tokens(
        task_id=task_id,
        text="a" * 100,
        limit_value=100,
    )

    row = get_resource_usage(usage_id)

    assert row is not None
    assert row["task_id"] == task_id
    assert row["resource_type"] == "estimated_input_tokens"
    assert row["amount"] == 38
    assert row["limit_value"] == 100
    assert row["status"] == "within_limit"

    details = json.loads(row["details_json"])
    assert details["fallback_margin"] == 1.5
    assert details["text_length"] == 100


def test_token_estimator_records_estimated_output_tokens_over_limit():
    task_id = make_task()

    usage_id = TokenEstimator().record_estimated_output_tokens(
        task_id=task_id,
        text="a" * 100,
        limit_value=10,
    )

    row = get_resource_usage(usage_id)

    assert row is not None
    assert row["resource_type"] == "estimated_output_tokens"
    assert row["amount"] == 38
    assert row["limit_value"] == 10
    assert row["status"] == "exceeded"


def test_context_builder_records_context_bundle_kb():
    task_id = make_task()

    usage_id = ContextBuilder(max_bundle_kb=500).record_bundle_size(
        task_id=task_id,
        payload={"message": "hello"},
    )

    row = get_resource_usage(usage_id)

    assert row is not None
    assert row["task_id"] == task_id
    assert row["resource_type"] == "context_bundle_kb"
    assert row["amount"] > 0
    assert row["limit_value"] == 500
    assert row["status"] == "within_limit"

    details = json.loads(row["details_json"])
    assert details["size_bytes"] > 0
    assert details["max_bundle_bytes"] == 512000
