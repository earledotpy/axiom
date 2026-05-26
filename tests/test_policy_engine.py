from axiom.core.policy_engine import PolicyEngine


def base_role_manifest() -> dict:
    return {
        "manifest_id": "role.test.v1",
        "manifest_type": "role",
        "schema_version": "axiom.manifest.v1",
        "manifest_version": "1.0.0",
        "approved_by_panel_version": "v1.11.4",
        "role": {"role_name": "test"},
        "allowed_tools": ["model_gateway.call"],
        "forbidden_tools": [],
        "budget_policy": {
            "max_estimated_input_tokens": 10,
            "max_estimated_output_tokens": 10,
            "max_provider_calls": 1,
            "max_wall_clock_seconds": 30,
        },
        "allowed_capabilities": {
            "model": {
                "allow_model_calls": True,
                "allowed_provider_groups": ["local_classifier"],
                "allow_local_classifier": True,
            },
            "task_queue": {
                "read_scope": "assigned_task",
                "write_scope": "own_result",
                "may_create_tasks": False,
                "may_update_own_result": True,
                "may_update_other_tasks": False,
            },
            "filesystem": {
                "read": False,
                "write": False,
                "allowed_roots": [],
            },
            "operator_control": {
                "allowed_commands": [],
            },
        },
        "network_policy": {
            "mode": "deny_all",
            "allowlist": [],
            "denylist": [],
            "redirect_policy": "deny",
            "timeout_seconds": 0,
            "max_response_bytes": 0,
        },
        "sandbox_policy": {
            "allowed": False,
            "max_ram_mb": 0,
            "max_wall_clock_seconds": 0,
            "network_access": "denied",
        },
        "memory_policy": {
            "read": False,
            "write": False,
            "max_query_results": 0,
            "write_requires_dedupe": True,
        },
        "audit_policy": {
            "log_task_id": True,
            "log_manifest_id": True,
            "log_tool_calls": True,
            "log_policy_denials": True,
        },
    }


def base_operator_manifest() -> dict:
    return {
        "manifest_id": "operator.status.v1",
        "manifest_type": "operator_control",
        "schema_version": "axiom.manifest.v1",
        "manifest_version": "1.0.0",
        "approved_by_panel_version": "v1.11.4",
        "operator_command": {"command_name": "status"},
        "authorization_policy": {},
        "allowed_tools": ["session_controller.status"],
        "forbidden_tools": [],
        "budget_policy": {},
        "allowed_capabilities": {
            "operator_control": {
                "allowed_commands": ["status"],
            },
        },
        "network_policy": {},
        "sandbox_policy": {},
        "memory_policy": {},
        "audit_policy": {},
    }


def model_call_context() -> dict:
    return {
        "provider_group": "local_classifier",
        "estimated_input_tokens": 1,
        "estimated_output_tokens": 1,
        "estimated_provider_calls": 1,
        "estimated_wall_clock_seconds": 1,
    }


def test_policy_engine_denies_unknown_tool_id():
    engine = PolicyEngine()
    manifest = base_role_manifest()

    decision = engine.authorize_tool_use("unknown.tool", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "unknown_tool_id"


def test_policy_engine_denies_tool_not_in_allowed_tools():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    manifest["allowed_tools"] = []

    decision = engine.authorize_tool_use("model_gateway.call", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "tool_not_in_allowed_tools"


def test_policy_engine_denies_tool_in_forbidden_tools():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    manifest["forbidden_tools"] = ["model_gateway.call"]

    decision = engine.authorize_tool_use("model_gateway.call", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "tool_in_forbidden_tools"


def test_policy_engine_denies_when_capability_source_is_false():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    manifest["allowed_capabilities"]["model"]["allow_model_calls"] = False

    decision = engine.authorize_tool_use("model_gateway.call", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "capability_source_not_granted"


def test_policy_engine_allows_when_all_steps_pass_for_role_tool():
    engine = PolicyEngine()
    manifest = base_role_manifest()

    decision = engine.authorize_tool_use(
        "model_gateway.call",
        manifest,
        model_call_context(),
    )

    assert decision.allowed is True
    assert decision.reason == "all_authorization_steps_passed"


def test_policy_engine_denies_missing_additional_check_context():
    engine = PolicyEngine()
    manifest = base_role_manifest()

    decision = engine.authorize_tool_use("model_gateway.call", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "additional_check_failed:provider_group_allowed"


def test_policy_engine_denies_when_budget_estimate_exceeds_limit():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    context = model_call_context()
    context["estimated_provider_calls"] = 2

    decision = engine.authorize_tool_use("model_gateway.call", manifest, context)

    assert decision.allowed is False
    assert decision.reason == "additional_check_failed:budget_policy_not_exceeded"


def test_policy_engine_denies_session_controller_with_role_manifest():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    manifest["allowed_tools"] = ["session_controller.status"]
    manifest["allowed_capabilities"]["operator_control"]["allowed_commands"] = ["status"]

    decision = engine.authorize_tool_use("session_controller.status", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "manifest_type_mismatch"


def test_policy_engine_allows_session_controller_with_operator_control_manifest():
    engine = PolicyEngine()
    manifest = base_operator_manifest()

    decision = engine.authorize_tool_use("session_controller.status", manifest, {})

    assert decision.allowed is True
    assert decision.reason == "all_authorization_steps_passed"


def test_policy_engine_denies_operator_control_command_mismatch_at_capability_source():
    engine = PolicyEngine()
    manifest = base_operator_manifest()
    manifest["operator_command"]["command_name"] = "resume"
    manifest["allowed_capabilities"]["operator_control"]["allowed_commands"] = ["resume"]

    decision = engine.authorize_tool_use("session_controller.status", manifest, {})

    assert decision.allowed is False
    assert decision.reason == "capability_source_not_granted"


def test_policy_engine_denies_missing_required_policy_object():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    del manifest["budget_policy"]

    decision = engine.validate_manifest_completeness(manifest)

    assert decision.allowed is False
    assert decision.reason == "missing_required_policy_object"


def test_policy_engine_denies_unknown_manifest_type():
    engine = PolicyEngine()
    manifest = base_role_manifest()
    manifest["manifest_type"] = "unknown"

    decision = engine.validate_manifest_completeness(manifest)

    assert decision.allowed is False
    assert decision.reason == "unknown_manifest_type"
