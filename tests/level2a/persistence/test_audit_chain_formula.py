import copy

from axiom.core.orchestrator.contracts import RejectionCode
from axiom.core.orchestrator.disposition import classify_failure
from axiom.persistence.level2a.audit_chain import (
    compute_audit_chain_hash,
    compute_event_payload_hash,
    verify_audit_chain,
)
from axiom.persistence.level2a.interfaces import (
    GateService,
    NonceLedger,
    OOBApprovalVerifier,
    RestrictedVerifierIdentity,
    RevocationLedger,
    TrustedTestPinningSource,
)


def _event(event_id: str, event_type: str, prior: str | None = None) -> dict:
    base = {
        "audit_event_version": "2A.1",
        "event_id": event_id,
        "event_type": event_type,
        "actor": "orchestrator_core",
        "event_time": "2026-06-04T08:15:00Z",
        "canonicalization": "RFC8785",
    }
    payload_hash = compute_event_payload_hash(base)
    base["event_payload_sha256"] = payload_hash
    base["prior_audit_hash"] = prior or "sha256:" + "0" * 64
    base["audit_chain_hash"] = compute_audit_chain_hash(payload_hash, prior)
    return base


def test_audit_chain_formula_uses_genesis_and_prior_hash_inputs():
    first = _event("AUD-12345678-1234-4234-9234-123456789abc", "mandate_received")
    second = _event(
        "AUD-12345678-1234-4234-9234-123456789abd",
        "docket_state_transitioned",
        first["audit_chain_hash"],
    )
    assert verify_audit_chain([first, second])


def test_t15_audit_chain_mutation_detected():
    first = _event("AUD-12345678-1234-4234-9234-123456789abc", "mandate_received")
    tampered = copy.deepcopy(first)
    tampered["event_type"] = "mandate_revoked"
    assert not verify_audit_chain([tampered])
    disposition = classify_failure(RejectionCode.AUDIT_CHAIN_VIOLATION)
    assert disposition.lifecycle_state == "audit_failed"


class StubNonceLedger:
    def __init__(self) -> None:
        self.consumed: set[str] = set()

    def has_consumed(self, nonce: str) -> bool:
        return nonce in self.consumed

    def consume_once(self, nonce: str) -> bool:
        if nonce in self.consumed:
            return False
        self.consumed.add(nonce)
        return True


class StubRevocationLedger:
    def __init__(self, revoked: set[str]) -> None:
        self.revoked = revoked

    def is_revoked(self, mandate_id: str) -> bool:
        return mandate_id in self.revoked


class StubGateService:
    def direct_query(self, *, nonce: str, docket_id: str, mandate_id: str) -> dict:
        return {"nonce": nonce, "docket_id": docket_id, "mandate_id": mandate_id, "fresh": True}


class StubOOBApprovalVerifier:
    def verify(self, *, docket_id: str, mandate_id: str, mandate_sha256: str, token: str) -> bool:
        return all([docket_id, mandate_id, mandate_sha256, token == "approved"])


class StubRestrictedVerifierIdentity:
    def __init__(self, restricted: bool) -> None:
        self.restricted = restricted

    def is_restricted_verifier(self) -> bool:
        return self.restricted


class StubTrustedTestPinningSource:
    def expected_hash_for(self, test_nodeid: str) -> str | None:
        if test_nodeid == "tests/level2a/security/test_hash_validation.py::test_matching_artifact_hash_is_allowed":
            return "sha256:" + "a" * 64
        return None


def test_interface_only_abstractions_are_satisfied_by_deterministic_stubs():
    nonce_ledger: NonceLedger = StubNonceLedger()
    revocation_ledger: RevocationLedger = StubRevocationLedger({"MND-ACCEPTED-2026-0003"})
    gate_service: GateService = StubGateService()
    oob: OOBApprovalVerifier = StubOOBApprovalVerifier()
    verifier: RestrictedVerifierIdentity = StubRestrictedVerifierIdentity(False)
    trusted_tests: TrustedTestPinningSource = StubTrustedTestPinningSource()

    assert nonce_ledger.consume_once("nonce_v1_" + "a" * 64)
    assert not nonce_ledger.consume_once("nonce_v1_" + "a" * 64)
    assert revocation_ledger.is_revoked("MND-ACCEPTED-2026-0003")
    assert gate_service.direct_query(nonce="n", docket_id="d", mandate_id="m")["fresh"]
    assert oob.verify(docket_id="d", mandate_id="m", mandate_sha256="sha256:" + "a" * 64, token="approved")
    assert not verifier.is_restricted_verifier()
    assert trusted_tests.expected_hash_for("tests/level2a/security/test_hash_validation.py::test_matching_artifact_hash_is_allowed")


def test_t09_and_t10_trusted_test_pin_fixture_rejects_missing_or_modified_tests():
    trusted_tests = StubTrustedTestPinningSource()
    assert trusted_tests.expected_hash_for("tests/unknown.py::test_missing") is None
    expected = trusted_tests.expected_hash_for("tests/level2a/security/test_hash_validation.py::test_matching_artifact_hash_is_allowed")
    assert expected != "sha256:" + "b" * 64
