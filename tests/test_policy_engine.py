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
        "budget_policy": {},
        "allowed_capabilities": {
            "model": {
                "allow_model_calls": True,
            },
            "operator_control": {
                "allowed_commands": [],
            },
        },
        "network_policy": {},
        "sandbox_policy": {},
        "memory_policy": {},
        "audit_policy": {},
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

    decision = engine.authorize_tool_use("model_gateway.call", manifest, {})

    assert decision.allowed is True
    assert decision.reason == "all_authorization_steps_passed"


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