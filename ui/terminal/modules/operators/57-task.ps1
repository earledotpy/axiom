# ============================================================
# AXIOM Terminal Task Detail Viewer
# File: C:\axiom\ui\terminal\modules\57-task.ps1
#
# Purpose:
#   Read-only task detail viewer for AXIOM Terminal.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It must not start, dispatch, complete, fail, cancel, repair,
#   or execute tasks.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomTaskDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomTaskQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomTaskDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomTaskDbPath
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

function Test-AxiomTaskTableExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TableName
    )

    $rows = Invoke-AxiomTaskQuery -Sql @"
SELECT name
FROM sqlite_master
WHERE type = 'table'
  AND name = ?
LIMIT 1
"@ -Params @($TableName)

    return ($rows -and $rows.Count -gt 0)
}

function Get-AxiomTaskLatestTaskId {
    $rows = Invoke-AxiomTaskQuery -Sql @"
SELECT task_id
FROM tasks
ORDER BY task_id DESC
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return [int]$rows[0].task_id
    }

    return $null
}

function Get-AxiomTaskRow {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    $rows = Invoke-AxiomTaskQuery -Sql @"
SELECT
    task_id,
    session_id,
    parent_task_id,
    chain_id,
    task_class,
    task_type,
    status,
    priority,
    manifest_id,
    created_at,
    started_at,
    completed_at,
    blocked_reason,
    substr(coalesce(goal_text, ''), 1, 500) AS goal_preview,
    substr(coalesce(result_text, ''), 1, 500) AS result_preview,
    substr(coalesce(result_json, ''), 1, 500) AS result_json_preview,
    substr(coalesce(error_info, ''), 1, 500) AS error_preview
FROM tasks
WHERE task_id = ?
LIMIT 1
"@ -Params @($TaskId)

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomTaskChildren {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    return Invoke-AxiomTaskQuery -Sql @"
SELECT
    task_id,
    task_class,
    task_type,
    status,
    priority,
    manifest_id,
    created_at
FROM tasks
WHERE parent_task_id = ?
ORDER BY task_id ASC
"@ -Params @($TaskId)
}

function Get-AxiomTaskSiblings {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Task
    )

    if ($null -eq $Task.parent_task_id) {
        return @()
    }

    return Invoke-AxiomTaskQuery -Sql @"
SELECT
    task_id,
    task_class,
    task_type,
    status,
    priority,
    manifest_id,
    created_at
FROM tasks
WHERE parent_task_id = ?
  AND task_id != ?
ORDER BY task_id ASC
"@ -Params @($Task.parent_task_id, $Task.task_id)
}

function Get-AxiomTaskSecurityEvents {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    if (-not (Test-AxiomTaskTableExists -TableName "security_events")) {
        return @()
    }

    return Invoke-AxiomTaskQuery -Sql @"
SELECT
    event_id,
    session_id,
    task_id,
    event_type,
    severity,
    reason,
    substr(coalesce(details_json, ''), 1, 300) AS details_preview,
    created_at
FROM security_events
WHERE task_id = ?
ORDER BY created_at DESC, event_id DESC
LIMIT 12
"@ -Params @($TaskId)
}

function Get-AxiomTaskProviderUsage {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    if (-not (Test-AxiomTaskTableExists -TableName "provider_usage")) {
        return @()
    }

    return Invoke-AxiomTaskQuery -Sql @"
SELECT
    usage_id,
    provider,
    model,
    status,
    estimated_input_tokens,
    estimated_output_tokens,
    actual_input_tokens,
    actual_output_tokens,
    actuals_unavailable,
    substr(coalesce(error_info, ''), 1, 240) AS error_preview,
    created_at,
    completed_at
FROM provider_usage
WHERE task_id = ?
ORDER BY usage_id DESC
LIMIT 12
"@ -Params @($TaskId)
}

function Get-AxiomTaskResourceUsage {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    if (-not (Test-AxiomTaskTableExists -TableName "resource_usage")) {
        return @()
    }

    return Invoke-AxiomTaskQuery -Sql @"
SELECT
    usage_id,
    resource_type,
    amount,
    limit_value,
    status,
    substr(coalesce(details_json, ''), 1, 240) AS details_preview,
    created_at
FROM resource_usage
WHERE task_id = ?
ORDER BY usage_id DESC
LIMIT 12
"@ -Params @($TaskId)
}

function Get-AxiomTaskExecutionRows {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TaskId
    )

    if (Test-AxiomTaskTableExists -TableName "task_execution_records") {
        return Invoke-AxiomTaskQuery -Sql @"
SELECT *
FROM task_execution_records
WHERE task_id = ?
ORDER BY rowid DESC
LIMIT 8
"@ -Params @($TaskId)
    }

    if (Test-AxiomTaskTableExists -TableName "task_executions") {
        return Invoke-AxiomTaskQuery -Sql @"
SELECT *
FROM task_executions
WHERE task_id = ?
ORDER BY rowid DESC
LIMIT 8
"@ -Params @($TaskId)
    }

    return @()
}

function Write-AxiomTaskLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-28}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Get-AxiomTaskStatusColor {
    param([string]$Status)

    switch ($Status) {
        "completed" { return "Green" }
        "running" { return "Yellow" }
        "pending" { return "Cyan" }
        "failed" { return "Red" }
        "quarantined" { return "Red" }
        "needs_human_input" { return "Yellow" }
        default { return "Gray" }
    }
}

function Write-AxiomTaskMiniTable {
    param(
        [string]$Title,
        [object[]]$Rows,
        [string]$EmptyMessage = "none"
    )

    Write-AxiomUiSection $Title

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  $EmptyMessage" -ForegroundColor DarkGray
        return
    }

    Write-Host ("  {0,-7} {1,-11} {2,-22} {3,-24} {4,-8} {5}" -f "task", "status", "class", "type", "priority", "manifest") -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $manifest = if ($row.manifest_id) { [string]$row.manifest_id } else { "-" }
        $priority = if ($null -ne $row.priority) { [string]$row.priority } else { "-" }
        $color = Get-AxiomTaskStatusColor -Status ([string]$row.status)

        Write-Host ("  {0,-7} {1,-11} {2,-22} {3,-24} {4,-8} {5}" -f `
            $row.task_id,
            $row.status,
            $row.task_class,
            $row.task_type,
            $priority,
            $manifest
        ) -ForegroundColor $color
    }
}

function Write-AxiomTaskSecurityEvents {
    param([object[]]$Rows)

    Write-AxiomUiSection "Security events"

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $color = if ($row.severity -eq "critical") { "Red" } elseif ($row.severity -eq "warning") { "Yellow" } else { "Gray" }

        Write-Host "  [$($row.event_id)] $($row.created_at) $($row.severity) $($row.event_type)" -ForegroundColor $color

        if ($row.reason) {
            Write-Host "      reason: $($row.reason)" -ForegroundColor DarkGray
        }

        if ($row.details_preview) {
            Write-Host "      details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function Write-AxiomTaskProviderUsage {
    param([object[]]$Rows)

    Write-AxiomUiSection "Provider usage"

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $color = if ($row.status -in @("failed", "rate_limited", "quota_exhausted", "abandoned_session_crash")) { "Red" } elseif ($row.status -eq "completed") { "Green" } else { "Yellow" }

        Write-Host "  usage=$($row.usage_id) provider=$($row.provider) model=$($row.model) status=$($row.status)" -ForegroundColor $color
        Write-Host "      est_in=$($row.estimated_input_tokens) est_out=$($row.estimated_output_tokens) act_in=$($row.actual_input_tokens) act_out=$($row.actual_output_tokens)" -ForegroundColor DarkGray

        if ($row.error_preview) {
            Write-Host "      error: $($row.error_preview)" -ForegroundColor Red
        }
    }
}

function Write-AxiomTaskResourceUsage {
    param([object[]]$Rows)

    Write-AxiomUiSection "Resource usage"

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $color = if ($row.status -eq "exceeded") { "Red" } elseif ($row.status -eq "within_limit") { "Green" } else { "Yellow" }

        Write-Host "  usage=$($row.usage_id) resource=$($row.resource_type) amount=$($row.amount) limit=$($row.limit_value) status=$($row.status)" -ForegroundColor $color

        if ($row.details_preview) {
            Write-Host "      details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function Write-AxiomTaskExecutionRows {
    param([object[]]$Rows)

    Write-AxiomUiSection "Execution records"

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none found or execution-record table absent" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $json = $row | ConvertTo-Json -Depth 6 -Compress
        if ($json.Length -gt 400) {
            $json = $json.Substring(0, 400) + "..."
        }

        Write-Host "  $json" -ForegroundColor Gray
    }
}

function axiom-task {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [int]$TaskId
    )

    Write-AxiomUiTitle "TASK DETAIL" "read-only - lifecycle + security"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomTaskLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomTaskDbPath)) {
        Write-AxiomTaskLine "database" "$script:AxiomTaskDbPath missing" "Red"
        Write-Host ""
        return
    }

    $task = Get-AxiomTaskRow -TaskId $TaskId

    if (-not $task) {
        Write-AxiomTaskLine "task_id" "$TaskId not found" "Red"
        Write-Host ""
        return
    }

    $statusColor = Get-AxiomTaskStatusColor -Status ([string]$task.status)

    Write-AxiomUiSection "Task"
    Write-AxiomTaskLine "task_id" ([string]$task.task_id) "Green"
    Write-AxiomTaskLine "session_id" ([string]$task.session_id) "Gray"
    Write-AxiomTaskLine "parent_task_id" ([string]$task.parent_task_id) "Gray"
    Write-AxiomTaskLine "chain_id" ([string]$task.chain_id) "Gray"
    Write-AxiomTaskLine "class" ([string]$task.task_class) "Cyan"
    Write-AxiomTaskLine "type" ([string]$task.task_type) "Cyan"
    Write-AxiomTaskLine "status" ([string]$task.status) $statusColor
    Write-AxiomTaskLine "priority" ([string]$task.priority) "Gray"
    Write-AxiomTaskLine "manifest_id" $(if ($task.manifest_id) { [string]$task.manifest_id } else { "missing" }) $(if ($task.manifest_id) { "Green" } else { "Yellow" })

    Write-AxiomUiSection "Timestamps"
    Write-AxiomTaskLine "created_at" ([string]$task.created_at) "Gray"
    Write-AxiomTaskLine "started_at" ([string]$task.started_at) "Gray"
    Write-AxiomTaskLine "completed_at" ([string]$task.completed_at) "Gray"

    Write-AxiomUiSection "Content previews"

    if ($task.goal_preview) {
        Write-AxiomTaskLine "goal" ([string]$task.goal_preview) "Gray"
    }
    else {
        Write-AxiomTaskLine "goal" "none" "DarkGray"
    }

    if ($task.result_preview) {
        Write-AxiomTaskLine "result_text" ([string]$task.result_preview) "Green"
    }

    if ($task.result_json_preview) {
        Write-AxiomTaskLine "result_json" ([string]$task.result_json_preview) "Green"
    }

    if ($task.blocked_reason) {
        Write-AxiomTaskLine "blocked_reason" ([string]$task.blocked_reason) "Yellow"
    }

    if ($task.error_preview) {
        Write-AxiomTaskLine "error" ([string]$task.error_preview) "Red"
    }

    $children = @(Get-AxiomTaskChildren -TaskId $TaskId)
    $siblings = @(Get-AxiomTaskSiblings -Task $task)
    $securityEvents = @(Get-AxiomTaskSecurityEvents -TaskId $TaskId)
    $providerUsage = @(Get-AxiomTaskProviderUsage -TaskId $TaskId)
    $resourceUsage = @(Get-AxiomTaskResourceUsage -TaskId $TaskId)
    $executionRows = @(Get-AxiomTaskExecutionRows -TaskId $TaskId)

    Write-AxiomTaskMiniTable -Title "Child tasks" -Rows $children -EmptyMessage "none"
    Write-AxiomTaskMiniTable -Title "Sibling tasks" -Rows $siblings -EmptyMessage "none"
    Write-AxiomTaskSecurityEvents -Rows $securityEvents
    Write-AxiomTaskProviderUsage -Rows $providerUsage
    Write-AxiomTaskResourceUsage -Rows $resourceUsage
    Write-AxiomTaskExecutionRows -Rows $executionRows

    Write-AxiomUiSection "Interpretation"
    Write-Host "  - This viewer is read-only." -ForegroundColor Gray
    Write-Host "  - It does not start, dispatch, complete, fail, cancel, or repair tasks." -ForegroundColor Gray
    Write-Host "  - A task must have manifest_id before transition to running." -ForegroundColor Gray
    Write-Host "  - More than one running task would violate AXIOM sequential execution." -ForegroundColor Gray
    Write-Host ""

    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-queue" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host ""
}

function axiom-task-latest {
    $latest = Get-AxiomTaskLatestTaskId

    if ($null -eq $latest) {
        Write-Host "[AXIOM] No tasks found." -ForegroundColor Yellow
        return
    }

    axiom-task $latest
}

