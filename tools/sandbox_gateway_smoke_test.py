from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from axiom.gateways.sandbox_gateway import (
    SandboxAuthorization,
    SandboxGateway,
    SandboxGatewayConfig,
    SandboxPolicy,
)
from axiom.persistence.repositories import create_session, create_task


TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"
SENTINEL = "AXIOM_SANDBOX_SMOKE_OK"


def _make_gateway(live: bool) -> SandboxGateway:
    return SandboxGateway(
        policy=SandboxPolicy(
            max_ram_mb=256,
            max_wall_clock_seconds=60,
            network_access="denied",
        ),
        config=SandboxGatewayConfig(
            real_execution_enabled=live,
            windows_job_object_approved=True,
            approved_by_panel_version="phase4_windows_job_object",
            kill_on_job_close=True,
            active_process_limit=1,
        ),
    )


def run_sandbox_gateway_smoke(*, live: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": "windows_job_object",
        "live": live,
        "max_ram_mb": 256,
        "max_wall_clock_seconds": 60,
        "network_access": "denied",
        "kill_on_job_close": True,
        "active_process_limit": 1,
        "sentinel": SENTINEL,
        "passed": False,
    }

    if not live:
        payload["result"] = "dry_run_only"
        payload["passed"] = True
        return payload

    session_id = create_session(operator_id="sandbox-gateway-smoke")
    task_id = create_task(
        session_id=session_id,
        chain_id=f"sandbox-gateway-smoke-{session_id}",
        task_class="system_maintenance",
        task_type="sandbox_gateway_smoke",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    payload["session_id"] = session_id
    payload["task_id"] = task_id

    result = _make_gateway(live=True).execute(
        [
            os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"),
            "/c",
            "exit",
            "0",
        ],
        SandboxAuthorization(
            manifest_id=TOOL_MAP_MANIFEST_ID,
            task_id=task_id,
            allow_execute=True,
        ),
        cwd=str(ROOT),
    )

    payload.update(
        {
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "ram_mb": result.ram_mb,
            "wall_clock_seconds": result.wall_clock_seconds,
            "ram_status": result.ram_status,
            "wall_clock_status": result.wall_clock_status,
            "passed": (
                result.exit_code == 0
                and result.timed_out is False
                and result.ram_status == "within_limit"
                and result.wall_clock_status == "within_limit"
            ),
        }
    )
    return payload


def _print_text(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a dry-run or explicit live Windows Job Object SandboxGateway smoke test."
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        payload = run_sandbox_gateway_smoke(live=args.live)
    except Exception as exc:
        payload = {
            "provider": "windows_job_object",
            "live": args.live,
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
