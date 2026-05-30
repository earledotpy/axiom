# AXIOM implementation helpers

function axiom-status { Invoke-AxiomPython @('tools\verify_foundation.py') }

function axiom-audit {
    Write-Host ""
    Write-Host "AXIOM lifecycle audit" -ForegroundColor Green
    Invoke-AxiomPython @('tools\audit_task_lifecycle.py')
    Write-Host ""
    Write-Host "AXIOM execution audit" -ForegroundColor Green
    Invoke-AxiomPython @('tools\audit_task_execution.py')
}

function axiom-agent-audit {
    Invoke-AxiomPython @('tools\audit_agent_boundary.py')
}

function axiom-policy-audit {
    Invoke-AxiomPython @('tools\audit_policy_security.py')
}

function axiom-operator-command-audit {
    Invoke-AxiomPython @('tools\audit_operator_command_ledger.py')
}

function axiom-telegram-gateway-audit {
    Invoke-AxiomPython @('tools\audit_telegram_gateway.py')
}

function axiom-phase6-audit {
    Invoke-AxiomPython @('tools\audit_phase6_closeout.py')
}

function axiom-phase7-inventory {
    Invoke-AxiomPython @('tools\audit_phase7_acceptance_inventory.py')
}

function axiom-phase7-acceptance {
    Invoke-AxiomPython @('tools\run_phase7_acceptance.py')
}

function axiom-phase7-e2e-gate {
    Invoke-AxiomPython @('tools\audit_phase7_e2e_gate.py')
}

function axiom-phase7-closeout {
    Invoke-AxiomPython @('tools\audit_phase7_closeout.py')
}

function axiom-phase9-closeout {
    Invoke-AxiomPython @('tools\audit_phase9_closeout.py')
}

function axiom-health {
    $sessionId = Get-AxiomLatestSessionId
    if (-not $sessionId) { Write-Host "[AXIOM] No latest session found." -ForegroundColor Yellow; return }
    Invoke-AxiomPython @('tools\supervisor_health_check.py', $sessionId)
}

function axiom-session {
    $sessionId = Get-AxiomLatestSessionId
    if ($sessionId) { Write-Host $sessionId -ForegroundColor Green }
    else { Write-Host "No session found." -ForegroundColor Yellow }
}

function axiom-preflight {
    Write-Host ""
    Write-Host "AXIOM PREFLIGHT" -ForegroundColor Green
    Write-Host "===============" -ForegroundColor Green
    Write-Host ""
    Write-Host "1. Foundation verification" -ForegroundColor Gray
    axiom-status
    Write-Host ""
    Write-Host "2. Lifecycle + execution audits" -ForegroundColor Gray
    axiom-audit
    Write-Host ""
    Write-Host "3. Policy/security audit" -ForegroundColor Gray
    axiom-policy-audit
    Write-Host ""
    Write-Host "4. Supervisor health" -ForegroundColor Gray
    axiom-health
    Write-Host ""
    Write-Host "5. Phase 5 agent boundary audit" -ForegroundColor Gray
    axiom-agent-audit
    Write-Host ""
    Write-Host "6. Phase 6 operator command ledger audit" -ForegroundColor Gray
    axiom-operator-command-audit
    Write-Host ""
    Write-Host "7. Phase 6G Telegram gateway audit" -ForegroundColor Gray
    axiom-telegram-gateway-audit
    Write-Host ""
    Write-Host "8. Phase 6I closeout audit" -ForegroundColor Gray
    axiom-phase6-audit
    Write-Host ""
    Write-Host "9. Phase 7A acceptance inventory audit" -ForegroundColor Gray
    axiom-phase7-inventory
    Write-Host ""
    Write-Host "10. Phase 7C full-goal E2E gate audit" -ForegroundColor Gray
    axiom-phase7-e2e-gate
    Write-Host ""
    Write-Host "11. Phase 7E closeout audit" -ForegroundColor Gray
    axiom-phase7-closeout
    Write-Host ""
    Write-Host "12. Phase 9 closeout audit" -ForegroundColor Gray
    axiom-phase9-closeout
}

function axiom-test {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    if (-not (Test-AxiomRoot)) { return }
    Push-Location $env:AXIOM_ROOT
    try {
        Invoke-AxiomVenv | Out-Null
        if ($Args -and $Args.Count -gt 0) { pytest @Args }
        else { pytest tests -v }
    }
    finally { Pop-Location }
}

function axiom-regression { axiom-test tests -v }
function axiom-snapshot { Invoke-AxiomPython @('tools\snapshot_project_state.py') }
function axiom-handoff {
    Invoke-AxiomPython @('tools\snapshot_project_state.py')
    Invoke-AxiomPython @('tools\generate_handoff.py')
    Invoke-AxiomPython @('tools\generate_handoff_bundle.py')
}

function axiom-command-index {
    $tool = Join-Path $env:AXIOM_ROOT 'tools\operator_command_index.py'
    if (Test-Path $tool) { Invoke-AxiomPython @('tools\operator_command_index.py') }
    else { Write-Host "operator_command_index.py not present." -ForegroundColor Yellow }
}

function axiom-readiness {
    $tool = Join-Path $env:AXIOM_ROOT 'tools\execution_readiness_check.py'
    if (Test-Path $tool) { Invoke-AxiomPython @('tools\execution_readiness_check.py') }
    else {
        Write-Host "execution_readiness_check.py not present yet." -ForegroundColor Yellow
        Write-Host "Use axiom-preflight for current safe readiness checks." -ForegroundColor Gray
    }
}

function axiom-sql {
    param([Parameter(Mandatory=$true)][string]$Query)
    $trim = $Query.Trim()
    if ($trim -notmatch '^(?i)(select|pragma|explain)\b') {
        Write-Host "[AXIOM] Refusing non-read-only SQL. Allowed starts: SELECT, PRAGMA, EXPLAIN." -ForegroundColor Red
        return
    }
    if ($trim -match '(?i)\b(insert|update|delete|drop|alter|create|replace|vacuum|attach|detach)\b') {
        Write-Host "[AXIOM] Refusing SQL containing mutation keyword." -ForegroundColor Red
        return
    }

    $code = @'
import os, sqlite3, sys, json
from pathlib import Path
q = sys.argv[1]
db = Path(os.environ.get("AXIOM_DB_PATH", r"C:\axiom\axiom.db"))
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
try:
    rows = conn.execute(q).fetchall()
    for row in rows:
        print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
finally:
    conn.close()
'@
    Invoke-AxiomPython @('-c', $code, $Query)
}

function axiom-find {
    param(
        [Parameter(Mandatory=$true)][string]$Pattern,
        [string]$Path = '.'
    )
    Push-Location $env:AXIOM_ROOT
    try {
        Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\(venv|\.pytest_cache|__pycache__|\.git)\\' } |
            Select-String -Pattern $Pattern -SimpleMatch
    }
    finally { Pop-Location }
}

function axiom-logs {
    $logPath = Join-Path $env:AXIOM_ROOT 'logs'
    if (-not (Test-Path $logPath)) { Write-Host "No logs directory." -ForegroundColor Yellow; return }
    Get-ChildItem $logPath -File | Sort-Object LastWriteTime -Descending | Select-Object -First 25 Name, LastWriteTime, Length | Format-Table -AutoSize
}

function axiom-tail-log {
    $logPath = Join-Path $env:AXIOM_ROOT 'logs'
    if (-not (Test-Path $logPath)) { Write-Host "No logs directory." -ForegroundColor Yellow; return }
    $latest = Get-ChildItem $logPath -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { Write-Host "No log files." -ForegroundColor Yellow; return }
    Write-Host "Tailing: $($latest.FullName)" -ForegroundColor Green
    Get-Content $latest.FullName -Wait
}
