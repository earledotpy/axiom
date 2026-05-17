from axiom.persistence.repositories import (
    create_session,
    create_task,
    get_active_manifest_fingerprints,
    get_manifest_fingerprint,
    get_session,
    get_task,
    log_security_event,
    log_session_event,
    record_provider_usage,
    update_task_status,
)


def test_repository_create_and_get_session():
    session_id = create_session(operator_id="test-operator")

    session = get_session(session_id)

    assert session is not None
    assert session["session_id"] == session_id
    assert session["operator_id"] == "test-operator"


def test_repository_log_session_event():
    session_id = create_session(operator_id="event-test")

    event_id = log_session_event(
        session_id=session_id,
        event_type="repository_test",
        details={"ok": True},
    )

    assert isinstance(event_id, int)
    assert event_id > 0


def test_repository_log_security_event():
    event_id = log_security_event(
        event_type="repository_security_test",
        severity="info",
        reason="test",
        details={"ok": True},
    )

    assert isinstance(event_id, int)
    assert event_id > 0


def test_repository_get_active_manifest_fingerprints_contains_tool_map():
    rows = get_active_manifest_fingerprints()
    manifest_ids = {row["manifest_id"] for row in rows}

    assert "security.tool_capability_map.v1" in manifest_ids


def test_repository_get_manifest_fingerprint_for_tool_map():
    row = get_manifest_fingerprint("security.tool_capability_map.v1")

    assert row is not None
    assert row["manifest_type"] == "tool_capability_map"


def test_repository_create_get_and_update_task():
    session_id = create_session(operator_id="task-test")
    manifest = get_manifest_fingerprint("security.tool_capability_map.v1")

    task_id = create_task(
        session_id=session_id,
        chain_id="chain-test",
        task_class="system_maintenance",
        task_type="repository_test",
        goal_text="verify task repository",
        input_json={"input": True},
        manifest_id=manifest["manifest_id"],
    )

    task = get_task(task_id)

    assert task is not None
    assert task["task_id"] == task_id
    assert task["status"] == "pending"
    assert task["manifest_id"] == "security.tool_capability_map.v1"

    update_task_status(
        task_id=task_id,
        status="completed",
        result_text="ok",
        result_json={"done": True},
    )

    updated = get_task(task_id)

    assert updated["status"] == "completed"
    assert updated["result_text"] == "ok"
    assert updated["completed_at"] is not None


def test_repository_record_provider_usage_rejects_invalid_provider():
    session_id = create_session(operator_id="provider-test")

    try:
        record_provider_usage(
            session_id=session_id,
            provider="paid_unknown_provider",
            status="started",
        )
    except Exception as exc:
        assert "CHECK" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Invalid provider was accepted")
