# ============================================================
# AXIOM Terminal Task Queue Panel
# File: C:\axiom\ui\terminal\modules\44-queue.ps1
#
# Purpose:
#   Read-only task queue visibility for AXIOM Terminal.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It must not call scheduler, executor, lifecycle, model,
#   network, sandbox, Telegram, or agent tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomQueueDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomQueueQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomQueueDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomQueueDbPath
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

function Get-AxiomQueueLatestSession {
    $rows = Invoke-AxiomQueueQuery -Sql @"
SELECT
    session_id,
    created_at,
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

function Get-AxiomQueueCounts {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Session
    )

    return Invoke-AxiomQueueQuery -Sql @"
SELECT
    status,
    COUNT(*) AS count
FROM tasks
WHERE session_id = ?
GROUP BY status
ORDER BY
    CASE status
        WHEN 'running' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'needs_human_input' THEN 3
        WHEN 'quarantined' THEN 4
        WHEN 'failed' THEN 5
        WHEN 'blocked_resource_limit' THEN 6
        WHEN 'cancelled' THEN 7
        WHEN 'completed' THEN 8
        ELSE 99
    END,
    status
"@ -Params @($Session.session_id)
}

function Get-AxiomQueueTasksByStatus {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Session,

        [Parameter(Mandatory = $true)]
        [string]$Status,

        [int]$Limit = 10
    )

    return Invoke-AxiomQueueQuery -Sql @"
SELECT
    task_id,
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
    substr(coalesce(goal_text, ''), 1, 90) AS goal_preview,
    substr(coalesce(error_info, ''), 1, 90) AS error_preview
FROM tasks
WHERE session_id = ?
  AND status = ?
ORDER BY
    CASE
        WHEN status = 'pending' THEN priority
        ELSE 0
    END ASC,
    created_at DESC,
    task_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Status, $Limit)
}

function Get-AxiomQueuePendingManifestBound {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Session,

        [int]$Limit = 10
    )

    return Invoke-AxiomQueueQuery -Sql @"
SELECT
    task_id,
    parent_task_id,
    chain_id,
    task_class,
    task_type,
    status,
    priority,
    manifest_id,
    created_at,
    substr(coalesce(goal_text, ''), 1, 90) AS goal_preview
FROM tasks
WHERE session_id = ?
  AND status = 'pending'
  AND manifest_id IS NOT NULL
ORDER BY priority ASC, created_at ASC, task_id ASC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Get-AxiomQueuePendingWithoutManifest {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Session,

        [int]$Limit = 10
    )

    return Invoke-AxiomQueueQuery -Sql @"
SELECT
    task_id,
    parent_task_id,
    chain_id,
    task_class,
    task_type,
    status,
    priority,
    manifest_id,
    created_at,
    substr(coalesce(goal_text, ''), 1, 90) AS goal_preview
FROM tasks
WHERE session_id = ?
  AND status = 'pending'
  AND manifest_id IS NULL
ORDER BY priority ASC, created_at ASC, task_id ASC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Write-AxiomQueueLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-26}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Write-AxiomQueueTaskTable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [object[]]$Rows,

        [string]$EmptyMessage = "none"
    )

    Write-AxiomUiSection $Title

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  $EmptyMessage" -ForegroundColor DarkGray
        return
    }

    Write-Host ("  {0,-7} {1,-10} {2,-22} {3,-24} {4,-9} {5}" -f "task", "status", "class", "type", "priority", "manifest") -ForegroundColor DarkGray
    Write-Host ("  {0,-7} {1,-10} {2,-22} {3,-24} {4,-9} {5}" -f "----", "------", "-----", "----", "--------", "--------") -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $manifest = if ($row.manifest_id) { [string]$row.manifest_id } else { "-" }
        $priority = if ($null -ne $row.priority) { [string]$row.priority } else { "-" }

        $color = "Gray"
        if ($row.status -eq "running") { $color = "Yellow" }
        elseif ($row.status -eq "failed" -or $row.status -eq "quarantined") { $color = "Red" }
        elseif ($row.status -eq "pending") { $color = "Cyan" }
        elseif ($row.status -eq "completed") { $color = "Green" }

        Write-Host ("  {0,-7} {1,-10} {2,-22} {3,-24} {4,-9} {5}" -f `
            $row.task_id,
            $row.status,
            $row.task_class,
            $row.task_type,
            $priority,
            $manifest
        ) -ForegroundColor $color

        if ($row.goal_preview) {
            Write-Host "          goal: $($row.goal_preview)" -ForegroundColor DarkGray
        }

        if ($row.blocked_reason) {
            Write-Host "          blocked: $($row.blocked_reason)" -ForegroundColor Yellow
        }

        if ($row.error_preview) {
            Write-Host "          error: $($row.error_preview)" -ForegroundColor Red
        }
    }
}

function axiom-queue {
    param(
        [int]$Limit = 10
    )

    Write-AxiomUiTitle "TASK QUEUE" "manifest-bound · operator-dispatched"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomQueueLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomQueueDbPath)) {
        Write-AxiomQueueLine "database" "$script:AxiomQueueDbPath missing" "Red"
        Write-Host ""
        return
    }

    $session = Get-AxiomQueueLatestSession

    if (-not $session) {
        Write-AxiomQueueLine "latest session" "none found" "Yellow"
        Write-Host ""
        return
    }

    Write-AxiomUiSection "Session"
    Write-AxiomQueueLine "session_id" ([string]$session.session_id) "Green"
    Write-AxiomQueueLine "scheduler_status" ([string]$session.scheduler_status) "Cyan"
    Write-AxiomQueueLine "autonomous_enabled" ([string]$session.autonomous_operation_enabled) "Yellow"
    Write-AxiomQueueLine "safe_pass_enabled" ([string]$session.safe_pass_enabled) "Yellow"

    if ($session.safe_pass_disabled_reason) {
        Write-AxiomQueueLine "safe_pass_reason" ([string]$session.safe_pass_disabled_reason) "Yellow"
    }

    $counts = @(Get-AxiomQueueCounts -Session $session)

    Write-AxiomUiRule
    Write-AxiomUiSection "Counts by status"

    if ($counts.Count -eq 0) {
        Write-Host "  no tasks in latest session" -ForegroundColor DarkGray
    }
    else {
        foreach ($row in $counts) {
            $color = "Gray"
            if ($row.status -eq "running") { $color = "Yellow" }
            elseif ($row.status -eq "pending") { $color = "Cyan" }
            elseif ($row.status -eq "failed" -or $row.status -eq "quarantined") { $color = "Red" }
            elseif ($row.status -eq "completed") { $color = "Green" }

            Write-AxiomQueueLine $row.status ([string]$row.count) $color
        }
    }

    $running = @(Get-AxiomQueueTasksByStatus -Session $session -Status "running" -Limit $Limit)
    $pendingManifestBound = @(Get-AxiomQueuePendingManifestBound -Session $session -Limit $Limit)
    $pendingWithoutManifest = @(Get-AxiomQueuePendingWithoutManifest -Session $session -Limit $Limit)
    $needsHumanInput = @(Get-AxiomQueueTasksByStatus -Session $session -Status "needs_human_input" -Limit $Limit)
    $quarantined = @(Get-AxiomQueueTasksByStatus -Session $session -Status "quarantined" -Limit $Limit)
    $failed = @(Get-AxiomQueueTasksByStatus -Session $session -Status "failed" -Limit $Limit)
    $completed = @(Get-AxiomQueueTasksByStatus -Session $session -Status "completed" -Limit 5)

    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Running tasks" -Rows $running -EmptyMessage "none; expected in healthy idle state"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Pending manifest-bound tasks" -Rows $pendingManifestBound -EmptyMessage "none"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Pending tasks missing manifest_id" -Rows $pendingWithoutManifest -EmptyMessage "none; required before running transition"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Needs human input" -Rows $needsHumanInput -EmptyMessage "none"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Quarantined tasks" -Rows $quarantined -EmptyMessage "none"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Failed tasks" -Rows $failed -EmptyMessage "none"
    Write-AxiomUiRule
    Write-AxiomQueueTaskTable -Title "Recent completed tasks" -Rows $completed -EmptyMessage "none"

    Write-AxiomUiRule
    Write-AxiomUiSection "Interpretation"
    Write-Host "  - More than one running task violates AXIOM sequential execution." -ForegroundColor Gray
    Write-Host "  - A task must have manifest_id before transition to running." -ForegroundColor Gray
    Write-Host "  - This panel is read-only. It does not dispatch, start, complete, or repair tasks." -ForegroundColor Gray
    Write-Host ""

    Write-AxiomUiRule
    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
