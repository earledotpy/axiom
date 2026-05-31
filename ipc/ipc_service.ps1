# ipc/ipc_service.ps1
# Unified IPC service — one process, one runspace per agent inbox.
# Replaces: loop_watcher.ps1, agent_bridge.ps1 (both agents), posture_daemon.ps1
#
# Memory: ~110 MB total vs ~360 MB for four separate pwsh processes.
# All coordination flows through ipc_messages.db — runspaces share no variables.
#
# Usage:
#   Start-Process pwsh -ArgumentList "-NoExit -File C:\axiom\ipc\ipc_service.ps1" -WindowStyle Minimized
#   Start-Process pwsh -ArgumentList "-NoExit -File C:\axiom\ipc\ipc_service.ps1 -NoPosture" -WindowStyle Minimized

param([switch]$NoPosture)

$scriptDir = "C:\axiom\ipc"

$pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, 4)
$pool.ApartmentState = [System.Threading.ApartmentState]::MTA
$pool.Open()

function New-InboxRunspace {
    param([string]$Agent, [string]$ScriptPath)
    $ps = [System.Management.Automation.PowerShell]::Create()
    $ps.RunspacePool = $pool
    # Use call operator so $PSScriptRoot inside the handler resolves to the script's directory
    $null = $ps.AddScript("& '$ScriptPath'")
    $handle = $ps.BeginInvoke()
    return [PSCustomObject]@{
        PS     = $ps
        Handle = $handle
        Agent  = $Agent
        Script = $ScriptPath
    }
}

$jobs = [System.Collections.Generic.List[PSCustomObject]]::new()
$jobs.Add((New-InboxRunspace -Agent "claude"      -ScriptPath "$scriptDir\_inbox_claude.ps1"))
$jobs.Add((New-InboxRunspace -Agent "codex"       -ScriptPath "$scriptDir\_inbox_codex.ps1"))
$jobs.Add((New-InboxRunspace -Agent "antigravity" -ScriptPath "$scriptDir\_inbox_antigravity.ps1"))
if (-not $NoPosture) {
    $jobs.Add((New-InboxRunspace -Agent "posture" -ScriptPath "$scriptDir\_posture_runspace.ps1"))
}

Write-Host "[ipc-service] started $($jobs.Count) runspaces (PID: $PID)"
Write-Host "[ipc-service] runspaces: $($jobs.Agent -join ', ')"

# Health-check + restart loop
while ($true) {
    Start-Sleep -Seconds 10

    for ($i = 0; $i -lt $jobs.Count; $i++) {
        $job = $jobs[$i]
        if (-not $job.Handle.IsCompleted) { continue }

        # Runspace exited — log errors and restart
        $errMsgs = $job.PS.Streams.Error | ForEach-Object { $_.ToString() }
        if ($errMsgs) {
            Write-Warning "[ipc-service] Runspace '$($job.Agent)' faulted: $($errMsgs[0])"
        } else {
            Write-Warning "[ipc-service] Runspace '$($job.Agent)' exited unexpectedly"
        }
        $job.PS.Dispose()

        Write-Host "[ipc-service] Restarting runspace '$($job.Agent)'..."
        $jobs[$i] = New-InboxRunspace -Agent $job.Agent -ScriptPath $job.Script
    }
}
