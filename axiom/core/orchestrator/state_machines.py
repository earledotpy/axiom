"""Table-driven Level 2A mandate and docket state machines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MandateState(str, Enum):
    DRAFTED = "drafted"
    OPERATOR_APPROVED = "operator_approved"
    SIGNED = "signed"
    SUBMITTED = "submitted"
    VALIDATED = "validated"
    ACTIVE = "active"
    EXECUTED = "executed"
    VERIFIED_EVIDENCE_RECORDED = "verified_evidence_recorded"
    COMPLETED = "completed"
    AUDIT_FAILED = "audit_failed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REJECTED = "rejected"
    DEAD_LETTER = "dead_letter"


class DocketState(str, Enum):
    CREATED = "created"
    MANDATE_INTAKE = "mandate_intake"
    MANDATE_VALIDATED = "mandate_validated"
    EXECUTION_PENDING = "execution_pending"
    RELAY_INGRESS_PENDING = "relay_ingress_pending"
    WORK_IN_PROGRESS = "work_in_progress"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED_EVIDENCE_RECORDED = "verified_evidence_recorded"
    VERIFIED_COMMIT = "verified_commit"
    AUDIT_ACCEPTED_PENDING_2B = "audit_accepted_pending_2b"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


MANDATE_TERMINAL_STATES = frozenset(
    {
        MandateState.COMPLETED,
        MandateState.AUDIT_FAILED,
        MandateState.EXPIRED,
        MandateState.REVOKED,
        MandateState.REJECTED,
        MandateState.DEAD_LETTER,
    }
)

DOCKET_TERMINAL_STATES = frozenset(
    {
        DocketState.VERIFIED_COMMIT,
        DocketState.FAILED,
        DocketState.DEAD_LETTER,
    }
)


@dataclass(frozen=True)
class Transition:
    from_state: Enum | str
    event: str
    to_state: Enum
    audit_event: str


MANDATE_TRANSITIONS: tuple[Transition, ...] = (
    Transition(MandateState.DRAFTED, "operator_approve", MandateState.OPERATOR_APPROVED, "operator_summary_recorded"),
    Transition(MandateState.OPERATOR_APPROVED, "sign", MandateState.SIGNED, "console_approval_recorded"),
    Transition(MandateState.SIGNED, "submit", MandateState.SUBMITTED, "mandate_received"),
    Transition(MandateState.SUBMITTED, "validate", MandateState.VALIDATED, "mandate_signature_validated"),
    Transition(MandateState.VALIDATED, "activate", MandateState.ACTIVE, "mandate_nonce_consumed"),
    Transition(MandateState.ACTIVE, "execution_complete", MandateState.EXECUTED, "docket_state_transitioned"),
    Transition(MandateState.EXECUTED, "record_evidence", MandateState.VERIFIED_EVIDENCE_RECORDED, "verifier_evidence_recorded"),
    Transition(MandateState.VERIFIED_EVIDENCE_RECORDED, "complete", MandateState.COMPLETED, "operator_summary_recorded"),
    Transition(MandateState.SUBMITTED, "expire", MandateState.EXPIRED, "mandate_expired"),
    Transition(MandateState.VALIDATED, "expire", MandateState.EXPIRED, "mandate_expired"),
    Transition(MandateState.ACTIVE, "expire", MandateState.EXPIRED, "mandate_expired"),
    Transition(MandateState.SUBMITTED, "revoke", MandateState.REVOKED, "mandate_revoked"),
    Transition(MandateState.VALIDATED, "revoke", MandateState.REVOKED, "mandate_revoked"),
    Transition(MandateState.ACTIVE, "revoke", MandateState.REVOKED, "mandate_revoked"),
    Transition(MandateState.SUBMITTED, "structural_failure", MandateState.DEAD_LETTER, "dead_letter_recorded"),
    Transition(MandateState.SUBMITTED, "rule_failure", MandateState.REJECTED, "mandate_scope_rejected"),
    Transition(MandateState.ACTIVE, "audit_failure", MandateState.AUDIT_FAILED, "audit_failed"),
)

DOCKET_TRANSITIONS: tuple[Transition, ...] = (
    Transition(DocketState.CREATED, "bind_mandate", DocketState.MANDATE_INTAKE, "docket_state_transitioned"),
    Transition(DocketState.MANDATE_INTAKE, "validate_mandate", DocketState.MANDATE_VALIDATED, "docket_state_transitioned"),
    Transition(DocketState.MANDATE_VALIDATED, "prepare_execution", DocketState.EXECUTION_PENDING, "docket_state_transitioned"),
    Transition(DocketState.EXECUTION_PENDING, "start_relay", DocketState.RELAY_INGRESS_PENDING, "relay_envelope_validated"),
    Transition(DocketState.RELAY_INGRESS_PENDING, "start_work", DocketState.WORK_IN_PROGRESS, "docket_state_transitioned"),
    Transition(DocketState.WORK_IN_PROGRESS, "request_verification", DocketState.VERIFICATION_PENDING, "verifier_handoff_requested"),
    Transition(DocketState.VERIFICATION_PENDING, "record_evidence", DocketState.VERIFIED_EVIDENCE_RECORDED, "verifier_evidence_recorded"),
    Transition(DocketState.VERIFIED_EVIDENCE_RECORDED, "commit", DocketState.VERIFIED_COMMIT, "verified_commit_recorded"),
    Transition(DocketState.VERIFIED_EVIDENCE_RECORDED, "delegate_2b", DocketState.AUDIT_ACCEPTED_PENDING_2B, "docket_state_transitioned"),
    Transition(DocketState.AUDIT_ACCEPTED_PENDING_2B, "escalate_2b", DocketState.VERIFICATION_PENDING, "verifier_handoff_requested"),
    Transition("*", "fail", DocketState.FAILED, "audit_failed"),
    Transition("*", "quarantine", DocketState.DEAD_LETTER, "dead_letter_recorded"),
)


def _coerce_state(state: Enum | str, enum_type: type[Enum]) -> Enum:
    if isinstance(state, enum_type):
        return state
    return enum_type(state)


def _transition_table(enum_type: type[Enum]) -> tuple[Transition, ...]:
    if enum_type is MandateState:
        return MANDATE_TRANSITIONS
    if enum_type is DocketState:
        return DOCKET_TRANSITIONS
    raise TypeError(f"unsupported state enum: {enum_type}")


def _terminal_states(enum_type: type[Enum]) -> frozenset[Enum]:
    if enum_type is MandateState:
        return MANDATE_TERMINAL_STATES
    if enum_type is DocketState:
        return DOCKET_TERMINAL_STATES
    raise TypeError(f"unsupported state enum: {enum_type}")


def next_state(state: Enum | str, event: str, enum_type: type[Enum]) -> Enum:
    current = _coerce_state(state, enum_type)
    if current in _terminal_states(enum_type):
        raise ValueError(f"terminal state has no outgoing transitions: {current.value}")
    for transition in _transition_table(enum_type):
        if transition.event != event:
            continue
        if transition.from_state == "*" or transition.from_state == current:
            return transition.to_state
    raise ValueError(f"invalid transition from {current.value} on {event}")


def can_transition(state: Enum | str, event: str, enum_type: type[Enum]) -> bool:
    try:
        next_state(state, event, enum_type)
    except ValueError:
        return False
    return True


def resolve_revocation_expiry(*, revoked: bool, expired: bool) -> MandateState | None:
    if revoked:
        return MandateState.REVOKED
    if expired:
        return MandateState.EXPIRED
    return None


def synchronize_mandate_from_docket(docket_state: DocketState | str) -> MandateState | None:
    state = _coerce_state(docket_state, DocketState)
    if state == DocketState.VERIFIED_COMMIT:
        return MandateState.COMPLETED
    if state in {DocketState.FAILED, DocketState.DEAD_LETTER}:
        return MandateState.AUDIT_FAILED
    return None
