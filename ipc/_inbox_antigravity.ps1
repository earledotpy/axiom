# ipc/_inbox_antigravity.ps1
# Antigravity (agy) inbox handler — dot-sourced inside ipc_service.ps1 runspace.
#
# Features vs legacy agent_bridge:
#   - Circuit-breaker replaces unconditional re: filter
#   - Adaptive ConPTY timeout: 45s base + 50ms per body character
#   - Retry counter with dead-letter threshold (3 attempts)
#   - Agent availability gate

$ipcDir    = "C:\axiom\ipc"
$sendScript = "$ipcDir\send.ps1"
$dbScript   = "$ipcDir\ipc_db.py"
$inbox      = "$ipcDir\to_antigravity.md"
$Agent      = "antigravity"
$agyExe     = "C:\Users\tanne\AppData\Local\agy\bin\agy.exe"

. "$ipcDir\conpty_capture.ps1"

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
    return ($LASTEXITCODE -eq 0)
}

function Set-AgentBlocked {
    param([string]$Reason)
    $until = (Get-Date).ToUniversalTime().AddHours(1).ToString("yyyy-MM-ddTHH:mm:ssZ")
    & python $dbScript set-agent-blocked --agent $Agent --until $until --reason $Reason 2>$null | Out-Null
    Write-Warning "[inbox-antigravity]    agent blocked until $until — $Reason"
}

function Set-AgentAvailable {
    & python $dbScript set-agent-available --agent $Agent 2>$null | Out-Null
}

function Invoke-Antigravity {
    param([string]$Prompt)
    # Adaptive timeout: 45s base + 50ms per character (longer prompts → longer allowance)
    $adaptiveTimeout = 45000 + ($Prompt.Length * 50)
    try {
        $out = Invoke-ConPtyCaptureHosted `
            -Command    $agyExe `
            -Arguments  @('--print', $Prompt) `
            -WorkingDir 'C:\axiom' `
            -TimeoutMs  $adaptiveTimeout
        if (-not $out) {
            return @{ Out = ""; Status = "empty-response" }
        }
        return @{ Out = $out; Status = "ok" }
    } catch {
        return @{ Out = ""; Status = "conpty-error:$_" }
    }
}

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-antigravity] started — adaptive timeout + retry/availability active"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    if (Test-AgentBlocked) {
        Write-Host "[inbox-antigravity]    agent blocked — skipping batch"
        continue
    }

    $agentBlocked = $false
    foreach ($msg in (Get-PendingMessages)) {
        if ($agentBlocked) { break }

        Write-Host "[inbox-antigravity] << id:$($msg.id) from:$($msg.from_agent) subject:`"$($msg.subject)`""

        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-antigravity]    (circuit-breaker: recent dupe, skipping)"
            Mark-Done -Id $msg.id
            continue
        }

        $preview = $msg.body.Substring(0, [Math]::Min(80, $msg.body.Length))
        Write-Host "[inbox-antigravity]    $preview$(if ($msg.body.Length -gt 80) {'...'})"
        $adaptiveMs = 45000 + ($msg.body.Length * 50)
        Write-Host "[inbox-antigravity]    thinking... (timeout: $([math]::Round($adaptiveMs/1000))s)"

        $result = Invoke-Antigravity -Prompt $msg.body

        switch -Wildcard ($result.Status) {
            "ok" {
                Set-AgentAvailable
                Mark-Done -Id $msg.id
                Write-Host "[inbox-antigravity] >> $($result.Out.Length) chars → $($msg.from_agent)"
                & $sendScript -To $msg.from_agent -From $Agent `
                    -Subject "re: $($msg.subject)" -Body $result.Out
            }
            "empty-response" {
                Write-Warning "[inbox-antigravity]    empty response — marking retry (id:$($msg.id))"
                $retryResult = Invoke-MarkRetry -Id $msg.id
                if ($retryResult -and $retryResult.dead_letter -eq 1) {
                    Write-Warning "[inbox-antigravity]    dead-letter threshold reached — notifying sender"
                    Mark-Done -Id $msg.id
                    & $sendScript -To $msg.from_agent -From $Agent `
                        -Subject "re: $($msg.subject)" `
                        -Body "ERROR: agy did not respond after 3 attempts (empty output) — message dead-lettered"
                }
            }
            "conpty-error:*" {
                Write-Warning "[inbox-antigravity]    ConPTY error: $($result.Status) — marking retry + blocking"
                $retryResult = Invoke-MarkRetry -Id $msg.id
                if ($retryResult -and $retryResult.dead_letter -eq 1) {
                    Mark-Done -Id $msg.id
                    & $sendScript -To $msg.from_agent -From $Agent `
                        -Subject "re: $($msg.subject)" `
                        -Body "ERROR: agy ConPTY capture failed after 3 attempts — message dead-lettered"
                }
                Set-AgentBlocked -Reason "ConPTY error on message id:$($msg.id)"
                $agentBlocked = $true
            }
        }
    }
}
