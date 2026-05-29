from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from axiom.app.status_report import build_status_report


@dataclass(frozen=True)
class AutonomousGateStep:
    step_number: int
    name: str
    passed: bool
    reason: str | None = None


@dataclass(frozen=True)
class AutonomousGatePanelData:
    steps: list[AutonomousGateStep]
    overall_ready: bool
    blocking_reasons: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [asdict(s) for s in self.steps],
            "overall_ready": self.overall_ready,
            "blocking_reasons": self.blocking_reasons,
            "details": self.details,
        }


def get_autonomous_gate_status(profile_label: str = "default") -> AutonomousGatePanelData:
    """
    Evaluate the full 7-step autonomous gate and return structured panel data.

    The 7 steps are:
    1. Database initialized
    2. Manifest fingerprints valid
    3. Current trusted model profile present
    4. Safe pass enabled
    5. Autonomous operation enabled
    6. Scheduler heartbeat fresh (< 120 seconds)
    7. No blocking tasks (needs_human_input or quarantined)
    """
    report = build_status_report(profile_label=profile_label)

    steps = [
        AutonomousGateStep(
            step_number=1,
            name="Database Initialized",
            passed=report.database_initialized,
            reason="Schema v1.11.4 loaded" if report.database_initialized else "Database not initialized",
        ),
        AutonomousGateStep(
            step_number=2,
            name="Manifest Fingerprints Valid",
            passed=report.manifest_fingerprints_valid,
            reason=(
                f"{report.details.get('active_manifest_count', 0)} active manifests"
                if report.manifest_fingerprints_valid
                else "Missing active manifests or tool-capability map"
            ),
        ),
        AutonomousGateStep(
            step_number=3,
            name="Current Trusted Model Profile",
            passed=report.current_trusted_model_profile_present,
            reason=(
                f"{report.details.get('current_model_profile', {}).get('model_name', 'unknown')}"
                if report.current_trusted_model_profile_present
                else "No current trusted model profile registered"
            ),
        ),
        AutonomousGateStep(
            step_number=4,
            name="Safe Pass Enabled",
            passed=report.safe_pass_enabled,
            reason=(
                "Safe pass enabled"
                if report.safe_pass_enabled
                else f"Safe pass disabled: {report.details.get('safe_pass_disabled_reason', 'unknown reason')}"
            ),
        ),
        AutonomousGateStep(
            step_number=5,
            name="Autonomous Operation Enabled",
            passed=report.autonomous_operation_enabled,
            reason="Operator enabled autonomous mode" if report.autonomous_operation_enabled else "Operator disabled autonomous mode",
        ),
        AutonomousGateStep(
            step_number=6,
            name="Scheduler Heartbeat Fresh",
            passed=report.scheduler_heartbeat_fresh,
            reason=(
                f"Last tick: {report.details.get('scheduler_heartbeat_last_freshness', 'unknown')}"
                if report.scheduler_heartbeat_fresh
                else "Scheduler heartbeat stale (> 120 seconds)"
            ),
        ),
        AutonomousGateStep(
            step_number=7,
            name="No Blocking Tasks",
            passed=report.no_blocking_tasks,
            reason=(
                "All tasks resolved"
                if report.no_blocking_tasks
                else f"{report.details.get('blocking_task_count', 0)} task(s) need human input or are quarantined"
            ),
        ),
    ]

    return AutonomousGatePanelData(
        steps=steps,
        overall_ready=report.autonomous_available,
        blocking_reasons=report.blocking_reasons,
        details=report.details,
    )
