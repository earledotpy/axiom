# ============================================================
# AXIOM Terminal Report
# File: C:\axiom\ui\terminal\modules\50-terminal-report.ps1
#
# Purpose:
#   Read-only AXIOM Terminal suite report.
#
# Boundary:
#   This module reports terminal/UI/operator environment state only.
#   It must not mutate AXIOM runtime state.
#   It must not run scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomTerminalReportPaths = [ordered]@{
    Root = $script:AxiomRoot
    TerminalRoot = $script:AxiomTerminalRoot
    Profile = (Join-Path $script:AxiomTerminalRoot "profile\profile-axiom.ps1")
    Modules = (Join-Path $script:AxiomTerminalRoot "modules")
    Registry = (Join-Path $script:AxiomTerminalRoot "registry\axiom-terminal-command-registry.json")
    VisualConfig = (Join-Path $script:AxiomTerminalRoot "profile\visual-mode.json")
    Themes = (Join-Path $script:AxiomTerminalRoot "themes")
    Assets = (Join-Path $script:AxiomTerminalRoot "assets")
    TerminalSettings = (Join-Path $script:AxiomTerminalRoot "terminal")
    Editor = (Join-Path $script:AxiomTerminalRoot "editor")
    ReportDir = (Join-Path $script:AxiomRoot "logs\terminal_reports")
}

function Get-AxiomTerminalReportRegistry {
    $path = $script:AxiomTerminalReportPaths.Registry

    if (-not (Test-Path $path)) {
        return $null
    }

    try {
        return Get-Content $path -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-AxiomTerminalReportVisualConfig {
    $path = $script:AxiomTerminalReportPaths.VisualConfig

    if (-not (Test-Path $path)) {
        return $null
    }

    try {
        return Get-Content $path -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-AxiomTerminalReportModules {
    $path = $script:AxiomTerminalReportPaths.Modules

    if (-not (Test-Path $path)) {
        return @()
    }

    return @(Get-ChildItem $path -Filter "*.ps1" | Sort-Object Name)
}

function Get-AxiomTerminalReportCommandSummary {
    $registry = Get-AxiomTerminalReportRegistry

    if (-not $registry) {
        return [pscustomobject]@{
            RegistryPresent = $false
            Total = 0
            Implemented = 0
            Planned = 0
            PlannedNext = 0
            Deprecated = 0
            Hidden = 0
            MissingLoadedImplemented = @()
            Commands = @()
        }
    }

    $commands = @($registry.commands)
    $missing = New-Object System.Collections.Generic.List[string]

    foreach ($cmd in $commands) {
        $status = ""
        if ($cmd.PSObject.Properties.Name -contains "status") {
            $status = [string]$cmd.status
        }

        $isPlanned = $status -in @("planned", "planned_next")
        $isDeprecated = $status -eq "deprecated"
        $isHidden = $status -eq "hidden"

        if (-not $isPlanned -and -not $isDeprecated -and -not $isHidden) {
            if (-not (Get-Command ([string]$cmd.name) -ErrorAction SilentlyContinue)) {
                $missing.Add([string]$cmd.name)
            }
        }
    }

    [pscustomobject]@{
        RegistryPresent = $true
        Total = $commands.Count
        Implemented = @($commands | Where-Object { -not ($_.PSObject.Properties.Name -contains "status") -or $_.status -eq "implemented" -or [string]::IsNullOrWhiteSpace([string]$_.status) }).Count
        Planned = @($commands | Where-Object { $_.status -eq "planned" }).Count
        PlannedNext = @($commands | Where-Object { $_.status -eq "planned_next" }).Count
        Deprecated = @($commands | Where-Object { $_.status -eq "deprecated" }).Count
        Hidden = @($commands | Where-Object { $_.status -eq "hidden" }).Count
        MissingLoadedImplemented = @($missing)
        Commands = $commands
    }
}

function Write-AxiomTerminalReportLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Convert-AxiomTerminalReportToText {
    $registry = Get-AxiomTerminalReportRegistry
    $visual = Get-AxiomTerminalReportVisualConfig
    $modules = @(Get-AxiomTerminalReportModules)
    $summary = Get-AxiomTerminalReportCommandSummary

    $lines = New-Object System.Collections.Generic.List[string]

    $lines.Add("AXIOM Terminal Report")
    $lines.Add("=====================")
    $lines.Add("")
    $lines.Add("Generated: $(Get-Date -Format o)")
    $lines.Add("AXIOM root: $script:AxiomRoot")
    $lines.Add("AXIOM Terminal root: $script:AxiomTerminalRoot")
    $lines.Add("Profile mode: $env:AXIOM_PROFILE_MODE")
    $lines.Add("Prompt engine: $env:AXIOM_PROMPT_ENGINE")
    $lines.Add("Startup banner: $env:AXIOM_STARTUP_BANNER")
    $lines.Add("")

    $lines.Add("Paths")
    $lines.Add("-----")
    foreach ($key in $script:AxiomTerminalReportPaths.Keys) {
        $path = $script:AxiomTerminalReportPaths[$key]
        $state = if (Test-Path $path) { "present" } else { "missing" }
        $lines.Add("${key}: $state :: $path")
    }
    $lines.Add("")

    $lines.Add("Modules")
    $lines.Add("-------")
    if ($modules.Count -eq 0) {
        $lines.Add("No modules found.")
    }
    else {
        foreach ($module in $modules) {
            $lines.Add("$($module.Name) :: $($module.FullName)")
        }
    }
    $lines.Add("")

    $lines.Add("Visual Config")
    $lines.Add("-------------")
    if ($visual) {
        $lines.Add("prompt_mode: $($visual.prompt_mode)")
        $lines.Add("startup_banner: $($visual.startup_banner)")
        $lines.Add("theme: $($visual.theme)")
    }
    else {
        $lines.Add("visual config unavailable")
    }
    $lines.Add("")

    $lines.Add("Command Registry")
    $lines.Add("----------------")
    $lines.Add("registry_present: $($summary.RegistryPresent)")
    $lines.Add("total: $($summary.Total)")
    $lines.Add("implemented: $($summary.Implemented)")
    $lines.Add("planned: $($summary.Planned)")
    $lines.Add("planned_next: $($summary.PlannedNext)")
    $lines.Add("deprecated: $($summary.Deprecated)")
    $lines.Add("hidden: $($summary.Hidden)")

    if ($summary.MissingLoadedImplemented.Count -gt 0) {
        $lines.Add("missing_loaded_implemented:")
        foreach ($name in $summary.MissingLoadedImplemented) {
            $lines.Add("- $name")
        }
    }
    else {
        $lines.Add("missing_loaded_implemented: none")
    }
    $lines.Add("")

    if ($registry) {
        $lines.Add("Commands by Category")
        $lines.Add("--------------------")

        $categories = @($summary.Commands | Group-Object category | Sort-Object Name)

        foreach ($category in $categories) {
            $lines.Add("")
            $lines.Add("[$($category.Name)]")

            foreach ($cmd in @($category.Group | Sort-Object name)) {
                $status = "implemented"
                if ($cmd.PSObject.Properties.Name -contains "status" -and -not [string]::IsNullOrWhiteSpace([string]$cmd.status)) {
                    $status = [string]$cmd.status
                }

                $primary = if ($cmd.primary) { "primary" } else { "secondary" }
                $risk = [string]$cmd.risk
                $mutates = [string]$cmd.mutates_axiom_runtime

                $lines.Add("- $($cmd.name) :: $status :: $primary :: risk=$risk :: mutates_runtime=$mutates")
            }
        }
        $lines.Add("")
    }

    $lines.Add("Operator Control Visibility")
    $lines.Add("---------------------------")
    $operatorCommandNames = @(
        "axiom-operator-commands",
        "axiom-operator-command-audit",
        "axiom-telegram-gateway",
        "axiom-telegram-gateway-audit"
    )
    foreach ($name in $operatorCommandNames) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        $state = if ($command) { "loaded" } else { "missing" }
        $lines.Add("${name}: $state")
    }
    $lines.Add("preflight_hook: tools\audit_operator_command_ledger.py")
    $lines.Add("telegram_preflight_hook: tools\audit_telegram_gateway.py")
    $lines.Add("runtime_mutation_shortcut: none")
    $lines.Add("")

    $lines.Add("Blocked Direct Shortcuts")
    $lines.Add("------------------------")
    if ($registry -and $registry.blocked_direct_shortcuts) {
        foreach ($blocked in @($registry.blocked_direct_shortcuts)) {
            $lines.Add("- $($blocked.name): $($blocked.reason)")
        }
    }
    else {
        $lines.Add("No blocked shortcut list found.")
    }
    $lines.Add("")

    $lines.Add("Extension Roadmap")
    $lines.Add("-----------------")
    $lines.Add("T12 complete: axiom-terminal-report")
    $lines.Add("T13 complete: terminal changelog/update-notes discipline")
    $lines.Add("T14 complete: docs/navigation panel")
    $lines.Add("T15 complete: system map showing runtime/tool/UI boundaries")
    $lines.Add("Phase 5 hardening complete: agent boundary audit is part of preflight visibility")
    $lines.Add("Phase 6E complete: operator command ledger visibility is part of terminal/preflight visibility")
    $lines.Add("Phase 6H complete: Telegram gateway visibility is read-only and part of terminal/preflight visibility")
    $lines.Add("Phase 7 current: E2E readiness/passing is documented; terminal panels remain report-only")
    $lines.Add("Phase 8A current: release-freeze documentation reconciliation only; no runtime capability added")
    $lines.Add("Recommended next:")
    $lines.Add("- Reduce repeated dashboard/readiness/report output into operator-critical summaries")
    $lines.Add("- Add gateway and calibration status panels only after runtime state is authoritative")
    $lines.Add("- Later: add TUI dashboard only after terminal read-only panels stabilize")
    $lines.Add("")
    $lines.Add("Boundary")
    $lines.Add("--------")
    $lines.Add("AXIOM Terminal is an operator UI layer. State-changing runtime behavior must live in approved AXIOM tools/runtime and preserve policy/audit gates.")

    return ($lines -join [Environment]::NewLine)
}

function axiom-terminal-report {
    param(
        [switch]$Save
    )

    $registry = Get-AxiomTerminalReportRegistry
    $visual = Get-AxiomTerminalReportVisualConfig
    $modules = @(Get-AxiomTerminalReportModules)
    $summary = Get-AxiomTerminalReportCommandSummary

    Write-Host ""
    Write-Host "AXIOM TERMINAL REPORT" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Environment" -ForegroundColor DarkGreen
    Write-AxiomTerminalReportLine "AXIOM root" $script:AxiomRoot $(if (Test-Path $script:AxiomRoot) { "Green" } else { "Red" })
    Write-AxiomTerminalReportLine "terminal root" $script:AxiomTerminalRoot $(if (Test-Path $script:AxiomTerminalRoot) { "Green" } else { "Red" })
    Write-AxiomTerminalReportLine "profile mode" ([string]$env:AXIOM_PROFILE_MODE) "Gray"
    Write-AxiomTerminalReportLine "prompt engine" ([string]$env:AXIOM_PROMPT_ENGINE) "Cyan"
    Write-AxiomTerminalReportLine "startup banner" ([string]$env:AXIOM_STARTUP_BANNER) "Cyan"

    Write-Host ""
    Write-Host "Terminal paths" -ForegroundColor DarkGreen
    foreach ($key in $script:AxiomTerminalReportPaths.Keys) {
        if ($key -eq "ReportDir") {
            continue
        }

        $path = $script:AxiomTerminalReportPaths[$key]
        $color = if (Test-Path $path) { "Green" } else { "Yellow" }
        Write-AxiomTerminalReportLine $key $path $color
    }

    Write-Host ""
    Write-Host "Modules" -ForegroundColor DarkGreen
    Write-AxiomTerminalReportLine "module count" ([string]$modules.Count) $(if ($modules.Count -gt 0) { "Green" } else { "Red" })

    if ($modules.Count -gt 0) {
        foreach ($module in $modules) {
            Write-Host "  - $($module.Name)" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Visual config" -ForegroundColor DarkGreen
    if ($visual) {
        Write-AxiomTerminalReportLine "prompt_mode" ([string]$visual.prompt_mode) "Cyan"
        Write-AxiomTerminalReportLine "startup_banner" ([string]$visual.startup_banner) "Cyan"
        Write-AxiomTerminalReportLine "theme" ([string]$visual.theme) "Cyan"
    }
    else {
        Write-AxiomTerminalReportLine "visual config" "unavailable" "Yellow"
    }

    Write-Host ""
    Write-Host "Command registry" -ForegroundColor DarkGreen
    Write-AxiomTerminalReportLine "registry present" ([string]$summary.RegistryPresent) $(if ($summary.RegistryPresent) { "Green" } else { "Red" })
    Write-AxiomTerminalReportLine "total commands" ([string]$summary.Total) "Gray"
    Write-AxiomTerminalReportLine "implemented" ([string]$summary.Implemented) "Green"
    Write-AxiomTerminalReportLine "planned" ([string]$summary.Planned) "Yellow"
    Write-AxiomTerminalReportLine "planned_next" ([string]$summary.PlannedNext) "Yellow"
    Write-AxiomTerminalReportLine "deprecated" ([string]$summary.Deprecated) "Gray"
    Write-AxiomTerminalReportLine "hidden" ([string]$summary.Hidden) "Gray"

    if ($summary.MissingLoadedImplemented.Count -gt 0) {
        Write-AxiomTerminalReportLine "missing implemented" ($summary.MissingLoadedImplemented -join ", ") "Red"
    }
    else {
        Write-AxiomTerminalReportLine "missing implemented" "none" "Green"
    }

    if ($registry) {
        Write-Host ""
        Write-Host "Primary command surface" -ForegroundColor DarkGreen

        $primary = @($summary.Commands | Where-Object { $_.primary -eq $true } | Sort-Object category, name)

        foreach ($cmd in $primary) {
            $status = "implemented"
            if ($cmd.PSObject.Properties.Name -contains "status" -and -not [string]::IsNullOrWhiteSpace([string]$cmd.status)) {
                $status = [string]$cmd.status
            }

            $color = if ($status -eq "implemented") { "Green" } elseif ($status -like "planned*") { "Yellow" } else { "Gray" }

            Write-Host ("  {0,-24} {1,-16} {2}" -f $cmd.name, $cmd.category, $status) -ForegroundColor $color
        }
    }

    Write-Host ""
    Write-Host "Operator control visibility" -ForegroundColor DarkGreen
    $operatorCommandNames = @(
        "axiom-operator-commands",
        "axiom-operator-command-audit",
        "axiom-telegram-gateway",
        "axiom-telegram-gateway-audit"
    )
    foreach ($name in $operatorCommandNames) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        $state = if ($command) { "loaded" } else { "missing" }
        $color = if ($command) { "Green" } else { "Red" }
        Write-AxiomTerminalReportLine $name $state $color
    }
    Write-AxiomTerminalReportLine "preflight hook" "tools\audit_operator_command_ledger.py" "Green"
    Write-AxiomTerminalReportLine "telegram hook" "tools\audit_telegram_gateway.py" "Green"
    Write-AxiomTerminalReportLine "mutation shortcut" "none" "Green"

    Write-Host ""
    Write-Host "Roadmap" -ForegroundColor DarkGreen
    Write-Host "  T12: axiom-terminal-report complete after this module is loaded." -ForegroundColor Gray
    Write-Host "  T13: terminal changelog/update-notes discipline complete." -ForegroundColor Gray
    Write-Host "  T14: docs/navigation panel complete." -ForegroundColor Gray
    Write-Host "  T15: system map showing runtime/tool/UI boundaries complete." -ForegroundColor Gray
    Write-Host "  Phase 5: agent boundary audit wired into verification visibility." -ForegroundColor Gray
    Write-Host "  Phase 6E: operator command ledger visibility wired into preflight/report/help." -ForegroundColor Gray
    Write-Host "  Phase 6H: Telegram gateway visibility wired into preflight/report/help." -ForegroundColor Gray
    Write-Host "  Phase 7: accepted E2E readiness/passing is visible through report-mode surfaces." -ForegroundColor Gray
    Write-Host "  Phase 8A: documentation reconciliation only; no runtime capability added." -ForegroundColor Gray
    Write-Host "  Next: reduce repeated state output; add gateway/calibration panels when authoritative." -ForegroundColor Gray

    Write-Host ""
    Write-Host "Boundary" -ForegroundColor DarkGreen
    Write-Host "  AXIOM Terminal reports and wraps safe tooling." -ForegroundColor Gray
    Write-Host "  Runtime mutation must remain in approved AXIOM tools with policy/audit gates." -ForegroundColor Gray
    Write-Host ""

    if ($Save) {
        $dir = $script:AxiomTerminalReportPaths.ReportDir
        New-Item -ItemType Directory -Force $dir | Out-Null

        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $path = Join-Path $dir "axiom_terminal_report_$stamp.md"

        Convert-AxiomTerminalReportToText | Set-Content $path -Encoding UTF8

        Write-Host "Saved report:" -ForegroundColor Green
        Write-Host "  $path" -ForegroundColor Gray
        Write-Host ""
    }
}

