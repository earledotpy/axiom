from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from axiom.gateways.network_gateway import (
    NetworkAuthorization,
    NetworkGateway,
    NetworkGatewayConfig,
    NetworkPolicy,
)
from axiom.persistence.repositories import create_session, create_task


BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
BRAVE_HOST = "api.search.brave.com"
BRAVE_API_KEY_ENV = "BRAVE_SEARCH_API_KEY"
TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def _make_gateway(live: bool) -> NetworkGateway:
    return NetworkGateway(
        policy=NetworkPolicy(
            mode="allowlist_only",
            allowlist=(BRAVE_HOST,),
            max_response_bytes=64 * 1024,
            redirect_policy="deny",
        ),
        config=NetworkGatewayConfig(
            real_fetch_enabled=live,
            provider_configuration_approved=True,
            approved_by_panel_version="phase4_brave_search_api",
            provider="brave_search",
            api_key_env_var=BRAVE_API_KEY_ENV,
            endpoint_url=BRAVE_ENDPOINT,
            timeout_seconds=10,
        ),
    )


def run_network_gateway_smoke(*, live: bool, query: str) -> dict[str, Any]:
    key_is_set = bool(os.environ.get(BRAVE_API_KEY_ENV))
    result: dict[str, Any] = {
        "provider": "brave_search",
        "endpoint": BRAVE_ENDPOINT,
        "api_key_env_var": BRAVE_API_KEY_ENV,
        "api_key_is_set": key_is_set,
        "live": live,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "max_response_bytes": 64 * 1024,
        "passed": False,
    }

    gateway = _make_gateway(live=live)

    if not live:
        result["result"] = "dry_run_only"
        result["passed"] = True
        return result

    session_id = create_session(operator_id="network-gateway-smoke")
    task_id = create_task(
        session_id=session_id,
        chain_id=f"network-gateway-smoke-{session_id}",
        task_class="system_maintenance",
        task_type="network_gateway_smoke",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    result["session_id"] = session_id
    result["task_id"] = task_id

    response = gateway.brave_web_search(
        query=query,
        count=3,
        authorization=NetworkAuthorization(
            manifest_id=TOOL_MAP_MANIFEST_ID,
            task_id=task_id,
            allow_fetch=True,
            max_response_bytes=64 * 1024,
        ),
    )

    result.update(
        {
            "status_code": response.status_code,
            "response_bytes": response.response_bytes,
            "passed": response.status_code == 200 and response.response_bytes > 0,
        }
    )
    return result


def _print_text(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a dry-run or explicit live Brave NetworkGateway smoke test."
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--query", default="AXIOM runtime")
    args = parser.parse_args()

    try:
        payload = run_network_gateway_smoke(live=args.live, query=args.query)
    except Exception as exc:
        payload = {
            "provider": "brave_search",
            "endpoint": BRAVE_ENDPOINT,
            "api_key_env_var": BRAVE_API_KEY_ENV,
            "api_key_is_set": bool(os.environ.get(BRAVE_API_KEY_ENV)),
            "live": args.live,
            "query_sha256": hashlib.sha256(args.query.encode("utf-8")).hexdigest(),
            "passed": False,
            "error": exc.__class__.__name__,
            "reason": str(exc),
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)

    return 0 if payload.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
