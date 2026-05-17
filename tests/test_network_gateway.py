import pytest

from axiom.gateways.network_gateway import (
    NetworkAccessDeniedError,
    NetworkGateway,
    NetworkPolicy,
    NetworkPolicyError,
)
from axiom.persistence.repositories import create_session, create_task, get_resource_usage_for_task

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def make_task() -> int:
    session_id = create_session(operator_id="network-gateway-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-network-gateway-test",
        task_class="system_maintenance",
        task_type="network_gateway_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def test_network_gateway_denies_by_default():
    gateway = NetworkGateway()

    with pytest.raises(NetworkAccessDeniedError):
        gateway.fetch_disabled("https://example.com")


def test_network_gateway_rejects_unsupported_scheme():
    gateway = NetworkGateway(NetworkPolicy(mode="allowlist_only", allowlist=("example.com",)))

    with pytest.raises(NetworkPolicyError):
        gateway.fetch_disabled("ftp://example.com/file.txt")


def test_network_gateway_rejects_missing_host():
    gateway = NetworkGateway(NetworkPolicy(mode="allowlist_only", allowlist=("example.com",)))

    with pytest.raises(NetworkPolicyError):
        gateway.fetch_disabled("https:///missing-host")


def test_network_gateway_allowlist_rejects_unlisted_host():
    gateway = NetworkGateway(NetworkPolicy(mode="allowlist_only", allowlist=("example.com",)))

    with pytest.raises(NetworkAccessDeniedError):
        gateway.fetch_disabled("https://not-example.com")


def test_network_gateway_allowlisted_fetch_still_fails_closed():
    gateway = NetworkGateway(NetworkPolicy(mode="allowlist_only", allowlist=("example.com",)))

    with pytest.raises(NetworkAccessDeniedError):
        gateway.fetch_disabled("https://example.com")


def test_network_gateway_dummy_response_records_network_response_bytes():
    task_id = make_task()
    gateway = NetworkGateway(
        NetworkPolicy(
            mode="allowlist_only",
            allowlist=("example.com",),
            max_response_bytes=100,
        )
    )

    result = gateway.record_dummy_response(
        task_id=task_id,
        url="https://example.com",
        body=b"hello",
        status_code=200,
    )

    rows = get_resource_usage_for_task(task_id)
    network_rows = [row for row in rows if row["resource_type"] == "network_response_bytes"]

    assert result.response_bytes == 5
    assert network_rows
    assert network_rows[-1]["amount"] == 5
    assert network_rows[-1]["limit_value"] == 100
    assert network_rows[-1]["status"] == "within_limit"


def test_network_gateway_dummy_response_rejects_oversized_response_after_accounting():
    task_id = make_task()
    gateway = NetworkGateway(
        NetworkPolicy(
            mode="allowlist_only",
            allowlist=("example.com",),
            max_response_bytes=3,
        )
    )

    with pytest.raises(NetworkPolicyError):
        gateway.record_dummy_response(
            task_id=task_id,
            url="https://example.com",
            body=b"hello",
            status_code=200,
        )

    rows = get_resource_usage_for_task(task_id)
    network_rows = [row for row in rows if row["resource_type"] == "network_response_bytes"]

    assert network_rows
    assert network_rows[-1]["amount"] == 5
    assert network_rows[-1]["limit_value"] == 3
    assert network_rows[-1]["status"] == "exceeded"
