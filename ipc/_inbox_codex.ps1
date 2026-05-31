# ipc/_inbox_codex.ps1
# Codex inbox handler — dot-sourced inside ipc_service.ps1 runspace.
#
# Features vs legacy agent_bridge:
#   - Circuit-breaker replaces unconditional re: filter
#   - Exit-code taxonomy: quota/crash vs empty vs ok
#   - Retry counter with dead-letter threshold (3 attempts)
#   - Agent availability gate (blocks all messages while agent is down)

$ipcDir    = "C:\axiom\ipc"
$sendScript = "$ipcDir\send.ps1"
$dbScript   = "$ipcDir\ipc_db.py"
$inbox      = "$ipcDir\to_codex.md"
$Agent      = "codex"

function Get-PendingMessages {
    $json = & python $dbScript pending --agent $Agent 2>$null
    if (-not $json) { return @() }
    try { return $json | ConvertFrom-Json } catch { return @() }
}

function Mark-Done {
    param([int]$Id)
    & python $dbScript done --id $Id 2>$null | Out-Null
}

function Invoke-MarkRetry {
    param([int]$Id)
    $json = & python $dbScript mark-retry --id $Id 2>$null
    if ($json) { try { return $json | ConvertFrom-Json } catch {} }
    return $null
}

function Test-RecentDupe {
    param([string]$From, [string]$Subject)
    & python $dbScript recent-check --from $From --to $Agent --subject $Subject --window 60 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Test-AgentBlocked {
    & python $dbScript is-agent-blocked --agent $Agent 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)  # exit 0 = blocked
}

function Set-AgentBlocked {
    param([string]$Reason)
    $until = (Get-Date).ToUniversalTime().AddHours(1).ToString("yyyy-MM-ddTHH:mm:ssZ")
    & python $dbScript set-agent-blocked --agent $Agent --until $until --reason $Reason 2>$null | Out-Null
    Write-Warning "[inbox-codex]    agent blocked until $until — $Reason"
}

function Set-AgentAvailable {
    & python $dbScript set-agent-available --agent $Agent 2>$null | Out-Null
}

function Invoke-Codex {
    param([string]$Prompt)
    $outFile = [System.IO.Path]::GetTempFileName()
    try {
        "" | & codex exec --output-last-message $outFile --sandbox workspace-write -C C:\axiom $Prompt *>$null
        $exitCode = $LASTEXITCODE
        $hasFile  = Test-Path $outFile
        $content  = if ($hasFile) { (Get-Content $outFile -Raw).Trim() } else { "" }

        if ($exitCode -ne 0 -and -not $hasFile) {
            return @{ Out = ""; Status = "quota-or-crash" }
        }
        if (-not $content) {
            return @{ Out = ""; Status = "empty-response" }
        }
        return @{ Out = $content; Status = "ok" }
    } finally {
        Remove-Item $outFile -ErrorAction SilentlyContinue
    }
}

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-codex] started — retry/availability/circuit-breaker active"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    # Availability gate — skip the entire batch if agent is blocked
    if (Test-AgentBlocked) {
        Write-Host "[inbox-codex]    agent blocked — skipping batch"
        continue
    }

    $agentBlocked = $false
    foreach ($msg in (Get-PendingMessages)) {
        if ($agentBlocked) { break }

        Write-Host "[inbox-codex] << id:$($msg.id) from:$($msg.from_agent) subject:`"$($msg.subject)`""

        # Circuit-breaker: skip if same from+subject processed within 60s
        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-codex]    (circuit-breaker: recent dupe, skipping)"
            Mark-Done -Id $msg.id
            continue
        }

        Write-Host "[inbox-codex]    thinking..."
        $result = Invoke-Codex -Prompt $msg.body

        switch ($result.Status) {
            "ok" {
                Set-AgentAvailable
                Mark-Done -Id $msg.id
                Write-Host "[inbox-codex] >> $($result.Out.Length) chars → $($msg.from_agent)"
                & $sendScript -To $msg.from_agent -From $Agent `
                    -Subject "re: $($msg.subject)" -Body $result.Out
            }
            "empty-response" {
                Write-Warning "[inbox-codex]    empty response — marking retry (id:$($msg.id))"
                $retryResult = Invoke-MarkRetry -Id $msg.id
                if ($retryResult -and $retryResult.dead_letter -eq 1) {
                    Write-Warning "[inbox-codex]    dead-letter threshold reached — notifying sender"
                    Mark-Done -Id $msg.id
                    & $sendScript -To $msg.from_agent -From $Agent `
                        -Subject "re: $($msg.subject)" `
                        -Body "ERROR: codex did not respond after 3 attempts (empty output) — message dead-lettered"
                }
            }
            "quota-or-crash" {
                Write-Warning "[inbox-codex]    quota or crash — marking retry + blocking agent"
                $retryResult = Invoke-MarkRetry -Id $msg.id
                if ($retryResult -and $retryResult.dead_letter -eq 1) {
                    Mark-Done -Id $msg.id
                    & $sendScript -To $msg.from_agent -From $Agent `
                        -Subject "re: $($msg.subject)" `
                        -Body "ERROR: codex unavailable after 3 attempts — message dead-lettered"
                }
                Set-AgentBlocked -Reason "quota-or-crash on message id:$($msg.id)"
                $agentBlocked = $true
            }
        }
    }
}
