# tmux bridge — send-keys injection + capture-pane for agent interaction.
# Supports psmux (native Windows) or falls back to Git Bash MSYS2 tmux.
# Falls back to $null if neither available; callers use ConPTY/codex-exec as fallback.
#
# ConPTY is retained alongside this for:
#   - One-shot headless capture (agy --print, audit runs)
#   - Windows-native processes using Win32 console APIs (not VT sequences)
#   - Backup when tmux session is not running

$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

function Get-TmuxBinary {
    # Test for psmux (native Windows) first, then fall back to MSYS2 tmux

    # Try to find psmux in PATH
    try {
        $cmd = Get-Command psmux -ErrorAction Stop
        if ($cmd) { return $cmd.Source }
    } catch {}

    # Try explicit paths
    $paths = @(
        "C:\Users\tanne\AppData\Local\Microsoft\WinGet\Packages\marlocarlo.psmux_Microsoft.Winget.Source_8wekyb3d8bbwe\psmux.exe",  # WinGet actual path
        "C:\Users\tanne\AppData\Local\Microsoft\WinGet\Packages\psmux.psmux_Active\psmux.exe",  # WinGet legacy path
        "C:\Program Files\psmux\psmux.exe",  # Common install
        "C:\Program Files\Git\usr\bin\tmux.exe"  # MSYS2 fallback
    )

    foreach ($path in $paths) {
        if (Test-Path $path -ErrorAction SilentlyContinue) {
            return $path
        }
    }

    return $null
}

$TMUX_EXE = Get-TmuxBinary

function Test-TmuxAvailable {
    return ($null -ne $TMUX_EXE)
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
