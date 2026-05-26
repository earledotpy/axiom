import pytest

from axiom.gateways.sandbox_gateway import (
    SandboxAuthorization,
    SandboxExecutionDeniedError,
    SandboxGateway,
    SandboxGatewayConfig,
    SandboxGatewayDisabledError,
    SandboxPolicy,
    SandboxPolicyError,
    SandboxProviderNotApprovedError,
    SandboxRuntimeError,
)
from axiom.persistence.repositories import create_session, create_task, get_resource_usage_for_task

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


class FakeJobAdapter:
    def __init__(
        self,
        *,
        completed: bool = True,
        exit_code: int = 0,
        peak_memory_bytes: int = 32 * 1024 * 1024,
    ):
        self.completed = completed
        self.exit_code = exit_code
        self.peak_memory_bytes_value = peak_memory_bytes
        self.calls = []
        self.closed = []

    def create_job(self):
        self.calls.append(("create_job",))
        return "job"

    def configure_limits(
        self,
        job_handle,
        *,
        ram_bytes,
        kill_on_job_close,
        active_process_limit,
    ):
        self.calls.append(
            (
                "configure_limits",
                job_handle,
                ram_bytes,
                kill_on_job_close,
                active_process_limit,
            )
        )

    def create_suspended_process(self, command, *, cwd):
        self.calls.append(("create_suspended_process", tuple(command), cwd))
        from axiom.gateways.sandbox_gateway import SandboxProcessHandle

        return SandboxProcessHandle(
            job_handle="job",
            process_handle="process",
            thread_handle="thread",
            process_id=123,
        )

    def assign_process(self, job_handle, process_handle):
        self.calls.append(("assign_process", job_handle, process_handle))

    def resume_thread(self, thread_handle):
        self.calls.append(("resume_thread", thread_handle))

    def wait_process(self, process_handle, timeout_ms):
        self.calls.append(("wait_process", process_handle, timeout_ms))
        return self.completed

    def terminate_job(self, job_handle, exit_code):
        self.calls.append(("terminate_job", job_handle, exit_code))

    def get_exit_code(self, process_handle):
        self.calls.append(("get_exit_code", process_handle))
        return self.exit_code

    def peak_job_memory_bytes(self, job_handle):
        self.calls.append(("peak_job_memory_bytes", job_handle))
        return self.peak_memory_bytes_value

    def close_handle(self, handle):
        self.calls.append(("close_handle", handle))
        self.closed.append(handle)


def make_task() -> int:
    session_id = create_session(operator_id="sandbox-gateway-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-sandbox-gateway-test",
        task_class="system_maintenance",
        task_type="sandbox_gateway_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def sandbox_auth(task_id: int, **overrides) -> SandboxAuthorization:
    values = {
        "manifest_id": "role.system_maintenance_noop.v1",
        "task_id": task_id,
        "allow_execute": True,
    }
    values.update(overrides)
    return SandboxAuthorization(**values)


def enabled_config() -> SandboxGatewayConfig:
    return SandboxGatewayConfig(
        real_execution_enabled=True,
        windows_job_object_approved=True,
        approved_by_panel_version="test",
    )


def test_sandbox_gateway_rejects_non_positive_ram_limit():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(SandboxPolicy(max_ram_mb=0))


def test_sandbox_gateway_rejects_non_positive_wall_clock_limit():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(SandboxPolicy(max_wall_clock_seconds=0))


def test_sandbox_gateway_rejects_network_access_not_denied():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(SandboxPolicy(network_access="allow"))


def test_sandbox_gateway_rejects_ram_above_canonical_cap():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(SandboxPolicy(max_ram_mb=257))


def test_sandbox_gateway_rejects_wall_clock_above_canonical_cap():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(SandboxPolicy(max_wall_clock_seconds=61))


def test_sandbox_gateway_rejects_active_process_limit_above_one():
    with pytest.raises(SandboxPolicyError):
        SandboxGateway(config=SandboxGatewayConfig(active_process_limit=2))


def test_sandbox_gateway_execute_disabled_rejects_empty_command():
    gateway = SandboxGateway()

    with pytest.raises(SandboxPolicyError):
        gateway.execute_disabled([])


def test_sandbox_gateway_execute_disabled_fails_closed():
    gateway = SandboxGateway()

    with pytest.raises(SandboxExecutionDeniedError):
        gateway.execute_disabled(["python", "-c", "print('hello')"])


def test_sandbox_gateway_records_dummy_usage_within_limits():
    task_id = make_task()
    gateway = SandboxGateway(
        SandboxPolicy(
            max_ram_mb=256,
            max_wall_clock_seconds=60,
            network_access="denied",
        )
    )

    result = gateway.record_dummy_usage(
        task_id=task_id,
        ram_mb=128,
        wall_clock_seconds=30,
    )

    rows = get_resource_usage_for_task(task_id)
    resource_types = {row["resource_type"] for row in rows}

    assert result.ram_status == "within_limit"
    assert result.wall_clock_status == "within_limit"
    assert "sandbox_ram_mb" in resource_types
    assert "sandbox_wall_clock_seconds" in resource_types


def test_sandbox_gateway_records_dummy_usage_exceeded_limits():
    task_id = make_task()
    gateway = SandboxGateway(
        SandboxPolicy(
            max_ram_mb=256,
            max_wall_clock_seconds=60,
            network_access="denied",
        )
    )

    result = gateway.record_dummy_usage(
        task_id=task_id,
        ram_mb=300,
        wall_clock_seconds=61,
    )

    rows = get_resource_usage_for_task(task_id)
    ram_rows = [row for row in rows if row["resource_type"] == "sandbox_ram_mb"]
    wall_rows = [row for row in rows if row["resource_type"] == "sandbox_wall_clock_seconds"]

    assert result.ram_status == "exceeded"
    assert result.wall_clock_status == "exceeded"
    assert ram_rows[-1]["amount"] == 300
    assert ram_rows[-1]["limit_value"] == 256
    assert ram_rows[-1]["status"] == "exceeded"
    assert wall_rows[-1]["amount"] == 61
    assert wall_rows[-1]["limit_value"] == 60
    assert wall_rows[-1]["status"] == "exceeded"


def test_sandbox_gateway_rejects_negative_dummy_ram():
    task_id = make_task()
    gateway = SandboxGateway()

    with pytest.raises(SandboxPolicyError):
        gateway.record_dummy_usage(task_id=task_id, ram_mb=-1, wall_clock_seconds=1)


def test_sandbox_gateway_rejects_negative_dummy_wall_clock():
    task_id = make_task()
    gateway = SandboxGateway()

    with pytest.raises(SandboxPolicyError):
        gateway.record_dummy_usage(task_id=task_id, ram_mb=1, wall_clock_seconds=-1)


def test_sandbox_gateway_execute_requires_explicit_enablement():
    task_id = make_task()
    gateway = SandboxGateway(
        config=SandboxGatewayConfig(
            windows_job_object_approved=True,
            approved_by_panel_version="test",
        ),
        job_adapter=FakeJobAdapter(),
    )

    with pytest.raises(SandboxGatewayDisabledError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id))


def test_sandbox_gateway_execute_requires_job_object_approval():
    task_id = make_task()
    gateway = SandboxGateway(
        config=SandboxGatewayConfig(real_execution_enabled=True),
        job_adapter=FakeJobAdapter(),
    )

    with pytest.raises(SandboxProviderNotApprovedError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id))


def test_sandbox_gateway_execute_requires_authorization():
    task_id = make_task()
    gateway = SandboxGateway(config=enabled_config(), job_adapter=FakeJobAdapter())

    with pytest.raises(SandboxExecutionDeniedError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id, allow_execute=False))


def test_sandbox_gateway_execute_rejects_empty_command_entry():
    task_id = make_task()
    gateway = SandboxGateway(config=enabled_config(), job_adapter=FakeJobAdapter())

    with pytest.raises(SandboxPolicyError):
        gateway.execute(["python", ""], sandbox_auth(task_id))


def test_sandbox_gateway_execute_assigns_suspended_process_to_limited_job():
    task_id = make_task()
    adapter = FakeJobAdapter(exit_code=7, peak_memory_bytes=64 * 1024 * 1024)
    gateway = SandboxGateway(
        policy=SandboxPolicy(max_ram_mb=128, max_wall_clock_seconds=30),
        config=enabled_config(),
        job_adapter=adapter,
    )

    result = gateway.execute(["python", "-V"], sandbox_auth(task_id), cwd="C:\\axiom")

    assert result.exit_code == 7
    assert result.timed_out is False
    assert result.command == ("python", "-V")
    assert result.ram_mb == 64.0
    assert result.ram_status == "within_limit"
    assert result.wall_clock_status == "within_limit"
    assert ("configure_limits", "job", 128 * 1024 * 1024, True, 1) in adapter.calls
    assert ("create_suspended_process", ("python", "-V"), "C:\\axiom") in adapter.calls
    assert ("assign_process", "job", "process") in adapter.calls
    assert ("resume_thread", "thread") in adapter.calls
    assert ("wait_process", "process", 30_000) in adapter.calls
    assert adapter.closed == ["thread", "process", "job"]


def test_sandbox_gateway_execute_records_resource_usage():
    task_id = make_task()
    gateway = SandboxGateway(config=enabled_config(), job_adapter=FakeJobAdapter())

    gateway.execute(["python", "-V"], sandbox_auth(task_id))

    rows = get_resource_usage_for_task(task_id)
    ram_rows = [row for row in rows if row["resource_type"] == "sandbox_ram_mb"]
    wall_rows = [row for row in rows if row["resource_type"] == "sandbox_wall_clock_seconds"]

    assert ram_rows
    assert wall_rows
    assert ram_rows[-1]["status"] == "within_limit"
    assert wall_rows[-1]["status"] == "within_limit"


def test_sandbox_gateway_execute_timeout_terminates_job_and_records_exceeded_wall_clock():
    task_id = make_task()
    adapter = FakeJobAdapter(completed=False)
    gateway = SandboxGateway(
        policy=SandboxPolicy(max_ram_mb=256, max_wall_clock_seconds=1),
        config=enabled_config(),
        job_adapter=adapter,
    )

    with pytest.raises(SandboxExecutionDeniedError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id))

    assert ("terminate_job", "job", 1) in adapter.calls
    rows = get_resource_usage_for_task(task_id)
    wall_rows = [row for row in rows if row["resource_type"] == "sandbox_wall_clock_seconds"]
    assert wall_rows[-1]["status"] == "exceeded"
    assert wall_rows[-1]["limit_value"] == 1


def test_sandbox_gateway_execute_ram_exceeded_records_usage_then_fails():
    task_id = make_task()
    gateway = SandboxGateway(
        policy=SandboxPolicy(max_ram_mb=1, max_wall_clock_seconds=60),
        config=enabled_config(),
        job_adapter=FakeJobAdapter(peak_memory_bytes=2 * 1024 * 1024),
    )

    with pytest.raises(SandboxExecutionDeniedError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id))

    rows = get_resource_usage_for_task(task_id)
    ram_rows = [row for row in rows if row["resource_type"] == "sandbox_ram_mb"]
    assert ram_rows[-1]["status"] == "exceeded"
    assert ram_rows[-1]["limit_value"] == 1


def test_sandbox_gateway_execute_wraps_adapter_failure():
    task_id = make_task()

    class FailingAdapter(FakeJobAdapter):
        def assign_process(self, job_handle, process_handle):
            raise RuntimeError("assign failed")

    gateway = SandboxGateway(config=enabled_config(), job_adapter=FailingAdapter())

    with pytest.raises(SandboxRuntimeError):
        gateway.execute(["python", "-V"], sandbox_auth(task_id))

    rows = get_resource_usage_for_task(task_id)
    resource_types = {row["resource_type"] for row in rows}
    assert "sandbox_ram_mb" in resource_types
    assert "sandbox_wall_clock_seconds" in resource_types
