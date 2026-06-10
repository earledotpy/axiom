import pytest

from axiom.security.level2a.sealing import generate_ed25519_keypair, sign_payload
from axiom.security.level2a.validators import signature_payload, validate_sealed_mandate


def _sealed_mandate(nonce: str = "nonce-1", expiry: str = "2099-01-01T00:00:00Z"):
    keypair = generate_ed25519_keypair()
    mandate = {
        "mandate_id": "MND-TEST-0001",
        "nonce": nonce,
        "expiry": expiry,
        "signer_public_key": keypair["public_key"],
        "body": {"action": "offline-test", "count": 2},
    }
    mandate["signature"] = sign_payload(signature_payload(mandate), keypair["private_key"])
    return mandate


def test_validate_sealed_mandate_accepts_valid_payload(tmp_path):
    mandate = _sealed_mandate()

    assert (
        validate_sealed_mandate(
            mandate,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )
        is True
    )


def test_validate_sealed_mandate_rejects_tampered_payload(tmp_path):
    mandate = _sealed_mandate()
    mandate["body"]["count"] = 3

    with pytest.raises(ValueError, match="ERR_SIGNATURE_INVALID"):
        validate_sealed_mandate(
            mandate,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )


def test_validate_sealed_mandate_rejects_expired_payload(tmp_path):
    mandate = _sealed_mandate(expiry="2020-01-01T00:00:00Z")

    with pytest.raises(ValueError, match="ERR_MANDATE_EXPIRED"):
        validate_sealed_mandate(
            mandate,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )


def test_validate_sealed_mandate_rejects_replayed_nonce(tmp_path):
    db_path = tmp_path / "nonce.db"
    first = _sealed_mandate(nonce="replay-1")
    second = _sealed_mandate(nonce="replay-1")

    assert (
        validate_sealed_mandate(
            first,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(db_path),
        )
        is True
    )
    with pytest.raises(ValueError, match="ERR_NONCE_REPLAY"):
        validate_sealed_mandate(
            second,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(db_path),
        )


def test_validate_sealed_mandate_rejects_missing_required_fields(tmp_path):
    mandate = _sealed_mandate()
    del mandate["nonce"]

    with pytest.raises(ValueError, match="ERR_MANDATE_MISSING_FIELDS:nonce"):
        validate_sealed_mandate(
            mandate,
            current_time="2026-06-06T00:00:00Z",
            nonce_registry_path=str(tmp_path / "nonce.db"),
        )
