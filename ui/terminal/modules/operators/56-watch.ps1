# ============================================================
# AXIOM Terminal Watch
# File: C:\axiom\ui\terminal\modules\56-watch.ps1
#
# Purpose:
#   Foreground read-only refresh panel for AXIOM Terminal.
#
# Boundary:
#   This module may call read-only AXIOM Terminal panels.
#   It must not mutate AXIOM runtime state.
#   It must not call scheduler/executor/model/network/sandbox tools.
#   It must not run axiom-preflight automatically.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

function Test-AxiomWatchCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Write-AxiomWatchHeader {
    param(
        [string]$Mode,
        [int]$IntervalSeconds,
        [int]$Iteration,
        [int]$MaxIterations
    )

    Clear-Host

    Write-Host "AXIOM WATCH" -ForegroundColor Green
    Write-Host "===========" -ForegroundColor Green
    Write-Host ""
    Write-Host "  mode:        $Mode" -ForegroundColor Gray
    Write-Host "  interval:    $IntervalSeconds seconds" -ForegroundColor Gray

    if ($MaxIterations -gt 0) {
        Write-Host "  iteration:   $Iteration / $MaxIterations" -ForegroundColor Gray
    }
    else {
        Write-Host "  iteration:   $Iteration / continuous" -ForegroundColor Gray
    }

    Write-Host "  boundary:    read-only terminal panels only" -ForegroundColor Yellow
    Write-Host "  stop:        Ctrl+C" -ForegroundColor DarkGray
    Write-Host ""
}

function Invoke-AxiomWatchPanel {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Mode
    )

    switch ($Mode) {
        "dashboard" {
            if (Test-AxiomWatchCommand "axiom-dashboard") {
                axiom-dashboard
            }
            else {
                Write-Host "axiom-dashboard is not loaded." -ForegroundColor Red
            }
        }

        "readiness" {
            if (Test-AxiomWatchCommand "axiom-readiness") {
                axiom-readiness
            }
            else {
                Write-Host "axiom-readiness is not loaded." -ForegroundColor Red
            }
        }

        "queue" {
            if (Test-AxiomWatchCommand "axiom-queue") {
                axiom-queue
            }
            else {
                Write-Host "axiom-queue is not loaded." -ForegroundColor Red
            }
        }

        "events" {
            if (Test-AxiomWatchCommand "axiom-events") {
                axiom-events
            }
            else {
                Write-Host "axiom-events is not loaded." -ForegroundColor Red
            }
        }

        "compact" {
            if (Test-AxiomWatchCommand "axiom-dashboard") {
                axiom-dashboard
            }

            if (Test-AxiomWatchCommand "axiom-readiness") {
                axiom-readiness
            }
        }

        "ops" {
            if (Test-AxiomWatchCommand "axiom-dashboard") {
                axiom-dashboard
            }

            if (Test-AxiomWatchCommand "axiom-readiness") {
                axiom-readiness
            }

            if (Test-AxiomWatchCommand "axiom-queue") {
                axiom-queue
            }

            if (Test-AxiomWatchCommand "axiom-events") {
                axiom-events
            }
        }

        default {
            Write-Host "Unknown watch mode: $Mode" -ForegroundColor Red
            Write-Host ""
            Write-Host "Allowed modes:" -ForegroundColor DarkGreen
            Write-Host "  dashboard" -ForegroundColor Gray
            Write-Host "  readiness" -ForegroundColor Gray
            Write-Host "  queue" -ForegroundColor Gray
            Write-Host "  events" -ForegroundColor Gray
            Write-Host "  compact" -ForegroundColor Gray
            Write-Host "  ops" -ForegroundColor Gray
        }
    }
}

function axiom-watch {
    param(
        [ValidateSet("dashboard", "readiness", "queue", "events", "compact", "ops")]
        [string]$Mode = "compact",

        [ValidateRange(2, 3600)]
        [int]$IntervalSeconds = 10,

        [ValidateRange(0, 10000)]
        [int]$MaxIterations = 0
    )

    Write-Host ""
    Write-Host "Starting AXIOM watch. Press Ctrl+C to stop." -ForegroundColor Green
    Write-Host "Mode: $Mode | Interval: $IntervalSeconds seconds | Read-only." -ForegroundColor Gray
    Start-Sleep -Milliseconds 700

    $iteration = 0

    try {
        while ($true) {
            $iteration++

            Write-AxiomWatchHeader `
                -Mode $Mode `
                -IntervalSeconds $IntervalSeconds `
                -Iteration $iteration `
                -MaxIterations $MaxIterations

            Invoke-AxiomWatchPanel -Mode $Mode

            if ($MaxIterations -gt 0 -and $iteration -ge $MaxIterations) {
                Write-Host ""
                Write-Host "AXIOM watch completed requested iterations." -ForegroundColor Green
                Write-Host ""
                break
            }

            Write-Host ""
            Write-Host "Refreshing in $IntervalSeconds seconds. Press Ctrl+C to stop." -ForegroundColor DarkGray
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        Write-Host ""
        Write-Host "AXIOM watch stopped." -ForegroundColor Yellow
        Write-Host ""
    }
    catch {
        Write-Host ""
        Write-Host "AXIOM watch stopped by error:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host ""
    }
}

function axiom-watch-once {
    param(
        [ValidateSet("dashboard", "readiness", "queue", "events", "compact", "ops")]
        [string]$Mode = "compact"
    )

    Write-AxiomWatchHeader `
        -Mode $Mode `
        -IntervalSeconds 0 `
        -Iteration 1 `
        -MaxIterations 1

    Invoke-AxiomWatchPanel -Mode $Mode
}

function axiom-watch-help {
    Write-Host ""
    Write-Host "AXIOM WATCH HELP" -ForegroundColor Green
    Write-Host "================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor DarkGreen
    Write-Host "  axiom-watch" -ForegroundColor Gray
    Write-Host "  axiom-watch -Mode dashboard -IntervalSeconds 10" -ForegroundColor Gray
    Write-Host "  axiom-watch -Mode ops -IntervalSeconds 15" -ForegroundColor Gray
    Write-Host "  axiom-watch -Mode queue -IntervalSeconds 5 -MaxIterations 6" -ForegroundColor Gray
    Write-Host "  axiom-watch-once -Mode ops" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Modes:" -ForegroundColor DarkGreen
    Write-Host "  dashboard    axiom-dashboard only" -ForegroundColor Gray
    Write-Host "  readiness    axiom-readiness only" -ForegroundColor Gray
    Write-Host "  queue        axiom-queue only" -ForegroundColor Gray
    Write-Host "  events       axiom-events only" -ForegroundColor Gray
    Write-Host "  compact      dashboard + readiness" -ForegroundColor Gray
    Write-Host "  ops          dashboard + readiness + queue + events" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Boundary:" -ForegroundColor DarkGreen
    Write-Host "  Watch calls read-only terminal panels only." -ForegroundColor Gray
    Write-Host "  It does not run axiom-preflight automatically." -ForegroundColor Gray
    Write-Host "  It does not dispatch, execute, repair, promote, register, or mutate runtime state." -ForegroundColor Gray
    Write-Host ""
}
