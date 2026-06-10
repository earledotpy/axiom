import pytest

from axiom.security.level2a.sealing import generate_ed25519_keypair, sign_payload
from axiom.security.level2a.validators import signature_payload, validate_sealed_envelope


def _sealed_envelope(
    *,
    envelope_id: str = "ENV-12345678-1234-4234-9234-123456789abc",
    nonce: str = "nonce_v1_" + "b" * 64,
    source_role: str = "operator_console",
    target_role: str = "orchestrator",
    blocked_action_indicators: list[str] | None = None,
) -> dict:
    keypair = generate_ed25519_keypair()
    envelope = {
        "relay_envelope_version": "2A.1",
        "envelope_id": envelope_id,
        "docket_id": "DK-2026-0007",
        "mandate_id": "MND-ACCEPTED-2026-0007-PHASE4-HUB-RELAY",
        "source_role": source_role,
        "target_role": target_role,
        "artifact_type": "patch_artifact",
        "artifact_ref": "governance/05_handoffs/phase4.json",
        "artifact_sha256": "sha256:" + "a" * 64,
        "allowed_action_type": "record_artifact",
        "blocked_action_indicators": blocked_action_indicators or [],
        "created_at": "2026-06-07T00:00:00Z",
        "nonce": nonce,
        "canonicalization": "RFC8785",
        "schema_hash": "sha256:" + "c" * 64,
        "expiry": "2099-01-01T00:00:00Z",
        "signer_public_key": keypair["public_key"],
    }
    envelope["signature"] = sign_payload(signature_payload(envelope), keypair["private_key"])
    return envelope


def test_validate_sealed_envelope_accepts_valid_envelope(tmp_path):
    envelope = _sealed_envelope()

    assert (
        validate_sealed_envelope(
            envelope,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )
        is True
    )


def test_validate_sealed_envelope_rejects_tampered_payload(tmp_path):
    envelope = _sealed_envelope()
    envelope["artifact_ref"] = "governance/05_handoffs/tampered.json"

    with pytest.raises(ValueError, match="ERR_SIGNATURE_INVALID"):
        validate_sealed_envelope(
            envelope,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )


def test_validate_sealed_envelope_rejects_structural_peer_to_peer_route(tmp_path):
    envelope = _sealed_envelope(source_role="builder_agent", target_role="reviewer_agent")

    with pytest.raises(ValueError, match="ERR_PEER_TO_PEER_AGENT_ROUTING"):
        validate_sealed_envelope(
            envelope,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )


def test_validate_sealed_envelope_rejects_blocked_action_indicators(tmp_path):
    envelope = _sealed_envelope(blocked_action_indicators=["shell_command_frame"])

    with pytest.raises(ValueError, match="ERR_RELAY_BLOCKED_ACTION"):
        validate_sealed_envelope(
            envelope,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )


def test_validate_sealed_envelope_rejects_duplicate_nonce(tmp_path):
    db_path = tmp_path / "nonce.db"
    first = _sealed_envelope(
        envelope_id="ENV-12345678-1234-4234-9234-123456789abc",
        nonce="nonce_v1_" + "d" * 64,
    )
    second = _sealed_envelope(
        envelope_id="ENV-12345678-1234-4234-9234-123456789abd",
        nonce="nonce_v1_" + "d" * 64,
    )

    assert (
        validate_sealed_envelope(
            first,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(db_path),
        )
        is True
    )
    with pytest.raises(ValueError, match="ERR_NONCE_REPLAY"):
        validate_sealed_envelope(
            second,
            current_time="2026-06-07T00:00:00Z",
            nonce_registry_path=str(db_path),
        )
