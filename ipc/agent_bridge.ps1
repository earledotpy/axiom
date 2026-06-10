param(
    [Parameter(Mandatory)][ValidateSet("codex","antigravity")][string]$Agent
)

Write-Output "[ipc-neutralized] agent_bridge.ps1 is disabled by Phase 2 Neutralize Raw Execution."
Write-Output "[ipc-neutralized] Inbound IPC may not auto-invoke $Agent. Use the terminal pane manually."
return
