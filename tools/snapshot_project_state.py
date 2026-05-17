from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.app.bootstrap_validation import BootstrapValidator
from axiom.app.status_report import build_status_report
from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.persistence.db import get_connection
from tools.verify_foundation import verify_foundation


TOOL_VERSION = "snapshot_project_state.v1"
LOG_DIR = ROOT / "logs"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _run_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def _latest_model_profiles(limit: int = 5) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT profile_id, profile_label, model_name, ollama_host,
                   ollama_model_tag, ollama_model_digest, quantization,
                   parameter_size, model_family, model_format, thinking_mode,
                   thinking_mode_rule_version, calibration_run_id,
                   is_current, registration_status, registered_at
            FROM model_profile_fingerprints
            ORDER BY profile_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def _latest_sessions(limit: int = 5) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT session_id, created_at, ended_at, scheduler_status,
                   safe_pass_enabled, safe_pass_disabled_reason,
                   safe_pass_disabled_at, autonomous_operation_enabled,
                   shutdown_requested
            FROM sessions
            ORDER BY session_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def _recent_security_events(limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_id, session_id, task_id, event_type, reason,
                   severity, created_at
            FROM security_events
            ORDER BY event_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def build_project_state_snapshot(profile_label: str = "default") -> dict[str, Any]:
    bootstrap = BootstrapValidator().run(raise_on_failure=False)
    status = build_status_report(profile_label=profile_label)
    readiness = evaluate_autonomous_readiness(profile_label=profile_label)
    foundation = verify_foundation(profile_label=profile_label)

    return {
        "tool_version": TOOL_VERSION,
        "snapshot_created_at_utc": _utc_timestamp(),
        "project_root": str(ROOT),
        "profile_label": profile_label,
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "git": {
            "rev_parse_head": _run_command(["git", "rev-parse", "HEAD"]),
            "status_short": _run_command(["git", "status", "--short"]),
        },
        "pytest": {
            "last_known_target": "198 passed",
            "note": "Snapshot does not run pytest; use pytest tests -v for live validation.",
        },
        "bootstrap": bootstrap.to_dict(),
        "status": status.to_dict(),
        "autonomous_readiness": readiness.to_dict(),
	"supervisor_health": foundation.get("supervisor_health"),
        "foundation_verification": foundation,
        "database_state": {
            "latest_model_profiles": _latest_model_profiles(),
            "latest_sessions": _latest_sessions(),
            "recent_security_events": _recent_security_events(),
        },
    }


def write_snapshot(profile_label: str = "default") -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_project_state_snapshot(profile_label=profile_label)
    path = LOG_DIR / f"project_state_snapshot_{_utc_timestamp()}.json"
    path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write an AXIOM project state snapshot for handoff/debugging."
    )
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--print", action="store_true", dest="print_json")
    args = parser.parse_args()

    path = write_snapshot(profile_label=args.profile_label)

    print(f"wrote project state snapshot: {path}")

    if args.print_json:
        print(path.read_text(encoding="utf-8"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())