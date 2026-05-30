Set-Location C:\axiom
& "$PSScriptRoot\watcher_service.ps1" -Agent claude
Start-Process pwsh -ArgumentList "-NoExit -File `"$PSScriptRoot\loop_watcher.ps1`" -Agent claude" -WindowStyle Minimized
# Register tmux session for this pane (no-op if tmux not installed)
. "$PSScriptRoot\tmux_bridge.ps1"
Register-TmuxSession -SessionName "axiom-claude"
claude
