from axiom.core.orchestrator.state_machines import (
    DocketState,
    MandateState,
    can_transition,
    synchronize_mandate_from_docket,
)


def test_verified_commit_synchronizes_one_way_to_mandate_completed():
    assert synchronize_mandate_from_docket(DocketState.VERIFIED_COMMIT) == MandateState.COMPLETED
    assert not can_transition(MandateState.COMPLETED, "commit", MandateState)


def test_t14_verifier_bypass_cannot_produce_verified_commit_from_builder_path():
    assert not can_transition(DocketState.WORK_IN_PROGRESS, "commit", DocketState)
    assert synchronize_mandate_from_docket(DocketState.WORK_IN_PROGRESS) is None


def test_t16_non_orchestrator_docket_write_is_rejected_by_missing_transition():
    assert not can_transition(DocketState.VERIFICATION_PENDING, "verifier_write_non_terminal", DocketState)


def test_t19_verifier_cannot_write_work_in_progress_state():
    assert not can_transition(DocketState.VERIFICATION_PENDING, "write_work_in_progress", DocketState)


def test_audit_accepted_pending_2b_remains_unsynchronized():
    assert synchronize_mandate_from_docket(DocketState.AUDIT_ACCEPTED_PENDING_2B) is None


def test_failed_or_dead_letter_dockets_do_not_complete_mandate():
    assert synchronize_mandate_from_docket(DocketState.FAILED) == MandateState.AUDIT_FAILED
    assert synchronize_mandate_from_docket(DocketState.DEAD_LETTER) == MandateState.AUDIT_FAILED
