# ============================================================
# AXIOM Terminal Docs / Navigation Panel
# File: C:\axiom\ui\terminal\modules\52-docs.ps1
#
# Purpose:
#   Fast local documentation and project-navigation panel.
#
# Boundary:
#   This module lists and opens local files only.
#   It must not mutate AXIOM runtime state.
#   It must not call scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomDocsIndex = [ordered]@{
    "terminal-spec" = @{
        label = "AXIOM Terminal spec"
        path = "ui\terminal\docs\AXIOM_TERMINAL_SPEC.md"
        category = "terminal"
    }
    "terminal-editor" = @{
        label = "AXIOM Terminal editor notes"
        path = "ui\terminal\docs\AXIOM_EDITOR.md"
        category = "terminal"
    }
    "terminal-apps" = @{
        label = "Recommended terminal applications"
        path = "ui\terminal\docs\RECOMMENDED_APPLICATIONS.md"
        category = "terminal"
    }
    "terminal-changelog" = @{
        label = "AXIOM Terminal changelog"
        path = "ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md"
        category = "terminal"
    }
    "terminal-registry" = @{
        label = "AXIOM Terminal command registry"
        path = "ui\terminal\registry\axiom-terminal-command-registry.json"
        category = "terminal"
    }
    "terminal-profile" = @{
        label = "AXIOM Terminal profile loader"
        path = "ui\terminal\profile\profile-axiom.ps1"
        category = "terminal"
    }
    "visual-config" = @{
        label = "AXIOM Terminal visual config"
        path = "ui\terminal\profile\visual-mode.json"
        category = "terminal"
    }
    "windows-terminal-snippet" = @{
        label = "Windows Terminal AXIOM snippet"
        path = "ui\terminal\terminal\windows-terminal-axiom-snippet.jsonc"
        category = "terminal"
    }
    "dashboard-theme" = @{
        label = "AXIOM Oh My Posh dashboard theme"
        path = "ui\terminal\themes\axiom-dashboard.omp.json"
        category = "terminal"
    }
    "schema" = @{
        label = "Canonical SQLite schema"
        path = "axiom\persistence\schema.sql"
        category = "runtime"
    }
    "db" = @{
        label = "Database connection layer"
        path = "axiom\persistence\db.py"
        category = "runtime"
    }
    "scheduler" = @{
        label = "Scheduler facade"
        path = "axiom\core\scheduler.py"
        category = "runtime"
    }
    "scheduler-loop" = @{
        label = "Scheduler loop skeleton"
        path = "axiom\core\scheduler_loop.py"
        category = "runtime"
    }
    "supervisor" = @{
        label = "Supervisor monitor"
        path = "axiom\core\supervisor_monitor.py"
        category = "runtime"
    }
    "state-machine" = @{
        label = "Task state machine"
        path = "axiom\core\state_machine.py"
        category = "runtime"
    }
    "task-committer" = @{
        label = "Task committer"
        path = "axiom\core\task_committer.py"
        category = "runtime"
    }
    "context-builder" = @{
        label = "Context builder"
        path = "axiom\core\context_builder.py"
        category = "runtime"
    }
    "token-estimator" = @{
        label = "Token estimator"
        path = "axiom\core\token_estimator.py"
        category = "runtime"
    }
    "manifest-schema" = @{
        label = "Manifest JSON schema"
        path = "axiom\policy\schemas\manifest_schema.json"
        category = "policy"
    }
    "tool-map-schema" = @{
        label = "Tool capability map schema"
        path = "axiom\policy\schemas\tool_capability_map_schema.json"
        category = "policy"
    }
    "tool-map" = @{
        label = "Tool capability map"
        path = "axiom\policy\security_artifacts\tool_capability_map.json"
        category = "policy"
    }
    "manifest-binder" = @{
        label = "Manifest binder"
        path = "axiom\core\manifest_binder.py"
        category = "policy"
    }
    "policy-engine" = @{
        label = "Policy engine"
        path = "axiom\core\policy_engine.py"
        category = "policy"
    }
    "model-gateway" = @{
        label = "Model gateway"
        path = "axiom\gateways\model_gateway.py"
        category = "gateway"
    }
    "network-gateway" = @{
        label = "Network gateway"
        path = "axiom\gateways\network_gateway.py"
        category = "gateway"
    }
    "sandbox-gateway" = @{
        label = "Sandbox gateway"
        path = "axiom\gateways\sandbox_gateway.py"
        category = "gateway"
    }
    "memory-gateway" = @{
        label = "Memory gateway"
        path = "axiom\gateways\memory_gateway.py"
        category = "gateway"
    }
    "phase5-agent-boundary" = @{
        label = "Phase 5 agent boundary"
        path = "docs\phase5.md"
        category = "agent"
    }
    "phase5-closeout" = @{
        label = "Phase 5 closeout"
        path = "docs\phase5.md"
        category = "agent"
    }
    "phase6" = @{
        label = "Phase 6 consolidated documentation"
        path = "docs\phase6.md"
        category = "agent"
    }
    "phase7-acceptance-inventory" = @{
        label = "Phase 7A acceptance inventory"
        path = "docs\phase7.md"
        category = "agent"
    }
    "phase7-acceptance-runner" = @{
        label = "Phase 7B acceptance runner"
        path = "docs\phase7.md"
        category = "agent"
    }
    "phase7-e2e-gate-audit" = @{
        label = "Phase 7C full-goal E2E gate audit"
        path = "docs\phase7.md"
        category = "agent"
    }
    "phase7-terminal-visibility" = @{
        label = "Phase 7D terminal visibility"
        path = "docs\phase7.md"
        category = "agent"
    }
    "phase7-closeout" = @{
        label = "Phase 7E closeout and hardening audit"
        path = "docs\phase7.md"
        category = "agent"
    }
    "phase8a-release-freeze" = @{
        label = "Phase 8A release freeze and documentation reconciliation"
        path = "docs\phase8.md"
        category = "agent"
    }
    "operator-command-parser" = @{
        label = "Operator command parser"
        path = "axiom\core\operator_command_parser.py"
        category = "runtime"
    }
    "operator-command-ledger" = @{
        label = "Operator command ledger"
        path = "axiom\core\operator_command_ledger.py"
        category = "runtime"
    }
    "operator-command-parser-tool" = @{
        label = "Operator command parser CLI"
        path = "tools\parse_operator_command.py"
        category = "tool"
    }
    "operator-command-ledger-tool" = @{
        label = "Operator command intent recorder"
        path = "tools\record_operator_command_intent.py"
        category = "tool"
    }
    "operator-command-ledger-audit" = @{
        label = "Operator command ledger audit"
        path = "tools\audit_operator_command_ledger.py"
        category = "tool"
    }
    "telegram-gateway" = @{
        label = "Telegram gateway local envelope boundary"
        path = "axiom\gateways\telegram_gateway.py"
        category = "gateway"
    }
    "telegram-gateway-audit" = @{
        label = "Telegram gateway audit"
        path = "tools\audit_telegram_gateway.py"
        category = "tool"
    }
    "phase6-closeout-audit" = @{
        label = "Phase 6 closeout audit"
        path = "tools\audit_phase6_closeout.py"
        category = "tool"
    }
    "phase7-acceptance-inventory-audit" = @{
        label = "Phase 7A acceptance inventory audit"
        path = "tools\audit_phase7_acceptance_inventory.py"
        category = "tool"
    }
    "phase7-acceptance-runner-tool" = @{
        label = "Phase 7B acceptance runner"
        path = "tools\run_phase7_acceptance.py"
        category = "tool"
    }
    "phase7-e2e-gate-audit-tool" = @{
        label = "Phase 7C full-goal E2E gate audit"
        path = "tools\audit_phase7_e2e_gate.py"
        category = "tool"
    }
    "phase7-closeout-audit-tool" = @{
        label = "Phase 7E closeout and hardening audit"
        path = "tools\audit_phase7_closeout.py"
        category = "tool"
    }
    "telegram-gateway-terminal" = @{
        label = "Telegram gateway terminal panel"
        path = "ui\terminal\modules\59-telegram-gateway.ps1"
        category = "terminal"
    }
    "phase7-terminal-module" = @{
        label = "Phase 7 terminal panel"
        path = "ui\terminal\modules\60-phase7.ps1"
        category = "terminal"
    }
    "operator-command-terminal" = @{
        label = "Operator command terminal panel"
        path = "ui\terminal\modules\58-operator-commands.ps1"
        category = "terminal"
    }
    "operator-status-manifest" = @{
        label = "Operator status manifest"
        path = "axiom\policy\operator_control_manifests\status.v1.json"
        category = "policy"
    }
    "agent-boundary-audit" = @{
        label = "Phase 5 agent boundary audit"
        path = "tools\audit_agent_boundary.py"
        category = "agent"
    }
    "agent-base" = @{
        label = "Agent base executor"
        path = "axiom\agents\base.py"
        category = "agent"
    }
    "agent-manual-cli" = @{
        label = "Agent manual CLI guard"
        path = "axiom\agents\manual_cli.py"
        category = "agent"
    }
    "agent-goal-planner" = @{
        label = "Goal planner agent"
        path = "axiom\agents\goal_planner.py"
        category = "agent"
    }
    "agent-task-planner" = @{
        label = "Task planner agent"
        path = "axiom\agents\task_planner.py"
        category = "agent"
    }
    "agent-tool-executor" = @{
        label = "Tool executor agent"
        path = "axiom\agents\tool_executor.py"
        category = "agent"
    }
    "agent-result-verifier" = @{
        label = "Result verifier agent"
        path = "axiom\agents\result_verifier.py"
        category = "agent"
    }
    "agent-smoke-tool" = @{
        label = "Manual agent foundation smoke tool"
        path = "tools\run_manual_agent_foundation_smoke.py"
        category = "agent"
    }
    "verify-foundation" = @{
        label = "Foundation verification tool"
        path = "tools\verify_foundation.py"
        category = "tool"
    }
    "audit-lifecycle" = @{
        label = "Task lifecycle audit tool"
        path = "tools\audit_task_lifecycle.py"
        category = "tool"
    }
    "audit-execution" = @{
        label = "Task execution audit tool"
        path = "tools\audit_task_execution.py"
        category = "tool"
    }
    "supervisor-health" = @{
        label = "Supervisor health tool"
        path = "tools\supervisor_health_check.py"
        category = "tool"
    }
    "snapshot" = @{
        label = "Project snapshot tool"
        path = "tools\snapshot_project_state.py"
        category = "tool"
    }
    "handoff" = @{
        label = "Handoff generator"
        path = "tools\generate_handoff.py"
        category = "tool"
    }
    "handoff-bundle" = @{
        label = "Handoff bundle generator"
        path = "tools\generate_handoff_bundle.py"
        category = "tool"
    }
}

function Resolve-AxiomDocsPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        return $RelativePath
    }

    return Join-Path $script:AxiomRoot $RelativePath
}

function Write-AxiomDocsLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-24}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Get-AxiomDocsEditorCommand {
    if (Get-Command axiom-edit -ErrorAction SilentlyContinue) {
        return "axiom-edit"
    }

    if (Get-Command micro -ErrorAction SilentlyContinue) {
        return "micro"
    }

    return $null
}

function Open-AxiomDocsFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        Write-Host "[AXIOM] File not found: $Path" -ForegroundColor Red
        return
    }

    if (Get-Command axiom-edit -ErrorAction SilentlyContinue) {
        axiom-edit $Path
        return
    }

    if (Get-Command micro -ErrorAction SilentlyContinue) {
        micro $Path
        return
    }

    Write-Host "[AXIOM] No terminal editor found. Path:" -ForegroundColor Yellow
    Write-Host "  $Path" -ForegroundColor Gray
}

function axiom-docs {
    param(
        [string]$Category = ""
    )

    Write-Host ""
    Write-Host "AXIOM DOCS / NAVIGATION" -ForegroundColor Green
    Write-Host "=======================" -ForegroundColor Green
    Write-Host ""

    Write-AxiomDocsLine "root" $script:AxiomRoot $(if (Test-Path $script:AxiomRoot) { "Green" } else { "Red" })
    Write-AxiomDocsLine "terminal root" $script:AxiomTerminalRoot $(if (Test-Path $script:AxiomTerminalRoot) { "Green" } else { "Red" })

    $editor = Get-AxiomDocsEditorCommand
    Write-AxiomDocsLine "editor" $(if ($editor) { $editor } else { "missing" }) $(if ($editor) { "Green" } else { "Yellow" })

    Write-Host ""

    $entries = foreach ($key in $script:AxiomDocsIndex.Keys) {
        $entry = $script:AxiomDocsIndex[$key]
        [pscustomobject]@{
            Key = $key
            Label = [string]$entry.label
            Path = [string]$entry.path
            Category = [string]$entry.category
            Exists = Test-Path (Resolve-AxiomDocsPath -RelativePath ([string]$entry.path))
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($Category)) {
        $entries = @($entries | Where-Object { $_.Category -eq $Category })
    }

    $groups = @($entries | Group-Object Category | Sort-Object Name)

    foreach ($group in $groups) {
        Write-Host $group.Name -ForegroundColor DarkGreen

        foreach ($item in @($group.Group | Sort-Object Key)) {
            $state = if ($item.Exists) { "ok" } else { "missing" }
            $color = if ($item.Exists) { "Gray" } else { "Yellow" }

            Write-Host ("  {0,-26} {1,-8} {2}" -f $item.Key, $state, $item.Label) -ForegroundColor $color
        }

        Write-Host ""
    }

    Write-Host "Usage" -ForegroundColor DarkGreen
    Write-Host "  axiom-doc <name>              Open indexed file" -ForegroundColor Gray
    Write-Host "  axiom-doc-path <name>         Print indexed file path" -ForegroundColor Gray
    Write-Host "  axiom-docs terminal           Show terminal docs only" -ForegroundColor Gray
    Write-Host "  axiom-docs runtime            Show runtime files only" -ForegroundColor Gray
    Write-Host "  axiom-docs agent              Show Phase 5 agent docs/files only" -ForegroundColor Gray
    Write-Host ""
}

function axiom-doc-path {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name
    )

    if (-not $script:AxiomDocsIndex.Contains($Name)) {
        Write-Host "[AXIOM] Unknown doc key: $Name" -ForegroundColor Red
        Write-Host "Run: axiom-docs" -ForegroundColor Gray
        return
    }

    $entry = $script:AxiomDocsIndex[$Name]
    $path = Resolve-AxiomDocsPath -RelativePath ([string]$entry.path)

    Write-Host $path -ForegroundColor Green
}

function axiom-doc {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name
    )

    if (-not $script:AxiomDocsIndex.Contains($Name)) {
        Write-Host "[AXIOM] Unknown doc key: $Name" -ForegroundColor Red
        Write-Host "Run: axiom-docs" -ForegroundColor Gray
        return
    }

    $entry = $script:AxiomDocsIndex[$Name]
    $path = Resolve-AxiomDocsPath -RelativePath ([string]$entry.path)

    Open-AxiomDocsFile -Path $path
}

function axiom-docs-terminal {
    axiom-docs -Category "terminal"
}

function axiom-docs-runtime {
    axiom-docs -Category "runtime"
}

function axiom-docs-policy {
    axiom-docs -Category "policy"
}

function axiom-docs-tools {
    axiom-docs -Category "tool"
}

function axiom-docs-agent {
    axiom-docs -Category "agent"
}




