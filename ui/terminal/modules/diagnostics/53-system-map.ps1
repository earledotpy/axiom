# ============================================================
# AXIOM Terminal System Map
# File: C:\axiom\ui\terminal\modules\53-system-map.ps1
#
# Purpose:
#   Static/read-only AXIOM boundary and architecture map.
#
# Boundary:
#   This module displays architecture structure only.
#   It must not mutate AXIOM runtime state.
#   It must not query AXIOM database.
#   It must not call scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

function Write-AxiomMapLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Write-AxiomMapSection {
    param(
        [string]$Title
    )

    Write-Host ""
    Write-Host $Title -ForegroundColor DarkGreen
}

function axiom-system-map {
    Write-Host ""
    Write-Host "AXIOM SYSTEM MAP" -ForegroundColor Green
    Write-Host "================" -ForegroundColor Green
    Write-Host ""

    Write-AxiomMapLine "AXIOM root" $script:AxiomRoot $(if (Test-Path $script:AxiomRoot) { "Green" } else { "Red" })
    Write-AxiomMapLine "Terminal root" $script:AxiomTerminalRoot $(if (Test-Path $script:AxiomTerminalRoot) { "Green" } else { "Red" })
    Write-AxiomMapLine "Current posture" "fail_closed_non_autonomous" "Yellow"
    Write-AxiomMapLine "Terminal role" "operator UI / implementation shell" "Cyan"
    Write-AxiomMapLine "Runtime role" "state, policy, lifecycle, execution gates" "Cyan"

    Write-AxiomMapSection "Layer 1 - AXIOM Terminal / Operator UI"
    Write-Host "  C:\axiom\ui\terminal" -ForegroundColor Gray
    Write-Host "    profile\profile-axiom.ps1         deterministic module loader" -ForegroundColor Gray
    Write-Host "    modules\*.ps1                     terminal commands and panels" -ForegroundColor Gray
    Write-Host "    registry\*.json                   terminal command registry" -ForegroundColor Gray
    Write-Host "    themes\*.omp.json                 Oh My Posh dashboard themes" -ForegroundColor Gray
    Write-Host "    terminal\*.jsonc                  Windows Terminal settings snippets" -ForegroundColor Gray
    Write-Host "    docs\*.md                         terminal docs/changelog/specs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Allowed here:" -ForegroundColor Green
    Write-Host "    read-only panels, navigation, editor workflows, terminal reports," -ForegroundColor Gray
    Write-Host "    terminal changelog, visual modes, safe wrappers around approved tools." -ForegroundColor Gray
    Write-Host "    Phase 5 agent docs/manual-test visibility without automatic control." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Not allowed here:" -ForegroundColor Yellow
    Write-Host "    direct runtime mutation, scheduler execution shortcuts, model promotion," -ForegroundColor Gray
    Write-Host "    safe-pass enablement, manifest repair, gateway calls, automatic agent control." -ForegroundColor Gray

    Write-AxiomMapSection "Layer 2 - Approved AXIOM Tools"
    Write-Host "  C:\axiom\tools" -ForegroundColor Gray
    Write-Host "    verify_foundation.py              foundation/safety verification" -ForegroundColor Gray
    Write-Host "    audit_task_lifecycle.py           task lifecycle audit" -ForegroundColor Gray
    Write-Host "    audit_task_execution.py           no-op execution audit" -ForegroundColor Gray
    Write-Host "    supervisor_health_check.py        supervisor heartbeat/coherence" -ForegroundColor Gray
    Write-Host "    snapshot_project_state.py         project snapshot" -ForegroundColor Gray
    Write-Host "    generate_handoff.py               handoff document" -ForegroundColor Gray
    Write-Host "    generate_handoff_bundle.py        handoff bundle" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Manual/test-only tools exist, but must not become casual terminal shortcuts:" -ForegroundColor Yellow
    Write-Host "    run_scheduler_loop.py" -ForegroundColor Gray
    Write-Host "    run_manual_noop_cycle.py" -ForegroundColor Gray
    Write-Host "    execute_noop_task.py" -ForegroundColor Gray
    Write-Host "    start_task.py / dispatch_next_task.py with manual override" -ForegroundColor Gray
    Write-Host "    execute_*_planning_task.py / execute_tool_execution_task.py" -ForegroundColor Gray
    Write-Host "    execute_result_verification_task.py" -ForegroundColor Gray
    Write-Host "    run_manual_agent_foundation_smoke.py" -ForegroundColor Gray

    Write-AxiomMapSection "Layer 2.5 - Phase 5 Manual Agent Foundation"
    Write-Host "  C:\axiom\axiom\agents" -ForegroundColor Gray
    Write-Host "    base.py                           manifest-bound executor base" -ForegroundColor Gray
    Write-Host "    goal_planner.py                   draft goal-plan artifact only" -ForegroundColor Gray
    Write-Host "    task_planner.py                   draft task-plan artifact only" -ForegroundColor Gray
    Write-Host "    tool_executor.py                  draft tool-plan artifact only" -ForegroundColor Gray
    Write-Host "    result_verifier.py                deterministic result summary only" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Current boundary:" -ForegroundColor Yellow
    Write-Host "    manual/test-only wrappers exist; no model, network, sandbox, memory," -ForegroundColor Gray
    Write-Host "    operator-control, automatic scheduling, or autonomous agent control." -ForegroundColor Gray

    Write-AxiomMapSection "Layer 3 - AXIOM Runtime Core"
    Write-Host "  C:\axiom\axiom\core" -ForegroundColor Gray
    Write-Host "    state_machine.py                  allowed task transitions" -ForegroundColor Gray
    Write-Host "    scheduler.py                      scheduler facade / run_once" -ForegroundColor Gray
    Write-Host "    scheduler_loop.py                 bounded foreground loop skeleton" -ForegroundColor Gray
    Write-Host "    task_committer.py                 commit/lifecycle coordination" -ForegroundColor Gray
    Write-Host "    supervisor_monitor.py             heartbeat and one-running-task checks" -ForegroundColor Gray
    Write-Host "    context_builder.py                future context bundle construction" -ForegroundColor Gray
    Write-Host "    token_estimator.py                token/resource estimation" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Runtime invariants:" -ForegroundColor Green
    Write-Host "    one running task at a time" -ForegroundColor Gray
    Write-Host "    strict sequential execution" -ForegroundColor Gray
    Write-Host "    manifest_id required before running transition" -ForegroundColor Gray
    Write-Host "    heartbeat ordering around blocking operations" -ForegroundColor Gray

    Write-AxiomMapSection "Layer 4 - Persistence / Database"
    Write-Host "  C:\axiom\axiom.db" -ForegroundColor Gray
    Write-Host "  C:\axiom\axiom\persistence\schema.sql" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Runtime state lives here:" -ForegroundColor Gray
    Write-Host "    sessions, tasks, scheduler_heartbeat, manifests, model profiles," -ForegroundColor Gray
    Write-Host "    provider usage, resource usage, plan artifacts, events, memory metadata." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Terminal read-only panels may query with SQLite mode=ro." -ForegroundColor Green
    Write-Host "  Terminal modules must not directly repair or rewrite database state." -ForegroundColor Yellow

    Write-AxiomMapSection "Layer 5 - Policy / Manifests / Tool Capability"
    Write-Host "  C:\axiom\axiom\policy" -ForegroundColor Gray
    Write-Host "    schemas\manifest_schema.json" -ForegroundColor Gray
    Write-Host "    schemas\tool_capability_map_schema.json" -ForegroundColor Gray
    Write-Host "    security_artifacts\tool_capability_map.json" -ForegroundColor Gray
    Write-Host "    role_manifests\*.json" -ForegroundColor Gray
    Write-Host "    operator_control_manifests\*.json" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Rules:" -ForegroundColor Green
    Write-Host "    PolicyEngine is stateless at runtime." -ForegroundColor Gray
    Write-Host "    ManifestBinder verifies schema and SHA256 integrity." -ForegroundColor Gray
    Write-Host "    Tool-capability lookups use boot-time cached validators/maps." -ForegroundColor Gray
    Write-Host "    SHA256 mismatch / manifest mismatch fails closed." -ForegroundColor Gray

    Write-AxiomMapSection "Layer 6 - Model Trust Boundary"
    Write-Host "  model_profile_fingerprints" -ForegroundColor Gray
    Write-Host "  classifier_calibration_runs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Current expected state:" -ForegroundColor Yellow
    Write-Host "    qwen3:4b may exist as candidate/non-current." -ForegroundColor Gray
    Write-Host "    current trusted profile remains absent by design." -ForegroundColor Gray
    Write-Host "    thinking_mode=unknown cannot become current." -ForegroundColor Gray
    Write-Host "    safe-pass remains disabled until calibration/trust prerequisites pass." -ForegroundColor Gray

    Write-AxiomMapSection "Layer 7 - Gateways / Future Execution"
    Write-Host "  C:\axiom\axiom\gateways" -ForegroundColor Gray
    Write-Host "    model_gateway.py                  local/cloud model boundary" -ForegroundColor Gray
    Write-Host "    network_gateway.py                future allowlisted fetch boundary" -ForegroundColor Gray
    Write-Host "    sandbox_gateway.py                future process sandbox boundary" -ForegroundColor Gray
    Write-Host "    memory_gateway.py                 future vector/memory boundary" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Current posture:" -ForegroundColor Yellow
    Write-Host "    no real model/cloud calls from terminal" -ForegroundColor Gray
    Write-Host "    no real network fetches" -ForegroundColor Gray
    Write-Host "    no sandbox process execution" -ForegroundColor Gray
    Write-Host "    no automatic agent control" -ForegroundColor Gray
    Write-Host "    no Telegram/operator control plane" -ForegroundColor Gray

    Write-AxiomMapSection "Operator flow"
    Write-Host "  Human operator" -ForegroundColor Gray
    Write-Host "      v" -ForegroundColor DarkGray
    Write-Host "  AXIOM Terminal" -ForegroundColor Gray
    Write-Host "      v read-only panels / safe wrappers" -ForegroundColor DarkGray
    Write-Host "  Approved tools under C:\axiom\tools" -ForegroundColor Gray
    Write-Host "      v" -ForegroundColor DarkGray
    Write-Host "  AXIOM runtime core / policy / persistence" -ForegroundColor Gray
    Write-Host "      v only when future gates are satisfied" -ForegroundColor DarkGray
    Write-Host "  Model / network / sandbox / memory gateways" -ForegroundColor Gray

    Write-Host ""
    Write-Host "Next safe commands" -ForegroundColor DarkGreen
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-docs" -ForegroundColor Gray
    Write-Host "  axiom-terminal-report" -ForegroundColor Gray
    Write-Host ""
}

function axiom-boundaries {
    Write-Host ""
    Write-Host "AXIOM BOUNDARIES" -ForegroundColor Green
    Write-Host "================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Terminal may do:" -ForegroundColor DarkGreen
    Write-Host "  - load modules" -ForegroundColor Gray
    Write-Host "  - show dashboards" -ForegroundColor Gray
    Write-Host "  - run read-only panels" -ForegroundColor Gray
    Write-Host "  - open files in terminal editor" -ForegroundColor Gray
    Write-Host "  - run approved verification/reporting tools" -ForegroundColor Gray
    Write-Host "  - maintain terminal docs/changelog" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Terminal must not directly do:" -ForegroundColor Yellow
    Write-Host "  - enable autonomous operation" -ForegroundColor Gray
    Write-Host "  - enable safe-pass" -ForegroundColor Gray
    Write-Host "  - promote model profiles" -ForegroundColor Gray
    Write-Host "  - repair manifests or re-register manifests casually" -ForegroundColor Gray
    Write-Host "  - dispatch/start/complete/cancel tasks as convenience shortcuts" -ForegroundColor Gray
    Write-Host "  - call model/cloud/network/sandbox gateways" -ForegroundColor Gray
    Write-Host "  - run automatic agent control or scheduler-to-agent integration" -ForegroundColor Gray
    Write-Host "  - bypass policy, audit, operator-control, or manifest gates" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Rule:" -ForegroundColor DarkGreen
    Write-Host "  Read-only visibility can live in terminal modules." -ForegroundColor Gray
    Write-Host "  State-changing runtime behavior must live in approved AXIOM tools/runtime first." -ForegroundColor Gray
    Write-Host ""
}

function axiom-runtime-map {
    Write-Host ""
    Write-Host "AXIOM RUNTIME MAP" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Core runtime:" -ForegroundColor DarkGreen
    Write-Host "  axiom\core\state_machine.py" -ForegroundColor Gray
    Write-Host "  axiom\core\scheduler.py" -ForegroundColor Gray
    Write-Host "  axiom\core\scheduler_loop.py" -ForegroundColor Gray
    Write-Host "  axiom\core\task_committer.py" -ForegroundColor Gray
    Write-Host "  axiom\core\supervisor_monitor.py" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Policy/runtime guardrails:" -ForegroundColor DarkGreen
    Write-Host "  axiom\core\manifest_binder.py" -ForegroundColor Gray
    Write-Host "  axiom\core\policy_engine.py" -ForegroundColor Gray
    Write-Host "  axiom\security\plan_injection_scanner.py" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Gateways:" -ForegroundColor DarkGreen
    Write-Host "  axiom\gateways\model_gateway.py" -ForegroundColor Gray
    Write-Host "  axiom\gateways\network_gateway.py" -ForegroundColor Gray
    Write-Host "  axiom\gateways\sandbox_gateway.py" -ForegroundColor Gray
    Write-Host "  axiom\gateways\memory_gateway.py" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Agents:" -ForegroundColor DarkGreen
    Write-Host "  axiom\agents\base.py" -ForegroundColor Gray
    Write-Host "  axiom\agents\goal_planner.py" -ForegroundColor Gray
    Write-Host "  axiom\agents\task_planner.py" -ForegroundColor Gray
    Write-Host "  axiom\agents\tool_executor.py" -ForegroundColor Gray
    Write-Host "  axiom\agents\result_verifier.py" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Persistence:" -ForegroundColor DarkGreen
    Write-Host "  axiom\persistence\db.py" -ForegroundColor Gray
    Write-Host "  axiom\persistence\schema.sql" -ForegroundColor Gray
    Write-Host "  axiom.db" -ForegroundColor Gray
    Write-Host ""
}

function axiom-terminal-map {
    Write-Host ""
    Write-Host "AXIOM TERMINAL MAP" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Terminal root:" -ForegroundColor DarkGreen
    Write-Host "  C:\axiom\ui\terminal" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Important subtrees:" -ForegroundColor DarkGreen
    Write-Host "  profile\       loader and visual config" -ForegroundColor Gray
    Write-Host "  modules\       AXIOM Terminal commands" -ForegroundColor Gray
    Write-Host "  registry\      command registry" -ForegroundColor Gray
    Write-Host "  docs\          terminal docs/changelog/specs" -ForegroundColor Gray
    Write-Host "  themes\        Oh My Posh themes" -ForegroundColor Gray
    Write-Host "  terminal\      Windows Terminal snippets" -ForegroundColor Gray
    Write-Host "  assets\        icons/backgrounds" -ForegroundColor Gray
    Write-Host "  editor\        terminal editor config" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Terminal diagnostics:" -ForegroundColor DarkGreen
    Write-Host "  axiom-doctor" -ForegroundColor Gray
    Write-Host "  axiom-registry" -ForegroundColor Gray
    Write-Host "  axiom-terminal-report" -ForegroundColor Gray
    Write-Host "  axiom-terminal-changelog" -ForegroundColor Gray
    Write-Host ""
}

