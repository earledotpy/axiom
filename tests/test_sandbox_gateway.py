import pytest

from axiom.gateways.sandbox_gateway import (
    SandboxExecutionDeniedError,
    SandboxGateway,
    SandboxPolicy,
    SandboxPolicyError,
)
from axiom.persistence.repositories import create_session, create_task, get_resource_usage_for_task

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="sandbox-gateway-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-sandbox-gateway-test",
        task_class="system_maintenance",
        task_type="sandbox_gateway_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
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
