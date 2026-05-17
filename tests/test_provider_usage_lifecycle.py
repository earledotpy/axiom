from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_provider_usage,
    record_provider_usage,
    update_provider_usage_status,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_provider_usage(status="started"):
    session_id = create_session(operator_id="provider-usage-lifecycle")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-provider-usage-lifecycle",
        task_class="system_maintenance",
        task_type="provider_usage_lifecycle_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    usage_id = record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status=status,
        model="qwen3:4b",
    )
    return usage_id


def test_update_provider_usage_status_to_completed_sets_actuals_and_completed_at():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="completed",
        estimated_input_tokens=10,
        estimated_output_tokens=20,
        actual_input_tokens=11,
        actual_output_tokens=21,
        charged_input_estimate=10,
        charged_output_estimate=20,
    )

    row = get_provider_usage(usage_id)

    assert row["status"] == "completed"
    assert row["estimated_input_tokens"] == 10
    assert row["estimated_output_tokens"] == 20
    assert row["actual_input_tokens"] == 11
    assert row["actual_output_tokens"] == 21
    assert row["charged_input_estimate"] == 10
    assert row["charged_output_estimate"] == 20
    assert row["completed_at"] is not None


def test_update_provider_usage_status_to_failed_sets_error_and_completed_at():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="failed",
        error_info="simulated failure",
    )

    row = get_provider_usage(usage_id)

    assert row["status"] == "failed"
    assert row["error_info"] == "simulated failure"
    assert row["completed_at"] is not None


def test_update_provider_usage_status_to_rate_limited_sets_completed_at():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="rate_limited",
        error_info="rate limited",
    )

    row = get_provider_usage(usage_id)

    assert row["status"] == "rate_limited"
    assert row["error_info"] == "rate limited"
    assert row["completed_at"] is not None


def test_update_provider_usage_status_to_quota_exhausted_sets_completed_at():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="quota_exhausted",
        error_info="quota exhausted",
    )

    row = get_provider_usage(usage_id)

    assert row["status"] == "quota_exhausted"
    assert row["error_info"] == "quota exhausted"
    assert row["completed_at"] is not None


def test_update_provider_usage_status_to_abandoned_session_crash_sets_completed_at():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="abandoned_session_crash",
        error_info="session crashed",
    )

    row = get_provider_usage(usage_id)

    assert row["status"] == "abandoned_session_crash"
    assert row["error_info"] == "session crashed"
    assert row["completed_at"] is not None


def test_update_provider_usage_status_preserves_existing_values_when_omitted():
    usage_id = make_provider_usage()

    update_provider_usage_status(
        usage_id=usage_id,
        status="completed",
        estimated_input_tokens=10,
    )

    update_provider_usage_status(
        usage_id=usage_id,
        status="completed",
        actual_input_tokens=11,
    )

    row = get_provider_usage(usage_id)

    assert row["estimated_input_tokens"] == 10
    assert row["actual_input_tokens"] == 11


def test_update_provider_usage_status_rejects_invalid_status():
    usage_id = make_provider_usage()

    try:
        update_provider_usage_status(
            usage_id=usage_id,
            status="invalid_status",
        )
    except Exception as exc:
        assert "CHECK" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Invalid provider usage status was accepted")
