# ============================================================
# AXIOM Terminal Dashboard
# File: C:\axiom\ui\terminal\modules\40-dashboard.ps1
#
# Purpose:
#   Read-only AXIOM operator dashboard for current system state.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro and does not call scheduler,
#   executor, model, network, sandbox, Telegram, or agent tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomDbPath = Join-Path $script:AxiomRoot "axiom.db"

# Load new panel modules for variant B
. "C:\axiom\ui\terminal\modules\shared\39-operator-ui.ps1" -ErrorAction SilentlyContinue

function Invoke-AxiomDashboardQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomDbPath
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

function Get-AxiomDashboardLatestSession {
    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    session_id,
    created_at,
    ended_at,
    scheduler_status,
    autonomous_operation_enabled,
    safe_pass_enabled,
    safe_pass_disabled_reason,
    shutdown_requested,
    current_chain_id
FROM sessions
ORDER BY session_id DESC
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomDashboardTaskCounts {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomDashboardQuery -Sql @"
SELECT
    status,
    COUNT(*) AS count
FROM tasks
WHERE session_id = ?
GROUP BY status
ORDER BY status
"@ -Params @($Session.session_id)
}

function Get-AxiomDashboardHeartbeat {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return $null
    }

    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    heartbeat_id,
    last_freshness_at,
    last_tick_started_at,
    last_tick_completed_at,
    active_task_id,
    active_chain_id,
    scheduler_state,
    last_action,
    tick_count,
    updated_at
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

function Get-AxiomDashboardRunningTasks {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomDashboardQuery -Sql @"
SELECT
    task_id,
    task_class,
    task_type,
    status,
    manifest_id,
    started_at
FROM tasks
WHERE session_id = ?
  AND status = 'running'
ORDER BY started_at DESC, task_id DESC
"@ -Params @($Session.session_id)
}

function Get-AxiomDashboardPendingManifestTasks {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomDashboardQuery -Sql @"
SELECT
    task_id,
    task_class,
    task_type,
    status,
    manifest_id,
    priority,
    created_at
FROM tasks
WHERE session_id = ?
  AND status = 'pending'
  AND manifest_id IS NOT NULL
ORDER BY priority ASC, created_at ASC, task_id ASC
LIMIT 5
"@ -Params @($Session.session_id)
}

function Get-AxiomDashboardLatestModelProfile {
    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    profile_id,
    profile_label,
    model_name,
    quantization,
    thinking_mode,
    thinking_mode_rule_version,
    calibration_run_id,
    is_current,
    registration_status,
    registered_at
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

function Get-AxiomDashboardManifestSummary {
    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    manifest_type,
    COUNT(*) AS count
FROM manifest_fingerprints
WHERE active = 1
GROUP BY manifest_type
ORDER BY manifest_type
"@

    if ($rows) {
        return $rows
    }

    return @()
}

function Get-AxiomDashboardRoleManifests {
    $rows = Invoke-AxiomDashboardQuery -Sql @"
SELECT
    role_name,
    manifest_id
FROM manifest_fingerprints
WHERE active = 1
  AND manifest_type = 'role'
ORDER BY role_name, manifest_id
"@

    if ($rows) {
        return $rows
    }

    return @()
}

function Get-AxiomDashboardRecentEvents {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomDashboardQuery -Sql @"
SELECT
    'session' AS source,
    event_type,
    details_json AS reason,
    created_at
FROM session_events
WHERE session_id = ?

UNION ALL

SELECT
    'security' AS source,
    event_type,
    reason,
    created_at
FROM security_events
WHERE session_id = ?

ORDER BY created_at DESC
LIMIT 5
"@ -Params @($Session.session_id, $Session.session_id)
}

function Write-AxiomDashboardLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-28}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Convert-AxiomBool {
    param([object]$Value)

    if ($null -eq $Value) {
        return "unknown"
    }

    if ([string]$Value -eq "1" -or $Value -eq 1 -or $Value -eq $true) {
        return "true"
    }

    return "false"
}

function Get-AxiomDashboardPosture {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session,

        [Parameter(Mandatory = $false)]
        [object]$ModelProfile,

        [Parameter(Mandatory = $false)]
        [object[]]$RunningTasks
    )

    $reasons = New-Object System.Collections.Generic.List[string]

    if (-not $Session) {
        $reasons.Add("no_session")
        return $reasons
    }

    if ((Convert-AxiomBool $Session.autonomous_operation_enabled) -ne "true") {
        $reasons.Add("autonomous_operation_disabled")
    }

    if ((Convert-AxiomBool $Session.safe_pass_enabled) -ne "true") {
        $reasons.Add("safe_pass_disabled")
    }

    if (-not $ModelProfile) {
        $reasons.Add("no_model_profile")
    }
    elseif ((Convert-AxiomBool $ModelProfile.is_current) -ne "true") {
        $reasons.Add("no_current_trusted_model_profile")
    }

    if ($RunningTasks -and $RunningTasks.Count -gt 1) {
        $reasons.Add("one_running_task_invariant_risk")
    }

    return $reasons
}

function axiom-dashboard {
    Write-AxiomUiTitle "AXIOM DASHBOARD" "read-only · fail-closed"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomDashboardLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomDbPath)) {
        Write-AxiomDashboardLine "database" "$script:AxiomDbPath missing" "Red"
        Write-Host ""
        return
    }

    $session = Get-AxiomDashboardLatestSession
    $model = Get-AxiomDashboardLatestModelProfile
    $taskCounts = Get-AxiomDashboardTaskCounts -Session $session
    $heartbeat = Get-AxiomDashboardHeartbeat -Session $session
    $runningTasks = @(Get-AxiomDashboardRunningTasks -Session $session)
    $pendingManifestTasks = @(Get-AxiomDashboardPendingManifestTasks -Session $session)
    $manifestSummary = @(Get-AxiomDashboardManifestSummary)
    $roleManifests = @(Get-AxiomDashboardRoleManifests)
    $events = @(Get-AxiomDashboardRecentEvents -Session $session)
    $blockingReasons = @(Get-AxiomDashboardPosture -Session $session -ModelProfile $model -RunningTasks $runningTasks)

    # Determine dashboard variant based on autonomous_operation_enabled
    $useVariantB = $false
    if ($session -and [string]$session.autonomous_operation_enabled -eq "1") {
        $useVariantB = $true
    }

    # Allow override via command-line arguments
    if ($args -contains "--force-variant") {
        $variantIdx = [Array]::IndexOf($args, "--force-variant")
        if ($variantIdx + 1 -lt $args.Count) {
            $forceVariant = $args[$variantIdx + 1]
            $useVariantB = ($forceVariant -eq "B")
        }
    }

    Write-AxiomUiSection "System"
    Write-AxiomDashboardLine "root" $script:AxiomRoot "Green"
    Write-AxiomDashboardLine "database" "present / read-only dashboard" "Green"
    Write-AxiomDashboardLine "operational mode" "fail_closed_non_autonomous" "Yellow"

    if ($blockingReasons.Count -eq 0) {
        Write-AxiomDashboardLine "blocking reasons" "none detected by dashboard" "Green"
    }
    else {
        Write-AxiomDashboardLine "blocking reasons" ($blockingReasons -join ", ") "Yellow"
    }

    Write-AxiomUiRule

    Write-AxiomUiSection "Latest session"
    if ($session) {
        Write-AxiomDashboardLine "session_id" ([string]$session.session_id) "Green"
        Write-AxiomDashboardLine "scheduler_status" ([string]$session.scheduler_status) "Cyan"
        Write-AxiomDashboardLine "autonomous_enabled" (Convert-AxiomBool $session.autonomous_operation_enabled) "Yellow"
        Write-AxiomDashboardLine "safe_pass_enabled" (Convert-AxiomBool $session.safe_pass_enabled) "Yellow"

        if ($session.safe_pass_disabled_reason) {
            Write-AxiomDashboardLine "safe_pass_reason" ([string]$session.safe_pass_disabled_reason) "Yellow"
        }

        Write-AxiomDashboardLine "shutdown_requested" (Convert-AxiomBool $session.shutdown_requested) "Gray"
    }
    else {
        Write-AxiomDashboardLine "session" "none found" "Yellow"
    }

    Write-AxiomUiRule

    Write-AxiomUiSection "Supervisor / heartbeat"
    if ($heartbeat) {
        Write-AxiomDashboardLine "scheduler_state" ([string]$heartbeat.scheduler_state) "Cyan"
        Write-AxiomDashboardLine "last_action" ([string]$heartbeat.last_action) "Cyan"
        Write-AxiomDashboardLine "active_task_id" ([string]$heartbeat.active_task_id) "Gray"
        Write-AxiomDashboardLine "tick_count" ([string]$heartbeat.tick_count) "Gray"
        Write-AxiomDashboardLine "last_freshness_at" ([string]$heartbeat.last_freshness_at) "Gray"
    }
    else {
        Write-AxiomDashboardLine "heartbeat" "none found" "Yellow"
    }

    Write-AxiomUiRule

    Write-AxiomUiSection "Task queue"
    if ($taskCounts -and $taskCounts.Count -gt 0) {
        foreach ($row in $taskCounts) {
            $color = if ($row.status -eq "running") { "Yellow" } elseif ($row.status -eq "failed" -or $row.status -eq "quarantined") { "Red" } else { "Gray" }
            Write-AxiomDashboardLine $row.status ([string]$row.count) $color
        }
    }
    else {
        Write-AxiomDashboardLine "tasks" "none in latest session" "Gray"
    }

    if ($pendingManifestTasks.Count -gt 0) {
        Write-AxiomDashboardLine "pending manifest-bound" ([string]$pendingManifestTasks.Count) "Cyan"
    }
    else {
        Write-AxiomDashboardLine "pending manifest-bound" "0" "Gray"
    }

    Write-AxiomUiRule

    Write-AxiomUiSection "Model profile"
    if ($model) {
        Write-AxiomDashboardLine "profile_id" ([string]$model.profile_id) "Gray"
        Write-AxiomDashboardLine "model" ([string]$model.model_name) "Cyan"
        Write-AxiomDashboardLine "quantization" ([string]$model.quantization) "Cyan"
        Write-AxiomDashboardLine "thinking_mode" ([string]$model.thinking_mode) "Yellow"
        Write-AxiomDashboardLine "rule_version" ([string]$model.thinking_mode_rule_version) "Gray"
        Write-AxiomDashboardLine "is_current" (Convert-AxiomBool $model.is_current) "Yellow"
        Write-AxiomDashboardLine "registration" ([string]$model.registration_status) "Yellow"
        Write-AxiomDashboardLine "calibration" ([string]$model.calibration_run_id) "Gray"
    }
    else {
        Write-AxiomDashboardLine "model profile" "none found" "Yellow"
    }

    Write-AxiomUiRule

    Write-AxiomUiSection "Manifests"
    if ($manifestSummary.Count -gt 0) {
        foreach ($row in $manifestSummary) {
            Write-AxiomDashboardLine $row.manifest_type ([string]$row.count) "Cyan"
        }
    }
    else {
        Write-AxiomDashboardLine "active manifests" "none found" "Yellow"
    }

    if ($roleManifests.Count -gt 0) {
        $roleNames = @($roleManifests | ForEach-Object { [string]$_.role_name } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

        if ($roleNames.Count -gt 0) {
            Write-AxiomDashboardLine "active roles" ($roleNames -join ", ") "Cyan"
        }
    }

    Write-AxiomUiRule

    # Variant-specific panels
    if ($useVariantB) {
        # Variant B: Dynamic panels for autonomous mode
        Write-Host ""
        Write-Host "  [VARIANT B: Autonomous Mode Panels]" -ForegroundColor Cyan

        # Execution trace
        Write-AxiomUiSection "Execution Trace"
        & "C:\axiom\ui\terminal\modules\62-execution-trace.ps1" | Out-Null

        # Approval gate
        Write-AxiomUiSection "Approval Gate"
        & "C:\axiom\ui\terminal\modules\63-approval-gate.ps1" | Out-Null

        # Autonomous posture
        Write-AxiomUiSection "Autonomous Posture"
        & "C:\axiom\ui\terminal\modules\64-autonomous-posture.ps1" | Out-Null

        Write-AxiomUiRule
    }
    else {
        # Variant A: Original recent events display
        Write-AxiomUiSection "Recent events"
        if ($events.Count -gt 0) {
            foreach ($event in $events) {
                $label = "$($event.source):$($event.event_type)"
                $value = $event.created_at
                Write-Host ("  {0,-36}" -f $label) -NoNewline -ForegroundColor DarkGray
                Write-Host ([string]$value) -ForegroundColor Gray
            }
        }
        else {
            Write-AxiomDashboardLine "events" "none found for latest session" "Gray"
        }

        Write-AxiomUiRule
    }

    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host "  axiom-regression" -ForegroundColor Gray
    Write-Host "  axiom-handoff" -ForegroundColor Gray
    Write-Host ""
}
