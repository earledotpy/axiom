# ============================================================
# AXIOM Terminal Now Panel
# File: C:\axiom\ui\terminal\modules\39-now.ps1
#
# Purpose:
#   Compact operator-critical state summary.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro and local files only.
#   It must not call scheduler, executor, model, network, sandbox,
#   Telegram, or agent tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomNowDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomNowQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomNowDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomNowDbPath
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

function Convert-AxiomNowBool {
    param([object]$Value)

    if ($null -eq $Value) {
        return "unknown"
    }

    if ([string]$Value -eq "1" -or $Value -eq 1 -or $Value -eq $true) {
        return "true"
    }

    return "false"
}

function Get-AxiomNowLatestSession {
    $rows = Invoke-AxiomNowQuery -Sql @"
SELECT
    session_id,
    scheduler_status,
    autonomous_operation_enabled,
    safe_pass_enabled,
    safe_pass_disabled_reason,
    shutdown_requested
FROM sessions
ORDER BY session_id DESC
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomNowTaskSummary {
    param([object]$Session)

    if (-not $Session) {
        return $null
    }

    $rows = Invoke-AxiomNowQuery -Sql @"
SELECT
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_count,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status IN ('failed', 'quarantined', 'needs_human_input') THEN 1 ELSE 0 END) AS attention_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    COUNT(*) AS total_count
FROM tasks
WHERE session_id = ?
"@ -Params @($Session.session_id)

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomNowLatestModel {
    $rows = Invoke-AxiomNowQuery -Sql @"
SELECT
    profile_id,
    model_name,
    quantization,
    thinking_mode,
    calibration_run_id,
    is_current,
    registration_status
FROM model_profile_fingerprints
WHERE profile_label = 'default'
ORDER BY profile_id DESC
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomNowActiveRoles {
    $rows = Invoke-AxiomNowQuery -Sql @"
SELECT role_name
FROM manifest_fingerprints
WHERE active = 1
  AND manifest_type = 'role'
  AND role_name IS NOT NULL
ORDER BY role_name
"@

    if ($rows) {
        return @($rows | ForEach-Object { [string]$_.role_name })
    }

    return @()
}

function Get-AxiomNowAgentBoundarySummary {
    $rows = Invoke-AxiomNowQuery -Sql @"
WITH expected(role_name, manifest_id, task_class) AS (
    VALUES
        ('goal_planner', 'role.goal_planner.v1', 'goal_planning'),
        ('task_planner', 'role.task_planner.v1', 'task_planning'),
        ('tool_executor', 'role.tool_executor.v1', 'tool_execution'),
        ('result_verifier', 'role.result_verifier.v1', 'result_verification')
),
manifest_summary AS (
    SELECT
        COUNT(*) AS required_count,
        SUM(CASE
            WHEN mf.manifest_id IS NOT NULL
             AND mf.manifest_type = 'role'
             AND mf.role_name = expected.role_name
             AND mf.active = 1
            THEN 1 ELSE 0 END) AS active_count
    FROM expected
    LEFT JOIN manifest_fingerprints AS mf
      ON mf.manifest_id = expected.manifest_id
),
agent_tasks AS (
    SELECT t.task_id
    FROM tasks AS t
    WHERE t.task_class IN (
        'goal_planning',
        'task_planning',
        'tool_execution',
        'result_verification'
    )
),
provider_summary AS (
    SELECT COUNT(*) AS provider_usage_count
    FROM provider_usage
    WHERE task_id IN (SELECT task_id FROM agent_tasks)
)
SELECT
    manifest_summary.required_count,
    manifest_summary.active_count,
    (SELECT COUNT(*) FROM agent_tasks) AS agent_task_count,
    provider_summary.provider_usage_count
FROM manifest_summary, provider_summary
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomNowHeartbeat {
    param([object]$Session)

    if (-not $Session) {
        return $null
    }

    $rows = Invoke-AxiomNowQuery -Sql @"
SELECT
    scheduler_state,
    last_action,
    active_task_id,
    last_freshness_at
FROM scheduler_heartbeat
WHERE session_id = ?
ORDER BY last_freshness_at DESC, heartbeat_id DESC
LIMIT 1
"@ -Params @($Session.session_id)

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function axiom-now {
    Write-AxiomUiTitle "AXIOM NOW"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomUiStatus "BLOCK" "root" "$script:AxiomRoot missing"
        return
    }

    if (-not (Test-Path $script:AxiomNowDbPath)) {
        Write-AxiomUiStatus "BLOCK" "database" "$script:AxiomNowDbPath missing"
        return
    }

    $session = Get-AxiomNowLatestSession
    $tasks = Get-AxiomNowTaskSummary -Session $session
    $model = Get-AxiomNowLatestModel
    $roles = @(Get-AxiomNowActiveRoles)
    $agentBoundary = Get-AxiomNowAgentBoundarySummary
    $heartbeat = Get-AxiomNowHeartbeat -Session $session
    $blockers = New-Object System.Collections.Generic.List[string]

    if (-not $session) {
        $blockers.Add("no_session")
    }
    elseif ((Convert-AxiomNowBool $session.autonomous_operation_enabled) -ne "true") {
        $blockers.Add("autonomous_disabled")
    }

    if ($session -and (Convert-AxiomNowBool $session.safe_pass_enabled) -ne "true") {
        $blockers.Add("safe_pass_disabled")
    }

    if (-not $model -or (Convert-AxiomNowBool $model.is_current) -ne "true") {
        $blockers.Add("no_current_trusted_model")
    }

    $modeStatus = if ($blockers.Count -gt 0) { "WARN" } else { "READY" }
    Write-AxiomUiStatus $modeStatus "posture" "fail_closed_non_autonomous"

    if ($blockers.Count -gt 0) {
        Write-AxiomUiLine "blockers" ($blockers -join ", ") "Yellow"
    }
    else {
        Write-AxiomUiLine "blockers" "none detected by axiom-now" "Green"
    }

    Write-AxiomUiSection "Operator-critical state"

    if ($session) {
        Write-AxiomUiLine "session" "id=$($session.session_id); scheduler=$($session.scheduler_status)" "Cyan"
        Write-AxiomUiLine "safe-pass" "$(Convert-AxiomNowBool $session.safe_pass_enabled); reason=$($session.safe_pass_disabled_reason)" "Yellow"
    }
    else {
        Write-AxiomUiLine "session" "none found" "Yellow"
    }

    if ($tasks) {
        $taskColor = if ([int]$tasks.attention_count -gt 0 -or [int]$tasks.running_count -gt 1) { "Red" } elseif ([int]$tasks.running_count -eq 1) { "Yellow" } else { "Gray" }
        Write-AxiomUiLine "tasks" "run=$($tasks.running_count); pending=$($tasks.pending_count); attention=$($tasks.attention_count); done=$($tasks.completed_count)" $taskColor
    }
    else {
        Write-AxiomUiLine "tasks" "unavailable" "Yellow"
    }

    if ($heartbeat) {
        Write-AxiomUiLine "heartbeat" "$($heartbeat.scheduler_state); last=$($heartbeat.last_action); active=$($heartbeat.active_task_id)" "Gray"
    }
    else {
        Write-AxiomUiLine "heartbeat" "none found" "Yellow"
    }

    if ($model) {
        Write-AxiomUiLine "model" "$($model.model_name) / current=$(Convert-AxiomNowBool $model.is_current) / $($model.registration_status)" "Yellow"
        Write-AxiomUiLine "calibration" ([string]$model.calibration_run_id) "Gray"
    }
    else {
        Write-AxiomUiLine "model" "none found" "Yellow"
    }

    if ($roles.Count -gt 0) {
        Write-AxiomUiLine "active roles" ($roles -join ", ") "Cyan"
    }
    else {
        Write-AxiomUiLine "active roles" "none found" "Yellow"
    }

    if ($agentBoundary) {
        $agentBoundaryOk = (
            [int]$agentBoundary.active_count -eq [int]$agentBoundary.required_count -and
            [int]$agentBoundary.provider_usage_count -eq 0
        )
        $agentBoundaryColor = if ($agentBoundaryOk) { "Green" } else { "Red" }
        Write-AxiomUiLine "agent boundary" "roles=$($agentBoundary.active_count)/$($agentBoundary.required_count); tasks=$($agentBoundary.agent_task_count); provider_usage=$($agentBoundary.provider_usage_count)" $agentBoundaryColor
    }
    else {
        Write-AxiomUiLine "agent boundary" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Next action"
    Write-Host "  axiom-preflight        Verify runtime state" -ForegroundColor Gray
    Write-Host "  axiom-dashboard        More state detail" -ForegroundColor Gray
    Write-Host "  axiom-docs agent       Phase 5 agent docs/files" -ForegroundColor Gray
    Write-Host ""
}
