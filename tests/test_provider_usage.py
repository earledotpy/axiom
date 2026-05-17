from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_provider_usage,
    get_provider_usage_for_session,
    get_provider_usage_for_task,
    record_provider_usage,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_session_and_task():
    session_id = create_session(operator_id="provider-usage-test")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-provider-usage-test",
        task_class="system_maintenance",
        task_type="provider_usage_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    return session_id, task_id


def test_record_and_get_provider_usage():
    session_id, task_id = make_session_and_task()

    usage_id = record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status="completed",
        model="qwen3:4b",
        estimated_input_tokens=10,
        estimated_output_tokens=20,
        actual_input_tokens=11,
        actual_output_tokens=21,
        actuals_unavailable=0,
        charged_input_estimate=10,
        charged_output_estimate=20,
    )

    row = get_provider_usage(usage_id)

    assert row is not None
    assert row["usage_id"] == usage_id
    assert row["session_id"] == session_id
    assert row["task_id"] == task_id
    assert row["provider"] == "ollama_local"
    assert row["status"] == "completed"
    assert row["model"] == "qwen3:4b"
    assert row["estimated_input_tokens"] == 10
    assert row["estimated_output_tokens"] == 20
    assert row["actual_input_tokens"] == 11
    assert row["actual_output_tokens"] == 21
    assert row["actuals_unavailable"] == 0
    assert row["charged_input_estimate"] == 10
    assert row["charged_output_estimate"] == 20
    assert row["completed_at"] is not None


def test_get_provider_usage_for_task_returns_rows():
    session_id, task_id = make_session_and_task()

    first_id = record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status="completed",
        model="qwen3:4b",
    )
    second_id = record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status="completed",
        model="qwen3:4b",
    )

    rows = get_provider_usage_for_task(task_id)
    ids = {row["usage_id"] for row in rows}

    assert first_id in ids
    assert second_id in ids


def test_get_provider_usage_for_session_returns_rows():
    session_id, task_id = make_session_and_task()

    usage_id = record_provider_usage(
        session_id=session_id,
        task_id=task_id,
        provider="ollama_local",
        status="completed",
        model="qwen3:4b",
    )

    rows = get_provider_usage_for_session(session_id)
    ids = {row["usage_id"] for row in rows}

    assert usage_id in ids


def test_record_provider_usage_rejects_invalid_provider():
    session_id, task_id = make_session_and_task()

    try:
        record_provider_usage(
            session_id=session_id,
            task_id=task_id,
            provider="paid_unknown_provider",
            status="completed",
        )
    except Exception as exc:
        assert "CHECK" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Invalid provider was accepted")


def test_record_provider_usage_rejects_unknown_session_id():
    _session_id, task_id = make_session_and_task()

    try:
        record_provider_usage(
            session_id=999999999,
            task_id=task_id,
            provider="ollama_local",
            status="completed",
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown session_id was accepted")


def test_record_provider_usage_rejects_unknown_task_id():
    session_id, _task_id = make_session_and_task()

    try:
        record_provider_usage(
            session_id=session_id,
            task_id=999999999,
            provider="ollama_local",
            status="completed",
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown task_id was accepted")
