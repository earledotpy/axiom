Set-Location C:\axiom
& "$PSScriptRoot\watcher_service.ps1" -Agent codex
# agent_bridge retired — ipc_service (started from Claude's pane) handles Codex routing
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-codex"
codex
