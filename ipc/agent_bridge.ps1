param(
    [Parameter(Mandatory)][ValidateSet("codex","antigravity")][string]$Agent
)

$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

$inbox      = "C:\axiom\ipc\to_$($Agent.ToLower()).md"
$sendScript = "C:\axiom\ipc\send.ps1"
$dbScript   = "C:\axiom\ipc\ipc_db.py"

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

function Invoke-Agent {
    param([string]$Prompt)

    if ($Agent -eq "codex") {
        # Piped-empty stdin forces EOF (no hang); --output-last-message captures clean answer.
        $outFile = [System.IO.Path]::GetTempFileName()
        "" | & codex exec --output-last-message $outFile --sandbox workspace-write -C C:\axiom $Prompt *> $null
        $out = if (Test-Path $outFile) { (Get-Content $outFile -Raw).Trim() } else { "ERROR: no output from codex" }
        Remove-Item $outFile -ErrorAction SilentlyContinue
        if (-not $out) { $out = "ERROR: codex returned empty output" }
        return $out
    } else {
        # agy writes to the TTY console handle directly (not stdout).
        # Invoke-ConPtyCaptureHosted spawns a fresh hidden pwsh host to sever
        # the nested-ConPTY inheritance that routes output to the parent WT pane.
        $agyExe = 'C:\Users\tanne\AppData\Local\agy\bin\agy.exe'
        try {
            $out = Invoke-ConPtyCaptureHosted `
                -Command    $agyExe `
                -Arguments  @('--print', $Prompt) `
                -WorkingDir 'C:\axiom' `
                -TimeoutMs  45000
            if (-not $out) { $out = "ERROR: agy returned empty output" }
        } catch {
            $out = "ERROR: ConPTY capture failed — $_"
        }
        return $out
    }
}

# FileSystemWatcher: fires on write, 2s fallback
$fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
$fsw.Filter = [System.IO.Path]::GetFileName($inbox)
$fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$fsw.EnableRaisingEvents = $true

Write-Host "[agent-bridge] $Agent ready — event-driven + SQLite dedup"
Write-Host "[agent-bridge] inbox  : $inbox`n"

while ($true) {
    $null = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
    if (-not (Test-Path $inbox)) { continue }

    foreach ($msg in (Get-PendingMessages)) {
        Write-Host "[agent-bridge] << id:$($msg.id) from:$($msg.from_agent)  subject:`"$($msg.subject)`""

        # Skip replies (prevent infinite loop)
        if ($msg.subject -match "^re:\s" -or $msg.subject.ToLower().StartsWith("re: ")) {
            Write-Host "[agent-bridge]    (reply detected, skipping execution)"
            Mark-Done -Id $msg.id
            continue
        }

        $preview = $msg.body.Substring(0, [Math]::Min(80, $msg.body.Length))
        Write-Host "[agent-bridge]    $preview$(if ($msg.body.Length -gt 80) {'...'})"
        Write-Host "[agent-bridge]    thinking..."

        $output = Invoke-Agent -Prompt $msg.body

        Mark-Done -Id $msg.id

        Write-Host "[agent-bridge] >> $($output.Length) chars — sending to $($msg.from_agent)`n"
        & $sendScript -To $msg.from_agent -From $Agent -Subject "re: $($msg.subject)" -Body $output
    }
}
