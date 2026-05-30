# AXIOM Development Workspace Launcher
# Opens a 3-pane Windows Terminal: Claude Code | Codex | Antigravity
# All panes start in C:\axiom using the AXIOM terminal profile styling.
#
# Usage: .\launch-workspace.ps1

# Start tmux server if tmux is installed (Git Bash MSYS2: pacman -S tmux)
# Each pane's startup script registers its own named session for send-keys injection.
$tmuxExe = "C:\Program Files\Git\usr\bin\tmux.exe"
if (Test-Path $tmuxExe) {
    & $tmuxExe start-server 2>$null
    Write-Host "[workspace] tmux server started"
} else {
    Write-Host "[workspace] tmux not found — interactive injection disabled (ConPTY remains active)"
}

wt new-tab -p "AXIOM - Claude Code" `
`; split-pane -V -p "AXIOM - Codex" --size 0.67 `
`; split-pane -V -p "AXIOM - Antigravity" --size 0.5
