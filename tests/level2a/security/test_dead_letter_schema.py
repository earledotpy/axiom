import pytest

from axiom.core.orchestrator.contracts import ContractValidationError, RejectionCode, validate_dead_letter_record
from axiom.core.orchestrator.disposition import classify_failure


def _valid_dead_letter() -> dict:
    return {
        "dead_letter_id": "DL-12345678-1234-4234-9234-123456789abc",
        "rejection_code": "ERR_INVALID_SCHEMA",
        "failure_reason": "unknown field",
        "raw_payload": "{}",
        "actor": "dead_letter_subsystem",
        "received_at": "2026-06-04T08:15:00Z",
    }


def test_dead_letter_record_accepts_distinct_dl_prefix():
    assert validate_dead_letter_record(_valid_dead_letter())


def test_dead_letter_record_rejects_evidence_prefix():
    record = _valid_dead_letter()
    record["dead_letter_id"] = "EVI-12345678-1234-4234-9234-123456789abc"
    with pytest.raises(ContractValidationError, match="invalid dead_letter_id"):
        validate_dead_letter_record(record)


def test_dead_letter_record_uses_closed_rejection_code_enum():
    record = _valid_dead_letter()
    record["rejection_code"] = "ERR_NOT_REGISTERED"
    with pytest.raises(ContractValidationError, match="invalid rejection_code"):
        validate_dead_letter_record(record)


def test_t01_unsigned_mandate_maps_to_rejected_plus_dead_letter_copy():
    disposition = classify_failure(RejectionCode.SIGNATURE_INVALID)
    assert disposition.lifecycle_state == "rejected"
    assert disposition.quarantine_copy_required


def test_t03_reused_nonce_maps_to_rejected_plus_dead_letter_copy():
    disposition = classify_failure(RejectionCode.NONCE_REPLAY)
    assert disposition.lifecycle_state == "rejected"
    assert disposition.quarantine_copy_required


def test_t12_posture_cache_authority_maps_to_rejected_plus_dead_letter_copy():
    disposition = classify_failure(RejectionCode.POSTURE_CACHE_AUTHORITY)
    assert disposition.lifecycle_state == "rejected"
    assert disposition.quarantine_copy_required


def test_t17_console_approval_without_oob_token_is_signature_invalid_fixture():
    disposition = classify_failure(RejectionCode.SIGNATURE_INVALID)
    assert disposition.rejection_code == RejectionCode.SIGNATURE_INVALID
