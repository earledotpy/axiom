"""Offline Ed25519 sealing helpers for Level 2A mandate payloads."""

from __future__ import annotations

import base64
import binascii
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption


def generate_ed25519_keypair() -> dict[str, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return {
        "private_key": _b64encode(
            private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        ),
        "public_key": _b64encode(public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)),
    }


def sign_payload(payload: Any, private_key: str) -> str:
    """Sign a payload's canonical Level 2A representation."""

    from axiom.security.level2a.canonical import canonicalize

    key = Ed25519PrivateKey.from_private_bytes(_b64decode(private_key))
    return _b64encode(key.sign(canonicalize(payload)))


def verify_payload_signature(payload: Any, signature: str, public_key: str) -> bool:
    """Return True only when signature verifies against payload canonical bytes."""

    from axiom.security.level2a.canonical import canonicalize

    try:
        key = Ed25519PublicKey.from_public_bytes(_b64decode(public_key))
        key.verify(_b64decode(signature), canonicalize(payload))
    except (InvalidSignature, ValueError):
        return False
    return True


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (binascii.Error, UnicodeEncodeError, ValueError) as exc:
        raise ValueError("ERR_INVALID_BASE64") from exc
