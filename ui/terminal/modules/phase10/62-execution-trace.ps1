# ============================================================
# AXIOM Terminal Execution Trace
# File: C:\axiom\ui\terminal\modules\62-execution-trace.ps1
#
# Purpose:
#   Visualize active pipeline stages for the current session.
#   Shows: [PLAN] ── [DISPATCH] ── [RUNNING] ── [VERIFY]
#
# Boundary:
#   Read-only. No runtime state mutations.
# ============================================================

. "C:\axiom\ui\terminal\modules\shared\39-operator-ui.ps1"
. "C:\axiom\ui\terminal\modules\operators\40-dashboard.ps1"

function Get-ExecutionTraceStages {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session -or -not $Session.session_id) {
        return $null
    }

    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    task_class,
    status,
    COUNT(*) AS count,
    MAX(created_at) AS latest_at
FROM tasks
WHERE session_id = ?
GROUP BY task_class, status
ORDER BY task_class, status
"@ -Params @($Session.session_id)

    return $rows
}

function axiom-execution-trace {
    Write-AxiomUiTitle "EXECUTION TRACE" "active pipeline stages"

    $session = Get-AxiomDashboardLatestSession

    if (-not $session) {
        Write-Host "  (No active session)" -ForegroundColor DarkGray
        return
    }

    $stages = Get-ExecutionTraceStages -Session $session

    # Map task_class/status to stage indicators
    $planCount = 0
    $dispatchCount = 0
    $runningStatus = "IDLE"
    $verifyCount = 0

    if ($stages) {
        foreach ($stage in $stages) {
            switch ($stage.task_class) {
                { @("goal_planning", "task_planning") -contains $_ } {
                    if ($stage.status -eq "completed") {
                        $planCount += 1
                    }
                }
                "task_dispatch" {
                    if ($stage.status -eq "completed") {
                        $dispatchCount += 1
                    } elseif ($stage.status -eq "running") {
                        $dispatchCount += 1
                    }
                }
                "tool_execution" {
                    if ($stage.status -eq "running") {
                        $runningStatus = "ACTIVE"
                    } elseif ($stage.status -eq "completed") {
                        $runningStatus = "DONE"
                    }
                }
                "result_verification" {
                    if ($stage.status -eq "completed") {
                        $verifyCount += 1
                    }
                }
            }
        }
    }

    # Render pipeline visualization
    Write-AxiomUiSection "Pipeline"

    $planColor = if ($planCount -gt 0) { "Green" } else { "DarkGray" }
    $dispatchColor = if ($dispatchCount -gt 0) { "Green" } else { "DarkGray" }
    $runningColor = if ($runningStatus -eq "ACTIVE") { "Green" } else { "DarkGray" }
    $verifyColor = if ($verifyCount -gt 0) { "Green" } else { "DarkGray" }

    Write-Host "  [PLAN" -NoNewline -ForegroundColor $planColor
    Write-Host ": $planCount] " -ForegroundColor $planColor -NoNewline
    Write-Host "── [DISPATCH" -NoNewline -ForegroundColor $dispatchColor
    Write-Host ": $dispatchCount] " -ForegroundColor $dispatchColor -NoNewline
    Write-Host "── [RUNNING" -NoNewline -ForegroundColor $runningColor
    Write-Host ": $runningStatus] " -ForegroundColor $runningColor -NoNewline
    Write-Host "── [VERIFY" -NoNewline -ForegroundColor $verifyColor
    Write-Host ": $verifyCount]" -ForegroundColor $verifyColor

    Write-AxiomUiRule

    # Show task summary if chain is active
    if ($session.current_chain_id) {
        Write-AxiomUiSection "Current Chain Tasks"

        $chainTasks = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    task_id,
    task_class,
    task_type,
    status,
    created_at
FROM tasks
WHERE session_id = ? AND chain_id = ?
ORDER BY created_at DESC
LIMIT 10
"@ -Params @($session.session_id, $session.current_chain_id)

        if ($chainTasks) {
            foreach ($task in $chainTasks) {
                $statusColor = Get-AxiomUiStatusColor -Status $task.status
                Write-Host "  " -NoNewline
                Write-Host ("[{0,-20}] " -f $task.status) -NoNewline -ForegroundColor $statusColor
                Write-Host $task.task_type -NoNewline -ForegroundColor Gray
                Write-Host " (id: $($task.task_id))" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  (No tasks in current chain)" -ForegroundColor DarkGray
        }
    }
}

axiom-execution-trace
