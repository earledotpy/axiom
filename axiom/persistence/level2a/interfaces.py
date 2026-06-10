"""Protocol-only abstractions for future Level 2A integrations."""

from __future__ import annotations

from typing import Protocol


class NonceLedger(Protocol):
    def has_consumed(self, nonce: str) -> bool:
        """Return whether the nonce has already been atomically consumed."""

    def consume_once(self, nonce: str) -> bool:
        """Atomically consume a nonce, returning False on uniqueness violation."""


class RevocationLedger(Protocol):
    def is_revoked(self, mandate_id: str) -> bool:
        """Return whether a structurally identifiable mandate is revoked."""


class AuditLedger(Protocol):
    def append_event(self, event: dict) -> None:
        """Append an already validated audit event."""

    def read_events(self) -> list[dict]:
        """Return audit events for chain recomputation."""


class GateService(Protocol):
    def direct_query(self, *, nonce: str, docket_id: str, mandate_id: str) -> dict:
        """Perform a direct posture query bound to nonce, docket, and mandate."""


class OOBApprovalVerifier(Protocol):
    def verify(self, *, docket_id: str, mandate_id: str, mandate_sha256: str, token: str) -> bool:
        """Verify an out-of-band approval token without creating the token."""


class RestrictedVerifierIdentity(Protocol):
    def is_restricted_verifier(self) -> bool:
        """Return whether the current identity satisfies future verifier rules."""


class TrustedTestPinningSource(Protocol):
    def expected_hash_for(self, test_nodeid: str) -> str | None:
        """Return the pinned test hash for an explicit trusted test nodeid."""
