param([Parameter(Mandatory)][string]$Agent)

$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

$inbox        = "C:\axiom\ipc\to_$($Agent.ToLower()).md"
$notifyScript = "C:\axiom\ipc\notify.ps1"
$jobName      = "ipc-watcher-$Agent"

if (Get-Job -Name $jobName -ErrorAction SilentlyContinue) {
    Remove-Job -Name $jobName -Force
}

Start-Job -Name $jobName -ScriptBlock {
    param($inbox, $agent, $notifyScript)

    # FileSystemWatcher: fires on write, 2s fallback — no LastWriteTime polling needed
    $fsw = [System.IO.FileSystemWatcher]::new([System.IO.Path]::GetDirectoryName($inbox))
    $fsw.Filter = [System.IO.Path]::GetFileName($inbox)
    $fsw.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
    $fsw.EnableRaisingEvents = $true

    while ($true) {
        $result = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::Changed, 2000)
        if (-not $result.TimedOut) {
            Start-Process pwsh -ArgumentList "-File `"$notifyScript`" -Message `"Check ipc/to_$($agent.ToLower()).md`" -Title `"IPC: message for $agent`""
        }
    }
} -ArgumentList $inbox, $Agent, $notifyScript | Out-Null

Write-Host "[ipc] watcher started for $Agent (job: $jobName)"
