# ============================================================
# AXIOM Terminal Operator UI Helpers
# File: C:\axiom\ui\terminal\modules\39-operator-ui.ps1
#
# Purpose:
#   Small shared formatting helpers for operator-facing panels.
#
# Boundary:
#   This module only writes terminal UI text. It must not mutate
#   AXIOM runtime state or call runtime tools.
# ============================================================

function Write-AxiomUiTitle {
    param([Parameter(Mandatory = $true)][string]$Title)

    Write-Host ""
    Write-Host $Title -ForegroundColor Green
    Write-Host ("=" * $Title.Length) -ForegroundColor Green
    Write-Host ""
}

function Write-AxiomUiSection {
    param([Parameter(Mandatory = $true)][string]$Title)

    Write-Host ""
    Write-Host $Title -ForegroundColor DarkGreen
}

function Write-AxiomUiLine {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [AllowEmptyString()][string]$Value,
        [string]$Color = "Gray",
        [int]$Width = 28
    )

    Write-Host ("  {0,-$Width}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Get-AxiomUiStatusColor {
    param([string]$Status)

    switch ($Status) {
        "PASS" { return "Green" }
        "READY" { return "Green" }
        "OK" { return "Green" }
        "INFO" { return "Cyan" }
        "WARN" { return "Yellow" }
        "BLOCK" { return "Red" }
        "FAIL" { return "Red" }
        default { return "Gray" }
    }
}

function Write-AxiomUiStatus {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Label,
        [AllowEmptyString()][string]$Detail = "",
        [int]$Width = 32
    )

    $color = Get-AxiomUiStatusColor -Status $Status
    Write-Host ("  [{0,-5}] " -f $Status) -NoNewline -ForegroundColor $color
    Write-Host ("{0,-$Width}" -f $Label) -NoNewline -ForegroundColor Gray
    Write-Host $Detail -ForegroundColor DarkGray
}

