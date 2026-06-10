from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
TOOL_VERSION = "operator_command_index.v10"


@dataclass(frozen=True)
class OperatorCommand:
    name: str
    command: str
    purpose: str
    when_to_run: str
    expected_exit_code: str
    notes: str
    read_only: bool = True
    requires_manual_test_override: bool = False
    dispatches_scheduler: bool = False
    executes_task_body: bool = False
    changes_task_state: bool = False
    calls_model: bool = False
    calls_network: bool = False
    calls_sandbox: bool = False

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
        read_only=False,
        changes_task_state=True,
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
        name="Supervisor Health Check",
        command="python tools\\supervisor_health_check.py",
        purpose="Assess the health of the autonomous supervisor.",
        when_to_run="When verifying scheduler state and active task constraints.",
        expected_exit_code="0 when supervisor is healthy; 1 when unhealthy.",
        notes="Checks for stale heartbeats and running task invariants.",
    ),
    OperatorCommand(
        name="Audit Task Lifecycle",
        command="python tools\\audit_task_lifecycle.py",
        purpose="Audit task lifecycle invariants for a session.",
        when_to_run="When verifying task state consistency or debugging stuck sessions.",
        expected_exit_code="0 on a clean audit; 1 on violations.",
        notes="Requires session_id.",
    ),
    OperatorCommand(
        name="Audit Task Execution",
        command="python tools\\audit_task_execution.py",
        purpose="Audit no-op task execution records for coherence.",
        when_to_run="After task execution tests to verify execution payload formatting and invariants.",
        expected_exit_code="0 on a clean audit; 1 on violations.",
        notes="Read-only. Does not mutate task state. Use --all-sessions to audit all.",
    ),
    OperatorCommand(
        name="Audit Policy Security",
        command="python tools\\audit_policy_security.py",
        purpose="Run read-only Phase 3 policy/security audit.",
        when_to_run="After Phase 3 policy/security changes and during preflight verification.",
        expected_exit_code="0 on a clean audit; 1 on violations.",
        notes=(
            "Read-only. Verifies manifest/tool-capability integrity, active "
            "role/operator manifest schema and policy completeness, operator-control "
            "command binding, tool-capability semantic contracts, scanner/schema "
            "coherence, scanner return-contract stability, and security-event "
            "schema/index/domain coverage. "
            "Source handoff: docs\\phase3.md."
        ),
        read_only=True,
        requires_manual_test_override=False,
        dispatches_scheduler=False,
        executes_task_body=False,
        changes_task_state=False,
        calls_model=False,
        calls_network=False,
        calls_sandbox=False,
    ),
    OperatorCommand(
        name="Execution Readiness Check",
        command="python tools\\execution_readiness_check.py",
        purpose="Reports whether the current session is ready for controlled execution based on lifecycle audit, execution audit, supervisor health, pending manifest-bound task count, and running task count.",
        when_to_run="Before attempting manual or autonomous dispatch and execution.",
        expected_exit_code="0 when ready for execution; 1 when blocked or not ready.",
        notes="Read-only. Does not dispatch, start, complete, or execute tasks.",
    ),
    OperatorCommand(
        name="Cloud Cascade Smoke Test",
        command="python tools\\cloud_cascade_smoke_test.py",
        purpose="Run dry-run readiness/key-visibility reporting or an explicit bounded live smoke test for the Phase 4 cloud model cascade.",
        when_to_run="After cloud provider env vars are configured, or when verifying the live ModelGateway cloud cascade.",
        expected_exit_code="0 when readiness passes and, with --live, the sentinel response matches; 1 on missing keys, provider failure, or sentinel mismatch.",
        notes=(
            "Dry-run by default and does not print API keys. Use --target "
            "groq|cerebras|sambanova|openrouter|cascade. Real model calls require "
            "--live. Source handoff: docs\\phase4.md."
        ),
        read_only=False,
        requires_manual_test_override=True,
        calls_model=True,
    ),
    OperatorCommand(
        name="Network Gateway Smoke Test",
        command="python tools\\network_gateway_smoke_test.py",
        purpose="Run dry-run readiness/key-visibility reporting or an explicit bounded live Brave Search NetworkGateway smoke test.",
        when_to_run="After BRAVE_SEARCH_API_KEY is configured, or when verifying the live NetworkGateway Brave provider path.",
        expected_exit_code="0 when dry-run readiness passes and, with --live, Brave returns a bounded response; 1 on missing key, policy denial, or provider failure.",
        notes=(
            "Dry-run by default and does not print API keys. Real Brave Search "
            "network calls require --live. Source handoff: docs\\phase4.md."
        ),
        read_only=False,
        requires_manual_test_override=True,
        calls_network=True,
    ),
    OperatorCommand(
        name="Sandbox Gateway Smoke Test",
        command="python tools\\sandbox_gateway_smoke_test.py",
        purpose="Run dry-run readiness reporting or an explicit bounded live Windows Job Object SandboxGateway smoke test.",
        when_to_run="After verifying Phase 4 SandboxGateway Job Object enforcement or when testing the live sandbox boundary.",
        expected_exit_code="0 when dry-run readiness passes and, with --live, the bounded process exits within limits; 1 on policy denial, timeout, RAM limit, or runtime failure.",
        notes=(
            "Dry-run by default. Real sandbox process execution requires --live. "
            "Uses Windows Job Object limits: kill-on-close, active process limit 1, "
            "256 MB RAM cap, 60 second wall-clock cap, network denied. "
            "Source handoff: docs\\phase4.md."
        ),
        read_only=False,
        requires_manual_test_override=True,
        calls_sandbox=True,
    ),
    OperatorCommand(
        name="Memory Gateway Smoke Test",
        command="python tools\\memory_gateway_smoke_test.py",
        purpose="Run dry-run readiness reporting or an explicit bounded live local Ollama MemoryGateway write/query smoke test.",
        when_to_run="After local Ollama is running with nomic-embed-text available, or when verifying the MemoryGateway embedding provider boundary.",
        expected_exit_code="0 when dry-run readiness passes and, with --live, MemoryGateway writes and queries the sentinel memory; 1 on provider, policy, invariant, or query failure.",
        notes=(
            "Dry-run by default. Real local Ollama /api/embed embedding calls "
            "and sqlite-vec write/query require --live. Does not call "
            "/api/chat or /api/generate. Source handoff: "
            "docs\\phase4.md."
        ),
        read_only=False,
        requires_manual_test_override=True,
        calls_model=True,
    ),
    OperatorCommand(
        name="Classifier Calibration Check",
        command="python tools\\run_calibration.py",
        purpose="Run dry-run classifier calibration scoring, or explicitly approved live/write-db calibration checks.",
        when_to_run="Only when classifier calibration work has separate approval outside Phase 4 gateway closeout.",
        expected_exit_code="0 when calibration passes; 1 when calibration fails or write approval is missing.",
        notes=(
            "Dry-run by default. Live cloud cascade classification requires --live. "
            "Writing classifier_calibration_runs requires --write-db and explicit "
            "classifier calibration approval token. This remains outside Phase 4 "
            "gateway authority."
        ),
        read_only=False,
        requires_manual_test_override=True,
        calls_model=True,
    ),
    OperatorCommand(
        name="Stage No-op Task",
        command="python tools\\stage_noop_task.py",
        purpose="Stage one pending manifest-bound no-op task without dispatching or executing it.",
        when_to_run=(
            "After foundation, lifecycle audit, execution audit, and supervisor "
            "health pass, when execution readiness is blocked only by "
            "no_pending_manifest_bound_task."
        ),
        expected_exit_code="0 when a pending no-op task is staged; 1 when staging is refused.",
        notes=(
            "State-changing but bounded. Inserts one pending task only. Does not "
            "dispatch scheduler work, start tasks, execute task bodies, call models, "
            "call networks, call sandbox, enable safe-pass, or enable autonomous operation."
        ),
        read_only=False,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Scheduler Tick",
        command="python tools\\scheduler_tick.py",
        purpose="Execute a single scheduler tick manually.",
        when_to_run="When testing scheduler progression or advancing the system state step-by-step.",
        expected_exit_code="0 on successful tick completion.",
        notes="Requires an active session.",
        read_only=False,
        requires_manual_test_override=True,
        dispatches_scheduler=True,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Run Scheduler Loop",
        command="python tools\\run_scheduler_loop.py",
        purpose="Run a bounded foreground scheduler loop.",
        when_to_run="To execute multiple scheduler ticks continuously in the foreground.",
        expected_exit_code="0 on successful bounded loop completion.",
        notes="Blocks by default when autonomous readiness is unavailable. Manual/test override only with --allow-when-autonomous-blocked.",
        read_only=False,
        requires_manual_test_override=True,
        dispatches_scheduler=True,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Dispatch Next Task",
        command="python tools\\dispatch_next_task.py",
        purpose="Dispatch the next eligible pending task in the active session.",
        when_to_run="When testing dispatcher logic manually.",
        expected_exit_code="0 on successful dispatch evaluation.",
        notes="Requires session_id. Use --manual-test-override to bypass readiness blocks.",
        read_only=False,
        requires_manual_test_override=True,
        dispatches_scheduler=True,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Start Task",
        command="python tools\\start_task.py",
        purpose="Transition a dispatched task from pending to running.",
        when_to_run="When manually executing a specific task.",
        expected_exit_code="0 on successful task start.",
        notes="Requires task_id. Use --manual-test-override to bypass readiness blocks.",
        read_only=False,
        requires_manual_test_override=True,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Execute No-op Task",
        command="python tools\\execute_noop_task.py",
        purpose="Execute a manifest-bound pending task through the deterministic no-op executor.",
        when_to_run="When manually testing the deterministic executor directly on a specific task.",
        expected_exit_code="0 on successful execution.",
        notes="Direct execution CLI is blocked unless --manual-test-override is passed while autonomous readiness is unavailable.",
        read_only=False,
        requires_manual_test_override=True,
        executes_task_body=True,
        changes_task_state=True,
    ),
    OperatorCommand(
        name="Run Manual No-op Cycle",
        command="python tools\\run_manual_noop_cycle.py",
        purpose="Run one manual scheduler-dispatched no-op execution cycle.",
        when_to_run="When verifying the complete dispatch-and-execute flow for a single task.",
        expected_exit_code="0 on successful cycle completion.",
        notes="Manual/test-only. Requires --allow-when-autonomous-blocked in the current fail-closed state.",
        read_only=False,
        requires_manual_test_override=True,
        dispatches_scheduler=True,
        executes_task_body=True,
        changes_task_state=True,
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
        name="Read-only Operator Console",
        command="python tools\\operator_console.py /axiom:show-active-state --json",
        purpose="Render read-only AXIOM governance console views from governance/80_records JSON.",
        when_to_run="When Jeremy or an agent needs active state, blockers, decision queue, evidence, or autonomy status without changing state.",
        expected_exit_code="0 on successful read-only view generation.",
        notes="Supports /axiom:show-active-state, /axiom:show-blockers, /axiom:show-decisions, /axiom:show-evidence, and /axiom:show-autonomy-status. Does not write ledger rows, mutate parser manifests, execute runtime actions, or enable autonomy.",
    ),
    OperatorCommand(
        name="Delegation Packet Tool",
        command="python tools\\delegation.py create --goal \"...\" --scope \"...\" --json",
        purpose="Create, list, and show advisory delegation packet JSON records under governance/80_records/delegations.",
        when_to_run="When Jeremy approves a scoped delegation or multi-agent cycle record without authority-bearing command execution.",
        expected_exit_code="0 when delegation record creation or inspection succeeds.",
        notes="Writes advisory_only governance JSON records only. Does not write ledger rows, mutate parser manifests, execute runtime actions, reactivate IPC, or enable autonomy.",
        read_only=False,
    ),
    OperatorCommand(
        name="Evaluation Report Tool",
        command="python tools\\evaluation.py create --target-artifact \"...\" --scope \"...\" --json",
        purpose="Create, list, show, and summarize advisory evaluation report JSON records under governance/80_records/evaluations.",
        when_to_run="When an agent needs to record verification, audit findings, blocker objections, or decision-ready evaluation evidence.",
        expected_exit_code="0 when evaluation record creation, inspection, or blocker summary generation succeeds.",
        notes="Writes advisory_only evaluation JSON records only. Does not write ledger rows, mutate parser manifests, execute runtime actions, reactivate IPC, enable autonomy, or accept work.",
        read_only=False,
    ),
    OperatorCommand(
        name="Task Card Tool",
        command="python tools\\task_card.py create --goal \"...\" --scope \"...\" --json",
        purpose="Create, list, show, and close advisory lightweight task cards under governance/80_records/tasks.",
        when_to_run="When routine low-risk governance work needs a concise JSON task record.",
        expected_exit_code="0 when task card creation or inspection succeeds.",
        notes="Writes advisory_only task-card JSON only. Does not create authority, run scheduler work, write legacy ledger rows, or enable autonomy.",
        read_only=False,
    ),
    OperatorCommand(
        name="Handoff Tool",
        command="python tools\\handoff.py create --title \"...\" --scope \"...\" --json",
        purpose="Create, list, and show advisory JSON handoffs under governance/80_records/handoffs.",
        when_to_run="When an agent needs to preserve synthesis, review, planning, audit, or mandate-candidate output.",
        expected_exit_code="0 when handoff record creation or inspection succeeds.",
        notes="Writes advisory_only handoff JSON only. Does not accept work, write bindings, execute runtime actions, or enable autonomy.",
        read_only=False,
    ),
    OperatorCommand(
        name="Evidence Tool",
        command="python tools\\evidence.py create --scope \"...\" --json",
        purpose="Create, list, and show evidence JSON records under governance/80_records/evidence.",
        when_to_run="When implementation, verification, command, skipped-check, assumption, or risk evidence needs to be preserved.",
        expected_exit_code="0 when evidence record creation or inspection succeeds.",
        notes="Writes evidence_only JSON. It records evidence supplied to it; it does not run tests, accept work, or execute runtime actions.",
        read_only=False,
    ),
    OperatorCommand(
        name="Decision Tool",
        command="python tools\\decision.py preview --decision approve --target-id \"...\" --scope \"...\" --json",
        purpose="Preview and explicitly record Operator decision JSON records under governance/80_records/decisions.",
        when_to_run="When Jeremy is ready to record approve, reject, defer, narrow_scope, request_review, request_remediation, or archive decisions.",
        expected_exit_code="0 when preview or confirmation-gated recording succeeds.",
        notes="Authority-bearing only on record with exact confirmation token. Does not execute runtime actions, write legacy ledger rows, or apply bindings.",
        read_only=False,
    ),
    OperatorCommand(
        name="Binding Tool",
        command="python tools\\binding.py apply --decision-id \"...\" --binding-type \"...\" --target \"...\" --scope \"...\" --json",
        purpose="Create active binding JSON records under governance/80_records/bindings from accepted approve decisions.",
        when_to_run="After an operator_accepted approve decision needs a current active binding effect.",
        expected_exit_code="0 when binding creation or inspection succeeds.",
        notes="Requires an accepted approve decision. Does not mutate runtime state, parser state, scheduler state, or legacy ledger rows.",
        read_only=False,
    ),
    OperatorCommand(
        name="Governance Command Tool",
        command="python tools\\governance_command.py record /axiom:show-active-state --json",
        purpose="Create JSON-first /axiom:* command manifests and validated command intent records.",
        when_to_run="When command transport intent should be validated against governance/80_records command manifests.",
        expected_exit_code="0 when command manifest creation, parsing, or accepted intent recording succeeds.",
        notes="Records command intent only. Does not execute /axiom:* actions, write legacy ledger rows, or interpret native CLI commands as Axiom authority.",
        read_only=False,
    ),
    OperatorCommand(
        name="Autonomy Grant Tool",
        command="python tools\\autonomy_grant.py draft --scope \"...\" --json",
        purpose="Draft, accept, inspect, and revoke autonomy grant JSON records under governance/80_records/autonomy.",
        when_to_run="When autonomy scope needs governance-visible records without enabling runtime autonomy.",
        expected_exit_code="0 when autonomy grant record creation or inspection succeeds.",
        notes="Accepted grants require accepted Operator decision and passed technical gate; runtime autonomy remains disabled in this implementation.",
        read_only=False,
    ),
    OperatorCommand(
        name="Full Pytest Suite",
        command="pytest tests -v",
        purpose="Run the full AXIOM regression suite.",
        when_to_run="After every implementation task.",
        expected_exit_code="0 when all tests pass.",
        notes="Use current live output as authoritative; snapshot and handoff tools do not run pytest.",
    ),
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")


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
            "- `python tools\\audit_policy_security.py` is the read-only Phase 3 policy/security audit; it currently covers tool-capability semantics, active manifest completeness, scanner contracts, and security-event audit support. Source handoff is `docs\\phase3.md`.",
            "- `python tools\\cloud_cascade_smoke_test.py` is the Phase 4 cloud cascade smoke wrapper; dry-run is default, and live model calls require `--live`. Source handoff is `docs\\phase4.md`.",
            "- `python tools\\network_gateway_smoke_test.py` is the Phase 4 Brave Search NetworkGateway smoke wrapper; dry-run is default, and live network calls require `--live`. Source handoff is `docs\\phase4.md`.",
            "- `python tools\\sandbox_gateway_smoke_test.py` is the Phase 4 Windows Job Object SandboxGateway smoke wrapper; dry-run is default, and live sandbox process execution requires `--live`. Source handoff is `docs\\phase4.md`.",
            "- `python tools\\memory_gateway_smoke_test.py` is the Phase 4 local Ollama MemoryGateway smoke wrapper; dry-run is default, and live /api/embed write/query calls require `--live`. Source handoff is `docs\\phase4.md`.",
            "- `python tools\\run_calibration.py` remains outside Phase 4 gateway authority; dry-run is default, live classification requires `--live`, and DB writes require explicit calibration approval.",
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
        try:
            paths = write_command_index()
        except PermissionError:
            paths = write_command_index(Path(tempfile.gettempdir()) / "axiom_logs")
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

