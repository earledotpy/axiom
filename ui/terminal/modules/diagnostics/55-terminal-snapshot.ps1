# ============================================================
# AXIOM Terminal Snapshot
# File: C:\axiom\ui\terminal\modules\55-terminal-snapshot.ps1
#
# Purpose:
#   Saved AXIOM Terminal suite state artifact.
#
# Boundary:
#   This module snapshots terminal/UI/operator-surface state only.
#   It must not mutate AXIOM runtime state.
#   It must not query or write AXIOM runtime database tables.
#   It must not call scheduler/executor/model/network/sandbox tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomTerminalSnapshotPaths = [ordered]@{
    Root = $script:AxiomRoot
    TerminalRoot = $script:AxiomTerminalRoot
    Profile = (Join-Path $script:AxiomTerminalRoot "profile\profile-axiom.ps1")
    Modules = (Join-Path $script:AxiomTerminalRoot "modules")
    Registry = (Join-Path $script:AxiomTerminalRoot "registry\axiom-terminal-command-registry.json")
    VisualConfig = (Join-Path $script:AxiomTerminalRoot "profile\visual-mode.json")
    Docs = (Join-Path $script:AxiomTerminalRoot "docs")
    Changelog = (Join-Path $script:AxiomTerminalRoot "docs\AXIOM_TERMINAL_CHANGELOG.md")
    Themes = (Join-Path $script:AxiomTerminalRoot "themes")
    Assets = (Join-Path $script:AxiomTerminalRoot "assets")
    TerminalSettings = (Join-Path $script:AxiomTerminalRoot "terminal")
    Editor = (Join-Path $script:AxiomTerminalRoot "editor")
    SnapshotDir = (Join-Path $script:AxiomRoot "logs\terminal_snapshots")
}

function Test-AxiomTerminalSnapshotModuleParse {
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
            return [pscustomobject]@{
                parse_ok = $false
                error = ($errors | Select-Object -First 1).Message
            }
        }

        return [pscustomobject]@{
            parse_ok = $true
            error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            parse_ok = $false
            error = $_.Exception.Message
        }
    }
}

function Get-AxiomTerminalSnapshotRegistry {
    $path = $script:AxiomTerminalSnapshotPaths.Registry

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

function Get-AxiomTerminalSnapshotVisualConfig {
    $path = $script:AxiomTerminalSnapshotPaths.VisualConfig

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

function Get-AxiomTerminalSnapshotFileState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return [pscustomobject]@{
            path = $Path
            exists = $false
            type = $null
            length = $null
            last_write_time = $null
        }
    }

    $item = Get-Item $Path

    return [pscustomobject]@{
        path = $Path
        exists = $true
        type = $(if ($item.PSIsContainer) { "directory" } else { "file" })
        length = $(if ($item.PSIsContainer) { $null } else { $item.Length })
        last_write_time = $item.LastWriteTime.ToString("o")
    }
}

function Get-AxiomTerminalSnapshotModules {
    $moduleDir = $script:AxiomTerminalSnapshotPaths.Modules

    if (-not (Test-Path $moduleDir)) {
        return @()
    }

    $modules = @(Get-ChildItem $moduleDir -Filter "*.ps1" | Sort-Object Name)
    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($module in $modules) {
        $parse = Test-AxiomTerminalSnapshotModuleParse -Path $module.FullName

        $rows.Add([pscustomobject]@{
            name = $module.Name
            path = $module.FullName
            length = $module.Length
            last_write_time = $module.LastWriteTime.ToString("o")
            parse_ok = $parse.parse_ok
            parse_error = $parse.error
        }) | Out-Null
    }

    return $rows.ToArray()
}

function Get-AxiomTerminalSnapshotCommands {
    $registry = Get-AxiomTerminalSnapshotRegistry

    if (-not $registry) {
        return @()
    }

    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($cmd in @($registry.commands)) {
        $name = [string]$cmd.name
        $loaded = $null -ne (Get-Command $name -ErrorAction SilentlyContinue)

        $status = "implemented"
        if ($cmd.PSObject.Properties.Name -contains "status" -and -not [string]::IsNullOrWhiteSpace([string]$cmd.status)) {
            $status = [string]$cmd.status
        }

        $rows.Add([pscustomobject]@{
            name = $name
            category = [string]$cmd.category
            primary = [bool]$cmd.primary
            risk = [string]$cmd.risk
            status = $status
            mutates_axiom_runtime = [bool]$cmd.mutates_axiom_runtime
            loaded = $loaded
            description = [string]$cmd.description
        }) | Out-Null
    }

    return $rows.ToArray()
}

function Get-AxiomTerminalSnapshotDocs {
    $docsDir = $script:AxiomTerminalSnapshotPaths.Docs

    if (-not (Test-Path $docsDir)) {
        return @()
    }

    $docs = @(Get-ChildItem $docsDir -File -Recurse | Sort-Object FullName)
    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($doc in $docs) {
        $relative = $doc.FullName.Replace($script:AxiomRoot, "").TrimStart("\")
        $rows.Add([pscustomobject]@{
            relative_path = $relative
            length = $doc.Length
            last_write_time = $doc.LastWriteTime.ToString("o")
        }) | Out-Null
    }

    return $rows.ToArray()
}

function New-AxiomTerminalSnapshotObject {
    $registry = Get-AxiomTerminalSnapshotRegistry
    $visual = Get-AxiomTerminalSnapshotVisualConfig
    $modules = @(Get-AxiomTerminalSnapshotModules)
    $commands = @(Get-AxiomTerminalSnapshotCommands)
    $docs = @(Get-AxiomTerminalSnapshotDocs)

    $pathStates = New-Object System.Collections.Generic.List[object]
    foreach ($key in $script:AxiomTerminalSnapshotPaths.Keys) {
        if ($key -eq "SnapshotDir") {
            continue
        }

        $pathStates.Add([pscustomobject]@{
            name = $key
            state = Get-AxiomTerminalSnapshotFileState -Path $script:AxiomTerminalSnapshotPaths[$key]
        }) | Out-Null
    }

    $loadedImplementedMissing = @(
        $commands |
            Where-Object {
                $_.status -notin @("planned", "planned_next", "deprecated", "hidden") -and
                $_.loaded -eq $false
            } |
            ForEach-Object { $_.name }
    )

    $parseFailures = @(
        $modules |
            Where-Object { $_.parse_ok -eq $false } |
            ForEach-Object { $_.name }
    )

    [pscustomobject]@{
        schema_version = "axiom.terminal.snapshot.v1"
        generated_at = (Get-Date -Format o)
        axiom_root = $script:AxiomRoot
        terminal_root = $script:AxiomTerminalRoot
        boundary = "Terminal suite snapshot only; no AXIOM runtime mutation."
        environment = [pscustomobject]@{
            profile_mode = $env:AXIOM_PROFILE_MODE
            prompt_engine = $env:AXIOM_PROMPT_ENGINE
            startup_banner = $env:AXIOM_STARTUP_BANNER
            theme_name = $env:AXIOM_THEME_NAME
            ps_version = $PSVersionTable.PSVersion.ToString()
        }
        paths = $pathStates.ToArray()
        visual_config = $visual
        registry = [pscustomobject]@{
            present = $null -ne $registry
            schema_version = $(if ($registry) { [string]$registry.schema_version } else { $null })
            command_count = $commands.Count
            implemented_count = @($commands | Where-Object { $_.status -eq "implemented" }).Count
            planned_count = @($commands | Where-Object { $_.status -eq "planned" }).Count
            planned_next_count = @($commands | Where-Object { $_.status -eq "planned_next" }).Count
            missing_loaded_implemented = $loadedImplementedMissing
        }
        modules = [pscustomobject]@{
            count = $modules.Count
            parse_failure_count = $parseFailures.Count
            parse_failures = $parseFailures
            items = $modules
        }
        commands = $commands
        docs = [pscustomobject]@{
            count = $docs.Count
            items = $docs
        }
    }
}

function Convert-AxiomTerminalSnapshotToMarkdown {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Snapshot
    )

    $lines = New-Object System.Collections.Generic.List[string]

    $lines.Add("# AXIOM Terminal Snapshot")
    $lines.Add("")
    $lines.Add("Generated: $($Snapshot.generated_at)")
    $lines.Add("")
    $lines.Add("Boundary: $($Snapshot.boundary)")
    $lines.Add("")
    $lines.Add("## Environment")
    $lines.Add("")
    $lines.Add("- AXIOM root: $($Snapshot.axiom_root)")
    $lines.Add("- Terminal root: $($Snapshot.terminal_root)")
    $lines.Add("- Profile mode: $($Snapshot.environment.profile_mode)")
    $lines.Add("- Prompt engine: $($Snapshot.environment.prompt_engine)")
    $lines.Add("- Startup banner: $($Snapshot.environment.startup_banner)")
    $lines.Add("- Theme name: $($Snapshot.environment.theme_name)")
    $lines.Add("- PowerShell: $($Snapshot.environment.ps_version)")
    $lines.Add("")

    $lines.Add("## Registry")
    $lines.Add("")
    $lines.Add("- Present: $($Snapshot.registry.present)")
    $lines.Add("- Schema version: $($Snapshot.registry.schema_version)")
    $lines.Add("- Command count: $($Snapshot.registry.command_count)")
    $lines.Add("- Implemented: $($Snapshot.registry.implemented_count)")
    $lines.Add("- Planned: $($Snapshot.registry.planned_count)")
    $lines.Add("- Planned next: $($Snapshot.registry.planned_next_count)")
    $lines.Add("")

    if ($Snapshot.registry.missing_loaded_implemented.Count -gt 0) {
        $lines.Add("### Missing loaded implemented commands")
        $lines.Add("")
        foreach ($name in $Snapshot.registry.missing_loaded_implemented) {
            $lines.Add("- $name")
        }
        $lines.Add("")
    }

    $lines.Add("## Modules")
    $lines.Add("")
    $lines.Add("- Count: $($Snapshot.modules.count)")
    $lines.Add("- Parse failure count: $($Snapshot.modules.parse_failure_count)")
    $lines.Add("")

    foreach ($module in $Snapshot.modules.items) {
        $state = if ($module.parse_ok) { "ok" } else { "parse-failed" }
        $lines.Add("- $($module.name) — $state")
        if (-not $module.parse_ok) {
            $lines.Add("  - Error: $($module.parse_error)")
        }
    }

    $lines.Add("")
    $lines.Add("## Commands")
    $lines.Add("")

    $groups = @($Snapshot.commands | Group-Object category | Sort-Object Name)

    foreach ($group in $groups) {
        $lines.Add("### $($group.Name)")
        $lines.Add("")

        foreach ($cmd in @($group.Group | Sort-Object name)) {
            $loaded = if ($cmd.loaded) { "loaded" } else { "missing" }
            $lines.Add("- $($cmd.name) — $($cmd.status), $loaded, risk=$($cmd.risk), mutates_runtime=$($cmd.mutates_axiom_runtime)")
        }

        $lines.Add("")
    }

    $lines.Add("## Docs")
    $lines.Add("")
    $lines.Add("- Count: $($Snapshot.docs.count)")
    $lines.Add("")

    foreach ($doc in $Snapshot.docs.items) {
        $lines.Add("- $($doc.relative_path)")
    }

    $lines.Add("")
    $lines.Add("## Next checks")
    $lines.Add("")
    $lines.Add("Run:")
    $lines.Add("")
    $lines.Add('```powershell')
    $lines.Add("axiom-terminal-test")
    $lines.Add("axiom-doctor")
    $lines.Add("axiom-registry")
    $lines.Add("axiom-preflight")
    $lines.Add('```')
    $lines.Add("")

    return ($lines -join [Environment]::NewLine)
}

function Write-AxiomTerminalSnapshotLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function axiom-terminal-snapshot {
    $snapshot = New-AxiomTerminalSnapshotObject

    $dir = $script:AxiomTerminalSnapshotPaths.SnapshotDir
    New-Item -ItemType Directory -Force $dir | Out-Null

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $jsonPath = Join-Path $dir "axiom_terminal_snapshot_$stamp.json"
    $mdPath = Join-Path $dir "axiom_terminal_snapshot_$stamp.md"

    $snapshot | ConvertTo-Json -Depth 30 | Set-Content $jsonPath -Encoding UTF8
    Convert-AxiomTerminalSnapshotToMarkdown -Snapshot $snapshot | Set-Content $mdPath -Encoding UTF8

    Write-Host ""
    Write-Host "AXIOM TERMINAL SNAPSHOT" -ForegroundColor Green
    Write-Host "=======================" -ForegroundColor Green
    Write-Host ""

    Write-AxiomTerminalSnapshotLine "json" $jsonPath "Green"
    Write-AxiomTerminalSnapshotLine "markdown" $mdPath "Green"
    Write-AxiomTerminalSnapshotLine "module count" ([string]$snapshot.modules.count) "Gray"
    Write-AxiomTerminalSnapshotLine "parse failures" ([string]$snapshot.modules.parse_failure_count) $(if ($snapshot.modules.parse_failure_count -eq 0) { "Green" } else { "Red" })
    Write-AxiomTerminalSnapshotLine "command count" ([string]$snapshot.registry.command_count) "Gray"
    Write-AxiomTerminalSnapshotLine "missing implemented" ([string]$snapshot.registry.missing_loaded_implemented.Count) $(if ($snapshot.registry.missing_loaded_implemented.Count -eq 0) { "Green" } else { "Red" })
    Write-Host ""

    Write-Host "Boundary" -ForegroundColor DarkGreen
    Write-Host "  Terminal snapshot only. AXIOM runtime state was not mutated." -ForegroundColor Gray
    Write-Host ""
}

