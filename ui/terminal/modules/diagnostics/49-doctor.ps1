# ============================================================
# AXIOM Terminal Doctor
# File: C:\axiom\ui\terminal\modules\49-doctor.ps1
#
# Purpose:
#   Consolidated AXIOM Terminal diagnostics.
#
# Boundary:
#   This module inspects terminal/UI/operator environment only.
#   It must not mutate AXIOM runtime state.
#   It must not run scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomDoctorPaths = [ordered]@{
    Root = $script:AxiomRoot
    TerminalRoot = $script:AxiomTerminalRoot
    Profile = (Join-Path $script:AxiomTerminalRoot "profile\profile-axiom.ps1")
    Modules = (Join-Path $script:AxiomTerminalRoot "modules")
    Registry = (Join-Path $script:AxiomTerminalRoot "registry\axiom-terminal-command-registry.json")
    VisualConfig = (Join-Path $script:AxiomTerminalRoot "profile\visual-mode.json")
    Themes = (Join-Path $script:AxiomTerminalRoot "themes")
    DashboardTheme = (Join-Path $script:AxiomTerminalRoot "themes\axiom-dashboard.omp.json")
    Assets = (Join-Path $script:AxiomTerminalRoot "assets")
    Background = (Join-Path $script:AxiomTerminalRoot "assets\axiom-crt-background.png")
    Icon = (Join-Path $script:AxiomTerminalRoot "assets\axiom-terminal-icon.png")
    TerminalSettings = (Join-Path $script:AxiomTerminalRoot "terminal")
    TerminalSnippet = (Join-Path $script:AxiomTerminalRoot "terminal\windows-terminal-axiom-snippet.jsonc")
    Editor = (Join-Path $script:AxiomTerminalRoot "editor")
    VenvActivate = (Join-Path $script:AxiomRoot "venv\Scripts\Activate.ps1")
    Database = (Join-Path $script:AxiomRoot "axiom.db")
}

function New-AxiomDoctorCheck {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail,
        [string]$Severity = "required"
    )

    [pscustomobject]@{
        Name = $Name
        Passed = $Passed
        Detail = $Detail
        Severity = $Severity
    }
}

function Write-AxiomDoctorCheck {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Check
    )

    $status = if ($Check.Passed) { "PASS" } else { "FAIL" }

    $color = if ($Check.Passed) {
        "Green"
    }
    elseif ($Check.Severity -eq "warning") {
        "Yellow"
    }
    else {
        "Red"
    }

    Write-Host ("  [{0,-4}] " -f $status) -NoNewline -ForegroundColor $color
    Write-Host ("{0,-34}" -f $Check.Name) -NoNewline -ForegroundColor Gray
    Write-Host $Check.Detail -ForegroundColor DarkGray
}

function Test-AxiomDoctorCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [string]$Severity = "required"
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue

    if ($cmd) {
        return New-AxiomDoctorCheck "command: $Name" $true $cmd.CommandType $Severity
    }

    return New-AxiomDoctorCheck "command: $Name" $false "missing" $Severity
}

function Test-AxiomDoctorPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Path,

        [string]$Severity = "required"
    )

    $exists = Test-Path $Path
    return New-AxiomDoctorCheck "path: $Name" $exists $Path $Severity
}

function Read-AxiomDoctorRegistry {
    $registryPath = $script:AxiomDoctorPaths.Registry

    if (-not (Test-Path $registryPath)) {
        return $null
    }

    try {
        return Get-Content $registryPath -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Test-AxiomDoctorRegistry {
    $checks = New-Object System.Collections.Generic.List[object]
    $registryPath = $script:AxiomDoctorPaths.Registry

    $exists = Test-Path $registryPath
    $checks.Add((New-AxiomDoctorCheck "registry file" $exists $registryPath))

    if (-not $exists) {
        return $checks
    }

    $registry = Read-AxiomDoctorRegistry
    $checks.Add((New-AxiomDoctorCheck "registry parses" ($null -ne $registry) "ConvertFrom-Json"))

    if (-not $registry) {
        return $checks
    }

    $schemaOk = $registry.schema_version -eq "axiom.terminal.command_registry.v1"
    $checks.Add((New-AxiomDoctorCheck "registry schema" $schemaOk ([string]$registry.schema_version)))

    $commands = @($registry.commands)
    $checks.Add((New-AxiomDoctorCheck "registry command count" ($commands.Count -gt 0) "count=$($commands.Count)"))

    $names = @($commands | ForEach-Object { [string]$_.name })
    $duplicates = @(
        $names |
            Group-Object |
            Where-Object { $_.Count -gt 1 } |
            ForEach-Object { $_.Name }
    )

    $checks.Add((New-AxiomDoctorCheck "registry unique names" ($duplicates.Count -eq 0) $(if ($duplicates.Count -eq 0) { "ok" } else { $duplicates -join ", " })))

    $implementedMissing = New-Object System.Collections.Generic.List[string]
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
                $implementedMissing.Add([string]$cmd.name)
            }
        }
    }

    $checks.Add((
        New-AxiomDoctorCheck `
            "implemented commands loaded" `
            ($implementedMissing.Count -eq 0) `
            $(if ($implementedMissing.Count -eq 0) { "ok" } else { $implementedMissing -join ", " })
    ))

    $mutableCommands = @($commands | Where-Object { $_.mutates_axiom_runtime -eq $true })
    $checks.Add((New-AxiomDoctorCheck "runtime-mutating commands" ($mutableCommands.Count -eq 0) "count=$($mutableCommands.Count)" "warning"))

    return $checks
}

function Test-AxiomDoctorModuleOrder {
    $checks = New-Object System.Collections.Generic.List[object]
    $moduleDir = $script:AxiomDoctorPaths.Modules

    if (-not (Test-Path $moduleDir)) {
        $checks.Add((New-AxiomDoctorCheck "module directory" $false $moduleDir))
        return $checks
    }

    $modules = @()
    $moduleGroups = @('core', 'foundation', 'utilities', 'shared', 'operators', 'diagnostics', 'phase10', 'safety')

    foreach ($group in $moduleGroups) {
        $groupPath = Join-Path $moduleDir $group
        if (Test-Path $groupPath) {
            $modules += @(Get-ChildItem $groupPath -Filter "*.ps1" -ErrorAction SilentlyContinue | Sort-Object Name)
        }
    }

    $moduleNames = @($modules | ForEach-Object { $_.Name })

    $checks.Add((New-AxiomDoctorCheck "module count" ($modules.Count -gt 0) "count=$($modules.Count)"))

    $requiredModules = @(
        "04-visual-mode.ps1",
        "05-visual.ps1",
        "06-oh-my-posh.ps1",
        "40-dashboard.ps1",
        "41-readiness.ps1",
        "42-registry-discipline.ps1",
        "45-model.ps1",
        "46-manifests.ps1",
        "47-budget.ps1",
        "48-events.ps1",
        "49-doctor.ps1",
        "60-phase7.ps1",
        "62-execution-trace.ps1",
        "63-approval-gate.ps1",
        "64-autonomous-posture.ps1",
        "90-safety-help.ps1"
    )

    foreach ($name in $requiredModules) {
        $exists = $moduleNames -contains $name
        $severity = if ($name -in @("45-model.ps1", "46-manifests.ps1", "47-budget.ps1", "48-events.ps1", "62-execution-trace.ps1", "63-approval-gate.ps1", "64-autonomous-posture.ps1")) { "warning" } else { "required" }
        $checks.Add((New-AxiomDoctorCheck "module: $name" $exists $(if ($exists) { "loaded path present" } else { "missing" }) $severity))
    }

    $visualModeIndex = [array]::IndexOf($moduleNames, "04-visual-mode.ps1")
    $visualIndex = [array]::IndexOf($moduleNames, "05-visual.ps1")
    $poshIndex = [array]::IndexOf($moduleNames, "06-oh-my-posh.ps1")

    $orderOk = ($visualModeIndex -ge 0 -and $visualIndex -ge 0 -and $poshIndex -ge 0 -and $visualModeIndex -lt $visualIndex -and $visualIndex -lt $poshIndex)

    $checks.Add((New-AxiomDoctorCheck "visual module order" $orderOk "04 before 05 before 06"))

    $oldVisualMode = Join-Path $moduleDir "43-visual-mode.ps1"
    $oldVisualModeInFoundation = Join-Path $moduleDir "foundation" "43-visual-mode.ps1"
    $checks.Add((New-AxiomDoctorCheck "old visual module absent" (-not ((Test-Path $oldVisualMode) -or (Test-Path $oldVisualModeInFoundation))) "43-visual-mode.ps1 should not remain" "warning"))

    return $checks
}

function Test-AxiomDoctorVisual {
    $checks = New-Object System.Collections.Generic.List[object]
    $configPath = $script:AxiomDoctorPaths.VisualConfig

    $configExists = Test-Path $configPath
    $checks.Add((New-AxiomDoctorCheck "visual config file" $configExists $configPath "warning"))

    if ($configExists) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $modeOk = [string]$config.prompt_mode -in @("native", "dashboard")
            $checks.Add((New-AxiomDoctorCheck "visual prompt_mode" $modeOk ([string]$config.prompt_mode)))
            $checks.Add((New-AxiomDoctorCheck "visual startup_banner" ($config.PSObject.Properties.Name -contains "startup_banner") ([string]$config.startup_banner)))
        }
        catch {
            $checks.Add((New-AxiomDoctorCheck "visual config parses" $false "ConvertFrom-Json failed" "warning"))
        }
    }

    $checks.Add((New-AxiomDoctorCheck "env prompt engine" ($env:AXIOM_PROMPT_ENGINE -in @("native", "oh-my-posh", $null, "")) "AXIOM_PROMPT_ENGINE=$env:AXIOM_PROMPT_ENGINE" "warning"))
    $checks.Add((New-AxiomDoctorCheck "env startup banner" ($env:AXIOM_STARTUP_BANNER -in @("0", "1", $null, "")) "AXIOM_STARTUP_BANNER=$env:AXIOM_STARTUP_BANNER" "warning"))

    return $checks
}

function Test-AxiomDoctorExternalTools {
    $checks = New-Object System.Collections.Generic.List[object]

    $python = Get-Command python -ErrorAction SilentlyContinue
    $pytest = Get-Command pytest -ErrorAction SilentlyContinue
    $venvPytest = Join-Path $script:AxiomRoot "venv\Scripts\pytest.exe"
    $venvPytestPackage = Join-Path $script:AxiomRoot "venv\Lib\site-packages\pytest"
    $micro = Get-Command micro -ErrorAction SilentlyContinue
    $git = Get-Command git -ErrorAction SilentlyContinue
    $wt = Get-Command wt.exe -ErrorAction SilentlyContinue
    $posh = Get-Command oh-my-posh -ErrorAction SilentlyContinue
    $pytestAvailable = ($null -ne $pytest) -or (Test-Path $venvPytest) -or (Test-Path $venvPytestPackage)
    $pytestDetail = if ($pytest) {
        $pytest.Source
    }
    elseif (Test-Path $venvPytest) {
        $venvPytest
    }
    elseif (Test-Path $venvPytestPackage) {
        "python -m pytest via venv"
    }
    else {
        "missing"
    }

    $checks.Add((New-AxiomDoctorCheck "tool: python" ($null -ne $python) $(if ($python) { $python.Source } else { "missing" })))
    $checks.Add((New-AxiomDoctorCheck "tool: pytest" $pytestAvailable $pytestDetail))
    $checks.Add((New-AxiomDoctorCheck "tool: micro" ($null -ne $micro) $(if ($micro) { $micro.Source } else { "missing" }) "warning"))
    $checks.Add((New-AxiomDoctorCheck "tool: git" ($null -ne $git) $(if ($git) { $git.Source } else { "missing" }) "warning"))
    $checks.Add((New-AxiomDoctorCheck "tool: wt.exe" ($null -ne $wt) $(if ($wt) { $wt.Source } else { "missing" }) "warning"))
    $checks.Add((New-AxiomDoctorCheck "tool: oh-my-posh" ($null -ne $posh) $(if ($posh) { $posh.Source } else { "missing" }) "warning"))

    return $checks
}

function Test-AxiomDoctorAxiomTools {
    $checks = New-Object System.Collections.Generic.List[object]

    $requiredTools = @(
        "tools\verify_foundation.py",
        "tools\audit_task_lifecycle.py",
        "tools\audit_task_execution.py",
        "tools\audit_policy_security.py",
        "tools\audit_agent_boundary.py",
        "tools\audit_operator_command_ledger.py",
        "tools\audit_telegram_gateway.py",
        "tools\audit_phase6_closeout.py",
        "tools\audit_phase7_acceptance_inventory.py",
        "tools\run_phase7_acceptance.py",
        "tools\audit_phase7_e2e_gate.py",
        "tools\audit_phase7_closeout.py",
        "tools\audit_phase9_closeout.py",
        "tools\record_operator_command_intent.py",
        "tools\supervisor_health_check.py",
        "tools\snapshot_project_state.py",
        "tools\generate_handoff.py",
        "tools\generate_handoff_bundle.py",
        "tools\operator_command_index.py"
    )

    foreach ($tool in $requiredTools) {
        $path = Join-Path $script:AxiomRoot $tool
        $checks.Add((New-AxiomDoctorCheck "AXIOM tool: $tool" (Test-Path $path) $path))
    }

    $dangerousManualTools = @(
        "tools\run_scheduler_loop.py",
        "tools\run_manual_noop_cycle.py",
        "tools\execute_noop_task.py",
        "tools\start_task.py",
        "tools\dispatch_next_task.py",
        "tools\execute_goal_planning_task.py",
        "tools\execute_task_planning_task.py",
        "tools\execute_tool_execution_task.py",
        "tools\execute_result_verification_task.py",
        "tools\run_manual_agent_foundation_smoke.py"
    )

    foreach ($tool in $dangerousManualTools) {
        $path = Join-Path $script:AxiomRoot $tool
        $checks.Add((New-AxiomDoctorCheck "manual/test tool present: $tool" (Test-Path $path) "must not be exposed as casual terminal shortcut" "warning"))
    }

    return $checks
}

function Test-AxiomDoctorUnsafeShortcuts {
    $checks = New-Object System.Collections.Generic.List[object]

    $blockedNames = @(
        "axiom-safe-pass-on",
        "axiom-enable-autonomous",
        "axiom-promote-model",
        "axiom-register-model",
        "axiom-run-scheduler",
        "axiom-run-noop-cycle",
        "axiom-execute-noop",
        "axiom-dispatch",
        "axiom-start-task"
    )

    foreach ($name in $blockedNames) {
        $exists = Get-Command $name -ErrorAction SilentlyContinue
        $checks.Add((New-AxiomDoctorCheck "unsafe shortcut absent: $name" ($null -eq $exists) $(if ($exists) { "loaded; remove it" } else { "absent" })))
    }

    return $checks
}

function axiom-doctor {
    Write-Host ""
    Write-Host "AXIOM TERMINAL DOCTOR" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    Write-Host ""

    $allChecks = New-Object System.Collections.Generic.List[object]

    Write-Host "Paths" -ForegroundColor DarkGreen
    foreach ($key in $script:AxiomDoctorPaths.Keys) {
        $severity = if ($key -in @("DashboardTheme", "Background", "Icon", "TerminalSnippet", "VisualConfig")) { "warning" } else { "required" }
        $check = Test-AxiomDoctorPath -Name $key -Path $script:AxiomDoctorPaths[$key] -Severity $severity
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "Module order" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorModuleOrder)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "Primary commands" -ForegroundColor DarkGreen
    $primaryCommands = @(
        "axiom",
        "axiom-help",
        "axiom-help-all",
        "axiom-now",
        "axiom-doctor",
        "axiom-registry",
        "axiom-guard",
        "axiom-edit",
        "ae",
        "axiom-preflight",
        "axiom-status",
        "axiom-audit",
        "axiom-policy-audit",
        "axiom-agent-audit",
        "axiom-operator-command-audit",
        "axiom-telegram-gateway-audit",
        "axiom-phase6-audit",
        "axiom-phase7-inventory",
        "axiom-phase7-acceptance",
        "axiom-phase7-e2e-gate",
        "axiom-phase7-closeout",
        "axiom-phase9-closeout",
        "axiom-health",
        "axiom-regression",
        "axiom-test",
        "axiom-dashboard",
        "axiom-readiness",
        "axiom-model",
        "axiom-manifests",
        "axiom-budget",
        "axiom-events",
        "axiom-operator-commands",
        "axiom-telegram-gateway",
        "axiom-phase7",
        "axiom-handoff",
        "axiom-logs",
        "axiom-visual-mode",
        "axiom-visual-native",
        "axiom-visual-dashboard"
    )

    foreach ($cmd in $primaryCommands) {
        $severity = if ($cmd -in @("axiom-model", "axiom-manifests", "axiom-budget", "axiom-events")) { "warning" } else { "required" }
        $check = Test-AxiomDoctorCommand -Name $cmd -Severity $severity
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "Registry" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorRegistry)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "Visual configuration" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorVisual)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "External tools" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorExternalTools)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "AXIOM tool files" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorAxiomTools)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    Write-Host ""
    Write-Host "Unsafe shortcut guard" -ForegroundColor DarkGreen
    foreach ($check in (Test-AxiomDoctorUnsafeShortcuts)) {
        $allChecks.Add($check)
        Write-AxiomDoctorCheck $check
    }

    $failures = @($allChecks | Where-Object { -not $_.Passed -and $_.Severity -ne "warning" })
    $warnings = @($allChecks | Where-Object { -not $_.Passed -and $_.Severity -eq "warning" })

    Write-Host ""

    if ($failures.Count -eq 0) {
        Write-Host "Doctor result: PASS" -ForegroundColor Green
    }
    else {
        Write-Host "Doctor result: FAIL" -ForegroundColor Red
        Write-Host ""
        Write-Host "Blocking failures:" -ForegroundColor Red

        foreach ($failure in $failures) {
            Write-Host "  - $($failure.Name): $($failure.Detail)" -ForegroundColor Red
        }
    }

    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Warnings:" -ForegroundColor Yellow

        foreach ($warning in $warnings) {
            Write-Host "  - $($warning.Name): $($warning.Detail)" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "Next safe commands" -ForegroundColor DarkGreen
    Write-Host "  axiom-registry" -ForegroundColor Gray
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
