from __future__ import annotations

from dataclasses import dataclass

from axiom.persistence.repositories import record_resource_usage


class SandboxExecutionDeniedError(RuntimeError):
    pass


class SandboxPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxPolicy:
    max_ram_mb: int = 256
    max_wall_clock_seconds: int = 60
    network_access: str = "denied"


@dataclass(frozen=True)
class SandboxUsageResult:
    task_id: int
    ram_usage_id: int
    wall_clock_usage_id: int
    ram_mb: float
    wall_clock_seconds: float
    ram_status: str
    wall_clock_status: str


class SandboxGateway:
    """
    Fail-closed SandboxGateway foundation.

    Real command/process execution is intentionally not implemented here.
    This boundary validates sandbox policy and records test/dummy usage only.
    """

    def __init__(self, policy: SandboxPolicy | None = None):
        self.policy = policy or SandboxPolicy()
        self._validate_policy()

    def _validate_policy(self) -> None:
        if self.policy.max_ram_mb <= 0:
            raise SandboxPolicyError("max_ram_mb must be positive")

        if self.policy.max_wall_clock_seconds <= 0:
            raise SandboxPolicyError("max_wall_clock_seconds must be positive")

        if self.policy.network_access != "denied":
            raise SandboxPolicyError("sandbox network_access must be denied in this phase")

    def execute_disabled(self, command: list[str]) -> None:
        if not command:
            raise SandboxPolicyError("command must not be empty")

        raise SandboxExecutionDeniedError(
            "Sandbox execution is not implemented in this phase"
        )

    def record_dummy_usage(
        self,
        task_id: int,
        ram_mb: int | float,
        wall_clock_seconds: int | float,
    ) -> SandboxUsageResult:
        if ram_mb < 0:
            raise SandboxPolicyError("ram_mb must be non-negative")

        if wall_clock_seconds < 0:
            raise SandboxPolicyError("wall_clock_seconds must be non-negative")

        ram_status = "within_limit"
        if ram_mb > self.policy.max_ram_mb:
            ram_status = "exceeded"

        wall_clock_status = "within_limit"
        if wall_clock_seconds > self.policy.max_wall_clock_seconds:
            wall_clock_status = "exceeded"

        ram_usage_id = record_resource_usage(
            task_id=task_id,
            resource_type="sandbox_ram_mb",
            amount=ram_mb,
            limit_value=self.policy.max_ram_mb,
            status=ram_status,
            details={
                "usage_source": "sandbox_gateway_dummy_usage",
            },
        )

        wall_clock_usage_id = record_resource_usage(
            task_id=task_id,
            resource_type="sandbox_wall_clock_seconds",
            amount=wall_clock_seconds,
            limit_value=self.policy.max_wall_clock_seconds,
            status=wall_clock_status,
            details={
                "usage_source": "sandbox_gateway_dummy_usage",
            },
        )

        return SandboxUsageResult(
            task_id=task_id,
            ram_usage_id=ram_usage_id,
            wall_clock_usage_id=wall_clock_usage_id,
            ram_mb=float(ram_mb),
            wall_clock_seconds=float(wall_clock_seconds),
            ram_status=ram_status,
            wall_clock_status=wall_clock_status,
        )
