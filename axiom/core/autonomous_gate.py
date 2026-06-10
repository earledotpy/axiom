from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.app.status_report import build_status_report


class AutonomousReadinessError(RuntimeError):
    pass


@dataclass(frozen=True)
class AutonomousReadinessDecision:
    allowed: bool
    blocking_reasons: list[str] = field(default_factory=list)
    status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_autonomous_readiness(
    profile_label: str = "default",
) -> AutonomousReadinessDecision:
    try:
        report = build_status_report(profile_label=profile_label)
    except Exception as exc:
        return AutonomousReadinessDecision(
            allowed=False,
            blocking_reasons=["autonomous_readiness_evaluation_error"],
            status={
                "profile_label": profile_label,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )

    return AutonomousReadinessDecision(
        allowed=report.autonomous_available,
        blocking_reasons=list(report.blocking_reasons),
        status=report.to_dict(),
    )


def require_autonomous_ready(profile_label: str = "default") -> None:
    decision = evaluate_autonomous_readiness(profile_label=profile_label)

    if not decision.allowed:
        reasons = ", ".join(decision.blocking_reasons) or "unknown"
        raise AutonomousReadinessError(
            f"Autonomous operation is not available: {reasons}"
        )
