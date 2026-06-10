"""Audit-chain hash utilities for inert Level 2A records."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from axiom.security.level2a.validators import validate_sha256_hash

EXCLUDED_PAYLOAD_HASH_FIELDS = frozenset(
    {
        "audit_chain_hash",
        "prior_audit_hash",
        "event_payload_sha256",
    }
)


def _sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_event_payload_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key not in EXCLUDED_PAYLOAD_HASH_FIELDS}
    return _sha256_prefixed(canonical_json_bytes(payload))


def compute_audit_chain_hash(event_payload_sha256: str, prior_audit_hash: str | None = None) -> str:
    if not validate_sha256_hash(event_payload_sha256):
        raise ValueError("event_payload_sha256 must be sha256:<64 lowercase hex>")
    if prior_audit_hash is None:
        input_text = f"GENESIS:{event_payload_sha256}"
    else:
        if not validate_sha256_hash(prior_audit_hash):
            raise ValueError("prior_audit_hash must be sha256:<64 lowercase hex>")
        input_text = f"{prior_audit_hash}:{event_payload_sha256}"
    return _sha256_prefixed(input_text.encode("utf-8"))


def verify_audit_chain(events: list[dict[str, Any]]) -> bool:
    previous: str | None = None
    for event in events:
        payload_hash = compute_event_payload_hash(event)
        if event.get("event_payload_sha256") != payload_hash:
            return False
        expected_chain_hash = compute_audit_chain_hash(payload_hash, previous)
        if event.get("audit_chain_hash") != expected_chain_hash:
            return False
        if previous is not None and event.get("prior_audit_hash") != previous:
            return False
        previous = expected_chain_hash
    return True
