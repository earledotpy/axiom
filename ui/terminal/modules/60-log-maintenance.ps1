# ============================================================
# AXIOM Terminal Log Maintenance
# File: C:\axiom\ui\terminal\modules\60-log-maintenance.ps1
#
# Purpose:
#   Terminal wrapper for approved AXIOM log maintenance tools.
#
# Boundary:
#   This module may call approved tools under C:\axiom\tools.
#   It must not mutate AXIOM runtime database state.
#   It must not run automatically from startup, dashboard, watch,
#   doctor, registry, or preflight.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

function axiom-archive-logs {
    $tool = Join-Path $script:AxiomRoot "tools\archive_logs.py"

    if (-not (Test-Path $tool)) {
        Write-Host "[AXIOM] Missing tool: $tool" -ForegroundColor Red
        return
    }

    Write-Host ""
    Write-Host "AXIOM LOG ARCHIVE" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    Write-Host ""
    Write-Host "This will archive older files from C:\axiom\logs into C:\axiom\logs\archive." -ForegroundColor Yellow
    Write-Host "It keeps the newest handoff bundle set and the newest 25 log files." -ForegroundColor Gray
    Write-Host "It deletes archived originals after writing the zip file." -ForegroundColor Yellow
    Write-Host ""

    python $tool
}

function axiom-archive-logs-path {
    $tool = Join-Path $script:AxiomRoot "tools\archive_logs.py"
    Write-Host $tool -ForegroundColor Green
}
