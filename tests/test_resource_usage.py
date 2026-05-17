import json

import pytest

from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_resource_usage,
    get_resource_usage_for_task,
    record_resource_usage,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="resource-usage-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-resource-usage-test",
        task_class="system_maintenance",
        task_type="resource_usage_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def test_record_resource_usage_for_task():
    task_id = make_task()

    usage_id = record_resource_usage(
        task_id=task_id,
        resource_type="estimated_input_tokens",
        amount=100,
        limit_value=500,
        status="within_limit",
        details={"provider": "test"},
    )

    row = get_resource_usage(usage_id)

    assert row is not None
    assert row["usage_id"] == usage_id
    assert row["task_id"] == task_id
    assert row["resource_type"] == "estimated_input_tokens"
    assert row["amount"] == 100
    assert row["limit_value"] == 500
    assert row["status"] == "within_limit"
    assert json.loads(row["details_json"]) == {"provider": "test"}


def test_get_resource_usage_for_task_returns_rows():
    task_id = make_task()

    first_id = record_resource_usage(
        task_id=task_id,
        resource_type="sandbox_wall_clock_seconds",
        amount=10,
        limit_value=60,
        status="within_limit",
        details={"phase": "first"},
    )
    second_id = record_resource_usage(
        task_id=task_id,
        resource_type="sandbox_ram_mb",
        amount=128,
        limit_value=256,
        status="within_limit",
        details={"phase": "second"},
    )

    rows = get_resource_usage_for_task(task_id)
    ids = {row["usage_id"] for row in rows}

    assert first_id in ids
    assert second_id in ids


def test_record_resource_usage_rejects_negative_amount():
    task_id = make_task()

    with pytest.raises(ValueError):
        record_resource_usage(
            task_id=task_id,
            resource_type="estimated_input_tokens",
            amount=-1,
            status="within_limit",
        )


def test_record_resource_usage_rejects_negative_limit_value():
    task_id = make_task()

    with pytest.raises(ValueError):
        record_resource_usage(
            task_id=task_id,
            resource_type="estimated_input_tokens",
            amount=1,
            limit_value=-1,
            status="within_limit",
        )


def test_record_resource_usage_rejects_unknown_task_id():
    try:
        record_resource_usage(
            task_id=999999999,
            resource_type="estimated_input_tokens",
            amount=1,
            status="within_limit",
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown task_id was accepted")
