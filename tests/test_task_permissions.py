import json

from axiom.persistence.repositories import (
    bind_task_permissions,
    create_session,
    create_task,
    get_task_permission,
    get_task_permissions,
)

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def test_bind_task_permissions_creates_permission_row():
    session_id = create_session(operator_id="task-permissions-create")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-task-permissions-create",
        task_class="system_maintenance",
        task_type="task_permissions_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    permission_id = bind_task_permissions(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        granted_capabilities={
            "model": {
                "allow_model_calls": True,
            }
        },
        granted_tools=["model_gateway.call"],
    )

    permission = get_task_permission(permission_id)

    assert permission is not None
    assert permission["permission_id"] == permission_id
    assert permission["task_id"] == task_id
    assert permission["manifest_id"] == TOOL_MAP_MANIFEST_ID
    assert json.loads(permission["granted_tools_json"]) == ["model_gateway.call"]
    assert json.loads(permission["granted_capabilities_json"]) == {
        "model": {
            "allow_model_calls": True,
        }
    }


def test_get_task_permissions_returns_all_permissions_for_task():
    session_id = create_session(operator_id="task-permissions-list")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-task-permissions-list",
        task_class="system_maintenance",
        task_type="task_permissions_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    first_id = bind_task_permissions(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        granted_capabilities={"model": {"allow_model_calls": True}},
        granted_tools=["model_gateway.call"],
    )
    second_id = bind_task_permissions(
        task_id=task_id,
        manifest_id=TOOL_MAP_MANIFEST_ID,
        granted_capabilities={"filesystem": {"read": True}},
        granted_tools=["filesystem.read"],
    )

    rows = get_task_permissions(task_id)
    ids = [row["permission_id"] for row in rows]

    assert first_id in ids
    assert second_id in ids


def test_bind_task_permissions_rejects_unknown_task_id():
    try:
        bind_task_permissions(
            task_id=999999999,
            manifest_id=TOOL_MAP_MANIFEST_ID,
            granted_capabilities={},
            granted_tools=[],
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown task_id was accepted")


def test_bind_task_permissions_rejects_unknown_manifest_id():
    session_id = create_session(operator_id="task-permissions-unknown-manifest")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-task-permissions-unknown-manifest",
        task_class="system_maintenance",
        task_type="task_permissions_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    try:
        bind_task_permissions(
            task_id=task_id,
            manifest_id="security.unknown_manifest.v1",
            granted_capabilities={},
            granted_tools=[],
        )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Unknown manifest_id was accepted")


def test_get_task_permissions_returns_empty_list_for_task_without_permissions():
    session_id = create_session(operator_id="task-permissions-empty")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-task-permissions-empty",
        task_class="system_maintenance",
        task_type="task_permissions_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    assert get_task_permissions(task_id) == []
