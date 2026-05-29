# tmux bridge — send-keys injection + capture-pane for agent interaction.
# Requires tmux installed via Git Bash MSYS2: pacman -S tmux
# Falls back to $null if tmux unavailable; callers use ConPTY/codex-exec as fallback.
#
# ConPTY is retained alongside this for:
#   - One-shot headless capture (agy --print, audit runs)
#   - Windows-native processes using Win32 console APIs (not VT sequences)
#   - Backup when tmux session is not running

$TMUX_EXE = "C:\Program Files\Git\usr\bin\tmux.exe"

function Test-TmuxAvailable {
    return (Test-Path $TMUX_EXE)
}

function Test-TmuxSession {
    param([string]$SessionName)
    if (-not (Test-TmuxAvailable)) { return $false }
    $result = & $TMUX_EXE has-session -t $SessionName 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-TmuxAgentPrompt {
    param(
        [Parameter(Mandatory)][string]$SessionName,
        [Parameter(Mandatory)][string]$Prompt,
        [int]$WaitMs        = 30000,
        [int]$PollMs        = 500,
        [string]$DoneMarker = ""    # optional string to detect completion in output
    )

    if (-not (Test-TmuxAvailable))              { return $null }
    if (-not (Test-TmuxSession $SessionName))   { return $null }

    # Clear any pending input, then inject prompt
    & $TMUX_EXE send-keys -t $SessionName "" C-c 2>$null
    Start-Sleep -Milliseconds 200
    & $TMUX_EXE send-keys -t $SessionName $Prompt Enter

    # Poll for completion or wait fixed duration
    $elapsed = 0
    $output  = ""
    while ($elapsed -lt $WaitMs) {
        Start-Sleep -Milliseconds $PollMs
        $elapsed += $PollMs
        $output = & $TMUX_EXE capture-pane -t $SessionName -p 2>$null | Out-String
        if ($DoneMarker -and $output -match [regex]::Escape($DoneMarker)) { break }
    }

    return $output.Trim()
}

function Register-TmuxSession {
    # Called from startup scripts to announce this pane's session name
    param([Parameter(Mandatory)][string]$SessionName)
    if (-not (Test-TmuxAvailable)) {
        Write-Host "[tmux] tmux not available — skipping session registration"
        return
    }
    # Create or attach to a named tmux session for this pane
    & $TMUX_EXE new-session -d -s $SessionName 2>$null
    Write-Host "[tmux] session registered: $SessionName"
}

function Get-TmuxPaneOutput {
    # Capture current visible content of a named session's active pane
    param([Parameter(Mandatory)][string]$SessionName, [int]$Lines = 50)
    if (-not (Test-TmuxSession $SessionName)) { return $null }
    return (& $TMUX_EXE capture-pane -t $SessionName -p -S -$Lines 2>$null | Out-String).Trim()
}
