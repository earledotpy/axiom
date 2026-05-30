# _inbox_codex.ps1 — Codex inbox handler (runs as a runspace inside ipc_service.ps1)
# Error taxonomy: exit-code + output-file presence distinguish quota/crash/empty/success.

$Agent      = "codex"
$inbox      = "C:\axiom\ipc\to_codex.md"
$sendScript = "C:\axiom\ipc\send.ps1"
$dbScript   = "C:\axiom\ipc\ipc_db.py"

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

function Invoke-Codex {
    param([string]$Prompt)
    $outFile = [System.IO.Path]::GetTempFileName()
    "" | & codex exec --output-last-message $outFile --sandbox workspace-write -C C:\axiom $Prompt *> $null
    $exitCode = $LASTEXITCODE
    $content  = if (Test-Path $outFile) { (Get-Content $outFile -Raw -ErrorAction SilentlyContinue).Trim() } else { $null }
    Remove-Item $outFile -ErrorAction SilentlyContinue
    return @{ ExitCode = $exitCode; Content = $content }
}

$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[inbox-codex] ready — event-driven + SQLite dedup"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[inbox-codex] << id:$($msg.id) from:$($msg.from_agent) subject:`"$($msg.subject)`""

        # Availability gate
        if (Test-AgentBlocked) {
            Write-Host "[inbox-codex]    codex is blocked (quota/crash cooldown), skipping"
            continue
        }

        # Circuit-breaker
        if (Test-RecentDupe -From $msg.from_agent -Subject $msg.subject) {
            Write-Host "[inbox-codex]    (circuit-breaker: dupe within 60s)"
            Mark-Done -Id $msg.id
            continue
        }

        Write-Host "[inbox-codex]    thinking..."
        $result = Invoke-Codex -Prompt $msg.body

        if ($result.ExitCode -ne 0 -and -not $result.Content) {
            # Quota exhaustion or crash
            $retryCount = [int]$msg.retry_count + 1
            Write-Warning "[inbox-codex]    codex unavailable (exit $($result.ExitCode)) — retry $retryCount/3"
            & python $dbScript mark-retry --id $msg.id 2>$null | Out-Null
            if ($retryCount -ge 3) {
                $until = (Get-Date).AddHours(1).ToString('o')
                & python $dbScript set-agent-blocked --agent $Agent --until $until --reason "3 consecutive failures (exit $($result.ExitCode))" 2>$null | Out-Null
                & "$PSScriptRoot\notify.ps1" -Title "IPC: Codex blocked" -Message "Dead-lettered after 3 failures — will retry after 1h"
                Mark-Done -Id $msg.id
            }
            continue
        }

        if (-not $result.Content) {
            # Empty response (exit 0 but no output)
            $retryCount = [int]$msg.retry_count + 1
            Write-Warning "[inbox-codex]    codex returned empty response — retry $retryCount/3"
            & python $dbScript mark-retry --id $msg.id 2>$null | Out-Null
            if ($retryCount -ge 3) {
                Mark-Done -Id $msg.id
            }
            continue
        }

        # Success
        & python $dbScript set-agent-available --agent $Agent 2>$null | Out-Null
        Mark-Done -Id $msg.id
        Write-Host "[inbox-codex] >> $($result.Content.Length) chars — sending to $($msg.from_agent)"
        & $sendScript -To $msg.from_agent -From $Agent -Subject "re: $($msg.subject)" -Body $result.Content -ConversationId $msg.id.ToString()
    }
}
