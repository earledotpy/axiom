# ipc_service.ps1 — Unified IPC background service
#
# Replaces four separate PowerShell processes with a single process using
# PowerShell runspaces (shared CLR + engine, isolated variable scope).
# Coordination flows through SQLite (ipc_messages.db) — no shared memory needed.
#
# Memory: ~110 MB (one process) vs ~360 MB (four processes).
#
# Usage:
#   .\ipc\ipc_service.ps1               # all four runspaces
#   .\ipc\ipc_service.ps1 -NoPosture    # skip posture poller
#   .\ipc\ipc_service.ps1 -Agents codex,antigravity  # specific agents only
#
# The ConPTY hosted capture spawned by _inbox_antigravity.ps1 still creates
# a short-lived pwsh child per agy message — that is unavoidable without
# redesigning the ConPTY approach.

param(
    [switch]  $NoPosture,
    [string[]]$Agents = @("claude", "codex", "antigravity")
)

$ErrorActionPreference = "Continue"

# ── Runspace pool ─────────────────────────────────────────────────────────────
$pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, 4)
$pool.Open()

# ── Job tracker ───────────────────────────────────────────────────────────────
$jobs = [System.Collections.Generic.List[hashtable]]::new()

function Start-HandlerRunspace {
    param([string]$Name, [string]$ScriptPath)

    if (-not (Test-Path $ScriptPath)) {
        Write-Warning "[ipc-service] handler not found: $ScriptPath — skipping $Name"
        return
    }

    $ps = [System.Management.Automation.PowerShell]::Create()
    $ps.RunspacePool = $pool

    # Dot-source the handler file inside the runspace
    $ps.AddScript(". '$ScriptPath'") | Out-Null

    $handle = $ps.BeginInvoke()
    $jobs.Add(@{ Name = $Name; PS = $ps; Handle = $handle; ScriptPath = $ScriptPath })
    Write-Host "[ipc-service] started runspace: $Name"
}

function Restart-HandlerRunspace {
    param([hashtable]$Job)
    try { $Job.PS.Dispose() } catch {}
    $ps = [System.Management.Automation.PowerShell]::Create()
    $ps.RunspacePool = $pool
    $ps.AddScript(". '$($Job.ScriptPath)'") | Out-Null
    $handle = $ps.BeginInvoke()
    $Job.PS     = $ps
    $Job.Handle = $handle
    Write-Host "[ipc-service] restarted runspace: $($Job.Name)"
}

# ── Start handlers ────────────────────────────────────────────────────────────
$root = $PSScriptRoot

foreach ($agent in $Agents) {
    $handlerMap = @{
        "claude"      = "$root\_inbox_claude.ps1"
        "codex"       = "$root\_inbox_codex.ps1"
        "antigravity" = "$root\_inbox_antigravity.ps1"
    }
    if ($handlerMap.ContainsKey($agent)) {
        Start-HandlerRunspace -Name "inbox-$agent" -ScriptPath $handlerMap[$agent]
    } else {
        Write-Warning "[ipc-service] unknown agent: $agent"
    }
}

if (-not $NoPosture) {
    Start-HandlerRunspace -Name "posture" -ScriptPath "$root\_posture_runspace.ps1"
}

Write-Host "[ipc-service] $($jobs.Count) runspace(s) active — monitoring"
Write-Host "[ipc-service] RAM tip: Get-Process pwsh | Measure-Object WorkingSet -Sum"
Write-Host ""

# ── Health-check loop ─────────────────────────────────────────────────────────
# Checks every 10s. Restarts any runspace that completed (faulted or exited).
# A healthy runspace loops forever and never completes.
while ($true) {
    Start-Sleep -Seconds 10

    for ($i = 0; $i -lt $jobs.Count; $i++) {
        $job = $jobs[$i]
        if ($job.Handle.IsCompleted) {
            $errors = $job.PS.Streams.Error
            if ($errors.Count -gt 0) {
                Write-Warning "[ipc-service] Runspace '$($job.Name)' faulted:"
                $errors | ForEach-Object { Write-Warning "  $_" }
            } else {
                Write-Warning "[ipc-service] Runspace '$($job.Name)' exited unexpectedly"
            }
            Restart-HandlerRunspace -Job $job
        }
    }
}
