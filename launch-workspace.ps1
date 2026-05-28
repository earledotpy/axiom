# AXIOM Development Workspace Launcher
# Opens a 3-pane Windows Terminal: Claude Code | Codex | Antigravity
# All panes start in C:\axiom using the AXIOM terminal profile styling.
#
# Usage: .\launch-workspace.ps1

wt new-tab -p "AXIOM - Claude Code" `
`; split-pane -V -p "AXIOM - Codex" --size 0.67 `
`; split-pane -V -p "AXIOM - Antigravity" --size 0.5
