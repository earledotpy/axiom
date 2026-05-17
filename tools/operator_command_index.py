from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
TOOL_VERSION = "operator_command_index.v2"


@dataclass(frozen=True)
class OperatorCommand:
    name: str
    command: str
    purpose: str
    when_to_run: str
    expected_exit_code: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


COMMANDS: tuple[OperatorCommand, ...] = (
    OperatorCommand(
        name="Bootstrap Check",
        command="python tools\\bootstrap_check.py",
        purpose="Validate AXIOM passive bootstrap foundation checks.",
        when_to_run="After schema, manifest, boot verifier, or bootstrap-validation changes.",
        expected_exit_code="0 when foundation checks pass; 1 when foundation checks fail.",
        notes="Autonomous mode may still be blocked even when this passes.",
    ),
    OperatorCommand(
        name="Status Check",
        command="python tools\\status_check.py",
        purpose="Show operator-visible AXIOM operational state.",
        when_to_run="When you need to see current foundation/autonomous/safe-pass state.",
        expected_exit_code="0 when database is initialized; 1 when database is not initialized.",
        notes="Reports fail-closed non-autonomous state without repairing it.",
    ),
    OperatorCommand(
        name="Repair Session State",
        command="python tools\\repair_session_state.py",
        purpose="Align latest session with fail-closed state when no current trusted model profile exists.",
        when_to_run="After model profile registration, bootstrap work, or suspicious session-state drift.",
        expected_exit_code="0 on successful repair/check.",
        notes="Uses schema-valid safe_pass_disabled_reason='no_stored_profile'.",
    ),
    OperatorCommand(
        name="Autonomous Readiness Check",
        command="python tools\\autonomous_readiness_check.py",
        purpose="Check whether AXIOM may enter autonomous operation.",
        when_to_run="Before any autonomous/scheduler/agent execution path.",
        expected_exit_code="0 when autonomous operation is allowed; 2 when blocked.",
        notes="Exit code 2 is expected in the current fail-closed non-autonomous state.",
    ),
    OperatorCommand(
        name="Verify Foundation",
        command="python tools\\verify_foundation.py",
        purpose="Run the core operator checks together and report coherent foundation state.",
        when_to_run="Before starting new implementation work or after completing a task.",
        expected_exit_code="0 when foundation is healthy; 1 when foundation fails.",
        notes="This is the main quick health command.",
    ),
    OperatorCommand(
        name="Snapshot Project State",
        command="python tools\\snapshot_project_state.py",
        purpose="Write a timestamped JSON snapshot of AXIOM project/database state.",
        when_to_run="Before handoff, debugging, or larger implementation transitions.",
        expected_exit_code="0 on successful snapshot write.",
        notes="Does not run pytest; records last-known test target.",
    ),
    OperatorCommand(
        name="Generate Handoff",
        command="python tools\\generate_handoff.py",
        purpose="Generate a human-readable Markdown handoff from the latest project snapshot.",
        when_to_run="Before moving to a new chat/session or briefing another model.",
        expected_exit_code="0 on successful handoff write.",
        notes="Use --print to display the handoff in terminal.",
    ),
    OperatorCommand(
        name="Operator Command Index",
        command="python tools\\operator_command_index.py",
        purpose="Show available operator commands and their intended use.",
        when_to_run="When unsure which maintenance or verification command to run next.",
        expected_exit_code="0 on successful display/export.",
        notes="Use --json, --markdown, or --write for alternate output formats.",
    ),
    OperatorCommand(
        name="Full Pytest Suite",
        command="pytest tests -v",
        purpose="Run the full AXIOM regression suite.",
        when_to_run="After every implementation task.",
        expected_exit_code="0 when all tests pass.",
        notes="Current expected target after this task is 210 passed.",
    ),
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def command_index_payload() -> dict[str, Any]:
    return {
        "tool_version": TOOL_VERSION,
        "generated_at_utc": _utc_timestamp(),
        "command_count": len(COMMANDS),
        "commands": [command.to_dict() for command in COMMANDS],
    }


def command_index_markdown() -> str:
    lines = [
        "# AXIOM Operator Command Index",
        "",
        f"Tool version: `{TOOL_VERSION}`",
        "",
        "| Command | Purpose | When to run | Expected exit code |",
        "|---|---|---|---|",
    ]

    for command in COMMANDS:
        lines.append(
            "| "
            f"`{command.command}` | "
            f"{command.purpose} | "
            f"{command.when_to_run} | "
            f"{command.expected_exit_code} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `python tools\\verify_foundation.py` is the preferred quick health check.",
            "- `python tools\\autonomous_readiness_check.py` returning exit code `2` is expected while AXIOM is fail-closed non-autonomous.",
            "- `pytest tests -v` remains the canonical regression check after implementation changes.",
            "",
        ]
    )

    return "\n".join(lines)


def write_command_index(output_dir: Path = LOG_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _utc_timestamp()

    json_path = output_dir / f"operator_command_index_{timestamp}.json"
    md_path = output_dir / f"operator_command_index_{timestamp}.md"

    json_path.write_text(
        json.dumps(command_index_payload(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(command_index_markdown(), encoding="utf-8")

    return {
        "json": json_path,
        "markdown": md_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print or export AXIOM operator command index."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        paths = write_command_index()
        print(f"wrote operator command index JSON: {paths['json']}")
        print(f"wrote operator command index Markdown: {paths['markdown']}")
        return 0

    if args.json:
        print(json.dumps(command_index_payload(), indent=2, sort_keys=True))
        return 0

    if args.markdown:
        print(command_index_markdown())
        return 0

    print("AXIOM operator command index")
    print("============================")
    for command in COMMANDS:
        print(f"{command.name}")
        print(f"  command: {command.command}")
        print(f"  purpose: {command.purpose}")
        print(f"  when: {command.when_to_run}")
        print(f"  exit: {command.expected_exit_code}")
        print(f"  notes: {command.notes}")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())