# ============================================================
# AXIOM Terminal Budget / Resource Usage Panel
# File: C:\axiom\ui\terminal\modules\47-budget.ps1
#
# Purpose:
#   Read-only provider/resource budget visibility.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It must not call providers, models, gateways, budget
#   reconciliation tools, or resource mutation paths.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomBudgetDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomBudgetQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomBudgetDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomBudgetDbPath
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

function Get-AxiomBudgetLatestSession {
    $rows = Invoke-AxiomBudgetQuery -Sql @"
SELECT
    session_id,
    created_at,
    scheduler_status,
    autonomous_operation_enabled,
    safe_pass_enabled
FROM sessions
ORDER BY session_id DESC
LIMIT 1
"@

    if ($rows -and $rows.Count -gt 0) {
        return $rows[0]
    }

    return $null
}

function Get-AxiomProviderUsageSummary {
    param(
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    provider,
    status,
    COUNT(*) AS count,
    COALESCE(SUM(estimated_input_tokens), 0) AS estimated_input_tokens,
    COALESCE(SUM(estimated_output_tokens), 0) AS estimated_output_tokens,
    COALESCE(SUM(actual_input_tokens), 0) AS actual_input_tokens,
    COALESCE(SUM(actual_output_tokens), 0) AS actual_output_tokens,
    COALESCE(SUM(charged_input_estimate), 0) AS charged_input_estimate,
    COALESCE(SUM(charged_output_estimate), 0) AS charged_output_estimate
FROM provider_usage
WHERE session_id = ?
GROUP BY provider, status
ORDER BY provider, status
"@ -Params @($Session.session_id)
}

function Get-AxiomProviderUsageRiskRows {
    param(
        [object]$Session,
        [int]$Limit = 10
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    usage_id,
    task_id,
    provider,
    model,
    status,
    estimated_input_tokens,
    estimated_output_tokens,
    actual_input_tokens,
    actual_output_tokens,
    actuals_unavailable,
    substr(coalesce(error_info, ''), 1, 100) AS error_preview,
    created_at,
    completed_at
FROM provider_usage
WHERE session_id = ?
  AND status IN ('failed', 'rate_limited', 'quota_exhausted', 'abandoned_session_crash')
ORDER BY created_at DESC, usage_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Get-AxiomProviderBudgetWindows {
    param(
        [int]$Limit = 10
    )

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    window_id,
    provider,
    window_start,
    window_end,
    budget_tokens,
    used_tokens,
    budget_requests,
    used_requests,
    status,
    updated_at
FROM provider_budget_windows
ORDER BY
    CASE status
        WHEN 'open' THEN 1
        WHEN 'exhausted' THEN 2
        WHEN 'closed' THEN 3
        ELSE 99
    END,
    window_start DESC
LIMIT ?
"@ -Params @($Limit)
}

function Get-AxiomProviderReconciliations {
    param(
        [int]$Limit = 10
    )

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    reconciliation_id,
    provider,
    date_range_start,
    date_range_end,
    operator_reported_input_tokens,
    operator_reported_output_tokens,
    local_estimated_tokens,
    adjustment_tokens,
    discrepancy_percent,
    confirmed_large_adjustment,
    created_at
FROM provider_usage_reconciliations
ORDER BY created_at DESC, reconciliation_id DESC
LIMIT ?
"@ -Params @($Limit)
}

function Get-AxiomResourceUsageSummary {
    param(
        [object]$Session
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    ru.resource_type,
    ru.status,
    COUNT(*) AS count,
    COALESCE(SUM(ru.amount), 0) AS total_amount,
    COALESCE(MAX(ru.amount), 0) AS max_amount,
    COALESCE(MAX(ru.limit_value), 0) AS max_limit
FROM resource_usage ru
JOIN tasks t ON t.task_id = ru.task_id
WHERE t.session_id = ?
GROUP BY ru.resource_type, ru.status
ORDER BY ru.resource_type, ru.status
"@ -Params @($Session.session_id)
}

function Get-AxiomResourceUsageExceeded {
    param(
        [object]$Session,
        [int]$Limit = 10
    )

    if (-not $Session) {
        return @()
    }

    return Invoke-AxiomBudgetQuery -Sql @"
SELECT
    ru.usage_id,
    ru.task_id,
    ru.resource_type,
    ru.amount,
    ru.limit_value,
    ru.status,
    substr(coalesce(ru.details_json, ''), 1, 100) AS details_preview,
    ru.created_at
FROM resource_usage ru
JOIN tasks t ON t.task_id = ru.task_id
WHERE t.session_id = ?
  AND ru.status = 'exceeded'
ORDER BY ru.created_at DESC, ru.usage_id DESC
LIMIT ?
"@ -Params @($Session.session_id, $Limit)
}

function Write-AxiomBudgetLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Format-AxiomBudgetNumber {
    param([object]$Value)

    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
        return "0"
    }

    try {
        return ([int64]$Value).ToString("N0")
    }
    catch {
        return [string]$Value
    }
}

function Write-AxiomProviderUsageTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no provider usage rows for latest session" -ForegroundColor DarkGray
        return
    }

    Write-Host ("  {0,-14} {1,-24} {2,-7} {3,-12} {4,-12} {5,-12} {6}" -f `
        "provider", "status", "count", "est_in", "est_out", "act_in", "act_out"
    ) -ForegroundColor DarkGray

    Write-Host ("  {0,-14} {1,-24} {2,-7} {3,-12} {4,-12} {5,-12} {6}" -f `
        "--------", "------", "-----", "------", "-------", "------", "-------"
    ) -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $color = "Gray"
        if ($row.status -in @("failed", "rate_limited", "quota_exhausted", "abandoned_session_crash")) {
            $color = "Red"
        }
        elseif ($row.status -eq "completed") {
            $color = "Green"
        }
        elseif ($row.status -eq "started") {
            $color = "Yellow"
        }

        Write-Host ("  {0,-14} {1,-24} {2,-7} {3,-12} {4,-12} {5,-12} {6}" -f `
            $row.provider,
            $row.status,
            $row.count,
            (Format-AxiomBudgetNumber $row.estimated_input_tokens),
            (Format-AxiomBudgetNumber $row.estimated_output_tokens),
            (Format-AxiomBudgetNumber $row.actual_input_tokens),
            (Format-AxiomBudgetNumber $row.actual_output_tokens)
        ) -ForegroundColor $color
    }
}

function Write-AxiomBudgetWindowTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no provider budget windows recorded" -ForegroundColor DarkGray
        return
    }

    Write-Host ("  {0,-12} {1,-10} {2,-12} {3,-12} {4,-10} {5,-10} {6}" -f `
        "provider", "status", "tokens", "used", "requests", "used_req", "window"
    ) -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $color = if ($row.status -eq "exhausted") { "Red" } elseif ($row.status -eq "open") { "Green" } else { "Gray" }

        Write-Host ("  {0,-12} {1,-10} {2,-12} {3,-12} {4,-10} {5,-10} {6} → {7}" -f `
            $row.provider,
            $row.status,
            (Format-AxiomBudgetNumber $row.budget_tokens),
            (Format-AxiomBudgetNumber $row.used_tokens),
            (Format-AxiomBudgetNumber $row.budget_requests),
            (Format-AxiomBudgetNumber $row.used_requests),
            $row.window_start,
            $row.window_end
        ) -ForegroundColor $color
    }
}

function Write-AxiomResourceUsageTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no resource usage rows for latest session" -ForegroundColor DarkGray
        return
    }

    Write-Host ("  {0,-30} {1,-14} {2,-7} {3,-12} {4,-12} {5}" -f `
        "resource_type", "status", "count", "total", "max", "limit"
    ) -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $color = if ($row.status -eq "exceeded") { "Red" } elseif ($row.status -eq "within_limit") { "Green" } else { "Yellow" }

        Write-Host ("  {0,-30} {1,-14} {2,-7} {3,-12} {4,-12} {5}" -f `
            $row.resource_type,
            $row.status,
            $row.count,
            $row.total_amount,
            $row.max_amount,
            $row.max_limit
        ) -ForegroundColor $color
    }
}

function Write-AxiomBudgetRiskRows {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        Write-Host "  provider=$($row.provider) status=$($row.status) task=$($row.task_id) usage=$($row.usage_id) created=$($row.created_at)" -ForegroundColor Red

        if ($row.error_preview) {
            Write-Host "    error: $($row.error_preview)" -ForegroundColor DarkGray
        }
    }
}

function Write-AxiomResourceExceededRows {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
        return
    }

    foreach ($row in $Rows) {
        Write-Host "  task=$($row.task_id) resource=$($row.resource_type) amount=$($row.amount) limit=$($row.limit_value) created=$($row.created_at)" -ForegroundColor Red

        if ($row.details_preview) {
            Write-Host "    details: $($row.details_preview)" -ForegroundColor DarkGray
        }
    }
}

function axiom-budget {
    param(
        [int]$Limit = 10
    )

    Write-AxiomUiTitle "BUDGET / RESOURCE USAGE" "provider usage · read-only"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomBudgetLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomBudgetDbPath)) {
        Write-AxiomBudgetLine "database" "$script:AxiomBudgetDbPath missing" "Red"
        Write-Host ""
        return
    }

    $session = Get-AxiomBudgetLatestSession

    if (-not $session) {
        Write-AxiomBudgetLine "latest session" "none found" "Yellow"
        Write-Host ""
        return
    }

    $providerSummary = @(Get-AxiomProviderUsageSummary -Session $session)
    $providerRisks = @(Get-AxiomProviderUsageRiskRows -Session $session -Limit $Limit)
    $budgetWindows = @(Get-AxiomProviderBudgetWindows -Limit $Limit)
    $reconciliations = @(Get-AxiomProviderReconciliations -Limit $Limit)
    $resourceSummary = @(Get-AxiomResourceUsageSummary -Session $session)
    $resourceExceeded = @(Get-AxiomResourceUsageExceeded -Session $session -Limit $Limit)

    Write-AxiomUiSection "Session"
    Write-AxiomBudgetLine "session_id" ([string]$session.session_id) "Green"
    Write-AxiomBudgetLine "scheduler_status" ([string]$session.scheduler_status) "Cyan"
    Write-AxiomBudgetLine "autonomous_enabled" ([string]$session.autonomous_operation_enabled) "Yellow"
    Write-AxiomBudgetLine "safe_pass_enabled" ([string]$session.safe_pass_enabled) "Yellow"

    Write-AxiomUiSection "Provider usage by status"
    Write-AxiomProviderUsageTable -Rows $providerSummary

    Write-AxiomUiSection "Provider risk rows"
    Write-AxiomBudgetRiskRows -Rows $providerRisks

    Write-AxiomUiSection "Provider budget windows"
    Write-AxiomBudgetWindowTable -Rows $budgetWindows

    Write-AxiomUiSection "Recent reconciliations"
    if ($reconciliations.Count -eq 0) {
        Write-Host "  none" -ForegroundColor DarkGray
    }
    else {
        foreach ($row in $reconciliations) {
            $color = if ($row.confirmed_large_adjustment -eq 1) { "Yellow" } else { "Gray" }
            Write-Host "  $($row.provider) $($row.date_range_start) → $($row.date_range_end) discrepancy=$($row.discrepancy_percent)% adjustment=$($row.adjustment_tokens)" -ForegroundColor $color
        }
    }

    Write-AxiomUiSection "Resource usage by status"
    Write-AxiomResourceUsageTable -Rows $resourceSummary

    Write-AxiomUiSection "Exceeded resource rows"
    Write-AxiomResourceExceededRows -Rows $resourceExceeded

    Write-AxiomUiSection "Canonical limits / current phase"
    Write-Host "  - context bundle cap: 500 KB serialized size" -ForegroundColor Gray
    Write-Host "  - sandbox cap when implemented: 256 MB RAM / 60 seconds wall-clock" -ForegroundColor Gray
    Write-Host "  - sqlite-vec batch cap: 100 vectors" -ForegroundColor Gray
    Write-Host "  - real model/cloud/network calls are not current-phase terminal actions" -ForegroundColor Yellow
    Write-Host ""

    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
