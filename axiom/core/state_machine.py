from __future__ import annotations

from dataclasses import dataclass
from typing import Final


class InvalidTransitionError(RuntimeError):
    pass


TASK_STATUSES: Final[set[str]] = {
    "pending",
    "running",
    "completed",
    "failed",
    "quarantined",
    "needs_human_input",
    "blocked_resource_limit",
    "cancelled",
}


TERMINAL_STATUSES: Final[set[str]] = {
    "completed",
    "failed",
    "quarantined",
    "cancelled",
}


ALLOWED_TASK_TRANSITIONS: Final[dict[str, set[str]]] = {
    "pending": {
        "running",
        "cancelled",
        "blocked_resource_limit",
        "needs_human_input",
        "quarantined",
    },
    "running": {
        "completed",
        "failed",
        "quarantined",
        "needs_human_input",
        "blocked_resource_limit",
        "cancelled",
    },
    "needs_human_input": {
        "pending",
        "running",
        "cancelled",
        "quarantined",
    },
    "blocked_resource_limit": {
        "pending",
        "cancelled",
    },
    "completed": set(),
    "failed": set(),
    "quarantined": set(),
    "cancelled": set(),
}


@dataclass(frozen=True)
class TransitionDecision:
    allowed: bool
    reason: str


class StateMachine:
    def can_transition(self, current_status: str, next_status: str) -> TransitionDecision:
        if current_status not in TASK_STATUSES:
            return TransitionDecision(False, "unknown_current_status")

        if next_status not in TASK_STATUSES:
            return TransitionDecision(False, "unknown_next_status")

        if next_status in ALLOWED_TASK_TRANSITIONS[current_status]:
            return TransitionDecision(True, "transition_allowed")

        if current_status in TERMINAL_STATUSES:
            return TransitionDecision(False, "terminal_status_cannot_transition")

        return TransitionDecision(False, "transition_not_allowed")

    def require_transition(self, current_status: str, next_status: str) -> None:
        decision = self.can_transition(current_status, next_status)

        if not decision.allowed:
            raise InvalidTransitionError(
                f"Invalid task status transition: {current_status!r} -> {next_status!r} ({decision.reason})"
            )
