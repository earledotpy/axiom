$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

Set-Location C:\axiom
. C:\axiom\ui\terminal\profile\profile-axiom.ps1
& "$PSScriptRoot\watcher_service.ps1" -Agent claude
# ipc_service hosts all agent runspaces in one process (~110 MB vs ~360 MB for four separate pwsh)
Start-Process pwsh -ArgumentList "-NoExit -File `"$PSScriptRoot\ipc_service.ps1`"" -WindowStyle Minimized
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-claude"
claude
