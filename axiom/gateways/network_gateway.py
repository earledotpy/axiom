from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

import requests
from axiom.persistence.repositories import record_resource_usage


class NetworkAccessDeniedError(RuntimeError):
    pass


class NetworkPolicyError(RuntimeError):
    pass


class NetworkGatewayDisabledError(RuntimeError):
    pass


class NetworkProviderNotApprovedError(RuntimeError):
    pass


class NetworkCredentialsError(RuntimeError):
    pass


class NetworkFetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class NetworkPolicy:
    mode: str = "deny_all"
    allowlist: tuple[str, ...] = ()
    max_response_bytes: int = 5 * 1024 * 1024
    redirect_policy: str = "deny"
    allowed_methods: tuple[str, ...] = ("GET",)


@dataclass(frozen=True)
class NetworkFetchResult:
    url: str
    status_code: int
    response_bytes: int
    body: bytes


@dataclass(frozen=True)
class NetworkGatewayConfig:
    real_fetch_enabled: bool = False
    provider_configuration_approved: bool = False
    approved_by_panel_version: str | None = None
    provider: str = "brave_search"
    api_key_env_var: str = "BRAVE_SEARCH_API_KEY"
    endpoint_url: str = "https://api.search.brave.com/res/v1/web/search"
    timeout_seconds: int = 10


@dataclass(frozen=True)
class NetworkAuthorization:
    manifest_id: str
    task_id: int
    allow_fetch: bool
    max_response_bytes: int


class HttpResponse(Protocol):
    status_code: int
    content: bytes
    headers: dict[str, str]


class HttpTransport(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any],
        timeout: int,
        allow_redirects: bool,
    ) -> HttpResponse:
        ...


class NetworkGateway:
    """
    Fail-closed NetworkGateway foundation.

    Real HTTP fetching is available only through explicit provider approval and
    real_fetch_enabled. The approved Phase 4 provider path is Brave web search.
    """

    BRAVE_SEARCH_HOST = "api.search.brave.com"
    BRAVE_SEARCH_PATH = "/res/v1/web/search"
    MAX_BRAVE_COUNT = 20

    def __init__(
        self,
        policy: NetworkPolicy | None = None,
        config: NetworkGatewayConfig | None = None,
        http_transport: HttpTransport | None = None,
    ):
        self.policy = policy or NetworkPolicy()
        self.config = config or NetworkGatewayConfig()
        self.http_transport = http_transport or requests

        if self.policy.max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        if self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def validate_url_allowed(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme != "https":
            raise NetworkPolicyError(f"Unsupported URL scheme: {parsed.scheme!r}")

        if not parsed.netloc:
            raise NetworkPolicyError("URL must include a host")

        if self.policy.redirect_policy != "deny":
            raise NetworkPolicyError("NetworkGateway only supports redirect_policy='deny'")

        if self.policy.mode == "deny_all":
            raise NetworkAccessDeniedError("Network access is denied by policy")

        if self.policy.mode != "allowlist_only":
            raise NetworkPolicyError(f"Unknown network policy mode: {self.policy.mode!r}")

        host = parsed.hostname or ""

        if host not in self.policy.allowlist:
            raise NetworkAccessDeniedError(f"Host not in network allowlist: {host}")

    def _require_real_fetch(self, authorization: NetworkAuthorization) -> str:
        if not self.config.real_fetch_enabled:
            raise NetworkGatewayDisabledError(
                "Network real fetch requires real_fetch_enabled"
            )
        if not self.config.provider_configuration_approved:
            raise NetworkProviderNotApprovedError(
                "network provider configuration is not approved"
            )
        if not self.config.approved_by_panel_version:
            raise NetworkProviderNotApprovedError(
                "approved_by_panel_version is required for real network fetch"
            )
        if self.config.provider != "brave_search":
            raise NetworkProviderNotApprovedError(
                f"unsupported network provider: {self.config.provider}"
            )
        if not authorization.manifest_id:
            raise NetworkProviderNotApprovedError("manifest_id is required")
        if authorization.task_id <= 0:
            raise NetworkProviderNotApprovedError("task_id must be positive")
        if not authorization.allow_fetch:
            raise NetworkAccessDeniedError("network fetch is not authorized")
        if authorization.max_response_bytes <= 0:
            raise NetworkPolicyError("authorization max_response_bytes must be positive")
        if authorization.max_response_bytes > self.policy.max_response_bytes:
            raise NetworkPolicyError(
                "authorization max_response_bytes exceeds gateway policy"
            )

        endpoint = urlparse(self.config.endpoint_url)
        if endpoint.scheme != "https":
            raise NetworkPolicyError("network provider endpoint must use https")
        if endpoint.hostname != self.BRAVE_SEARCH_HOST:
            raise NetworkAccessDeniedError("network provider endpoint host is not approved")
        if endpoint.path != self.BRAVE_SEARCH_PATH:
            raise NetworkAccessDeniedError("network provider endpoint path is not approved")
        if endpoint.query or endpoint.fragment:
            raise NetworkAccessDeniedError(
                "network provider endpoint must not include query or fragment"
            )

        self.validate_url_allowed(self.config.endpoint_url)

        api_key = os.environ.get(self.config.api_key_env_var, "")
        if not api_key:
            raise NetworkCredentialsError(
                f"missing API key environment variable: {self.config.api_key_env_var}"
            )
        return api_key

    def fetch_disabled(self, url: str) -> NetworkFetchResult:
        """
        Explicit fail-closed fetch method.

        This exists so callers cannot accidentally mistake the foundation gateway
        for a real network client.
        """
        self.validate_url_allowed(url)
        raise NetworkAccessDeniedError("Real network fetch is not implemented in this phase")

    def brave_web_search(
        self,
        query: str,
        authorization: NetworkAuthorization,
        *,
        count: int = 5,
        country: str = "us",
        search_lang: str = "en",
        safesearch: str = "moderate",
    ) -> NetworkFetchResult:
        if not query.strip():
            raise NetworkPolicyError("query must not be empty")
        if count <= 0 or count > self.MAX_BRAVE_COUNT:
            raise NetworkPolicyError(f"count must be between 1 and {self.MAX_BRAVE_COUNT}")
        if safesearch not in {"off", "moderate", "strict"}:
            raise NetworkPolicyError("invalid safesearch value")

        api_key = self._require_real_fetch(authorization)
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query.strip(),
            "count": count,
            "country": country,
            "search_lang": search_lang,
            "safesearch": safesearch,
        }

        try:
            response = self.http_transport.get(
                self.config.endpoint_url,
                headers=headers,
                params=params,
                timeout=self.config.timeout_seconds,
                allow_redirects=False,
            )
        except Exception as exc:
            raise NetworkFetchError(f"network provider request failed: {exc}") from exc

        status_code = int(response.status_code)
        body = bytes(response.content)
        response_bytes = len(body)

        usage_status = "within_limit"
        if response_bytes > authorization.max_response_bytes:
            usage_status = "exceeded"

        usage_id = record_resource_usage(
            task_id=authorization.task_id,
            resource_type="network_response_bytes",
            amount=response_bytes,
            limit_value=authorization.max_response_bytes,
            status=usage_status,
            details={
                "url": self.config.endpoint_url,
                "status_code": status_code,
                "provider": self.config.provider,
                "usage_source": "network_gateway_brave_web_search",
            },
        )

        if response.headers.get("location"):
            raise NetworkFetchError(f"network provider redirect denied; usage_id={usage_id}")

        if usage_status == "exceeded":
            raise NetworkPolicyError(
                f"Network response size {response_bytes} exceeds limit "
                f"{authorization.max_response_bytes}; usage_id={usage_id}"
            )

        if status_code >= 400:
            raise NetworkFetchError(
                f"network provider returned HTTP {status_code}; usage_id={usage_id}"
            )

        return NetworkFetchResult(
            url=self.config.endpoint_url,
            status_code=status_code,
            response_bytes=response_bytes,
            body=body,
        )

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
