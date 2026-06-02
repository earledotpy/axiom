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
#   Start-Process pwsh -ArgumentList "-NoExit -File C:\axiom\ipc\ipc_service.ps1 -Agents codex,antigravity" -WindowStyle Minimized

param(
    [switch]   $NoPosture,
    [string[]] $Agents = @("claude", "codex", "antigravity")
)

$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

$root = $PSScriptRoot

$pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, 4)
$pool.ApartmentState = [System.Threading.ApartmentState]::MTA
$pool.Open()

$handlerMap = @{
    "claude"      = "$root\_inbox_claude.ps1"
    "codex"       = "$root\_inbox_codex.ps1"
    "antigravity" = "$root\_inbox_antigravity.ps1"
}

function New-InboxRunspace {
    param([string]$Agent, [string]$ScriptPath)
    if (-not (Test-Path $ScriptPath)) {
        Write-Warning "[ipc-service] handler not found: $ScriptPath — skipping $Agent"
        return $null
    }
    $ps = [System.Management.Automation.PowerShell]::Create()
    $ps.RunspacePool = $pool
    $null = $ps.AddScript(". '$ScriptPath'")
    $handle = $ps.BeginInvoke()
    Write-Host "[ipc-service] started runspace: $Agent"
    return [PSCustomObject]@{
        PS     = $ps
        Handle = $handle
        Agent  = $Agent
        Script = $ScriptPath
    }
}

$jobs = [System.Collections.Generic.List[PSCustomObject]]::new()

foreach ($agent in $Agents) {
    if ($handlerMap.ContainsKey($agent)) {
        $job = New-InboxRunspace -Agent $agent -ScriptPath $handlerMap[$agent]
        if ($job) { $jobs.Add($job) }
    } else {
        Write-Warning "[ipc-service] unknown agent: $agent"
    }
}

if (-not $NoPosture) {
    $job = New-InboxRunspace -Agent "posture" -ScriptPath "$root\_posture_runspace.ps1"
    if ($job) { $jobs.Add($job) }
}

Write-Host "[ipc-service] $($jobs.Count) runspace(s) active (PID: $PID)"

# Health-check + restart loop
while ($true) {
    Start-Sleep -Seconds 10

    for ($i = 0; $i -lt $jobs.Count; $i++) {
        $job = $jobs[$i]
        if (-not $job.Handle.IsCompleted) { continue }

        $errMsgs = $job.PS.Streams.Error | ForEach-Object { $_.ToString() }
        if ($errMsgs) {
            Write-Warning "[ipc-service] Runspace '$($job.Agent)' faulted: $($errMsgs[0])"
        } else {
            Write-Warning "[ipc-service] Runspace '$($job.Agent)' exited unexpectedly"
        }
        $job.PS.Dispose()

        Write-Host "[ipc-service] Restarting runspace '$($job.Agent)'..."
        $newJob = New-InboxRunspace -Agent $job.Agent -ScriptPath $job.Script
        if ($newJob) { $jobs[$i] = $newJob }
    }
}
