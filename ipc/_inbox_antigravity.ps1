# _inbox_antigravity.ps1 — Antigravity inbox handler (runs as a runspace inside ipc_service.ps1)
# Adaptive timeout: base 45s + 50ms per character of prompt body.

$Agent      = "antigravity"
$inbox      = "C:\axiom\ipc\to_antigravity.md"
$sendScript = "C:\axiom\ipc\send.ps1"
$dbScript   = "C:\axiom\ipc\ipc_db.py"
$agyExe     = 'C:\Users\tanne\AppData\Local\agy\bin\agy.exe'

. "$PSScriptRoot\conpty_capture.ps1"

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

function Test-AgentBlocked {
    & python $dbScript is-agent-blocked --agent $Agent 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-antigravity] ready — event-driven + SQLite dedup"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[inbox-antigravity] << id:$($msg.id) from:$($msg.from_agent) subject:`"$($msg.subject)`""

        # Availability gate
        if (Test-AgentBlocked) {
            Write-Host "[inbox-antigravity]    agy is blocked (cooldown), skipping"
            continue
        }

        # Circuit-breaker
        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-antigravity]    (circuit-breaker: dupe within 60s)"
            Mark-Done -Id $msg.id
            continue
        }

        # Adaptive timeout: 45s base + 50ms per character
        $adaptiveTimeout = 45000 + ($msg.body.Length * 50)
        Write-Host "[inbox-antigravity]    thinking... (timeout: ${adaptiveTimeout}ms)"

        try {
            $output = Invoke-ConPtyCaptureHosted `
                -Command    $agyExe `
                -Arguments  @('--print', $msg.body) `
                -WorkingDir 'C:\axiom' `
                -TimeoutMs  $adaptiveTimeout
        } catch {
            $output = "ERROR: ConPTY capture failed — $_"
        }

        if (-not $output -or $output -match '^ERROR:') {
            $retryCount = [int]$msg.retry_count + 1
            Write-Warning "[inbox-antigravity]    agy returned no output — retry $retryCount/3"
            & python $dbScript mark-retry --id $msg.id 2>$null | Out-Null
            if ($retryCount -ge 3) {
                $until = (Get-Date).AddHours(2).ToString('o')
                & python $dbScript set-agent-blocked --agent $Agent --until $until --reason "3 consecutive empty responses" 2>$null | Out-Null
                & "$PSScriptRoot\notify.ps1" -Title "IPC: Antigravity blocked" -Message "Dead-lettered after 3 empty responses — 2h cooldown"
                Mark-Done -Id $msg.id
            }
            continue
        }

        # Success
        & python $dbScript set-agent-available --agent $Agent 2>$null | Out-Null
        Mark-Done -Id $msg.id
        Write-Host "[inbox-antigravity] >> $($output.Length) chars — sending to $($msg.from_agent)"
        & $sendScript -To $msg.from_agent -From $Agent -Subject "re: $($msg.subject)" -Body $output -ConversationId $msg.id.ToString()
    }
}
