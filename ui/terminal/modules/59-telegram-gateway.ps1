# ============================================================
# AXIOM Terminal Telegram Gateway Panel
# File: C:\axiom\ui\terminal\modules\59-telegram-gateway.ps1
#
# Purpose:
#   Read-only inspection of Phase 6G Telegram gateway state.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It reads SQLite using mode=ro only and reads config locally.
#   It must not process Telegram envelopes, confirm intents, poll Telegram,
#   register webhooks, send Telegram messages, or execute commands.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomTelegramGatewayDbPath = Join-Path $script:AxiomRoot "axiom.db"
$script:AxiomTelegramGatewayConfigPath = Join-Path $script:AxiomRoot "config\axiom.yaml"

function Invoke-AxiomTelegramGatewayPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Code,

        [hashtable]$Payload = @{}
    )

    $jsonPayload = $Payload | ConvertTo-Json -Depth 8 -Compress

    try {
        $json = $jsonPayload | python -c $Code 2>$null

        if ([string]::IsNullOrWhiteSpace($json)) {
            return $null
        }

        return $json | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-AxiomTelegramGatewayConfigSummary {
    $code = @'
import json
import sys
from pathlib import Path

import yaml

payload = json.loads(sys.stdin.read())
path = Path(payload["config"])

if not path.exists():
    print(json.dumps({"present": False}))
    raise SystemExit(0)

data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
section = data.get("telegram_gateway", {}) or {}

print(json.dumps({
    "present": True,
    "enabled": bool(section.get("enabled", False)),
    "operator_whitelist_count": len(section.get("operator_whitelist") or []),
    "allowed_chat_ids_count": len(section.get("allowed_chat_ids") or []),
    "capability_hash_count": len(section.get("capability_token_sha256") or []),
    "plaintext_token_field_present": "capability_tokens" in section,
    "max_message_length": int(section.get("max_message_length", 128)),
    "per_sender_limit_per_minute": int(section.get("per_sender_limit_per_minute", 6)),
    "per_chat_limit_per_minute": int(section.get("per_chat_limit_per_minute", 12)),
    "global_limit_per_minute": int(section.get("global_limit_per_minute", 30)),
    "confirmation_expiry_seconds": int(section.get("confirmation_expiry_seconds", 300)),
}, sort_keys=True))
'@

    Invoke-AxiomTelegramGatewayPython -Code $code -Payload @{
        config = $script:AxiomTelegramGatewayConfigPath
    }
}

function Invoke-AxiomTelegramGatewayQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,

        [object[]]$Params = @()
    )

    if (-not (Test-Path $script:AxiomTelegramGatewayDbPath)) {
        return $null
    }

    $code = @'
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
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    required = {"external_adapter_messages", "external_confirmation_requests"}
    missing = sorted(required - tables)
    if missing:
        print(json.dumps({"missing_tables": missing}, sort_keys=True))
        raise SystemExit(0)

    rows = conn.execute(sql, params).fetchall()
    print(json.dumps({"rows": [dict(row) for row in rows]}, ensure_ascii=False, sort_keys=True))
finally:
    conn.close()
'@

    $payload = @{
        db = $script:AxiomTelegramGatewayDbPath
        sql = $Sql
        params = $Params
    }

    Invoke-AxiomTelegramGatewayPython -Code $code -Payload $payload
}

function Get-AxiomTelegramGatewayStorageSummary {
    $result = Invoke-AxiomTelegramGatewayQuery -Sql @"
SELECT
    COUNT(*) AS total_messages,
    COALESCE(SUM(CASE WHEN decision_status = 'confirmation_required' THEN 1 ELSE 0 END), 0) AS confirmation_required_count,
    COALESCE(SUM(CASE WHEN decision_status = 'accepted' THEN 1 ELSE 0 END), 0) AS accepted_count,
    COALESCE(SUM(CASE WHEN decision_status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected_count,
    (
        SELECT COUNT(*)
        FROM external_confirmation_requests
        WHERE confirmation_status = 'pending'
    ) AS pending_confirmation_count,
    (
        SELECT COUNT(*)
        FROM external_confirmation_requests
        WHERE confirmation_status = 'expired'
    ) AS expired_confirmation_count
FROM external_adapter_messages
"@

    return $result
}

function Get-AxiomTelegramGatewayPendingConfirmations {
    param([int]$Limit = 5)

    Invoke-AxiomTelegramGatewayQuery -Sql @"
SELECT
    cr.confirmation_id,
    cr.command_name,
    cr.confirmation_status,
    cr.expires_at,
    em.platform_sender_id,
    em.platform_chat_id,
    em.created_at
FROM external_confirmation_requests AS cr
JOIN external_adapter_messages AS em
  ON em.message_id = cr.message_id
WHERE cr.confirmation_status = 'pending'
ORDER BY cr.confirmation_id DESC
LIMIT ?
"@ -Params @($Limit)
}

function Get-AxiomTelegramGatewayRecentMessages {
    param([int]$Limit = 8)

    Invoke-AxiomTelegramGatewayQuery -Sql @"
SELECT
    message_id,
    platform_message_id,
    platform_sender_id,
    platform_chat_id,
    command_text,
    decision_status,
    denial_reason,
    created_at
FROM external_adapter_messages
ORDER BY message_id DESC
LIMIT ?
"@ -Params @($Limit)
}

function axiom-telegram-gateway {
    param([int]$Limit = 8)

    Write-AxiomUiTitle "AXIOM TELEGRAM GATEWAY"

    Write-AxiomUiStatus "READ" "boundary" "local config + SQLite mode=ro; no Telegram runtime"

    if (-not (Test-Path $script:AxiomTelegramGatewayConfigPath)) {
        Write-AxiomUiStatus "BLOCK" "config" "$script:AxiomTelegramGatewayConfigPath missing"
        return
    }

    $config = Get-AxiomTelegramGatewayConfigSummary

    Write-AxiomUiSection "Config posture"
    if ($config -and $config.present) {
        $enabledColor = if ($config.enabled) { "Yellow" } else { "Green" }
        Write-AxiomUiLine "enabled" ([string]$config.enabled) $enabledColor
        Write-AxiomUiLine "whitelist" "operators=$($config.operator_whitelist_count); chats=$($config.allowed_chat_ids_count); capability_hashes=$($config.capability_hash_count)" "Gray"
        Write-AxiomUiLine "limits" "sender/min=$($config.per_sender_limit_per_minute); chat/min=$($config.per_chat_limit_per_minute); global/min=$($config.global_limit_per_minute)" "Gray"
        Write-AxiomUiLine "message" "max_chars=$($config.max_message_length); confirm_expiry_s=$($config.confirmation_expiry_seconds)" "Gray"
        Write-AxiomUiLine "secret field" $(if ($config.plaintext_token_field_present) { "plaintext capability_tokens present" } else { "hash-only" }) $(if ($config.plaintext_token_field_present) { "Red" } else { "Green" })
    }
    else {
        Write-AxiomUiLine "config" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Storage summary"
    $summaryResult = Get-AxiomTelegramGatewayStorageSummary
    if ($summaryResult -and $summaryResult.missing_tables) {
        Write-AxiomUiLine "schema" "missing: $($summaryResult.missing_tables -join ', ')" "Yellow"
    }
    elseif ($summaryResult -and $summaryResult.rows -and $summaryResult.rows.Count -gt 0) {
        $summary = $summaryResult.rows[0]
        Write-AxiomUiLine "messages" "total=$($summary.total_messages); confirmation_required=$($summary.confirmation_required_count); accepted=$($summary.accepted_count); rejected=$($summary.rejected_count)" "Gray"
        Write-AxiomUiLine "confirmations" "pending=$($summary.pending_confirmation_count); expired=$($summary.expired_confirmation_count)" $(if ($summary.pending_confirmation_count -gt 0) { "Yellow" } else { "Green" })
    }
    else {
        Write-AxiomUiLine "summary" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Pending confirmations"
    $pendingResult = Get-AxiomTelegramGatewayPendingConfirmations -Limit 5
    if ($pendingResult -and $pendingResult.rows -and $pendingResult.rows.Count -gt 0) {
        foreach ($row in @($pendingResult.rows)) {
            Write-Host ("  #{0} {1} sender={2} chat={3} expires={4}" -f $row.confirmation_id, $row.command_name, $row.platform_sender_id, $row.platform_chat_id, $row.expires_at) -ForegroundColor Yellow
        }
    }
    else {
        Write-AxiomUiLine "pending" "none" "Green"
    }

    Write-AxiomUiSection "Recent external decisions"
    $recentResult = Get-AxiomTelegramGatewayRecentMessages -Limit $Limit
    if ($recentResult -and $recentResult.rows -and $recentResult.rows.Count -gt 0) {
        foreach ($row in @($recentResult.rows)) {
            $reason = if ([string]::IsNullOrWhiteSpace([string]$row.denial_reason)) { "ok" } else { [string]$row.denial_reason }
            $color = if ($row.decision_status -eq "rejected") { "Yellow" } elseif ($row.decision_status -eq "accepted") { "Green" } else { "Gray" }
            Write-Host ("  #{0} {1} cmd={2} sender={3} reason={4}" -f $row.message_id, $row.decision_status, $row.command_text, $row.platform_sender_id, $reason) -ForegroundColor $color
        }
    }
    else {
        Write-AxiomUiLine "messages" "none" "Green"
    }

    Write-AxiomUiSection "Tools"
    Write-Host "  python tools\audit_telegram_gateway.py" -ForegroundColor Gray
    Write-Host "  axiom-telegram-gateway-audit" -ForegroundColor Gray
    Write-Host ""
}
