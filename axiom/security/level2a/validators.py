"""Strict Level 2A scalar validators."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

UTC_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA256_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def validate_utc_timestamp(value: str) -> bool:
    if not isinstance(value, str) or not UTC_TIMESTAMP_PATTERN.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return True


def parse_utc_timestamp(value: str) -> datetime:
    if not validate_utc_timestamp(value):
        raise ValueError(f"invalid Level 2A UTC timestamp: {value!r}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def is_expired(current_time: str, expiry_time: str) -> bool:
    return parse_utc_timestamp(current_time) >= parse_utc_timestamp(expiry_time)


def validate_sha256_hash(value: str) -> bool:
    return isinstance(value, str) and bool(SHA256_HASH_PATTERN.fullmatch(value))


def require_hash_match(expected_hash: str, actual_hash: str) -> bool:
    if not validate_sha256_hash(expected_hash) or not validate_sha256_hash(actual_hash):
        raise ValueError("hashes must use sha256:<64 lowercase hex>")
    if expected_hash != actual_hash:
        raise ValueError("ERR_HASH_MISMATCH")
    return True


def reject_broad_pytest_collection(target: str) -> bool:
    broad_targets = {"pytest", "tests/", "tests", "tests/level2a/", "tests/level2a"}
    normalized = target.strip().replace("\\", "/")
    path_part, _, node_id = normalized.partition("::")
    has_glob = any(marker in normalized for marker in ("*", "?", "[", "]"))
    single_python_file = path_part.endswith(".py") and "/" in path_part and not path_part.endswith("/")

    if (
        not normalized
        or normalized in broad_targets
        or has_glob
        or path_part in broad_targets
        or path_part.endswith("/")
        or not single_python_file
        or ("::" in normalized and not node_id)
    ):
        raise ValueError("ERR_BROAD_COLLECTION_VIOLATION")
    return True


SEALED_MANDATE_REQUIRED_FIELDS = ("nonce", "expiry", "signer_public_key", "signature")
SEALED_ENVELOPE_REQUIRED_FIELDS = ("expiry", "signer_public_key", "signature")
ENVELOPE_SEALING_FIELDS = frozenset({"expiry", "signer_public_key", "signature"})
AGENT_ROUTE_ROLES = frozenset({"builder_agent", "reviewer_agent", "verifier_account"})


def signature_payload(mandate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(mandate, dict):
        raise ValueError("ERR_MANDATE_NOT_OBJECT")
    return {key: value for key, value in mandate.items() if key != "signature"}


def relay_contract_payload(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise ValueError("ERR_ENVELOPE_NOT_OBJECT")
    return {key: value for key, value in envelope.items() if key not in ENVELOPE_SEALING_FIELDS}


def validate_sealed_mandate(
    mandate: dict[str, Any],
    *,
    current_time: str | None = None,
    nonce_registry_path: str | None = None,
    register_nonce: bool = True,
) -> bool:
    """Validate a sealed mandate payload without activating runtime authority."""

    if not isinstance(mandate, dict):
        raise ValueError("ERR_MANDATE_NOT_OBJECT")

    missing = [field for field in SEALED_MANDATE_REQUIRED_FIELDS if not mandate.get(field)]
    if missing:
        raise ValueError("ERR_MANDATE_MISSING_FIELDS:" + ",".join(missing))

    expiry = mandate["expiry"]
    if not isinstance(expiry, str) or not validate_utc_timestamp(expiry):
        raise ValueError("ERR_INVALID_EXPIRY")

    if current_time is None:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not validate_utc_timestamp(current_time):
        raise ValueError("ERR_INVALID_CURRENT_TIME")
    if is_expired(current_time, expiry):
        raise ValueError("ERR_MANDATE_EXPIRED")

    payload = signature_payload(mandate)

    from axiom.security.level2a.canonical import canonicalize
    from axiom.security.level2a.nonce_registry import NonceRegistry
    from axiom.security.level2a.sealing import verify_payload_signature

    canonicalize(payload)
    if not verify_payload_signature(payload, mandate["signature"], mandate["signer_public_key"]):
        raise ValueError("ERR_SIGNATURE_INVALID")

    if register_nonce:
        registry = NonceRegistry(nonce_registry_path)
        if not registry.register_nonce(mandate["nonce"]):
            raise ValueError("ERR_NONCE_REPLAY")

    return True


def validate_sealed_envelope(
    envelope: dict[str, Any],
    *,
    current_time: str | None = None,
    nonce_registry_path: str | None = None,
    register_nonce: bool = True,
) -> bool:
    """Validate a sealed relay envelope without activating runtime authority."""

    if not isinstance(envelope, dict):
        raise ValueError("ERR_ENVELOPE_NOT_OBJECT")

    missing = [field for field in SEALED_ENVELOPE_REQUIRED_FIELDS if not envelope.get(field)]
    if missing:
        raise ValueError("ERR_ENVELOPE_MISSING_FIELDS:" + ",".join(missing))

    from axiom.core.orchestrator.contracts import ContractValidationError, validate_relay_envelope
    from axiom.security.level2a.canonical import canonicalize
    from axiom.security.level2a.nonce_registry import NonceRegistry
    from axiom.security.level2a.sealing import verify_payload_signature

    contract_payload = relay_contract_payload(envelope)
    try:
        validate_relay_envelope(contract_payload)
    except ContractValidationError as exc:
        raise ValueError(str(exc)) from exc

    if _is_peer_to_peer_agent_route(contract_payload):
        raise ValueError("ERR_PEER_TO_PEER_AGENT_ROUTING")

    expiry = envelope["expiry"]
    if not isinstance(expiry, str) or not validate_utc_timestamp(expiry):
        raise ValueError("ERR_INVALID_EXPIRY")
    if current_time is None:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not validate_utc_timestamp(current_time):
        raise ValueError("ERR_INVALID_CURRENT_TIME")
    if is_expired(current_time, expiry):
        raise ValueError("ERR_ENVELOPE_EXPIRED")

    payload = signature_payload(envelope)
    canonicalize(payload)
    if not verify_payload_signature(payload, envelope["signature"], envelope["signer_public_key"]):
        raise ValueError("ERR_SIGNATURE_INVALID")

    if register_nonce:
        registry = NonceRegistry(nonce_registry_path)
        if not registry.register_nonce(envelope["nonce"]):
            raise ValueError("ERR_NONCE_REPLAY")

    return True


def _is_peer_to_peer_agent_route(envelope: dict[str, Any]) -> bool:
    return envelope.get("source_role") in AGENT_ROUTE_ROLES and envelope.get("target_role") in AGENT_ROUTE_ROLES
