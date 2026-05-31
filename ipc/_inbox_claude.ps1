# ipc/_inbox_claude.ps1
# Claude Code inbox handler — dot-sourced inside ipc_service.ps1 runspace.
#
# TYPE dispatch:
#   command      → Invoke-Expression, reply with stdout
#   ai-prompt    → append to pending_for_claude.md + notify, no auto-reply
#   notification → notify only, no auto-reply

$ipcDir       = "C:\axiom\ipc"
$sendScript   = "$ipcDir\send.ps1"
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

function Test-RecentDupe {
    param([string]$From, [string]$Subject)
    & python $dbScript recent-check --from $From --to $Agent --subject $Subject --window 60 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Append-PendingPrompt {
    param($Msg)
    $entry = @"

---
FROM: $($Msg.from_agent)
SUBJECT: $($Msg.subject)
TIME: $($Msg.time)

$($Msg.body)
"@
    Add-Content -Path $pendingFile -Value $entry -Encoding UTF8
}

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-claude] started — TYPE dispatch + circuit-breaker active"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[inbox-claude] << id:$($msg.id) from:$($msg.from_agent) type:$($msg.type) subject:`"$($msg.subject)`""

        # Circuit-breaker: skip if same from+subject processed within 60s
        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-claude]    (circuit-breaker: recent dupe, skipping)"
            Mark-Done -Id $msg.id
            continue
        }

        $msgType = if ($msg.type) { $msg.type } else { "ai-prompt" }

        switch ($msgType) {
            "command" {
                Write-Host "[inbox-claude]    dispatch: command — executing"
                try {
                    $output = Invoke-Expression $msg.body 2>&1 | Out-String
                } catch {
                    $output = "ERROR: $_"
                }
                Mark-Done -Id $msg.id
                $trimmed = $output.Trim()
                Write-Host "[inbox-claude] >> $($trimmed.Length) chars → $($msg.from_agent)"
                & $sendScript -To $msg.from_agent -From $Agent `
                    -Subject "re: $($msg.subject)" -Body $trimmed -Type "command"
            }
            "notification" {
                Write-Host "[inbox-claude]    dispatch: notification — notifying only"
                Mark-Done -Id $msg.id
                & $notifyScript -Title "IPC notification from $($msg.from_agent)" -Message $msg.subject
            }
            default {
                # ai-prompt or unknown — queue for interactive review
                Write-Host "[inbox-claude]    dispatch: $msgType — queuing for review"
                Append-PendingPrompt -Msg $msg
                Mark-Done -Id $msg.id
                & $notifyScript -Title "IPC > claude ($($msg.from_agent))" -Message $msg.subject
            }
        }
    }
}
