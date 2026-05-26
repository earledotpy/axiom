from dataclasses import dataclass

import pytest

from axiom.gateways.network_gateway import (
    NetworkAccessDeniedError,
    NetworkAuthorization,
    NetworkCredentialsError,
    NetworkFetchError,
    NetworkGateway,
    NetworkGatewayConfig,
    NetworkGatewayDisabledError,
    NetworkPolicy,
    NetworkPolicyError,
    NetworkProviderNotApprovedError,
)
from axiom.persistence.repositories import create_session, create_task, get_resource_usage_for_task

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


@dataclass
class FakeHttpResponse:
    status_code: int
    content: bytes
    headers: dict[str, str]


class FakeHttpTransport:
    def __init__(self, response: FakeHttpResponse | None = None):
        self.response = response or FakeHttpResponse(
            status_code=200,
            content=b'{"web":{"results":[]}}',
            headers={},
        )
        self.calls = []

    def get(self, url, *, headers, params, timeout, allow_redirects):
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "params": dict(params),
                "timeout": timeout,
                "allow_redirects": allow_redirects,
            }
        )
        return self.response


def make_task() -> int:
    session_id = create_session(operator_id="network-gateway-test")
    return create_task(
        session_id=session_id,
        chain_id="chain-network-gateway-test",
        task_class="system_maintenance",
        task_type="network_gateway_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )


def approved_policy(max_response_bytes: int = 1024) -> NetworkPolicy:
    return NetworkPolicy(
        mode="allowlist_only",
        allowlist=("api.search.brave.com",),
        max_response_bytes=max_response_bytes,
    )


def approved_config() -> NetworkGatewayConfig:
    return NetworkGatewayConfig(
        real_fetch_enabled=True,
        provider_configuration_approved=True,
        approved_by_panel_version="test",
    )


def network_auth(task_id: int, **overrides) -> NetworkAuthorization:
    values = {
        "manifest_id": "role.system_maintenance_noop.v1",
        "task_id": task_id,
        "allow_fetch": True,
        "max_response_bytes": 1024,
    }
    values.update(overrides)
    return NetworkAuthorization(**values)


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


def test_network_gateway_real_fetch_requires_explicit_enablement():
    task_id = make_task()
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=NetworkGatewayConfig(
            provider_configuration_approved=True,
            approved_by_panel_version="test",
        ),
        http_transport=FakeHttpTransport(),
    )

    with pytest.raises(NetworkGatewayDisabledError):
        gateway.brave_web_search("axiom", network_auth(task_id))


def test_network_gateway_real_fetch_requires_provider_approval():
    task_id = make_task()
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=NetworkGatewayConfig(real_fetch_enabled=True),
        http_transport=FakeHttpTransport(),
    )

    with pytest.raises(NetworkProviderNotApprovedError):
        gateway.brave_web_search("axiom", network_auth(task_id))


def test_network_gateway_real_fetch_requires_api_key(monkeypatch):
    task_id = make_task()
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=approved_config(),
        http_transport=FakeHttpTransport(),
    )

    with pytest.raises(NetworkCredentialsError):
        gateway.brave_web_search("axiom", network_auth(task_id))


def test_network_gateway_brave_web_search_uses_approved_endpoint_and_headers(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    transport = FakeHttpTransport()
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=approved_config(),
        http_transport=transport,
    )

    result = gateway.brave_web_search(
        "axiom runtime",
        network_auth(task_id),
        count=3,
        country="us",
        search_lang="en",
        safesearch="strict",
    )

    assert result.status_code == 200
    assert result.response_bytes == len(b'{"web":{"results":[]}}')
    assert len(transport.calls) == 1

    call = transport.calls[0]
    assert call["url"] == "https://api.search.brave.com/res/v1/web/search"
    assert call["headers"]["X-Subscription-Token"] == "test-secret"
    assert call["headers"]["Accept"] == "application/json"
    assert call["params"] == {
        "q": "axiom runtime",
        "count": 3,
        "country": "us",
        "search_lang": "en",
        "safesearch": "strict",
    }
    assert call["timeout"] == 10
    assert call["allow_redirects"] is False


def test_network_gateway_brave_web_search_records_response_bytes(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=approved_policy(max_response_bytes=100),
        config=approved_config(),
        http_transport=FakeHttpTransport(
            FakeHttpResponse(status_code=200, content=b"{}", headers={})
        ),
    )

    gateway.brave_web_search("axiom", network_auth(task_id, max_response_bytes=100))

    rows = get_resource_usage_for_task(task_id)
    network_rows = [row for row in rows if row["resource_type"] == "network_response_bytes"]

    assert network_rows
    assert network_rows[-1]["amount"] == 2
    assert network_rows[-1]["limit_value"] == 100
    assert network_rows[-1]["status"] == "within_limit"
    assert "test-secret" not in (network_rows[-1]["details_json"] or "")
    assert "network_gateway_brave_web_search" in network_rows[-1]["details_json"]


def test_network_gateway_brave_web_search_rejects_oversized_response_after_accounting(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=approved_policy(max_response_bytes=3),
        config=approved_config(),
        http_transport=FakeHttpTransport(
            FakeHttpResponse(status_code=200, content=b"hello", headers={})
        ),
    )

    with pytest.raises(NetworkPolicyError):
        gateway.brave_web_search("axiom", network_auth(task_id, max_response_bytes=3))

    rows = get_resource_usage_for_task(task_id)
    network_rows = [row for row in rows if row["resource_type"] == "network_response_bytes"]

    assert network_rows[-1]["amount"] == 5
    assert network_rows[-1]["limit_value"] == 3
    assert network_rows[-1]["status"] == "exceeded"


def test_network_gateway_brave_web_search_rejects_http_error_after_accounting(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=approved_config(),
        http_transport=FakeHttpTransport(
            FakeHttpResponse(status_code=429, content=b"rate limit", headers={})
        ),
    )

    with pytest.raises(NetworkFetchError):
        gateway.brave_web_search("axiom", network_auth(task_id))

    rows = get_resource_usage_for_task(task_id)
    network_rows = [row for row in rows if row["resource_type"] == "network_response_bytes"]

    assert network_rows[-1]["amount"] == len(b"rate limit")
    assert network_rows[-1]["status"] == "within_limit"


def test_network_gateway_brave_web_search_denies_redirect(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=approved_config(),
        http_transport=FakeHttpTransport(
            FakeHttpResponse(
                status_code=302,
                content=b"",
                headers={"location": "https://example.com"},
            )
        ),
    )

    with pytest.raises(NetworkFetchError):
        gateway.brave_web_search("axiom", network_auth(task_id))


def test_network_gateway_brave_web_search_rejects_count_above_brave_cap(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=approved_policy(),
        config=approved_config(),
        http_transport=FakeHttpTransport(),
    )

    with pytest.raises(NetworkPolicyError):
        gateway.brave_web_search("axiom", network_auth(task_id), count=21)


def test_network_gateway_brave_web_search_rejects_unapproved_endpoint_host(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-secret")
    gateway = NetworkGateway(
        policy=NetworkPolicy(
            mode="allowlist_only",
            allowlist=("example.com",),
            max_response_bytes=1024,
        ),
        config=NetworkGatewayConfig(
            real_fetch_enabled=True,
            provider_configuration_approved=True,
            approved_by_panel_version="test",
            endpoint_url="https://example.com/res/v1/web/search",
        ),
        http_transport=FakeHttpTransport(),
    )

    with pytest.raises(NetworkAccessDeniedError):
        gateway.brave_web_search("axiom", network_auth(task_id))


def test_network_gateway_brave_web_search_rejects_endpoint_query_or_fragment(monkeypatch):
    task_id = make_task()
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-key")

    for endpoint_url in (
        "https://api.search.brave.com/res/v1/web/search?x=1",
        "https://api.search.brave.com/res/v1/web/search#frag",
    ):
        gateway = NetworkGateway(
            NetworkPolicy(
                mode="allowlist_only",
                allowlist=("api.search.brave.com",),
                max_response_bytes=100,
            ),
            config=NetworkGatewayConfig(
                real_fetch_enabled=True,
                provider_configuration_approved=True,
                approved_by_panel_version="test",
                endpoint_url=endpoint_url,
            ),
            http_transport=FakeHttpTransport(
                FakeHttpResponse(status_code=200, content=b"{}", headers={})
            ),
        )

        with pytest.raises(NetworkAccessDeniedError):
            gateway.brave_web_search("axiom", network_auth(task_id, max_response_bytes=100))
