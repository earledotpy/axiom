# ============================================================
# AXIOM Terminal Registry Discipline
# File: C:\axiom\ui\terminal\modules\42-registry-discipline.ps1
#
# Purpose:
#   Validate AXIOM Terminal command registry coherence.
#
# Boundary:
#   Read-only terminal self-audit.
#   Does not mutate AXIOM runtime state.
#   Does not query AXIOM database.
#   Does not execute scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomTerminalRegistryPath = Join-Path $script:AxiomRoot "ui\terminal\registry\axiom-terminal-command-registry.json"

function New-AxiomRegistryCheck {
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

function Write-AxiomRegistryCheck {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Check
    )

    $status = if ($Check.Passed) { "PASS" } else { "FAIL" }
    $color = if ($Check.Passed) { "Green" } elseif ($Check.Severity -eq "warning") { "Yellow" } else { "Red" }

    Write-Host ("  [{0,-4}] " -f $status) -NoNewline -ForegroundColor $color
    Write-Host ("{0,-36}" -f $Check.Name) -NoNewline -ForegroundColor Gray
    Write-Host $Check.Detail -ForegroundColor DarkGray
}

function Get-AxiomTerminalRegistry {
    if (-not (Test-Path $script:AxiomTerminalRegistryPath)) {
        return $null
    }

    try {
        return Get-Content $script:AxiomTerminalRegistryPath -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Test-AxiomCommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue

    if ($cmd) {
        return $true
    }

    return $false
}

function Test-AxiomRegistryCommandShape {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Command
    )

    $missing = New-Object System.Collections.Generic.List[string]

    foreach ($field in @("name", "category", "primary", "mutates_axiom_runtime", "risk", "description")) {
        if (-not ($Command.PSObject.Properties.Name -contains $field)) {
            $missing.Add($field)
        }
    }

    if ($missing.Count -gt 0) {
        return @{
            passed = $false
            detail = "missing: $($missing -join ', ')"
        }
    }

    return @{
        passed = $true
        detail = "shape-ok"
    }
}

function Test-AxiomTerminalRegistry {
    $checks = New-Object System.Collections.Generic.List[object]

    $registryPathExists = Test-Path $script:AxiomTerminalRegistryPath
    $checks.Add((New-AxiomRegistryCheck "registry file exists" $registryPathExists $script:AxiomTerminalRegistryPath))

    if (-not $registryPathExists) {
        return $checks
    }

    $registry = Get-AxiomTerminalRegistry
    $checks.Add((New-AxiomRegistryCheck "registry JSON parses" ($null -ne $registry) "ConvertFrom-Json"))

    if (-not $registry) {
        return $checks
    }

    $schemaOk = ($registry.schema_version -eq "axiom.terminal.command_registry.v1")
    $checks.Add((New-AxiomRegistryCheck "schema version" $schemaOk ([string]$registry.schema_version)))

    $commands = @($registry.commands)
    $checks.Add((New-AxiomRegistryCheck "commands array present" ($commands.Count -gt 0) "count=$($commands.Count)"))

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

    $allowedStatuses = @(
        "",
        "implemented",
        "planned",
        "planned_next",
        "deprecated",
        "hidden"
    )

    $names = @()
    foreach ($cmd in $commands) {
        if ($cmd.name) {
            $names += [string]$cmd.name
        }
    }

    $duplicateNames = @(
        $names |
            Group-Object |
            Where-Object { $_.Count -gt 1 } |
            ForEach-Object { $_.Name }
    )

    $checks.Add((New-AxiomRegistryCheck "unique command names" ($duplicateNames.Count -eq 0) $(if ($duplicateNames.Count -eq 0) { "ok" } else { $duplicateNames -join ", " })))

    foreach ($cmd in $commands) {
        $name = [string]$cmd.name

        if ([string]::IsNullOrWhiteSpace($name)) {
            $checks.Add((New-AxiomRegistryCheck "command name" $false "blank command name"))
            continue
        }

        $shape = Test-AxiomRegistryCommandShape -Command $cmd
        $checks.Add((New-AxiomRegistryCheck "shape: $name" ([bool]$shape.passed) ([string]$shape.detail)))

        if ($cmd.category) {
            $categoryOk = $allowedCategories -contains [string]$cmd.category
            $checks.Add((New-AxiomRegistryCheck "category: $name" $categoryOk ([string]$cmd.category)))
        }

        if ($cmd.risk) {
            $riskOk = $allowedRisks -contains [string]$cmd.risk
            $checks.Add((New-AxiomRegistryCheck "risk: $name" $riskOk ([string]$cmd.risk)))
        }

        $status = ""
        if ($cmd.PSObject.Properties.Name -contains "status") {
            $status = [string]$cmd.status
        }

        $statusOk = $allowedStatuses -contains $status
        $checks.Add((New-AxiomRegistryCheck "status: $name" $statusOk $(if ($status) { $status } else { "implicit-implemented" })))

        $isPlanned = $status -in @("planned", "planned_next")
        $isDeprecated = $status -eq "deprecated"
        $isHidden = $status -eq "hidden"

        $shouldExist = -not $isPlanned -and -not $isDeprecated -and -not $isHidden

        if ($shouldExist) {
            $exists = Test-AxiomCommandExists -Name $name
            $checks.Add((New-AxiomRegistryCheck "loaded command: $name" $exists $(if ($exists) { "Get-Command ok" } else { "missing from current shell" })))
        }
        else {
            $checks.Add((New-AxiomRegistryCheck "loaded command: $name" $true "not required for status=$status" "warning"))
        }

        if ($cmd.mutates_axiom_runtime -eq $true) {
            $hasBackingTool = ($cmd.PSObject.Properties.Name -contains "backing_tools") -and (@($cmd.backing_tools).Count -gt 0)
            $checks.Add((New-AxiomRegistryCheck "runtime mutation gate: $name" $hasBackingTool "state-changing commands require approved backing tools"))
        }
    }

    $aliases = @($registry.compatibility_aliases)
    foreach ($alias in $aliases) {
        $aliasName = [string]$alias.name
        $prefer = [string]$alias.prefer

        if ([string]::IsNullOrWhiteSpace($aliasName)) {
            $checks.Add((New-AxiomRegistryCheck "alias name" $false "blank alias name"))
            continue
        }

        $preferKnown = $names -contains $prefer
        $checks.Add((New-AxiomRegistryCheck "alias target: $aliasName" $preferKnown "prefer=$prefer"))

        $aliasExists = Test-AxiomCommandExists -Name $aliasName
        $checks.Add((New-AxiomRegistryCheck "alias loaded: $aliasName" $aliasExists $(if ($aliasExists) { "Get-Command ok" } else { "not loaded" }) "warning"))
    }

    $blocked = @($registry.blocked_direct_shortcuts)
    $checks.Add((New-AxiomRegistryCheck "blocked shortcuts documented" ($blocked.Count -gt 0) "count=$($blocked.Count)"))

    foreach ($blockedItem in $blocked) {
        $blockedName = [string]$blockedItem.name
        $blockedReason = [string]$blockedItem.reason

        $nameOk = -not [string]::IsNullOrWhiteSpace($blockedName)
        $reasonOk = -not [string]::IsNullOrWhiteSpace($blockedReason)

        $checks.Add((New-AxiomRegistryCheck "blocked shortcut: $blockedName" ($nameOk -and $reasonOk) $(if ($reasonOk) { "reason documented" } else { "missing reason" })))
    }

    return $checks
}

function axiom-registry {
    Write-Host ""
    Write-Host "AXIOM TERMINAL REGISTRY AUDIT" -ForegroundColor Green
    Write-Host "=============================" -ForegroundColor Green
    Write-Host ""

    $checks = @(Test-AxiomTerminalRegistry)

    foreach ($check in $checks) {
        Write-AxiomRegistryCheck $check
    }

    $failures = @($checks | Where-Object { -not $_.Passed -and $_.Severity -ne "warning" })
    $warnings = @($checks | Where-Object { -not $_.Passed -and $_.Severity -eq "warning" })

    Write-Host ""

    if ($failures.Count -eq 0) {
        Write-Host "Registry discipline: PASS" -ForegroundColor Green
    }
    else {
        Write-Host "Registry discipline: FAIL" -ForegroundColor Red
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
}

function axiom-registry-check {
    axiom-registry
}
