# ============================================================
# AXIOM Terminal Changelog
# File: C:\axiom\ui\terminal\modules\51-changelog.ps1
#
# Purpose:
#   Terminal-suite changelog and update-note discipline.
#
# Boundary:
#   This module may read and append to AXIOM Terminal docs only.
#   It must not mutate AXIOM runtime state.
#   It must not touch AXIOM database, scheduler, model profiles,
#   manifests, safe-pass, tasks, gateways, or runtime tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomTerminalDocsRoot = Join-Path $script:AxiomTerminalRoot "docs"
$script:AxiomTerminalChangelogPath = Join-Path $script:AxiomTerminalDocsRoot "AXIOM_TERMINAL_CHANGELOG.md"

function Initialize-AxiomTerminalChangelog {
    New-Item -ItemType Directory -Force $script:AxiomTerminalDocsRoot | Out-Null

    if (-not (Test-Path $script:AxiomTerminalChangelogPath)) {
        @"
# AXIOM Terminal Changelog

Purpose: track AXIOM Terminal suite changes separately from AXIOM runtime implementation.

Boundary: this changelog describes terminal UI/operator-surface changes only. Runtime state changes, model trust, safe-pass, scheduler behavior, manifests, and task lifecycle changes belong in AXIOM runtime handoff/snapshot artifacts.

## Notes

"@ | Set-Content -Path $script:AxiomTerminalChangelogPath -Encoding UTF8
    }
}

function Write-AxiomTerminalChangelogLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-28}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function axiom-terminal-changelog {
    param(
        [int]$Tail = 80
    )

    Initialize-AxiomTerminalChangelog

    Write-Host ""
    Write-Host "AXIOM TERMINAL CHANGELOG" -ForegroundColor Green
    Write-Host "========================" -ForegroundColor Green
    Write-Host ""

    Write-AxiomTerminalChangelogLine "path" $script:AxiomTerminalChangelogPath "Gray"
    Write-AxiomTerminalChangelogLine "mode" "terminal documentation only" "Yellow"
    Write-AxiomTerminalChangelogLine "runtime mutation" "none" "Green"
    Write-Host ""

    if (-not (Test-Path $script:AxiomTerminalChangelogPath)) {
        Write-Host "  changelog missing" -ForegroundColor Red
        Write-Host ""
        return
    }

    Write-Host "Recent entries" -ForegroundColor DarkGreen
    Write-Host ""

    Get-Content $script:AxiomTerminalChangelogPath -Tail $Tail | ForEach-Object {
        Write-Host $_ -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "Commands" -ForegroundColor DarkGreen
    Write-Host "  axiom-terminal-note `"note text`"       Append timestamped terminal note" -ForegroundColor Gray
    Write-Host "  axiom-edit ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md" -ForegroundColor Gray
    Write-Host ""
}

function axiom-terminal-note {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Note,

        [string]$Category = "terminal"
    )

    Initialize-AxiomTerminalChangelog

    if ([string]::IsNullOrWhiteSpace($Note)) {
        Write-Host "[AXIOM] Refusing blank changelog note." -ForegroundColor Red
        return
    }

    $stamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

    $entry = @"

## $stamp - $Category

$Note

"@

    Add-Content -Path $script:AxiomTerminalChangelogPath -Value $entry -Encoding UTF8

    Write-Host ""
    Write-Host "AXIOM Terminal changelog updated." -ForegroundColor Green
    Write-AxiomTerminalChangelogLine "path" $script:AxiomTerminalChangelogPath "Gray"
    Write-AxiomTerminalChangelogLine "category" $Category "Gray"
    Write-AxiomTerminalChangelogLine "runtime mutation" "none" "Green"
    Write-Host ""
}

function axiom-terminal-changelog-path {
    Initialize-AxiomTerminalChangelog
    Write-Host $script:AxiomTerminalChangelogPath -ForegroundColor Green
}

