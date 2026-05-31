Set-Location C:\axiom
& "$PSScriptRoot\watcher_service.ps1" -Agent antigravity
# agent_bridge retired — ipc_service (started from Claude's pane) handles Antigravity routing
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-antigravity"
agy
