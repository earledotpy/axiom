$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

Set-Location C:\axiom
. C:\axiom\ui\terminal\profile\profile-axiom.ps1
& "$PSScriptRoot\watcher_service.ps1" -Agent codex
# agent_bridge retired — ipc_service (started from Claude's pane) handles Codex routing
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-codex"
codex
