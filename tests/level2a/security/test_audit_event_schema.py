import pytest

from axiom.core.orchestrator.contracts import ContractValidationError, validate_audit_event


def _valid_event() -> dict:
    return {
        "audit_event_version": "2A.1",
        "event_id": "AUD-12345678-1234-4234-9234-123456789abc",
        "event_type": "docket_state_transitioned",
        "actor": "orchestrator_core",
        "event_time": "2026-06-04T08:15:00Z",
        "prior_audit_hash": "sha256:" + "0" * 64,
        "event_payload_sha256": "sha256:" + "1" * 64,
        "audit_chain_hash": "sha256:" + "2" * 64,
        "canonicalization": "RFC8785",
    }


def test_audit_event_accepts_closed_enum_values():
    assert validate_audit_event(_valid_event())


def test_audit_event_rejects_unknown_fields_and_free_text_actor():
    event = _valid_event()
    event["actor"] = "builder_agent"
    with pytest.raises(ContractValidationError, match="invalid actor"):
        validate_audit_event(event)
    event = _valid_event()
    event["extra"] = "not allowed"
    with pytest.raises(ContractValidationError, match="unknown fields"):
        validate_audit_event(event)


def test_audit_event_rejects_offset_timestamp():
    event = _valid_event()
    event["event_time"] = "2026-06-04T08:15:00+02:00"
    with pytest.raises(ContractValidationError, match="invalid event_time"):
        validate_audit_event(event)
