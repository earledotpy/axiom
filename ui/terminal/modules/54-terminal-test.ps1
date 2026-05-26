# ============================================================
# AXIOM Terminal Test
# File: C:\axiom\ui\terminal\modules\54-terminal-test.ps1
#
# Purpose:
#   Terminal-suite regression check.
#
# Boundary:
#   This module tests AXIOM Terminal loadability and command surface.
#   It must not mutate AXIOM runtime state.
#   It must not query or write AXIOM database.
#   It must not call scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomTerminalTestPaths = [ordered]@{
    Root = $script:AxiomRoot
    TerminalRoot = $script:AxiomTerminalRoot
    Profile = (Join-Path $script:AxiomTerminalRoot "profile\profile-axiom.ps1")
    Modules = (Join-Path $script:AxiomTerminalRoot "modules")
    Registry = (Join-Path $script:AxiomTerminalRoot "registry\axiom-terminal-command-registry.json")
    VisualConfig = (Join-Path $script:AxiomTerminalRoot "profile\visual-mode.json")
    Docs = (Join-Path $script:AxiomTerminalRoot "docs")
    Changelog = (Join-Path $script:AxiomTerminalRoot "docs\AXIOM_TERMINAL_CHANGELOG.md")
    Themes = (Join-Path $script:AxiomTerminalRoot "themes")
    DashboardTheme = (Join-Path $script:AxiomTerminalRoot "themes\axiom-dashboard.omp.json")
}

function New-AxiomTerminalTestResult {
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

function Write-AxiomTerminalTestResult {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Result
    )

    $status = if ($Result.Passed) { "PASS" } else { "FAIL" }

    $color = if ($Result.Passed) {
        "Green"
    }
    elseif ($Result.Severity -eq "warning") {
        "Yellow"
    }
    else {
        "Red"
    }

    Write-Host ("  [{0,-4}] " -f $status) -NoNewline -ForegroundColor $color
    Write-Host ("{0,-38}" -f $Result.Name) -NoNewline -ForegroundColor Gray
    Write-Host $Result.Detail -ForegroundColor DarkGray
}

function Test-AxiomTerminalPath {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Severity = "required"
    )

    New-AxiomTerminalTestResult `
        -Name "path: $Name" `
        -Passed (Test-Path $Path) `
        -Detail $Path `
        -Severity $Severity
}

function Test-AxiomTerminalCommand {
    param(
        [string]$Name,
        [string]$Severity = "required"
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue

    New-AxiomTerminalTestResult `
        -Name "command: $Name" `
        -Passed ($null -ne $cmd) `
        -Detail $(if ($cmd) { [string]$cmd.CommandType } else { "missing" }) `
        -Severity $Severity
}

function Test-AxiomTerminalModuleParse {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $tokens = $null
    $errors = $null

    try {
        [System.Management.Automation.Language.Parser]::ParseFile(
            $Path,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        if ($errors -and $errors.Count -gt 0) {
            $message = ($errors | Select-Object -First 1).Message

            return New-AxiomTerminalTestResult `
                -Name "parse: $(Split-Path -Leaf $Path)" `
                -Passed $false `
                -Detail $message
        }

        return New-AxiomTerminalTestResult `
            -Name "parse: $(Split-Path -Leaf $Path)" `
            -Passed $true `
            -Detail "syntax-ok"
    }
    catch {
        return New-AxiomTerminalTestResult `
            -Name "parse: $(Split-Path -Leaf $Path)" `
            -Passed $false `
            -Detail $_.Exception.Message
    }
}

function Get-AxiomTerminalTestRegistry {
    $path = $script:AxiomTerminalTestPaths.Registry

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

function Test-AxiomTerminalRegistryShape {
    $results = New-Object System.Collections.Generic.List[object]
    $registryPath = $script:AxiomTerminalTestPaths.Registry

    $exists = Test-Path $registryPath
    $results.Add((New-AxiomTerminalTestResult "registry file exists" $exists $registryPath))

    if (-not $exists) {
        return $results
    }

    $registry = Get-AxiomTerminalTestRegistry
    $results.Add((New-AxiomTerminalTestResult "registry parses" ($null -ne $registry) "ConvertFrom-Json"))

    if (-not $registry) {
        return $results
    }

    $schemaOk = $registry.schema_version -eq "axiom.terminal.command_registry.v1"
    $results.Add((New-AxiomTerminalTestResult "registry schema" $schemaOk ([string]$registry.schema_version)))

    $commands = @($registry.commands)
    $results.Add((New-AxiomTerminalTestResult "registry commands present" ($commands.Count -gt 0) "count=$($commands.Count)"))

    $names = @($commands | ForEach-Object { [string]$_.name })
    $duplicates = @(
        $names |
            Group-Object |
            Where-Object { $_.Count -gt 1 } |
            ForEach-Object { $_.Name }
    )

    $results.Add((New-AxiomTerminalTestResult "registry unique command names" ($duplicates.Count -eq 0) $(if ($duplicates.Count -eq 0) { "ok" } else { $duplicates -join ", " })))

    $allowedCategories = @(
        "core",
        "editing",
        "verification",
        "state_visibility",
        "reports",
        "terminal_ui"
    )

    $allowedRisks = @(
        "low",
        "medium",
        "high",
        "critical"
    )

    foreach ($cmd in $commands) {
        $name = [string]$cmd.name

        if ([string]::IsNullOrWhiteSpace($name)) {
            $results.Add((New-AxiomTerminalTestResult "registry command name" $false "blank name"))
            continue
        }

        foreach ($field in @("name", "category", "primary", "mutates_axiom_runtime", "risk", "description")) {
            $hasField = $cmd.PSObject.Properties.Name -contains $field
            $results.Add((New-AxiomTerminalTestResult "registry field: $name.$field" $hasField $(if ($hasField) { "present" } else { "missing" })))
        }

        if ($cmd.PSObject.Properties.Name -contains "category") {
            $categoryOk = $allowedCategories -contains [string]$cmd.category
            $results.Add((New-AxiomTerminalTestResult "registry category: $name" $categoryOk ([string]$cmd.category)))
        }

        if ($cmd.PSObject.Properties.Name -contains "risk") {
            $riskOk = $allowedRisks -contains [string]$cmd.risk
            $results.Add((New-AxiomTerminalTestResult "registry risk: $name" $riskOk ([string]$cmd.risk)))
        }

        if ($cmd.mutates_axiom_runtime -eq $true) {
            $results.Add((New-AxiomTerminalTestResult "runtime mutation denied: $name" $false "terminal registry should not contain runtime-mutating command"))
        }
    }

    return $results
}

function Test-AxiomTerminalImplementedCommands {
    $results = New-Object System.Collections.Generic.List[object]
    $registry = Get-AxiomTerminalTestRegistry

    if (-not $registry) {
        $results.Add((New-AxiomTerminalTestResult "implemented commands" $false "registry unavailable"))
        return $results
    }

    $commands = @($registry.commands)

    foreach ($cmd in $commands) {
        $status = ""
        if ($cmd.PSObject.Properties.Name -contains "status") {
            $status = [string]$cmd.status
        }

        $isPlanned = $status -in @("planned", "planned_next")
        $isDeprecated = $status -eq "deprecated"
        $isHidden = $status -eq "hidden"

        if (-not $isPlanned -and -not $isDeprecated -and -not $isHidden) {
            $name = [string]$cmd.name
            $exists = Get-Command $name -ErrorAction SilentlyContinue

            $results.Add((New-AxiomTerminalTestResult "loaded implemented: $name" ($null -ne $exists) $(if ($exists) { "loaded" } else { "missing" })))
        }
    }

    return $results
}

function Test-AxiomTerminalModuleOrder {
    $results = New-Object System.Collections.Generic.List[object]
    $moduleDir = $script:AxiomTerminalTestPaths.Modules

    if (-not (Test-Path $moduleDir)) {
        $results.Add((New-AxiomTerminalTestResult "module directory" $false $moduleDir))
        return $results
    }

    $moduleNames = @(
        Get-ChildItem $moduleDir -Filter "*.ps1" |
            Sort-Object Name |
            ForEach-Object { $_.Name }
    )

    $requiredOrder = @(
        "04-visual-mode.ps1",
        "05-visual.ps1",
        "06-oh-my-posh.ps1"
    )

    foreach ($name in $requiredOrder) {
        $results.Add((New-AxiomTerminalTestResult "module present: $name" ($moduleNames -contains $name) $(if ($moduleNames -contains $name) { "present" } else { "missing" })))
    }

    $visualModeIndex = [array]::IndexOf($moduleNames, "04-visual-mode.ps1")
    $visualIndex = [array]::IndexOf($moduleNames, "05-visual.ps1")
    $poshIndex = [array]::IndexOf($moduleNames, "06-oh-my-posh.ps1")

    $orderOk = (
        $visualModeIndex -ge 0 -and
        $visualIndex -ge 0 -and
        $poshIndex -ge 0 -and
        $visualModeIndex -lt $visualIndex -and
        $visualIndex -lt $poshIndex
    )

    $results.Add((New-AxiomTerminalTestResult "visual load order" $orderOk "04 before 05 before 06"))

    $oldVisual = Join-Path $moduleDir "43-visual-mode.ps1"
    $results.Add((New-AxiomTerminalTestResult "old visual module absent" (-not (Test-Path $oldVisual)) "43-visual-mode.ps1 should not remain" "warning"))

    return $results
}

function Test-AxiomTerminalVisualConfig {
    $results = New-Object System.Collections.Generic.List[object]
    $path = $script:AxiomTerminalTestPaths.VisualConfig

    $exists = Test-Path $path
    $results.Add((New-AxiomTerminalTestResult "visual config exists" $exists $path "warning"))

    if (-not $exists) {
        return $results
    }

    try {
        $config = Get-Content $path -Raw | ConvertFrom-Json
        $modeOk = [string]$config.prompt_mode -in @("native", "dashboard")
        $bannerField = $config.PSObject.Properties.Name -contains "startup_banner"
        $themeField = $config.PSObject.Properties.Name -contains "theme"

        $results.Add((New-AxiomTerminalTestResult "visual config parses" $true "ConvertFrom-Json"))
        $results.Add((New-AxiomTerminalTestResult "visual prompt mode" $modeOk ([string]$config.prompt_mode)))
        $results.Add((New-AxiomTerminalTestResult "visual startup_banner field" $bannerField $(if ($bannerField) { [string]$config.startup_banner } else { "missing" })))
        $results.Add((New-AxiomTerminalTestResult "visual theme field" $themeField $(if ($themeField) { [string]$config.theme } else { "missing" })))
    }
    catch {
        $results.Add((New-AxiomTerminalTestResult "visual config parses" $false $_.Exception.Message "warning"))
    }

    return $results
}

function Test-AxiomTerminalUnsafeShortcuts {
    $results = New-Object System.Collections.Generic.List[object]

    $blocked = @(
        "axiom-safe-pass-on",
        "axiom-enable-autonomous",
        "axiom-promote-model",
        "axiom-trust-model",
        "axiom-register-model",
        "axiom-run-scheduler",
        "axiom-run-noop-cycle",
        "axiom-execute-noop",
        "axiom-dispatch",
        "axiom-start-task",
        "axiom-repair-session",
        "axiom-register-manifests"
    )

    foreach ($name in $blocked) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        $results.Add((New-AxiomTerminalTestResult "unsafe absent: $name" ($null -eq $cmd) $(if ($cmd) { "loaded; remove it" } else { "absent" })))
    }

    return $results
}

function Test-AxiomTerminalRequiredCommands {
    $results = New-Object System.Collections.Generic.List[object]

    $required = @(
        "axiom",
        "axiom-help",
        "axiom-help-all",
        "axiom-now",
        "axiom-doctor",
        "axiom-registry",
        "axiom-dashboard",
        "axiom-readiness",
        "axiom-model",
        "axiom-manifests",
        "axiom-budget",
        "axiom-events",
        "axiom-terminal-report",
        "axiom-terminal-changelog",
        "axiom-docs",
        "axiom-system-map"
    )

    foreach ($name in $required) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        $results.Add((New-AxiomTerminalTestResult "required command: $name" ($null -ne $cmd) $(if ($cmd) { "loaded" } else { "missing" })))
    }

    return $results
}

function Invoke-AxiomTerminalTestSuite {
    $results = New-Object System.Collections.Generic.List[object]

    foreach ($key in $script:AxiomTerminalTestPaths.Keys) {
        $severity = if ($key -in @("VisualConfig", "Changelog", "DashboardTheme")) { "warning" } else { "required" }
        $results.Add((Test-AxiomTerminalPath -Name $key -Path $script:AxiomTerminalTestPaths[$key] -Severity $severity))
    }

    $moduleDir = $script:AxiomTerminalTestPaths.Modules
    if (Test-Path $moduleDir) {
        $modules = @(Get-ChildItem $moduleDir -Filter "*.ps1" | Sort-Object Name)

        foreach ($module in $modules) {
            $results.Add((Test-AxiomTerminalModuleParse -Path $module.FullName))
        }
    }

    foreach ($result in (Test-AxiomTerminalModuleOrder)) {
        $results.Add($result)
    }

    foreach ($result in (Test-AxiomTerminalRegistryShape)) {
        $results.Add($result)
    }

    foreach ($result in (Test-AxiomTerminalImplementedCommands)) {
        $results.Add($result)
    }

    foreach ($result in (Test-AxiomTerminalVisualConfig)) {
        $results.Add($result)
    }

    foreach ($result in (Test-AxiomTerminalRequiredCommands)) {
        $results.Add($result)
    }

    foreach ($result in (Test-AxiomTerminalUnsafeShortcuts)) {
        $results.Add($result)
    }

    return $results.ToArray()
}

function axiom-terminal-test {
    param(
        [switch]$Quiet
    )

    if (-not $Quiet) {
        Write-Host ""
        Write-Host "AXIOM TERMINAL TEST" -ForegroundColor Green
        Write-Host "===================" -ForegroundColor Green
        Write-Host ""
    }

    $results = @(Invoke-AxiomTerminalTestSuite)

    if (-not $Quiet) {
        foreach ($result in $results) {
            Write-AxiomTerminalTestResult $result
        }
    }

    $failures = @($results | Where-Object { -not $_.Passed -and $_.Severity -ne "warning" })
    $warnings = @($results | Where-Object { -not $_.Passed -and $_.Severity -eq "warning" })

    if (-not $Quiet) {
        Write-Host ""

        if ($failures.Count -eq 0) {
            Write-Host "Terminal test result: PASS" -ForegroundColor Green
        }
        else {
            Write-Host "Terminal test result: FAIL" -ForegroundColor Red
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
        Write-Host "Boundary" -ForegroundColor DarkGreen
        Write-Host "  This test validates AXIOM Terminal only." -ForegroundColor Gray
        Write-Host "  It does not run AXIOM runtime verification." -ForegroundColor Gray
        Write-Host "  Run axiom-preflight separately for runtime state." -ForegroundColor Gray
        Write-Host ""
    }

    if ($failures.Count -gt 0) {
        return $false
    }

    return $true
}

