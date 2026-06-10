import pytest

from axiom.core.orchestrator.contracts import RejectionCode
from axiom.core.orchestrator.disposition import Disposition, classify_failure
from axiom.core.orchestrator.state_machines import (
    DocketState,
    MandateState,
    can_transition,
    next_state,
    resolve_revocation_expiry,
)


def test_mandate_lifecycle_happy_path_is_table_driven():
    state = MandateState.DRAFTED
    for event in (
        "operator_approve",
        "sign",
        "submit",
        "validate",
        "activate",
        "execution_complete",
        "record_evidence",
        "complete",
    ):
        state = next_state(state, event, MandateState)
    assert state == MandateState.COMPLETED


def test_docket_lifecycle_happy_path_reaches_verified_commit_only_by_commit_event():
    state = DocketState.CREATED
    for event in (
        "bind_mandate",
        "validate_mandate",
        "prepare_execution",
        "start_relay",
        "start_work",
        "request_verification",
        "record_evidence",
        "commit",
    ):
        state = next_state(state, event, DocketState)
    assert state == DocketState.VERIFIED_COMMIT


def test_t02_expired_mandate_transitions_to_expired():
    assert next_state(MandateState.SUBMITTED, "expire", MandateState) == MandateState.EXPIRED


def test_t18_exact_expiry_boundary_is_expired_not_rejected():
    disposition = classify_failure(RejectionCode.MANDATE_EXPIRED)
    assert disposition.lifecycle_state == "expired"
    assert disposition.lifecycle_state != "rejected"


def test_t20_revoked_mandate_produces_revoked_not_rejected():
    disposition = classify_failure(RejectionCode.MANDATE_REVOKED)
    assert disposition.lifecycle_state == "revoked"
    assert disposition.lifecycle_state != "rejected"


def test_revoked_wins_over_expired_when_both_apply():
    assert resolve_revocation_expiry(revoked=True, expired=True) == MandateState.REVOKED


def test_rejected_and_dead_letter_disposition_are_distinct():
    structural = classify_failure(RejectionCode.INVALID_SCHEMA)
    rule = classify_failure(RejectionCode.SIGNATURE_INVALID)
    assert structural.disposition == Disposition.DEAD_LETTER
    assert structural.quarantine_copy_required is False
    assert rule.disposition == Disposition.REJECTED_WITH_QUARANTINE
    assert rule.quarantine_copy_required is True


def test_t21_terminal_states_have_no_outgoing_transitions():
    with pytest.raises(ValueError, match="terminal state"):
        next_state(MandateState.COMPLETED, "activate", MandateState)
    with pytest.raises(ValueError, match="terminal state"):
        next_state(DocketState.VERIFIED_COMMIT, "fail", DocketState)


def test_t13_direct_docket_write_is_not_a_valid_transition_event():
    assert not can_transition(DocketState.WORK_IN_PROGRESS, "direct_write", DocketState)
