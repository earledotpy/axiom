# _inbox_claude.ps1 — Claude inbox handler (runs as a runspace inside ipc_service.ps1)
# TYPE routing: 'command' → Invoke-Expression; 'ai-prompt'/'notification' → forward to Claude's session

$Agent      = "claude"
$inbox      = "C:\axiom\ipc\to_claude.md"
$sendScript = "C:\axiom\ipc\send.ps1"
$dbScript   = "C:\axiom\ipc\ipc_db.py"
$pendingFile = "C:\axiom\ipc\pending_for_claude.md"

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

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-claude] ready — event-driven + SQLite dedup"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[inbox-claude] << id:$($msg.id) from:$($msg.from_agent) type:$($msg.type) subject:`"$($msg.subject)`""

        # Circuit-breaker: skip if same from/subject was processed within 60s
        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-claude]    (circuit-breaker: dupe within 60s)"
            Mark-Done -Id $msg.id
            continue
        }

        if ($msg.type -eq 'command') {
            Write-Host "[inbox-claude]    cmd: $($msg.body)"
            try {
                $output = Invoke-Expression $msg.body 2>&1 | Out-String
            } catch {
                $output = "ERROR: $_"
            }
            Mark-Done -Id $msg.id
            $trimmed = $output.Trim()
            Write-Host "[inbox-claude] >> $($trimmed.Length) chars — sending back to $($msg.from_agent)"
            & $sendScript -To $msg.from_agent -From $Agent -Subject "re: $($msg.subject)" -Body $trimmed -Type "notification" -ConversationId $msg.id.ToString()
        } else {
            # ai-prompt or notification: forward to Claude's interactive session
            $entry = "`n---`nFROM: $($msg.from_agent)`nSUBJECT: $($msg.subject)`n`n$($msg.body)`n"
            Add-Content -Path $pendingFile -Value $entry -Encoding UTF8
            & "$PSScriptRoot\notify.ps1" -Title "IPC → Claude" -Message "From $($msg.from_agent): $($msg.subject)"
            Mark-Done -Id $msg.id
            Write-Host "[inbox-claude]    forwarded to pending_for_claude.md (no auto-reply)"
        }
    }
}
