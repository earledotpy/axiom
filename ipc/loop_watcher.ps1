param([string]$Agent = "claude")

$inbox      = "C:\axiom\ipc\to_$($Agent.ToLower()).md"
$sendScript = "C:\axiom\ipc\send.ps1"
$dbScript   = "C:\axiom\ipc\ipc_db.py"

function Get-PendingMessages {
    # DB is canonical — returns only unprocessed messages, survives restarts
    $json = & python $dbScript pending --agent $Agent 2>$null
    if (-not $json) { return @() }
    try { return $json | ConvertFrom-Json } catch { return @() }
}

function Mark-Done {
    param([int]$Id)
    & python $dbScript done --id $Id 2>$null | Out-Null
}

# FileSystemWatcher: fires on write, 2s fallback
$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[loop-watcher] started for $Agent"
Write-Host "[loop-watcher] inbox  : $inbox"
Write-Host "[loop-watcher] ready — event-driven + SQLite dedup`n"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[loop-watcher] << id:$($msg.id) from:$($msg.from_agent)  subject:`"$($msg.subject)`""

        # Skip replies (prevent infinite loop)
        if ($msg.subject -match "^re:\s" -or $msg.subject.ToLower().StartsWith("re: ")) {
            Write-Host "[loop-watcher]    (reply detected, skipping execution)"
            Mark-Done -Id $msg.id
            continue
        }

        Write-Host "[loop-watcher]    cmd : $($msg.body)"

        try {
            $output = Invoke-Expression $msg.body 2>&1 | Out-String
        } catch {
            $output = "ERROR: $_"
        }

        Mark-Done -Id $msg.id

        $trimmed = $output.Trim()
        Write-Host "[loop-watcher] >> $($trimmed.Length) chars — sending back to $($msg.from_agent)`n"
        & $sendScript -To $msg.from_agent -From $Agent -Subject "re: $($msg.subject)" -Body $trimmed
    }
}
