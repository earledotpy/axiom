# ============================================================
# AXIOM Terminal Operator Command Ledger Panel
# File: C:\axiom\ui\terminal\modules\58-operator-commands.ps1
#
# Purpose:
#   Read-only inspection of Phase 6 operator command intent records.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It must not call tools\record_operator_command_intent.py.
#   It must not execute scheduler, agent, model, network, sandbox, memory, or
#   Telegram behavior.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomOperatorCommandsDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomOperatorCommandsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomOperatorCommandsDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomOperatorCommandsDbPath
        sql = $Sql
        params = $Params
    } | ConvertTo-Json -Depth 8 -Compress

    $python = @'
import json
import sqlite3
import sys

payload = json.loads(sys.stdin.read())
db = payload["db"]
sql = payload["sql"]
params = payload.get("params", [])

conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

try:
    rows = conn.execute(sql, params).fetchall()
    print(json.dumps([dict(row) for row in rows], ensure_ascii=False))
finally:
    conn.close()
'@

    try {
        $json = $payload | python -c $python 2>$null

        if ([string]::IsNullOrWhiteSpace($json)) {
            return @()
        }

        return @($json | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Get-AxiomOperatorCommandSummary {
    $rows = Invoke-AxiomOperatorCommandsQuery -Sql @"
SELECT
    COUNT(*) AS total_count,
    COALESCE(SUM(CASE WHEN authorization_status = 'pending' THEN 1 ELSE 0 END), 0) AS pending_auth_count,
    COALESCE(SUM(CASE WHEN authorization_status = 'authorized' THEN 1 ELSE 0 END), 0) AS authorized_count,
    COALESCE(SUM(CASE WHEN authorization_status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected_auth_count,
    COALESCE(SUM(CASE WHEN command_status = 'pending' THEN 1 ELSE 0 END), 0) AS pending_command_count
FROM operator_commands
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomOperatorCommandLatest {
    param([int]$Limit = 10)

    return Invoke-AxiomOperatorCommandsQuery -Sql @"
SELECT
    oc.command_id,
    oc.task_id,
    oc.command_name,
    oc.authorization_status,
    oc.command_status,
    oc.manifest_id,
    t.status AS task_status,
    oc.created_at
FROM operator_commands AS oc
LEFT JOIN tasks AS t
  ON t.task_id = oc.task_id
ORDER BY oc.command_id DESC
LIMIT ?
"@ -Params @($Limit)
}

function axiom-operator-commands {
    param([int]$Limit = 10)

    Write-AxiomUiTitle "OPERATOR COMMAND LEDGER" "append-only - hash-chained"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomUiStatus "BLOCK" "root" "$script:AxiomRoot missing"
        return
    }

    if (-not (Test-Path $script:AxiomOperatorCommandsDbPath)) {
        Write-AxiomUiStatus "BLOCK" "database" "$script:AxiomOperatorCommandsDbPath missing"
        return
    }

    Write-AxiomUiStatus "READ" "boundary" "SQLite mode=ro; no command execution"

    $summary = Get-AxiomOperatorCommandSummary
    if ($summary) {
        Write-AxiomUiLine "total" "$($summary.total_count)" "Cyan"
        Write-AxiomUiLine "auth" "pending=$($summary.pending_auth_count); authorized=$($summary.authorized_count); rejected=$($summary.rejected_auth_count)" "Gray"
        Write-AxiomUiLine "command" "pending=$($summary.pending_command_count)" "Gray"
    }
    else {
        Write-AxiomUiLine "summary" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Latest intent rows"
    $rows = @(Get-AxiomOperatorCommandLatest -Limit $Limit)

    if ($rows.Count -eq 0) {
        Write-AxiomUiLine "ledger" "no operator command rows found" "Yellow"
    }
    else {
        foreach ($row in $rows) {
            $line = "#{0} task={1} {2} auth={3} command={4} task_status={5}" -f `
                $row.command_id,
                $row.task_id,
                $row.command_name,
                $row.authorization_status,
                $row.command_status,
                $row.task_status

            $color = if ($row.authorization_status -eq "pending" -and $row.command_status -eq "pending") { "Gray" } else { "Yellow" }
            Write-Host "  $line" -ForegroundColor $color
        }
    }

    Write-AxiomUiSection "Tools"
    Write-Host "  python tools\audit_operator_command_ledger.py" -ForegroundColor Gray
    Write-Host "  python tools\record_operator_command_intent.py status --json" -ForegroundColor DarkGray
    Write-Host ""
}

