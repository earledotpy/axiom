from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from axiom.persistence.repositories import record_resource_usage


class NetworkAccessDeniedError(RuntimeError):
    pass


class NetworkPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class NetworkPolicy:
    mode: str = "deny_all"
    allowlist: tuple[str, ...] = ()
    max_response_bytes: int = 5 * 1024 * 1024
    redirect_policy: str = "deny"


@dataclass(frozen=True)
class NetworkFetchResult:
    url: str
    status_code: int
    response_bytes: int
    body: bytes


class NetworkGateway:
    """
    Fail-closed NetworkGateway foundation.

    Real HTTP fetching remains deferred. This gateway only validates network
    policy and provides a controlled test/dummy response path for accounting.
    """

    def __init__(self, policy: NetworkPolicy | None = None):
        self.policy = policy or NetworkPolicy()

    def validate_url_allowed(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise NetworkPolicyError(f"Unsupported URL scheme: {parsed.scheme!r}")

        if not parsed.netloc:
            raise NetworkPolicyError("URL must include a host")

        if self.policy.mode == "deny_all":
            raise NetworkAccessDeniedError("Network access is denied by policy")

        if self.policy.mode != "allowlist_only":
            raise NetworkPolicyError(f"Unknown network policy mode: {self.policy.mode!r}")

        host = parsed.hostname or ""

        if host not in self.policy.allowlist:
            raise NetworkAccessDeniedError(f"Host not in network allowlist: {host}")

    def fetch_disabled(self, url: str) -> NetworkFetchResult:
        """
        Explicit fail-closed fetch method.

        This exists so callers cannot accidentally mistake the foundation gateway
        for a real network client.
        """
        self.validate_url_allowed(url)
        raise NetworkAccessDeniedError("Real network fetch is not implemented in this phase")

    def record_dummy_response(
        self,
        task_id: int,
        url: str,
        body: bytes,
        status_code: int = 200,
    ) -> NetworkFetchResult:
        """
        Test-only accounting path.

        Validates policy and response size, records network_response_bytes, and
        returns a NetworkFetchResult without performing any network I/O.
        """
        self.validate_url_allowed(url)

        response_bytes = len(body)

        status = "within_limit"
        if response_bytes > self.policy.max_response_bytes:
            status = "exceeded"

        usage_id = record_resource_usage(
            task_id=task_id,
            resource_type="network_response_bytes",
            amount=response_bytes,
            limit_value=self.policy.max_response_bytes,
            status=status,
            details={
                "url": url,
                "status_code": status_code,
                "usage_source": "network_gateway_dummy_response",
            },
        )

        if status == "exceeded":
            raise NetworkPolicyError(
                f"Network response size {response_bytes} exceeds limit {self.policy.max_response_bytes}; "
                f"usage_id={usage_id}"
            )

        return NetworkFetchResult(
            url=url,
            status_code=status_code,
            response_bytes=response_bytes,
            body=body,
        )
