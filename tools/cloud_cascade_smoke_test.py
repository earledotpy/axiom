from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.model_gateway import (  # noqa: E402
    CloudCascadeConfig,
    CloudProviderConfig,
    ModelGateway,
)
from axiom.persistence.repositories import create_session, create_task  # noqa: E402


TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"
APPROVED_BY_PANEL_VERSION = "phase4-smoke-test"

PROVIDER_SPECS: dict[str, dict[str, Any]] = {
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "api_key_env_var": "GROQ_API_KEY",
        "timeout_seconds": 30,
        "max_tokens": 32,
        "sentinel": "AXIOM_GROQ_SMOKE_OK",
    },
    "cerebras": {
        "model": "gpt-oss-120b",
        "api_key_env_var": "CEREBRAS_API_KEY",
        "timeout_seconds": 30,
        "max_tokens": 96,
        "sentinel": "AXIOM_CEREBRAS_SMOKE_OK",
    },
    "sambanova": {
        "model": "Meta-Llama-3.3-70B-Instruct",
        "api_key_env_var": "SAMBANOVA_API_KEY",
        "timeout_seconds": 30,
        "max_tokens": 32,
        "sentinel": "AXIOM_SAMBANOVA_SMOKE_OK",
    },
    "openrouter": {
        "model": "openrouter/auto",
        "api_key_env_var": "OPENROUTER_API_KEY",
        "timeout_seconds": 60,
        "max_tokens": 256,
        "sentinel": "AXIOM_OPENROUTER_SMOKE_OK",
    },
}

CASCADE_ORDER = ("groq", "cerebras", "sambanova", "openrouter")
SMOKE_TARGETS = (*CASCADE_ORDER, "cascade")


def provider_order_for_target(target: str) -> tuple[str, ...]:
    if target == "cascade":
        return CASCADE_ORDER
    if target not in PROVIDER_SPECS:
        raise ValueError(f"unknown cloud smoke target: {target}")
    return (target,)


def sentinel_for_target(target: str) -> str:
    if target == "cascade":
        return "AXIOM_CLOUD_CASCADE_SMOKE_OK"
    return str(PROVIDER_SPECS[target]["sentinel"])


def max_tokens_for_target(target: str) -> int:
    if target == "cascade":
        return max(int(PROVIDER_SPECS[name]["max_tokens"]) for name in CASCADE_ORDER)
    return int(PROVIDER_SPECS[target]["max_tokens"])


def build_cloud_cascade_config(target: str, *, live: bool) -> CloudCascadeConfig:
    order = provider_order_for_target(target)
    providers = tuple(
        CloudProviderConfig(
            provider=name,
            model=str(PROVIDER_SPECS[name]["model"]),
            api_key_env_var=str(PROVIDER_SPECS[name]["api_key_env_var"]),
            timeout_seconds=int(PROVIDER_SPECS[name]["timeout_seconds"]),
        )
        for name in order
    )

    return CloudCascadeConfig(
        provider_configuration_approved=True,
        approved_by_panel_version=APPROVED_BY_PANEL_VERSION,
        provider_order=order,
        providers=providers,
        real_calls_enabled=live,
    )


def smoke_payload(target: str) -> dict[str, Any]:
    sentinel = sentinel_for_target(target)
    return {
        "messages": [
            {
                "role": "user",
                "content": f"Reply with exactly: {sentinel}",
            }
        ],
        "temperature": 0,
        "max_tokens": max_tokens_for_target(target),
    }


def key_visibility(config: CloudCascadeConfig) -> dict[str, bool]:
    return {
        provider.api_key_env_var: bool(os.environ.get(provider.api_key_env_var))
        for provider in config.providers
    }


def run_cloud_cascade_smoke(target: str, *, live: bool) -> dict[str, Any]:
    config = build_cloud_cascade_config(target, live=live)
    readiness = ModelGateway().evaluate_cloud_cascade_readiness(config)
    payload: dict[str, Any] = {
        "target": target,
        "live": live,
        "ready": readiness.ready,
        "reason": readiness.reason,
        "provider_order": list(readiness.provider_order),
        "approved_by_panel_version": readiness.approved_by_panel_version,
        "key_visibility": key_visibility(config),
        "sentinel": sentinel_for_target(target),
        "max_tokens": max_tokens_for_target(target),
    }

    if not live:
        payload["called_provider"] = None
        payload["sentinel_matched"] = None
        return payload

    session_id = create_session(operator_id=f"{target}-cloud-smoke-tool")
    task_id = create_task(
        session_id=session_id,
        chain_id=f"chain-{target}-cloud-smoke-tool",
        task_class="system_maintenance",
        task_type=f"{target}_cloud_smoke_tool",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    result = ModelGateway().call_cloud_cascade(
        config,
        smoke_payload(target),
        task_id=task_id,
        session_id=session_id,
    )
    response_text = result.response_text.strip()
    payload.update(
        {
            "called_provider": result.provider,
            "called_model": result.model,
            "response_text_length": len(response_text),
            "sentinel_matched": response_text == sentinel_for_target(target),
            "provider_usage_id": result.provider_usage_id,
            "provider_call_usage_id": result.provider_call_usage_id,
            "session_id": session_id,
            "task_id": task_id,
        }
    )
    return payload


def print_text_report(payload: dict[str, Any]) -> None:
    print("AXIOM cloud cascade smoke test")
    print("==============================")
    print(f"target: {payload['target']}")
    print(f"live: {payload['live']}")
    print(f"ready: {payload['ready']}")
    print(f"reason: {payload['reason']}")
    print(f"provider_order: {', '.join(payload['provider_order'])}")
    print(f"sentinel: {payload['sentinel']}")
    print(f"max_tokens: {payload['max_tokens']}")
    print("")
    print("key_visibility:")
    for name, visible in payload["key_visibility"].items():
        print(f"- {name}: {'set' if visible else 'missing'}")

    if not payload["live"]:
        print("")
        print("result: dry_run_only")
        return

    print("")
    print(f"called_provider: {payload['called_provider']}")
    print(f"called_model: {payload['called_model']}")
    print(f"response_text_length: {payload['response_text_length']}")
    print(f"sentinel_matched: {payload['sentinel_matched']}")
    print(f"provider_usage_id: {payload['provider_usage_id']}")
    print(f"provider_call_usage_id: {payload['provider_call_usage_id']}")
    print(f"session_id: {payload['session_id']}")
    print(f"task_id: {payload['task_id']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run AXIOM Phase 4 cloud cascade smoke checks. Defaults to dry-run "
            "readiness/key-visibility reporting. Use --live for real model calls."
        )
    )
    parser.add_argument(
        "--target",
        choices=SMOKE_TARGETS,
        default="cascade",
        help="Provider or full cascade target to smoke test.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Perform the bounded real cloud call. Without this, no model call is made.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        payload = run_cloud_cascade_smoke(args.target, live=args.live)
    except Exception as exc:
        failure_payload = {
            "target": args.target,
            "live": args.live,
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(failure_payload, indent=2, sort_keys=True))
        else:
            print("AXIOM cloud cascade smoke test")
            print("==============================")
            print(f"passed: False")
            print(f"error_type: {failure_payload['error_type']}")
            print(f"error: {failure_payload['error']}")
        return 1

    payload["passed"] = bool(
        payload["ready"]
        and (not payload["live"] or payload.get("sentinel_matched") is True)
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text_report(payload)
        print("")
        print(f"passed: {payload['passed']}")

    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
