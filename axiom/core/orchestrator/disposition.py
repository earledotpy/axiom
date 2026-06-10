"""Rejected/dead-letter disposition classification for Level 2A."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from axiom.core.orchestrator.contracts import RejectionCode


class Disposition(str, Enum):
    DEAD_LETTER = "dead_letter"
    REJECTED_WITH_QUARANTINE = "rejected_plus_dead_letter_copy"
    EXPIRED = "expired"
    REVOKED = "revoked"
    AUDIT_FAILED = "audit_failed"


STRUCTURAL_FAILURES = frozenset(
    {
        RejectionCode.MALFORMED_INPUT,
        RejectionCode.INVALID_SCHEMA,
        RejectionCode.CANONICALIZATION_FAILED,
    }
)

RULE_FAILURES = frozenset(
    {
        RejectionCode.SIGNATURE_INVALID,
        RejectionCode.NONCE_REPLAY,
        RejectionCode.SCOPE_VIOLATION,
        RejectionCode.BLOCKED_PATH_VIOLATION,
        RejectionCode.HASH_MISMATCH,
        RejectionCode.RELAY_BLOCKED_ACTION,
        RejectionCode.VERIFIER_HANDOFF_VIOLATION,
        RejectionCode.BROAD_COLLECTION_VIOLATION,
        RejectionCode.POSTURE_CACHE_AUTHORITY,
    }
)


@dataclass(frozen=True)
class FailureDisposition:
    rejection_code: RejectionCode
    disposition: Disposition
    lifecycle_state: str
    quarantine_copy_required: bool


def classify_failure(rejection_code: RejectionCode | str) -> FailureDisposition:
    code = RejectionCode(rejection_code)
    if code in STRUCTURAL_FAILURES:
        return FailureDisposition(code, Disposition.DEAD_LETTER, "dead_letter", False)
    if code == RejectionCode.MANDATE_EXPIRED:
        return FailureDisposition(code, Disposition.EXPIRED, "expired", False)
    if code == RejectionCode.MANDATE_REVOKED:
        return FailureDisposition(code, Disposition.REVOKED, "revoked", False)
    if code == RejectionCode.AUDIT_CHAIN_VIOLATION:
        return FailureDisposition(code, Disposition.AUDIT_FAILED, "audit_failed", False)
    if code in RULE_FAILURES:
        return FailureDisposition(code, Disposition.REJECTED_WITH_QUARANTINE, "rejected", True)
    raise ValueError(f"unmapped rejection code: {code.value}")
