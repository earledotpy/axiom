from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.snapshot_project_state import write_snapshot


TOOL_VERSION = "generate_handoff.v1"
LOG_DIR = ROOT / "logs"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def find_latest_snapshot(log_dir: Path = LOG_DIR) -> Path | None:
    snapshots = sorted(
        log_dir.glob("project_state_snapshot_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return snapshots[0] if snapshots else None


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_model_profile(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    profile_label = snapshot.get("profile_label", "default")
    profiles = (
        snapshot.get("database_state", {})
        .get("latest_model_profiles", [])
    )

    for profile in profiles:
        if profile.get("profile_label") == profile_label:
            return profile

    return None


def _latest_session(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    sessions = (
        snapshot.get("database_state", {})
        .get("latest_sessions", [])
    )
    return sessions[0] if sessions else None


def build_handoff_markdown(snapshot: dict[str, Any]) -> str:
    bootstrap = snapshot.get("bootstrap", {})
    readiness = snapshot.get("autonomous_readiness", {})
    status = snapshot.get("status", {})
    foundation = snapshot.get("foundation_verification", {})
    supervisor = snapshot.get("supervisor_health") or foundation.get("supervisor_health", {})
    supervisor_health = supervisor.get("health") if supervisor else None
    task_execution_audit = (
        snapshot.get("task_execution_audit")
        or foundation.get("task_execution_audit", {})
    )

    latest_profile = _latest_model_profile(snapshot)
    latest_session = _latest_session(snapshot)

    blocking_reasons = readiness.get("blocking_reasons", [])
    operational_mode = bootstrap.get("operational_mode", "unknown")
    foundation_passed = bootstrap.get("passed", False)
    autonomous_allowed = readiness.get("allowed", False)

    lines: list[str] = [
        "# AXIOM Project Handoff",
        "",
        "## Summary",
        "",
        f"- Tool version: `{TOOL_VERSION}`",
        f"- Snapshot created UTC: `{snapshot.get('snapshot_created_at_utc', 'unknown')}`",
        f"- Project root: `{snapshot.get('project_root', 'unknown')}`",
        f"- Pytest last known target: `{snapshot.get('pytest', {}).get('last_known_target', 'unknown')}`",
        f"- Foundation passed: `{foundation_passed}`",
        f"- Operational mode: `{operational_mode}`",
        f"- Autonomous allowed: `{autonomous_allowed}`",
        f"- Fail-closed coherent: `{foundation.get('fail_closed_coherent', 'unknown')}`",
        "",
        "## Current Operating Interpretation",
        "",
    ]

    if foundation_passed and not autonomous_allowed:
        lines.extend(
            [
                "AXIOM foundation is healthy, but autonomous operation is intentionally blocked.",
                "This is a valid fail-closed non-autonomous state.",
                "",
            ]
        )
    elif foundation_passed and autonomous_allowed:
        lines.extend(
            [
                "AXIOM foundation is healthy and autonomous operation is currently allowed.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "AXIOM foundation validation is failing. Do not proceed to autonomous work.",
                "",
            ]
        )

    lines.extend(
        [
            "## Blocking Reasons",
            "",
        ]
    )

    if blocking_reasons:
        for reason in blocking_reasons:
            lines.append(f"- `{reason}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Supervisor Health", ""])

    if supervisor:
        lines.append(f"- Checked: `{supervisor.get('checked')}`")
        lines.append(f"- Reason: `{supervisor.get('reason')}`")

        if supervisor_health:
            lines.append(f"- Healthy: `{supervisor_health.get('healthy')}`")
            lines.append(f"- Scheduler stale: `{supervisor_health.get('scheduler_stale')}`")
            lines.append(f"- Running count: `{supervisor_health.get('running_count')}`")
            lines.append(f"- Active task present: `{supervisor_health.get('active_task_present')}`")
            lines.append(f"- Active task status: `{supervisor_health.get('active_task_status')}`")
        else:
            lines.append("- Health payload: `None`")
    else:
        lines.append("- Supervisor health not present in snapshot.")
        
    lines.extend(["", "## Task Execution Audit", ""])

    if task_execution_audit:
        lines.append(f"- Checked: `{task_execution_audit.get('checked')}`")
        lines.append(f"- Passed: `{task_execution_audit.get('passed')}`")
        lines.append(f"- Scope: `{task_execution_audit.get('scope')}`")
        lines.append(f"- Session ID: `{task_execution_audit.get('session_id')}`")
        lines.append(
            f"- Checked task count: `{task_execution_audit.get('checked_task_count')}`"
        )
        lines.append(
            f"- Violation count: `{task_execution_audit.get('violation_count')}`"
        )
    else:
        lines.append("- Task execution audit not present in snapshot.")

    lines.extend(["", "## Latest Model Profile", ""])

    if latest_profile:
        for key in (
            "profile_id",
            "profile_label",
            "model_name",
            "ollama_host",
            "ollama_model_tag",
            "ollama_model_digest",
            "quantization",
            "parameter_size",
            "model_family",
            "model_format",
            "thinking_mode",
            "thinking_mode_rule_version",
            "calibration_run_id",
            "is_current",
            "registration_status",
            "registered_at",
        ):
            lines.append(f"- {key}: `{latest_profile.get(key)}`")
    else:
        lines.append("- No model profile rows found.")

    lines.extend(["", "## Latest Session", ""])

    if latest_session:
        for key in (
            "session_id",
            "created_at",
            "scheduler_status",
            "safe_pass_enabled",
            "safe_pass_disabled_reason",
            "safe_pass_disabled_at",
            "autonomous_operation_enabled",
            "shutdown_requested",
        ):
            lines.append(f"- {key}: `{latest_session.get(key)}`")
    else:
        lines.append("- No session rows found.")

    lines.extend(
        [
            "",
            "## Verification Commands",
            "",
            "Run these from `C:\\axiom`:",
            "",
            "```powershell",
            ".\\venv\\Scripts\\Activate.ps1",
            "python tools\\verify_foundation.py",
            "python tools\\bootstrap_check.py",
            "python tools\\status_check.py",
            "python tools\\autonomous_readiness_check.py",
            "pytest tests -v",
            "```",
            "",
            "## Next Recommended Action",
            "",
        ]
    )

    if foundation_passed and not autonomous_allowed:
        lines.extend(
            [
                "Do not enable autonomous operation yet.",
                "",
                "Next work should remain in fail-closed foundation hardening, calibration workflow preparation, or operator-control plumbing.",
                "The current blocker is absence of a current trusted model profile and safe-pass remains disabled.",
            ]
        )
    elif foundation_passed and autonomous_allowed:
        lines.append("Proceed only with panel-approved autonomous execution tests.")
    else:
        lines.append("Repair failing foundation checks before adding new features.")

    lines.append("")
    return "\n".join(lines)


def write_handoff(
    snapshot_path: Path | None = None,
    output_dir: Path = LOG_DIR,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if snapshot_path is None:
        snapshot_path = find_latest_snapshot(output_dir)

    if snapshot_path is None:
        snapshot_path = write_snapshot(profile_label="default")

    snapshot = load_snapshot(snapshot_path)
    markdown = build_handoff_markdown(snapshot)

    output_path = output_dir / f"axiom_handoff_{_utc_timestamp()}.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown AXIOM handoff from the latest project snapshot."
    )
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--print", action="store_true", dest="print_markdown")
    args = parser.parse_args()

    handoff_path = write_handoff(snapshot_path=args.snapshot)

    print(f"wrote AXIOM handoff: {handoff_path}")

    if args.print_markdown:
        print(handoff_path.read_text(encoding="utf-8"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())