# ============================================================
# AXIOM Terminal Model Profile Panel
# File: C:\axiom\ui\terminal\modules\45-model.ps1
#
# Purpose:
#   Read-only model profile / trust-boundary visibility.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only.
#   It does not call Ollama, register fingerprints, promote profiles,
#   enable safe-pass, or alter calibration rows.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomModelDbPath = Join-Path $script:AxiomRoot "axiom.db"

function Invoke-AxiomModelQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomModelDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomModelDbPath
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

function Get-AxiomModelProfiles {
    param(
        [string]$ProfileLabel = "default",
        [int]$Limit = 10
    )

    return Invoke-AxiomModelQuery -Sql @"
SELECT
    profile_id,
    profile_label,
    model_name,
    ollama_host,
    ollama_model_tag,
    substr(ollama_model_digest, 1, 32) AS digest_preview,
    quantization,
    parameter_size,
    model_family,
    model_format,
    thinking_mode,
    thinking_mode_rule_version,
    calibration_run_id,
    is_current,
    registration_status,
    registered_by_tool_version,
    registered_at,
    substr(coalesce(notes, ''), 1, 180) AS notes_preview
FROM model_profile_fingerprints
WHERE profile_label = ?
ORDER BY profile_id DESC
LIMIT ?
"@ -Params @($ProfileLabel, $Limit)
}

function Get-AxiomCurrentModelProfiles {
    param(
        [string]$ProfileLabel = "default"
    )

    return Invoke-AxiomModelQuery -Sql @"
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
WHERE profile_label = ?
  AND is_current = 1
ORDER BY profile_id DESC
"@ -Params @($ProfileLabel)
}

function Get-AxiomModelCalibration {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CalibrationRunId
    )

    return Invoke-AxiomModelQuery -Sql @"
SELECT
    calibration_run_id,
    calibration_set_id,
    model_name,
    ollama_host,
    threshold,
    passed,
    false_positive_rate,
    false_negative_rate,
    approved_by_panel_version,
    created_at
FROM classifier_calibration_runs
WHERE calibration_run_id = ?
LIMIT 1
"@ -Params @($CalibrationRunId)
}

function Get-AxiomModelProfileLabels {
    return Invoke-AxiomModelQuery -Sql @"
SELECT
    profile_label,
    COUNT(*) AS profile_count,
    SUM(CASE WHEN is_current = 1 THEN 1 ELSE 0 END) AS current_count
FROM model_profile_fingerprints
GROUP BY profile_label
ORDER BY profile_label
"@
}

function Convert-AxiomModelBool {
    param([object]$Value)

    if ($null -eq $Value) {
        return $false
    }

    if ([string]$Value -eq "1" -or $Value -eq 1 -or $Value -eq $true) {
        return $true
    }

    return $false
}

function Write-AxiomModelLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-30}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Get-AxiomModelTrustAssessment {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Profile
    )

    $reasons = New-Object System.Collections.Generic.List[string]

    $isCurrent = Convert-AxiomModelBool $Profile.is_current

    if (-not $isCurrent) {
        $reasons.Add("is_current_not_set")
    }

    if ([string]$Profile.registration_status -ne "current") {
        $reasons.Add("registration_status_not_current")
    }

    if ([string]$Profile.thinking_mode -ne "disabled") {
        $reasons.Add("thinking_mode_not_disabled")
    }

    if ([string]::IsNullOrWhiteSpace([string]$Profile.calibration_run_id)) {
        $reasons.Add("missing_calibration_run_id")
    }
    elseif ([string]$Profile.calibration_run_id -eq "pending_calibration") {
        $reasons.Add("pending_calibration")
    }

    if ($reasons.Count -eq 0) {
        return [pscustomobject]@{
            trusted = $true
            reasons = @()
        }
    }

    return [pscustomobject]@{
        trusted = $false
        reasons = @($reasons)
    }
}

function Write-AxiomModelProfileTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no model profiles found" -ForegroundColor Yellow
        return
    }

    Write-Host ("  {0,-5} {1,-10} {2,-14} {3,-8} {4,-11} {5,-12} {6,-9} {7}" -f `
        "id", "label", "model", "current", "registration", "thinking", "quant", "calibration"
    ) -ForegroundColor DarkGray

    Write-Host ("  {0,-5} {1,-10} {2,-14} {3,-8} {4,-11} {5,-12} {6,-9} {7}" -f `
        "--", "-----", "-----", "-------", "------------", "--------", "-----", "-----------"
    ) -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $isCurrent = Convert-AxiomModelBool $row.is_current
        $assessment = Get-AxiomModelTrustAssessment -Profile $row

        $color = "Gray"
        if ($assessment.trusted) {
            $color = "Green"
        }
        elseif ($isCurrent -and -not $assessment.trusted) {
            $color = "Red"
        }
        elseif ($row.registration_status -eq "candidate") {
            $color = "Yellow"
        }

        Write-Host ("  {0,-5} {1,-10} {2,-14} {3,-8} {4,-12} {5,-12} {6,-9} {7}" -f `
            $row.profile_id,
            $row.profile_label,
            $row.model_name,
            $row.is_current,
            $row.registration_status,
            $row.thinking_mode,
            $row.quantization,
            $row.calibration_run_id
        ) -ForegroundColor $color
    }
}

function axiom-model {
    param(
        [string]$ProfileLabel = "default",
        [int]$Limit = 10
    )

    Write-Host ""
    Write-Host "AXIOM MODEL PROFILE / TRUST BOUNDARY" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomModelLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomModelDbPath)) {
        Write-AxiomModelLine "database" "$script:AxiomModelDbPath missing" "Red"
        Write-Host ""
        return
    }

    $labels = @(Get-AxiomModelProfileLabels)
    $profiles = @(Get-AxiomModelProfiles -ProfileLabel $ProfileLabel -Limit $Limit)
    $currentProfiles = @(Get-AxiomCurrentModelProfiles -ProfileLabel $ProfileLabel)

    Write-Host "Profile labels" -ForegroundColor DarkGreen
    if ($labels.Count -eq 0) {
        Write-AxiomModelLine "labels" "none found" "Yellow"
    }
    else {
        foreach ($label in $labels) {
            $color = if ([int]$label.current_count -gt 0) { "Green" } else { "Yellow" }
            Write-AxiomModelLine $label.profile_label "profiles=$($label.profile_count), current=$($label.current_count)" $color
        }
    }

    Write-Host ""
    Write-Host "Profiles for label: $ProfileLabel" -ForegroundColor DarkGreen
    Write-AxiomModelProfileTable -Rows $profiles

    Write-Host ""
    Write-Host "Trust assessment" -ForegroundColor DarkGreen

    if ($currentProfiles.Count -eq 0) {
        Write-AxiomModelLine "current trusted profile" "absent" "Yellow"
        Write-AxiomModelLine "interpretation" "expected in current fail-closed phase" "Gray"
    }
    elseif ($currentProfiles.Count -gt 1) {
        Write-AxiomModelLine "current trusted profile" "multiple current rows detected" "Red"
        Write-AxiomModelLine "count" ([string]$currentProfiles.Count) "Red"
    }
    else {
        $current = $currentProfiles[0]
        $assessment = Get-AxiomModelTrustAssessment -Profile $current

        if ($assessment.trusted) {
            Write-AxiomModelLine "current trusted profile" "trusted" "Green"
        }
        else {
            Write-AxiomModelLine "current trusted profile" "invalid current trust boundary" "Red"
            Write-AxiomModelLine "reasons" ($assessment.reasons -join ", ") "Red"
        }
    }

    if ($profiles.Count -gt 0) {
        $latest = $profiles[0]
        $latestAssessment = Get-AxiomModelTrustAssessment -Profile $latest

        Write-Host ""
        Write-Host "Latest profile detail" -ForegroundColor DarkGreen
        Write-AxiomModelLine "profile_id" ([string]$latest.profile_id) "Gray"
        Write-AxiomModelLine "model" ([string]$latest.model_name) "Cyan"
        Write-AxiomModelLine "host" ([string]$latest.ollama_host) "Gray"
        Write-AxiomModelLine "tag" ([string]$latest.ollama_model_tag) "Gray"
        Write-AxiomModelLine "digest preview" ([string]$latest.digest_preview) "Gray"
        Write-AxiomModelLine "quantization" ([string]$latest.quantization) "Cyan"
        Write-AxiomModelLine "parameter_size" ([string]$latest.parameter_size) "Gray"
        Write-AxiomModelLine "family/format" "$($latest.model_family) / $($latest.model_format)" "Gray"
        Write-AxiomModelLine "thinking_mode" ([string]$latest.thinking_mode) $(if ($latest.thinking_mode -eq "disabled") { "Green" } else { "Yellow" })
        Write-AxiomModelLine "thinking rule" ([string]$latest.thinking_mode_rule_version) "Gray"
        Write-AxiomModelLine "registration" ([string]$latest.registration_status) $(if ($latest.registration_status -eq "current") { "Green" } else { "Yellow" })
        Write-AxiomModelLine "is_current" ([string]$latest.is_current) $(if ((Convert-AxiomModelBool $latest.is_current)) { "Green" } else { "Yellow" })
        Write-AxiomModelLine "calibration" ([string]$latest.calibration_run_id) $(if ($latest.calibration_run_id -eq "pending_calibration") { "Yellow" } else { "Gray" })
        Write-AxiomModelLine "trusted now" ([string]$latestAssessment.trusted) $(if ($latestAssessment.trusted) { "Green" } else { "Yellow" })

        if (-not $latestAssessment.trusted) {
            Write-AxiomModelLine "blocking reasons" ($latestAssessment.reasons -join ", ") "Yellow"
        }

        if ($latest.calibration_run_id) {
            $calibrationRows = @(Get-AxiomModelCalibration -CalibrationRunId ([string]$latest.calibration_run_id))

            Write-Host ""
            Write-Host "Calibration row" -ForegroundColor DarkGreen

            if ($calibrationRows.Count -eq 0) {
                Write-AxiomModelLine "calibration" "row missing" "Red"
            }
            else {
                $cal = $calibrationRows[0]
                Write-AxiomModelLine "calibration_run_id" ([string]$cal.calibration_run_id) "Gray"
                Write-AxiomModelLine "model" ([string]$cal.model_name) "Gray"
                Write-AxiomModelLine "passed" ([string]$cal.passed) $(if ((Convert-AxiomModelBool $cal.passed)) { "Green" } else { "Yellow" })
                Write-AxiomModelLine "threshold" ([string]$cal.threshold) "Gray"
                Write-AxiomModelLine "approved_by" ([string]$cal.approved_by_panel_version) "Gray"
                Write-AxiomModelLine "created_at" ([string]$cal.created_at) "Gray"
            }
        }
    }

    Write-Host ""
    Write-Host "Canonical rule" -ForegroundColor DarkGreen
    Write-Host "  A profile is trusted only when registration_status=current," -ForegroundColor Gray
    Write-Host "  thinking_mode=disabled, calibration exists and passed, and is_current=1." -ForegroundColor Gray
    Write-Host "  Do not manually promote candidate profiles." -ForegroundColor Yellow
    Write-Host ""

    Write-Host "Next safe commands" -ForegroundColor DarkGreen
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
