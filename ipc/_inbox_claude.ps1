# ipc/_inbox_claude.ps1
# Phase 2: Claude IPC handling is review-only. Command frames are rejected by
# ipc_db.py and this script must not execute message bodies.

$IPC_PHASE2_NEUTRALIZE_ACTIVE = $true

$ipcDir       = "C:\axiom\ipc"
$dbScript     = "$ipcDir\ipc_db.py"
$inbox        = "$ipcDir\to_claude.md"
$pendingFile  = "$ipcDir\pending_for_claude.md"
$notifyScript = "$ipcDir\notify.ps1"
$Agent        = "claude"

function Get-PendingMessages {
    $json = & python $dbScript pending --agent $Agent 2>$null
    if (-not $json) { return @() }
    try { return $json | ConvertFrom-Json } catch { return @() }
}

function Mark-Done {
    param([int]$Id)
    & python $dbScript done --id $Id 2>$null | Out-Null
}

function Append-PendingPrompt {
    param($Msg)
    $entry = @"

---
FROM: $($Msg.from_agent)
SUBJECT: $($Msg.subject)
TIME: $($Msg.time)
TYPE: $($Msg.type)

$($Msg.body)
"@
    Add-Content -Path $pendingFile -Value $entry -Encoding UTF8
}

Write-Host "[inbox-claude] started in Phase 2 review-only mode"

while ($true) {
    Start-Sleep -Seconds 2
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[inbox-claude] << id:$($msg.id) from:$($msg.from_agent) type:$($msg.type) subject:`"$($msg.subject)`""
        Append-PendingPrompt -Msg $msg
        Mark-Done -Id $msg.id
        & $notifyScript -Title "IPC > claude ($($msg.from_agent))" -Message $msg.subject
    }
}
