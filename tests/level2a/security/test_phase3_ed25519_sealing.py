from axiom.security.level2a.sealing import (
    generate_ed25519_keypair,
    sign_payload,
    verify_payload_signature,
)


def test_generate_ed25519_keypair_produces_valid_pair():
    keypair = generate_ed25519_keypair()
    payload = {"mandate_id": "MND-TEST", "nonce": "nonce-1"}

    signature = sign_payload(payload, keypair["private_key"])

    assert verify_payload_signature(payload, signature, keypair["public_key"]) is True


def test_signature_rejects_modified_payload_value():
    keypair = generate_ed25519_keypair()
    payload = {"mandate_id": "MND-TEST", "nonce": "nonce-1"}
    signature = sign_payload(payload, keypair["private_key"])

    tampered = {"mandate_id": "MND-TAMPERED", "nonce": "nonce-1"}

    assert verify_payload_signature(tampered, signature, keypair["public_key"]) is False


def test_signature_rejects_mismatched_public_key():
    signer = generate_ed25519_keypair()
    other = generate_ed25519_keypair()
    payload = {"mandate_id": "MND-TEST", "nonce": "nonce-1"}
    signature = sign_payload(payload, signer["private_key"])

    assert verify_payload_signature(payload, signature, other["public_key"]) is False
