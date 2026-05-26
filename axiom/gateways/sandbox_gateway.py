from __future__ import annotations

import platform
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

from axiom.persistence.repositories import record_resource_usage


class SandboxExecutionDeniedError(RuntimeError):
    pass


class SandboxPolicyError(RuntimeError):
    pass


class SandboxGatewayDisabledError(RuntimeError):
    pass


class SandboxProviderNotApprovedError(RuntimeError):
    pass


class SandboxRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxPolicy:
    max_ram_mb: int = 256
    max_wall_clock_seconds: int = 60
    network_access: str = "denied"


@dataclass(frozen=True)
class SandboxGatewayConfig:
    real_execution_enabled: bool = False
    windows_job_object_approved: bool = False
    approved_by_panel_version: str | None = None
    kill_on_job_close: bool = True
    active_process_limit: int = 1


@dataclass(frozen=True)
class SandboxAuthorization:
    manifest_id: str
    task_id: int
    allow_execute: bool


@dataclass(frozen=True)
class SandboxUsageResult:
    task_id: int
    ram_usage_id: int
    wall_clock_usage_id: int
    ram_mb: float
    wall_clock_seconds: float
    ram_status: str
    wall_clock_status: str


@dataclass(frozen=True)
class SandboxExecutionResult(SandboxUsageResult):
    exit_code: int | None
    timed_out: bool
    command: tuple[str, ...]


@dataclass(frozen=True)
class SandboxProcessHandle:
    job_handle: object
    process_handle: object
    thread_handle: object
    process_id: int


class JobObjectAdapter(Protocol):
    def create_job(self) -> object:
        ...

    def configure_limits(
        self,
        job_handle: object,
        *,
        ram_bytes: int,
        kill_on_job_close: bool,
        active_process_limit: int,
    ) -> None:
        ...

    def create_suspended_process(
        self,
        command: list[str],
        *,
        cwd: str | None,
    ) -> SandboxProcessHandle:
        ...

    def assign_process(self, job_handle: object, process_handle: object) -> None:
        ...

    def resume_thread(self, thread_handle: object) -> None:
        ...

    def wait_process(self, process_handle: object, timeout_ms: int) -> bool:
        ...

    def terminate_job(self, job_handle: object, exit_code: int) -> None:
        ...

    def get_exit_code(self, process_handle: object) -> int:
        ...

    def peak_job_memory_bytes(self, job_handle: object) -> int:
        ...

    def close_handle(self, handle: object) -> None:
        ...


class WindowsJobObjectAdapter:
    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise SandboxRuntimeError("Windows Job Objects require Windows")

        import win32api
        import win32con
        import win32event
        import win32job
        import win32process

        self.win32api = win32api
        self.win32con = win32con
        self.win32event = win32event
        self.win32job = win32job
        self.win32process = win32process

    def create_job(self) -> object:
        return self.win32job.CreateJobObject(None, f"AXIOMSandbox-{uuid.uuid4()}")

    def configure_limits(
        self,
        job_handle: object,
        *,
        ram_bytes: int,
        kill_on_job_close: bool,
        active_process_limit: int,
    ) -> None:
        info = self.win32job.QueryInformationJobObject(
            job_handle,
            self.win32job.JobObjectExtendedLimitInformation,
        )
        flags = (
            self.win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
            | self.win32job.JOB_OBJECT_LIMIT_JOB_MEMORY
            | self.win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
        )
        if kill_on_job_close:
            flags |= self.win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        info["BasicLimitInformation"]["LimitFlags"] = flags
        info["BasicLimitInformation"]["ActiveProcessLimit"] = active_process_limit
        info["ProcessMemoryLimit"] = ram_bytes
        info["JobMemoryLimit"] = ram_bytes
        self.win32job.SetInformationJobObject(
            job_handle,
            self.win32job.JobObjectExtendedLimitInformation,
            info,
        )

    def create_suspended_process(
        self,
        command: list[str],
        *,
        cwd: str | None,
    ) -> SandboxProcessHandle:
        startup = self.win32process.STARTUPINFO()
        flags = self.win32process.CREATE_SUSPENDED | self.win32con.CREATE_NO_WINDOW
        command_line = subprocess.list2cmdline(command)
        process_handle, thread_handle, process_id, _thread_id = self.win32process.CreateProcess(
            None,
            command_line,
            None,
            None,
            False,
            flags,
            None,
            cwd,
            startup,
        )
        return SandboxProcessHandle(
            job_handle=None,
            process_handle=process_handle,
            thread_handle=thread_handle,
            process_id=int(process_id),
        )

    def assign_process(self, job_handle: object, process_handle: object) -> None:
        self.win32job.AssignProcessToJobObject(job_handle, process_handle)

    def resume_thread(self, thread_handle: object) -> None:
        self.win32process.ResumeThread(thread_handle)

    def wait_process(self, process_handle: object, timeout_ms: int) -> bool:
        result = self.win32event.WaitForSingleObject(process_handle, timeout_ms)
        return result == self.win32event.WAIT_OBJECT_0

    def terminate_job(self, job_handle: object, exit_code: int) -> None:
        self.win32job.TerminateJobObject(job_handle, exit_code)

    def get_exit_code(self, process_handle: object) -> int:
        return int(self.win32process.GetExitCodeProcess(process_handle))

    def peak_job_memory_bytes(self, job_handle: object) -> int:
        info = self.win32job.QueryInformationJobObject(
            job_handle,
            self.win32job.JobObjectExtendedLimitInformation,
        )
        return int(info.get("PeakJobMemoryUsed") or 0)

    def close_handle(self, handle: object) -> None:
        if handle is not None:
            self.win32api.CloseHandle(handle)


class SandboxGateway:
    """
    Fail-closed SandboxGateway foundation.

    Real command/process execution is available only on Windows through an
    explicitly enabled and approved Job Object path.
    """

    MAX_RAM_MB = 256
    MAX_WALL_CLOCK_SECONDS = 60

    def __init__(
        self,
        policy: SandboxPolicy | None = None,
        config: SandboxGatewayConfig | None = None,
        job_adapter: JobObjectAdapter | None = None,
    ):
        self.policy = policy or SandboxPolicy()
        self.config = config or SandboxGatewayConfig()
        self.job_adapter = job_adapter
        self._validate_policy()

    def _validate_policy(self) -> None:
        if self.policy.max_ram_mb <= 0:
            raise SandboxPolicyError("max_ram_mb must be positive")
        if self.policy.max_ram_mb > self.MAX_RAM_MB:
            raise SandboxPolicyError("max_ram_mb exceeds AXIOM sandbox cap")

        if self.policy.max_wall_clock_seconds <= 0:
            raise SandboxPolicyError("max_wall_clock_seconds must be positive")
        if self.policy.max_wall_clock_seconds > self.MAX_WALL_CLOCK_SECONDS:
            raise SandboxPolicyError("max_wall_clock_seconds exceeds AXIOM sandbox cap")

        if self.policy.network_access != "denied":
            raise SandboxPolicyError("sandbox network_access must be denied in this phase")

        if self.config.active_process_limit != 1:
            raise SandboxPolicyError("active_process_limit must remain 1")

    def _require_real_execution(self, authorization: SandboxAuthorization) -> None:
        if not self.config.real_execution_enabled:
            raise SandboxGatewayDisabledError(
                "Sandbox execution requires real_execution_enabled"
            )
        if not self.config.windows_job_object_approved:
            raise SandboxProviderNotApprovedError(
                "Windows Job Object execution is not approved"
            )
        if not self.config.approved_by_panel_version:
            raise SandboxProviderNotApprovedError(
                "approved_by_panel_version is required for sandbox execution"
            )
        if not self.config.kill_on_job_close:
            raise SandboxPolicyError("kill_on_job_close must remain enabled")
        if not authorization.manifest_id:
            raise SandboxProviderNotApprovedError("manifest_id is required")
        if authorization.task_id <= 0:
            raise SandboxProviderNotApprovedError("task_id must be positive")
        if not authorization.allow_execute:
            raise SandboxExecutionDeniedError("sandbox execution is not authorized")

    def execute_disabled(self, command: list[str]) -> None:
        if not command:
            raise SandboxPolicyError("command must not be empty")

        raise SandboxExecutionDeniedError(
            "Sandbox execution is not implemented in this phase"
        )

    def execute(
        self,
        command: list[str],
        authorization: SandboxAuthorization,
        *,
        cwd: str | None = None,
    ) -> SandboxExecutionResult:
        if not command:
            raise SandboxPolicyError("command must not be empty")
        if any(not part for part in command):
            raise SandboxPolicyError("command entries must not be empty")

        self._require_real_execution(authorization)

        adapter = self.job_adapter or WindowsJobObjectAdapter()
        ram_bytes = self.policy.max_ram_mb * 1024 * 1024
        timeout_ms = self.policy.max_wall_clock_seconds * 1000
        job_handle = None
        process_handle = None
        thread_handle = None
        timed_out = False
        exit_code: int | None = None
        peak_memory_bytes = 0
        start = time.monotonic()

        try:
            job_handle = adapter.create_job()
            adapter.configure_limits(
                job_handle,
                ram_bytes=ram_bytes,
                kill_on_job_close=self.config.kill_on_job_close,
                active_process_limit=self.config.active_process_limit,
            )
            proc = adapter.create_suspended_process(command, cwd=cwd)
            process_handle = proc.process_handle
            thread_handle = proc.thread_handle
            adapter.assign_process(job_handle, process_handle)
            adapter.resume_thread(thread_handle)
            completed = adapter.wait_process(process_handle, timeout_ms)
            if not completed:
                timed_out = True
                adapter.terminate_job(job_handle, 1)
            else:
                exit_code = adapter.get_exit_code(process_handle)

            peak_memory_bytes = adapter.peak_job_memory_bytes(job_handle)
        except Exception as exc:
            wall_clock_seconds = time.monotonic() - start
            self.record_dummy_usage(
                task_id=authorization.task_id,
                ram_mb=0,
                wall_clock_seconds=wall_clock_seconds,
            )
            raise SandboxRuntimeError(f"Sandbox execution failed: {exc}") from exc
        finally:
            for handle in (thread_handle, process_handle, job_handle):
                if handle is not None:
                    adapter.close_handle(handle)

        wall_clock_seconds = time.monotonic() - start
        if timed_out:
            wall_clock_seconds = max(
                wall_clock_seconds,
                float(self.policy.max_wall_clock_seconds) + 0.001,
            )
        ram_mb = peak_memory_bytes / (1024 * 1024)

        result = self.record_dummy_usage(
            task_id=authorization.task_id,
            ram_mb=ram_mb,
            wall_clock_seconds=wall_clock_seconds,
        )

        execution_result = SandboxExecutionResult(
            task_id=result.task_id,
            ram_usage_id=result.ram_usage_id,
            wall_clock_usage_id=result.wall_clock_usage_id,
            ram_mb=result.ram_mb,
            wall_clock_seconds=result.wall_clock_seconds,
            ram_status=result.ram_status,
            wall_clock_status=result.wall_clock_status,
            exit_code=exit_code,
            timed_out=timed_out,
            command=tuple(command),
        )

        if timed_out:
            raise SandboxExecutionDeniedError("Sandbox process exceeded wall-clock limit")
        if execution_result.ram_status == "exceeded":
            raise SandboxExecutionDeniedError("Sandbox process exceeded RAM limit")

        return execution_result

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
