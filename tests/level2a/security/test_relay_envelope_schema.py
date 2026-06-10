import pytest

from axiom.core.orchestrator.contracts import ContractValidationError, validate_relay_envelope


def _valid_envelope() -> dict:
    return {
        "relay_envelope_version": "2A.1",
        "envelope_id": "ENV-12345678-1234-4234-9234-123456789abc",
        "docket_id": "DK-2026-0003",
        "mandate_id": "MND-ACCEPTED-2026-0003-PHASE1-ORCHESTRATOR-IMPLEMENTATION",
        "source_role": "operator_console",
        "target_role": "orchestrator",
        "artifact_type": "patch_artifact",
        "artifact_ref": "governance/05_handoffs/review.json",
        "artifact_sha256": "sha256:" + "a" * 64,
        "allowed_action_type": "record_artifact",
        "blocked_action_indicators": [],
        "created_at": "2026-06-04T08:15:00Z",
        "nonce": "nonce_v1_" + "b" * 64,
        "canonicalization": "RFC8785",
        "schema_hash": "sha256:" + "c" * 64,
    }


def test_relay_envelope_accepts_valid_inert_artifact_route():
    assert validate_relay_envelope(_valid_envelope())


def test_relay_envelope_rejects_unknown_fields():
    envelope = _valid_envelope()
    envelope["extra"] = "not allowed"
    with pytest.raises(ContractValidationError, match="unknown fields"):
        validate_relay_envelope(envelope)


def test_t06_shell_command_relay_frame_rejected():
    envelope = _valid_envelope()
    envelope["blocked_action_indicators"] = ["shell_command_frame"]
    with pytest.raises(ContractValidationError, match="ERR_RELAY_BLOCKED_ACTION"):
        validate_relay_envelope(envelope)


def test_t07_peer_to_peer_agent_routing_frame_rejected():
    envelope = _valid_envelope()
    envelope["blocked_action_indicators"] = ["peer_to_peer_agent_routing_frame"]
    with pytest.raises(ContractValidationError, match="ERR_RELAY_BLOCKED_ACTION"):
        validate_relay_envelope(envelope)


def test_web_chat_is_source_only_not_target_role():
    envelope = _valid_envelope()
    envelope["source_role"] = "web_chat_advisory_surface"
    assert validate_relay_envelope(envelope)
    envelope["target_role"] = "web_chat_advisory_surface"
    with pytest.raises(ContractValidationError, match="invalid target_role"):
        validate_relay_envelope(envelope)
