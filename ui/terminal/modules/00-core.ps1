# AXIOM Terminal core helpers

function Test-AxiomRoot {
    if (-not (Test-Path $env:AXIOM_ROOT)) {
        Write-Host "[AXIOM] Missing root: $env:AXIOM_ROOT" -ForegroundColor Red
        return $false
    }
    return $true
}

function Test-AxiomVenv {
    $venv = Join-Path $env:AXIOM_ROOT 'venv\Scripts\Activate.ps1'
    if (-not (Test-Path $venv)) {
        Write-Host "[AXIOM] Missing venv activation script: $venv" -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Invoke-AxiomVenv {
    if (Test-AxiomVenv) {
        . (Join-Path $env:AXIOM_ROOT 'venv\Scripts\Activate.ps1')
        return $true
    }
    return $false
}

function Invoke-AxiomPython {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    if (-not (Test-AxiomRoot)) { return }
    Push-Location $env:AXIOM_ROOT
    try {
        Invoke-AxiomVenv | Out-Null
        & python @Arguments
    }
    finally { Pop-Location }
}

function Invoke-AxiomPythonCapture {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    if (-not (Test-AxiomRoot)) { return $null }
    Push-Location $env:AXIOM_ROOT
    try {
        Invoke-AxiomVenv | Out-Null
        $output = & python @Arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[AXIOM] Python command failed." -ForegroundColor Red
            $output | ForEach-Object { Write-Host $_ }
            return $null
        }
        return (($output | Out-String).Trim())
    }
    finally { Pop-Location }
}

function Get-AxiomTimestamp {
    return (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
}

function Get-AxiomLatestSessionId {
    $dbPath = Join-Path $env:AXIOM_ROOT 'axiom.db'
    if (-not (Test-Path $dbPath)) {
        Write-Host "[AXIOM] Database not found: $dbPath" -ForegroundColor Red
        return $null
    }

    $code = @'
import os
import sqlite3
from pathlib import Path

db = Path(os.environ.get("AXIOM_DB_PATH", r"C:\axiom\axiom.db"))
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
try:
    row = conn.execute("SELECT session_id FROM sessions ORDER BY session_id DESC LIMIT 1").fetchone()
    print(row[0] if row else "")
finally:
    conn.close()
'@

    $sessionId = Invoke-AxiomPythonCapture @('-c', $code)
    if ([string]::IsNullOrWhiteSpace($sessionId)) { return $null }
    return $sessionId.Trim()
}

function Enter-Axiom {
    if (-not (Test-AxiomRoot)) { return }
    Set-Location $env:AXIOM_ROOT
    Invoke-AxiomVenv | Out-Null
    Write-Host ""
    Write-Host "AXIOM operator console attached." -ForegroundColor Green
    Write-Host "root: $env:AXIOM_ROOT" -ForegroundColor DarkGreen
    Write-Host "mode: $env:AXIOM_PROFILE_MODE" -ForegroundColor DarkGreen
    Write-Host ""
}

function axiom { Enter-Axiom }
function axiom-home { Enter-Axiom }
function axiom-root { Write-Host $env:AXIOM_ROOT -ForegroundColor Green }
function axiom-terminal-root { Write-Host $env:AXIOM_TERMINAL_ROOT -ForegroundColor Green }
function axiom-venv { Invoke-AxiomVenv | Out-Null }

function axiom-refresh { . $PROFILE }
