# ============================================================
# AXIOM Terminal Approval Gate
# File: C:\axiom\ui\terminal\modules\63-approval-gate.ps1
#
# Purpose:
#   List tasks awaiting operator countersign or quarantine review.
#   Shows blocked tasks requiring human input.
#
# Boundary:
#   Read-only. No runtime state mutations.
# ============================================================

. "C:\axiom\ui\terminal\modules\shared\39-operator-ui.ps1"
. "C:\axiom\ui\terminal\modules\operators\40-dashboard.ps1"

function Get-BlockedTasks {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session -or -not $Session.session_id) {
        return @()
    }

    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    task_id,
    task_type,
    status,
    created_at,
    manifest_id
FROM tasks
WHERE session_id = ? AND (status = 'needs_human_input' OR status = 'quarantined')
ORDER BY created_at ASC
"@ -Params @($Session.session_id)

    return @($rows)
}

function axiom-approval-gate {
    Write-AxiomUiTitle "APPROVAL GATE" "blocked tasks awaiting countersign"

    $session = Get-AxiomDashboardLatestSession

    if (-not $session) {
        Write-Host "  (No active session)" -ForegroundColor DarkGray
        return
    }

    $blocked = Get-BlockedTasks -Session $session

    Write-AxiomUiSection "Pending Authorization"

    if (-not $blocked -or $blocked.Count -eq 0) {
        Write-Host "  (No blocked tasks)" -ForegroundColor Green
    } else {
        foreach ($task in $blocked) {
            $statusColor = if ($task.status -eq "quarantined") { "Magenta" } else { "Yellow" }
            $cmd = if ($task.status -eq "needs_human_input") {
                "axiom-task-resume $($task.task_id)"
            } else {
                "axiom-task-quarantine-review $($task.task_id)"
            }

            Write-Host "  " -NoNewline
            $statusLabel = "[{0,-18}]" -f ($task.status.ToUpper())
            Write-Host $statusLabel -NoNewline -ForegroundColor $statusColor
            Write-Host " $($task.task_type)" -NoNewline -ForegroundColor Gray
            Write-Host " (task #$($task.task_id))" -ForegroundColor DarkGray

            Write-Host "    " -NoNewline
            Write-Host "→ " -NoNewline -ForegroundColor Cyan
            Write-Host $cmd -ForegroundColor Cyan
            Write-Host ""
        }

        Write-AxiomUiRule

        Write-Host "  Action: Run the command above to approve or review." -ForegroundColor DarkGray
    }
}

axiom-approval-gate
