# ============================================================
# AXIOM Terminal Execution Readiness
# File: C:\axiom\ui\terminal\modules\41-readiness.ps1
#
# Purpose:
#   Read-only execution readiness report for AXIOM Terminal.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro and inspects local files only.
#   It does not call scheduler, executor, model, network, sandbox,
#   Telegram, or agent tools.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomReadinessDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomReadinessQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomReadinessDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomReadinessDbPath
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

function Get-AxiomReadinessLatestSession {
    $rows = Invoke-AxiomReadinessQuery -Sql @"
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

function Get-AxiomReadinessTaskSummary {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return $null
    }

    $rows = Invoke-AxiomReadinessQuery -Sql @"
SELECT
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_count,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'pending' AND manifest_id IS NOT NULL THEN 1 ELSE 0 END) AS pending_manifest_bound_count,
    SUM(CASE WHEN status = 'pending' AND manifest_id IS NULL THEN 1 ELSE 0 END) AS pending_without_manifest_count,
    SUM(CASE WHEN status = 'needs_human_input' THEN 1 ELSE 0 END) AS needs_human_input_count,
    SUM(CASE WHEN status = 'quarantined' THEN 1 ELSE 0 END) AS quarantined_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    COUNT(*) AS total_count
FROM tasks
WHERE session_id = ?
"@ -Params @($Session.session_id)

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomReadinessHeartbeat {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Session
    )

    if (-not $Session) {
        return $null
    }

    $rows = Invoke-AxiomReadinessQuery -Sql @"
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

function Get-AxiomReadinessCurrentModelProfile {
    $rows = Invoke-AxiomReadinessQuery -Sql @"
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
  AND is_current = 1
  AND registration_status = 'current'
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomReadinessLatestModelProfile {
    $rows = Invoke-AxiomReadinessQuery -Sql @"
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

function Get-AxiomReadinessManifestSummary {
    $rows = Invoke-AxiomReadinessQuery -Sql @"
SELECT
    manifest_type,
    COUNT(*) AS count
FROM manifest_fingerprints
WHERE active = 1
GROUP BY manifest_type
ORDER BY manifest_type
"@

    if ($rows) {
        return @($rows)
    }

    return @()
}

function Get-AxiomReadinessToolMapPresent {
    $rows = Invoke-AxiomReadinessQuery -Sql @"
SELECT
    manifest_id,
    relative_path,
    active
FROM manifest_fingerprints
WHERE manifest_id = 'security.tool_capability_map.v1'
  AND manifest_type = 'tool_capability_map'
  AND active = 1
LIMIT 1
"@

    return ($rows -and $rows.Count -gt 0)
}

function Convert-AxiomReadinessBool {
    param([object]$Value)

    if ($null -eq $Value) {
        return $false
    }

    if ([string]$Value -eq "1" -or $Value -eq 1 -or $Value -eq $true) {
        return $true
    }

    return $false
}

function Convert-AxiomReadinessInt {
    param([object]$Value)

    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
        return 0
    }

    return [int]$Value
}

function Get-AxiomReadinessHeartbeatAgeSeconds {
    param(
        [Parameter(Mandatory = $false)]
        [object]$Heartbeat
    )

    if (-not $Heartbeat -or -not $Heartbeat.last_freshness_at) {
        return $null
    }

    try {
        $raw = [string]$Heartbeat.last_freshness_at
        $normalized = $raw.Replace("Z", "+00:00")
        $dt = [datetimeoffset]::Parse($normalized)
        $age = [datetimeoffset]::UtcNow - $dt.ToUniversalTime()
        return [math]::Round($age.TotalSeconds, 0)
    }
    catch {
        return $null
    }
}

function New-AxiomReadinessCheck {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail,
        [string]$Severity = "required"
    )

    [pscustomobject]@{
        Name = $Name
        Passed = $Passed
        Detail = $Detail
        Severity = $Severity
    }
}

function Write-AxiomReadinessCheck {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Check
    )

    $status = if ($Check.Passed) { "PASS" } elseif ($Check.Severity -eq "warning") { "WARN" } else { "BLOCK" }
    $color = if ($Check.Passed) { "Green" } elseif ($Check.Severity -eq "warning") { "Yellow" } else { "Red" }

    Write-Host ("  [{0,-5}] " -f $status) -NoNewline -ForegroundColor $color
    Write-Host ("{0,-34}" -f $Check.Name) -NoNewline -ForegroundColor Gray
    Write-Host $Check.Detail -ForegroundColor DarkGray
}

function axiom-readiness {
    Write-AxiomUiTitle "EXECUTION READINESS" "30+ checks - read-only"

    $checks = New-Object System.Collections.Generic.List[object]

    $rootExists = Test-Path $script:AxiomRoot
    $dbExists = Test-Path $script:AxiomReadinessDbPath
    $venvExists = Test-Path (Join-Path $script:AxiomRoot "venv\Scripts\Activate.ps1")

    $checks.Add((New-AxiomReadinessCheck "AXIOM root" $rootExists $script:AxiomRoot))
    $checks.Add((New-AxiomReadinessCheck "AXIOM database" $dbExists $script:AxiomReadinessDbPath))
    $checks.Add((New-AxiomReadinessCheck "AXIOM venv" $venvExists "venv\Scripts\Activate.ps1"))

    if (-not $rootExists -or -not $dbExists) {
        foreach ($check in $checks) {
            Write-AxiomReadinessCheck $check
        }

        Write-Host ""
        Write-Host "Readiness: BLOCKED" -ForegroundColor Red
        Write-Host ""
        return
    }

    $session = Get-AxiomReadinessLatestSession
    $taskSummary = Get-AxiomReadinessTaskSummary -Session $session
    $heartbeat = Get-AxiomReadinessHeartbeat -Session $session
    $currentModel = Get-AxiomReadinessCurrentModelProfile
    $latestModel = Get-AxiomReadinessLatestModelProfile
    $manifestSummary = @(Get-AxiomReadinessManifestSummary)
    $toolMapPresent = Get-AxiomReadinessToolMapPresent

    $hasSession = $null -ne $session
    $checks.Add((New-AxiomReadinessCheck "latest session exists" $hasSession $(if ($hasSession) { "session_id=$($session.session_id)" } else { "no session found" })))

    if ($session) {
        $autonomousEnabled = Convert-AxiomReadinessBool $session.autonomous_operation_enabled
        $safePassEnabled = Convert-AxiomReadinessBool $session.safe_pass_enabled
        $shutdownRequested = Convert-AxiomReadinessBool $session.shutdown_requested

        $checks.Add((New-AxiomReadinessCheck "autonomous remains blocked" (-not $autonomousEnabled) "expected in current phase"))
        $checks.Add((New-AxiomReadinessCheck "safe-pass remains disabled" (-not $safePassEnabled) "expected in current phase"))
        $checks.Add((New-AxiomReadinessCheck "shutdown not requested" (-not $shutdownRequested) "shutdown_requested=$shutdownRequested"))

        if ($session.safe_pass_disabled_reason) {
            $checks.Add((New-AxiomReadinessCheck "safe-pass reason present" $true ([string]$session.safe_pass_disabled_reason) "warning"))
        }
    }

    if ($taskSummary) {
        $runningCount = Convert-AxiomReadinessInt $taskSummary.running_count
        $pendingManifestBoundCount = Convert-AxiomReadinessInt $taskSummary.pending_manifest_bound_count
        $pendingWithoutManifestCount = Convert-AxiomReadinessInt $taskSummary.pending_without_manifest_count
        $needsHumanInputCount = Convert-AxiomReadinessInt $taskSummary.needs_human_input_count
        $quarantinedCount = Convert-AxiomReadinessInt $taskSummary.quarantined_count
        $failedCount = Convert-AxiomReadinessInt $taskSummary.failed_count

        $checks.Add((New-AxiomReadinessCheck "one-running-task invariant" ($runningCount -le 1) "running_count=$runningCount"))
        $checks.Add((New-AxiomReadinessCheck "no running task" ($runningCount -eq 0) "running_count=$runningCount"))
        $checks.Add((New-AxiomReadinessCheck "pending manifest-bound tasks" ($pendingManifestBoundCount -gt 0) "count=$pendingManifestBoundCount" "warning"))
        $checks.Add((New-AxiomReadinessCheck "pending without manifest" ($pendingWithoutManifestCount -eq 0) "count=$pendingWithoutManifestCount"))
        $checks.Add((New-AxiomReadinessCheck "needs human input" ($needsHumanInputCount -eq 0) "count=$needsHumanInputCount" "warning"))
        $checks.Add((New-AxiomReadinessCheck "quarantined tasks" ($quarantinedCount -eq 0) "count=$quarantinedCount" "warning"))
        $checks.Add((New-AxiomReadinessCheck "failed tasks" ($failedCount -eq 0) "count=$failedCount" "warning"))
    }
    else {
        $checks.Add((New-AxiomReadinessCheck "task summary" $false "unavailable"))
    }

    $hasHeartbeat = $null -ne $heartbeat
    $checks.Add((New-AxiomReadinessCheck "scheduler heartbeat exists" $hasHeartbeat $(if ($hasHeartbeat) { "heartbeat_id=$($heartbeat.heartbeat_id)" } else { "none found" })))

    if ($heartbeat) {
        $ageSeconds = Get-AxiomReadinessHeartbeatAgeSeconds -Heartbeat $heartbeat

        if ($null -ne $ageSeconds) {
            $fresh = $ageSeconds -le 120
            $checks.Add((New-AxiomReadinessCheck "heartbeat freshness estimate" $fresh "age_seconds=$ageSeconds; threshold=120"))
        }
        else {
            $checks.Add((New-AxiomReadinessCheck "heartbeat freshness estimate" $false "unable to parse last_freshness_at" "warning"))
        }

        $activeTaskId = [string]$heartbeat.active_task_id
        $checks.Add((New-AxiomReadinessCheck "heartbeat active task clear" ([string]::IsNullOrWhiteSpace($activeTaskId)) "active_task_id=$activeTaskId"))
    }

    $checks.Add((New-AxiomReadinessCheck "tool-capability map active" $toolMapPresent "security.tool_capability_map.v1"))

    $hasActiveManifests = $manifestSummary.Count -gt 0
    $checks.Add((New-AxiomReadinessCheck "active manifests present" $hasActiveManifests "active_manifest_groups=$($manifestSummary.Count)"))

    $hasCurrentTrustedModel = $null -ne $currentModel
    $checks.Add((New-AxiomReadinessCheck "current trusted model profile" (-not $hasCurrentTrustedModel) "absent by design in current phase"))

    if ($latestModel) {
        $checks.Add((New-AxiomReadinessCheck "latest model profile recorded" $true "$($latestModel.model_name) / $($latestModel.registration_status) / current=$($latestModel.is_current)" "warning"))
    }
    else {
        $checks.Add((New-AxiomReadinessCheck "latest model profile recorded" $false "none found" "warning"))
    }

    $lifecycleAuditTool = Test-Path (Join-Path $script:AxiomRoot "tools\audit_task_lifecycle.py")
    $executionAuditTool = Test-Path (Join-Path $script:AxiomRoot "tools\audit_task_execution.py")
    $supervisorTool = Test-Path (Join-Path $script:AxiomRoot "tools\supervisor_health_check.py")
    $foundationTool = Test-Path (Join-Path $script:AxiomRoot "tools\verify_foundation.py")

    $checks.Add((New-AxiomReadinessCheck "foundation tool exists" $foundationTool "tools\verify_foundation.py"))
    $checks.Add((New-AxiomReadinessCheck "lifecycle audit tool exists" $lifecycleAuditTool "tools\audit_task_lifecycle.py"))
    $checks.Add((New-AxiomReadinessCheck "execution audit tool exists" $executionAuditTool "tools\audit_task_execution.py"))
    $checks.Add((New-AxiomReadinessCheck "supervisor health tool exists" $supervisorTool "tools\supervisor_health_check.py"))

    foreach ($check in $checks) {
        Write-AxiomReadinessCheck $check
    }

    $blockingFailures = @($checks | Where-Object { -not $_.Passed -and $_.Severity -ne "warning" })
    $warnings = @($checks | Where-Object { -not $_.Passed -and $_.Severity -eq "warning" })

    Write-Host ""

    if ($blockingFailures.Count -eq 0) {
        Write-Host "Readiness: READY FOR SAFE MANUAL IMPLEMENTATION STEP" -ForegroundColor Green
        Write-Host "Meaning: State is clean enough to continue bounded implementation work." -ForegroundColor Gray
    }
    else {
        Write-Host "Readiness: BLOCKED" -ForegroundColor Red
        Write-Host "Meaning: Resolve blocking checks before relying on this session for implementation work." -ForegroundColor Gray
    }

    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $($warning.Name): $($warning.Detail)" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host "  axiom-regression" -ForegroundColor Gray
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host ""
}

