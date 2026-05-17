import pytest

from axiom.core.state_machine import InvalidTransitionError, StateMachine


def test_state_machine_allows_pending_to_running():
    decision = StateMachine().can_transition("pending", "running")

    assert decision.allowed is True
    assert decision.reason == "transition_allowed"


def test_state_machine_allows_running_to_completed():
    decision = StateMachine().can_transition("running", "completed")

    assert decision.allowed is True
    assert decision.reason == "transition_allowed"


def test_state_machine_rejects_completed_to_running():
    decision = StateMachine().can_transition("completed", "running")

    assert decision.allowed is False
    assert decision.reason == "terminal_status_cannot_transition"


def test_state_machine_rejects_unknown_current_status():
    decision = StateMachine().can_transition("bogus", "running")

    assert decision.allowed is False
    assert decision.reason == "unknown_current_status"


def test_state_machine_rejects_unknown_next_status():
    decision = StateMachine().can_transition("pending", "bogus")

    assert decision.allowed is False
    assert decision.reason == "unknown_next_status"


def test_state_machine_require_transition_raises_for_invalid_transition():
    with pytest.raises(InvalidTransitionError):
        StateMachine().require_transition("completed", "running")
