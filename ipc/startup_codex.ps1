Set-Location C:\axiom
& "$PSScriptRoot\watcher_service.ps1" -Agent codex
Start-Process pwsh -ArgumentList "-NoExit -File `"$PSScriptRoot\agent_bridge.ps1`" -Agent codex" -WindowStyle Minimized
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-codex"
codex
