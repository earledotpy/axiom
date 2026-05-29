# ============================================================
# AXIOM Terminal Event Panel
# File: C:\axiom\ui\terminal\modules\48-events.ps1
#
# Purpose:
#   Read-only recent session/security event visibility.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It must not insert events, repair sessions, alter scheduler
#   state, execute operator-control actions, or change policy state.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomEventsDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomEventsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomEventsDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomEventsDbPath
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

function Get-AxiomEventsLatestSession {
    $rows = Invoke-AxiomEventsQuery -Sql @"
SELECT
    session_id,
    created_at,
    ended_at,
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

function Get-AxiomSessionEventCounts {
    param(
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    event_type,
    COUNT(*) AS count
FROM session_events
WHERE session_id = ?
GROUP BY event_type
ORDER BY count DESC, event_type
"@ -Params @($Session.session_id)
}

function Get-AxiomSecurityEventCounts {
    param(
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    severity,
    event_type,
    COUNT(*) AS count
FROM security_events
WHERE session_id = ?
GROUP BY severity, event_type
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'warning' THEN 2
        WHEN 'info' THEN 3
        ELSE 99
    END,
    count DESC,
    event_type
"@ -Params @($Session.session_id)
}

function Get-AxiomRecentSessionEvents {
    param(
        [object]$Session,
        [int]$Limit = 12
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    event_id,
    event_type,
    substr(coalesce(details_json, ''), 1, 160) AS details_preview,
    created_at
FROM session_events
WHERE session_id = ?
ORDER BY created_at DESC, event_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Get-AxiomRecentSecurityEvents {
    param(
        [object]$Session,
        [int]$Limit = 12
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    event_id,
    task_id,
    event_type,
    severity,
    reason,
    substr(coalesce(details_json, ''), 1, 160) AS details_preview,
    created_at
FROM security_events
WHERE session_id = ?
ORDER BY created_at DESC, event_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Get-AxiomRecentSecurityRisks {
    param(
        [object]$Session,
        [int]$Limit = 10
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    event_id,
    task_id,
    event_type,
    severity,
    reason,
    substr(coalesce(details_json, ''), 1, 160) AS details_preview,
    created_at
FROM security_events
WHERE session_id = ?
  AND severity IN ('critical', 'warning')
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'warning' THEN 2
        ELSE 99
    END,
    created_at DESC,
    event_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Get-AxiomGlobalRecentSecurityRisks {
    param(
        [int]$Limit = 10
    )

    return Invoke-AxiomEventsQuery -Sql @"
SELECT
    event_id,
    session_id,
    task_id,
    event_type,
    severity,
    reason,
    substr(coalesce(details_json, ''), 1, 160) AS details_preview,
    created_at
FROM security_events
WHERE severity IN ('critical', 'warning')
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'warning' THEN 2
        ELSE 99
    END,
    created_at DESC,
    event_id DESC
LIMIT ?
"@ -Params @($Limit)
}

function Write-AxiomEventsLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Get-AxiomEventSeverityColor {
    param([string]$Severity)

    if ($Severity -eq "critical") {
        return "Red"
    }

    if ($Severity -eq "warning") {
        return "Yellow"
    }

    return "Gray"
}

function Write-AxiomSessionEventTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no session events for latest session" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        Write-Host "  [$($row.event_id)] $($row.created_at)  $($row.event_type)" -ForegroundColor Gray

        if ($row.details_preview) {
            Write-Host "       details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function Write-AxiomSecurityEventTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no security events for latest session" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $color = Get-AxiomEventSeverityColor -Severity ([string]$row.severity)

        Write-Host "  [$($row.event_id)] $($row.created_at)  $($row.severity)  $($row.event_type)  task=$($row.task_id)" -ForegroundColor $color

        if ($row.reason) {
            Write-Host "       reason: $($row.reason)" -ForegroundColor DarkGray
        }

        if ($row.details_preview) {
            Write-Host "       details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function Write-AxiomSecurityRiskTable {
    param(
        [object[]]$Rows,
        [bool]$Global = $false
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        $color = Get-AxiomEventSeverityColor -Severity ([string]$row.severity)

        if ($Global) {
            Write-Host "  [$($row.event_id)] session=$($row.session_id) task=$($row.task_id) $($row.severity) $($row.event_type) $($row.created_at)" -ForegroundColor $color
        }
        else {
            Write-Host "  [$($row.event_id)] task=$($row.task_id) $($row.severity) $($row.event_type) $($row.created_at)" -ForegroundColor $color
        }

        if ($row.reason) {
            Write-Host "       reason: $($row.reason)" -ForegroundColor DarkGray
        }

        if ($row.details_preview) {
            Write-Host "       details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function axiom-events {
    param(
        [int]$Limit = 12,
        [switch]$GlobalRisks
    )

    Write-AxiomUiTitle "LIVE EVENT STREAM" "session events · security events"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomEventsLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomEventsDbPath)) {
        Write-AxiomEventsLine "database" "$script:AxiomEventsDbPath missing" "Red"
        Write-Host ""
        return
    }

    $session = Get-AxiomEventsLatestSession

    if (-not $session) {
        Write-AxiomEventsLine "latest session" "none found" "Yellow"
        Write-Host ""
        return
    }

    $sessionCounts = @(Get-AxiomSessionEventCounts -Session $session)
    $securityCounts = @(Get-AxiomSecurityEventCounts -Session $session)
    $sessionEvents = @(Get-AxiomRecentSessionEvents -Session $session -Limit $Limit)
    $securityEvents = @(Get-AxiomRecentSecurityEvents -Session $session -Limit $Limit)
    $securityRisks = @(Get-AxiomRecentSecurityRisks -Session $session -Limit $Limit)

    Write-AxiomUiSection "Session"
    Write-AxiomEventsLine "session_id" ([string]$session.session_id) "Green"
    Write-AxiomEventsLine "scheduler_status" ([string]$session.scheduler_status) "Cyan"
    Write-AxiomEventsLine "autonomous_enabled" ([string]$session.autonomous_operation_enabled) "Yellow"
    Write-AxiomEventsLine "safe_pass_enabled" ([string]$session.safe_pass_enabled) "Yellow"

    if ($session.safe_pass_disabled_reason) {
        Write-AxiomEventsLine "safe_pass_reason" ([string]$session.safe_pass_disabled_reason) "Yellow"
    }

    Write-AxiomUiRule
    Write-AxiomUiSection "Event counts"

    if ($sessionCounts.Count -eq 0) {
        Write-AxiomEventsLine "session events" "0" "Gray"
    }
    else {
        foreach ($row in $sessionCounts) {
            Write-AxiomEventsLine "session:$($row.event_type)" ([string]$row.count) "Gray"
        }
    }

    if ($securityCounts.Count -eq 0) {
        Write-AxiomEventsLine "security events" "0" "Gray"
    }
    else {
        foreach ($row in $securityCounts) {
            $color = Get-AxiomEventSeverityColor -Severity ([string]$row.severity)
            Write-AxiomEventsLine "security:$($row.severity):$($row.event_type)" ([string]$row.count) $color
        }
    }

    Write-AxiomUiRule
    Write-AxiomUiSection "Recent security risks"
    Write-AxiomSecurityRiskTable -Rows $securityRisks

    if ($GlobalRisks) {
        $globalRiskRows = @(Get-AxiomGlobalRecentSecurityRisks -Limit $Limit)

        Write-AxiomUiRule
        Write-AxiomUiSection "Recent global security risks"
        Write-AxiomSecurityRiskTable -Rows $globalRiskRows -Global
    }

    Write-AxiomUiRule
    Write-AxiomUiSection "Recent session events"
    Write-AxiomSessionEventTable -Rows $sessionEvents

    Write-AxiomUiRule
    Write-AxiomUiSection "Recent security events"
    Write-AxiomSecurityEventTable -Rows $securityEvents

    Write-AxiomUiRule
    Write-AxiomUiSection "Interpretation"
    Write-Host "  - Critical security events should be treated as fail-closed signals." -ForegroundColor Gray
    Write-Host "  - Warning events may require investigation before continuing implementation." -ForegroundColor Gray
    Write-Host "  - This panel is read-only. It does not insert, repair, or acknowledge events." -ForegroundColor Gray
    Write-Host ""

    Write-AxiomUiRule
    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
