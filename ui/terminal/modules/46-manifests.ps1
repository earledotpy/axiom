# ============================================================
# AXIOM Terminal Manifest Integrity Panel
# File: C:\axiom\ui\terminal\modules\46-manifests.ps1
#
# Purpose:
#   Read-only manifest/tool-capability integrity visibility.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro, reads manifest files from disk,
#   and computes local SHA256 hashes.
#
#   It must not run register_manifests.py.
#   It must not repair, activate, deactivate, or rewrite manifests.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomManifestDbPath = Join-Path $script:AxiomRoot "axiom.db"
$script:AxiomPolicyRoot = Join-Path $script:AxiomRoot "axiom\policy"
$script:AxiomToolCapabilityMapPath = Join-Path $script:AxiomPolicyRoot "security_artifacts\tool_capability_map.json"
$script:AxiomManifestSchemaPath = Join-Path $script:AxiomPolicyRoot "schemas\manifest_schema.json"
$script:AxiomToolCapabilityMapSchemaPath = Join-Path $script:AxiomPolicyRoot "schemas\tool_capability_map_schema.json"

function Invoke-AxiomManifestQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomManifestDbPath)) {
        return $null
    }

    $payload = @{
        db = $script:AxiomManifestDbPath
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

function Get-AxiomActiveManifestRows {
    return Invoke-AxiomManifestQuery -Sql @"
SELECT
    fingerprint_id,
    manifest_id,
    manifest_type,
    relative_path,
    sha256,
    schema_version,
    manifest_version,
    role_name,
    command_name,
    approved_by_panel_version,
    active,
    registered_by_tool_version,
    registered_at
FROM manifest_fingerprints
WHERE active = 1
ORDER BY
    CASE manifest_type
        WHEN 'tool_capability_map' THEN 1
        WHEN 'role' THEN 2
        WHEN 'operator_control' THEN 3
        ELSE 99
    END,
    manifest_id
"@
}

function Get-AxiomInactiveManifestCount {
    $rows = Invoke-AxiomManifestQuery -Sql @"
SELECT COUNT(*) AS count
FROM manifest_fingerprints
WHERE active = 0
"@

    if ($rows -and $rows.Count -gt 0) {
        return [int]$rows[0].count
    }

    return 0
}

function Get-AxiomManifestTypeCounts {
    return Invoke-AxiomManifestQuery -Sql @"
SELECT
    manifest_type,
    active,
    COUNT(*) AS count
FROM manifest_fingerprints
GROUP BY manifest_type, active
ORDER BY manifest_type, active DESC
"@
}

function Resolve-AxiomManifestFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $normalized = $RelativePath.Replace("/", "\")

    if ($normalized -like "policy\*") {
        return Join-Path (Join-Path $script:AxiomRoot "axiom") $normalized
    }

    return Join-Path $script:AxiomRoot $normalized
}

function Get-AxiomFileSha256 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    catch {
        return $null
    }
}

function Read-AxiomJsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Write-AxiomManifestLine {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "Gray"
    )

    Write-Host ("  {0,-32}" -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Write-AxiomManifestRowTable {
    param(
        [object[]]$Rows
    )

    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host "  no active manifests registered" -ForegroundColor Yellow
        return
    }

    Write-Host ("  {0,-34} {1,-19} {2,-8} {3,-10} {4}" -f `
        "manifest_id", "type", "hash", "binding", "path"
    ) -ForegroundColor DarkGray

    Write-Host ("  {0,-34} {1,-19} {2,-8} {3,-10} {4}" -f `
        "-----------", "----", "----", "-------", "----"
    ) -ForegroundColor DarkGray

    foreach ($row in $Rows) {
        $filePath = Resolve-AxiomManifestFilePath -RelativePath ([string]$row.relative_path)
        $actualHash = Get-AxiomFileSha256 -Path $filePath
        $registeredHash = ([string]$row.sha256).ToLowerInvariant()

        $hashStatus = "missing"
        $color = "Red"

        if ($actualHash) {
            if ($actualHash -eq $registeredHash) {
                $hashStatus = "match"
                $color = "Green"
            }
            else {
                $hashStatus = "mismatch"
                $color = "Red"
            }
        }

        $binding = "-"
        if ($row.manifest_type -eq "role") {
            $binding = [string]$row.role_name
        }
        elseif ($row.manifest_type -eq "operator_control") {
            $binding = [string]$row.command_name
        }
        elseif ($row.manifest_type -eq "tool_capability_map") {
            $binding = "security"
        }

        Write-Host ("  {0,-34} {1,-19} {2,-8} {3,-10} {4}" -f `
            $row.manifest_id,
            $row.manifest_type,
            $hashStatus,
            $binding,
            $row.relative_path
        ) -ForegroundColor $color
    }
}

function Get-AxiomManifestHashFindings {
    param(
        [object[]]$Rows
    )

    $findings = New-Object System.Collections.Generic.List[object]

    foreach ($row in $Rows) {
        $filePath = Resolve-AxiomManifestFilePath -RelativePath ([string]$row.relative_path)
        $actualHash = Get-AxiomFileSha256 -Path $filePath
        $registeredHash = ([string]$row.sha256).ToLowerInvariant()

        if (-not $actualHash) {
            $findings.Add([pscustomobject]@{
                manifest_id = $row.manifest_id
                status = "missing_file"
                detail = $filePath
            })
            continue
        }

        if ($actualHash -ne $registeredHash) {
            $findings.Add([pscustomobject]@{
                manifest_id = $row.manifest_id
                status = "sha256_mismatch"
                detail = "registered=$registeredHash actual=$actualHash"
            })
        }
    }

    return $findings.ToArray()
}

function Get-AxiomToolCapabilityMapSummary {
    $toolMap = Read-AxiomJsonFile -Path $script:AxiomToolCapabilityMapPath

    if (-not $toolMap) {
        return [pscustomobject]@{
            exists = (Test-Path $script:AxiomToolCapabilityMapPath)
            json_ok = $false
            schema_version = $null
            artifact_id = $null
            approved_by = $null
            tool_count = 0
            operator_control_tool_count = 0
            standard_tool_count = 0
        }
    }

    $toolNames = @($toolMap.tools.PSObject.Properties.Name)
    $operatorControlTools = @($toolNames | Where-Object { $_ -like "session_controller.*" })
    $standardTools = @($toolNames | Where-Object { $_ -notlike "session_controller.*" })

    return [pscustomobject]@{
        exists = $true
        json_ok = $true
        schema_version = [string]$toolMap.schema_version
        artifact_id = [string]$toolMap.artifact_id
        approved_by = [string]$toolMap.approved_by_panel_version
        tool_count = $toolNames.Count
        operator_control_tool_count = $operatorControlTools.Count
        standard_tool_count = $standardTools.Count
    }
}

function axiom-manifests {
    Write-AxiomUiTitle "MANIFEST INTEGRITY" "SHA256 · active manifests"

    if (-not (Test-Path $script:AxiomRoot)) {
        Write-AxiomManifestLine "root" "$script:AxiomRoot missing" "Red"
        Write-Host ""
        return
    }

    if (-not (Test-Path $script:AxiomManifestDbPath)) {
        Write-AxiomManifestLine "database" "$script:AxiomManifestDbPath missing" "Red"
        Write-Host ""
        return
    }

    $rows = @(Get-AxiomActiveManifestRows)
    $inactiveCount = Get-AxiomInactiveManifestCount
    $typeCounts = @(Get-AxiomManifestTypeCounts)
    $findings = @(Get-AxiomManifestHashFindings -Rows $rows)
    $toolMapSummary = Get-AxiomToolCapabilityMapSummary

    Write-AxiomUiSection "Files"
    Write-AxiomManifestLine "manifest schema" $script:AxiomManifestSchemaPath $(if (Test-Path $script:AxiomManifestSchemaPath) { "Green" } else { "Red" })
    Write-AxiomManifestLine "tool map schema" $script:AxiomToolCapabilityMapSchemaPath $(if (Test-Path $script:AxiomToolCapabilityMapSchemaPath) { "Green" } else { "Red" })
    Write-AxiomManifestLine "tool capability map" $script:AxiomToolCapabilityMapPath $(if (Test-Path $script:AxiomToolCapabilityMapPath) { "Green" } else { "Red" })

    Write-AxiomUiSection "Registry counts"
    Write-AxiomManifestLine "active rows" ([string]$rows.Count) $(if ($rows.Count -gt 0) { "Green" } else { "Yellow" })
    Write-AxiomManifestLine "inactive rows" ([string]$inactiveCount) "Gray"

    if ($typeCounts.Count -gt 0) {
        foreach ($countRow in $typeCounts) {
            $label = "$($countRow.manifest_type) active=$($countRow.active)"
            Write-AxiomManifestLine $label ([string]$countRow.count) "Gray"
        }
    }

    Write-AxiomUiSection "Active manifest rows"
    Write-AxiomManifestRowTable -Rows $rows

    Write-AxiomUiSection "Tool-capability map"
    Write-AxiomManifestLine "exists" ([string]$toolMapSummary.exists) $(if ($toolMapSummary.exists) { "Green" } else { "Red" })
    Write-AxiomManifestLine "json parses" ([string]$toolMapSummary.json_ok) $(if ($toolMapSummary.json_ok) { "Green" } else { "Red" })
    Write-AxiomManifestLine "schema_version" ([string]$toolMapSummary.schema_version) "Gray"
    Write-AxiomManifestLine "artifact_id" ([string]$toolMapSummary.artifact_id) "Gray"
    Write-AxiomManifestLine "approved_by" ([string]$toolMapSummary.approved_by) "Gray"
    Write-AxiomManifestLine "tool count" ([string]$toolMapSummary.tool_count) $(if ($toolMapSummary.tool_count -ge 14) { "Green" } else { "Yellow" })
    Write-AxiomManifestLine "standard tools" ([string]$toolMapSummary.standard_tool_count) "Gray"
    Write-AxiomManifestLine "operator-control tools" ([string]$toolMapSummary.operator_control_tool_count) "Gray"

    Write-AxiomUiSection "Integrity assessment"

    if ($findings.Count -eq 0 -and $rows.Count -gt 0) {
        Write-AxiomManifestLine "registered file hashes" "all active rows match disk" "Green"
    }
    elseif ($rows.Count -eq 0) {
        Write-AxiomManifestLine "registered file hashes" "no active rows to check" "Yellow"
    }
    else {
        Write-AxiomManifestLine "registered file hashes" "$($findings.Count) finding(s)" "Red"

        foreach ($finding in $findings) {
            Write-Host "  - $($finding.manifest_id): $($finding.status)" -ForegroundColor Red
            Write-Host "    $($finding.detail)" -ForegroundColor DarkGray
        }
    }

    $toolMapRegistered = @($rows | Where-Object { $_.manifest_id -eq "security.tool_capability_map.v1" -and $_.manifest_type -eq "tool_capability_map" })

    if ($toolMapRegistered.Count -eq 1) {
        Write-AxiomManifestLine "tool map registered" "security.tool_capability_map.v1 active" "Green"
    }
    elseif ($toolMapRegistered.Count -eq 0) {
        Write-AxiomManifestLine "tool map registered" "missing active row" "Red"
    }
    else {
        Write-AxiomManifestLine "tool map registered" "multiple active rows" "Red"
    }

    Write-AxiomUiSection "Canonical rule"
    Write-Host "  Manifest SHA256 mismatch, missing registration, or tool-capability-map" -ForegroundColor Gray
    Write-Host "  integrity failure must fail closed. This panel reports only; it does not repair." -ForegroundColor Gray
    Write-Host ""

    Write-AxiomUiSection "Next safe commands"
    Write-Host "  axiom-dashboard" -ForegroundColor Gray
    Write-Host "  axiom-readiness" -ForegroundColor Gray
    Write-Host "  axiom-preflight" -ForegroundColor Gray
    Write-Host ""
}
