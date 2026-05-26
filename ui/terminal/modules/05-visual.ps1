# ============================================================
# AXIOM Terminal Visual Layer
# File: C:\axiom\ui\terminal\modules\05-visual.ps1
#
# Goal:
#   Restore the cleaner first-overhaul AXIOM Terminal feel:
#   - compact useful startup status
#   - short working prompt
#   - no constant mode/git/venv clutter on every input line
#   - no runtime mutation
# ============================================================

# -----------------------------
# Fallback constants
# -----------------------------

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomMode) {
    $script:AxiomMode = "fail_closed_non_autonomous"
}

if (-not $script:AxiomTerminalVersion) {
    $script:AxiomTerminalVersion = "AXIOM Terminal"
}

# -----------------------------
# ANSI palette
# -----------------------------

$script:AxiomEsc = [char]27
$script:AxiomAnsi = @{
    Reset = "$script:AxiomEsc[0m"
    Dim   = "$script:AxiomEsc[38;2;91;124;110m"
    Green = "$script:AxiomEsc[38;2;168;255;96m"
    DarkGreen = "$script:AxiomEsc[38;2;120;216;111m"
    Cyan  = "$script:AxiomEsc[38;2;105;214;197m"
    Blue  = "$script:AxiomEsc[38;2;124;199;255m"
    Amber = "$script:AxiomEsc[38;2;255;209;102m"
    Red   = "$script:AxiomEsc[38;2;255;107;107m"
    Soft  = "$script:AxiomEsc[38;2;199;247;199m"
}

# -----------------------------
# Terminal title
# -----------------------------

try {
    $Host.UI.RawUI.WindowTitle = "AXIOM Terminal"
}
catch {
    # Some hosts do not allow title writes.
}

# -----------------------------
# PSReadLine appearance
# -----------------------------

try {
    if (Get-Module -ListAvailable -Name PSReadLine) {
        Import-Module PSReadLine -ErrorAction SilentlyContinue

        Set-PSReadLineOption -EditMode Windows -ErrorAction SilentlyContinue
        Set-PSReadLineOption -BellStyle None -ErrorAction SilentlyContinue
        Set-PSReadLineOption -PredictionSource History -ErrorAction SilentlyContinue
        Set-PSReadLineOption -PredictionViewStyle InlineView -ErrorAction SilentlyContinue
        Set-PSReadLineOption -HistoryNoDuplicates:$true -ErrorAction SilentlyContinue

        Set-PSReadLineOption -Colors @{
            Command   = '#A8FF60'
            Parameter = '#69D6C5'
            String    = '#FFD166'
            Number    = '#7CC7FF'
            Operator  = '#C7F7C7'
            Variable  = '#9EF7E6'
            Error     = '#FF6B6B'
            Comment   = '#5B7C6E'
            Keyword   = '#78D86F'
        } -ErrorAction SilentlyContinue
    }
}
catch {
    # Visual tuning must never block shell startup.
}

# -----------------------------
# Lightweight status helpers
# -----------------------------

function Get-AxiomVisualRootState {
    if (Test-Path $script:AxiomRoot) {
        return "root-ok"
    }

    return "root-missing"
}

function Get-AxiomVisualVenvState {
    $activate = Join-Path $script:AxiomRoot "venv\Scripts\Activate.ps1"

    if ($env:VIRTUAL_ENV -and ($env:VIRTUAL_ENV -like "*\axiom\venv*")) {
        return "venv-active"
    }

    if (Test-Path $activate) {
        return "venv-ready"
    }

    return "venv-missing"
}

function Get-AxiomVisualDbState {
    $db = Join-Path $script:AxiomRoot "axiom.db"

    if (Test-Path $db) {
        return "db-present"
    }

    return "db-missing"
}

function Get-AxiomVisualGitState {
    $git = Get-Command git -ErrorAction SilentlyContinue

    if (-not $git) {
        return "git-unavailable"
    }

    if (-not (Test-Path (Join-Path $script:AxiomRoot ".git"))) {
        return "git-none"
    }

    Push-Location $script:AxiomRoot
    try {
        $branch = git branch --show-current 2>$null

        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
            return "git-unknown"
        }

        $status = git status --porcelain 2>$null

        if ($status) {
            return "git:$($branch.Trim())*"
        }

        return "git:$($branch.Trim())"
    }
    catch {
        return "git-unknown"
    }
    finally {
        Pop-Location
    }
}

function Get-AxiomPromptLeaf {
    $location = (Get-Location).Path
    $leaf = Split-Path -Leaf $location

    if ([string]::IsNullOrWhiteSpace($leaf)) {
        return $location
    }

    return $leaf.ToLowerInvariant()
}

# -----------------------------
# Startup banner
# -----------------------------

function Write-AxiomStartupBanner {
    $a = $script:AxiomAnsi

    $rootState = Get-AxiomVisualRootState
    $venvState = Get-AxiomVisualVenvState
    $dbState = Get-AxiomVisualDbState
    $gitState = Get-AxiomVisualGitState

    $rootColor = if ($rootState -eq "root-ok") { $a.Green } else { $a.Red }
    $venvColor = if ($venvState -eq "venv-active") { $a.Green } elseif ($venvState -eq "venv-ready") { $a.Amber } else { $a.Red }
    $dbColor = if ($dbState -eq "db-present") { $a.Green } else { $a.Red }
    $gitColor = if ($gitState -like "*`*") { $a.Amber } elseif ($gitState -like "git:*") { $a.Cyan } else { $a.Dim }

    Write-Host ""
    Write-Host "$($a.Green) AXIOM TERMINAL$($a.Reset) $($a.Dim):: operator console$($a.Reset)"
    Write-Host "$($a.Dim) boundary:$($a.Reset) $($a.Amber)fail-closed / non-autonomous$($a.Reset)"
    Write-Host "$($a.Dim) status:  $($rootColor)$rootState$($a.Reset)  $($venvColor)$venvState$($a.Reset)  $($dbColor)$dbState$($a.Reset)  $($gitColor)$gitState$($a.Reset)"
    Write-Host "$($a.Dim) next:    $($a.Soft)axiom-now$($a.Reset)  $($a.Dim)|$($a.Reset)  $($a.Soft)axiom-preflight$($a.Reset)  $($a.Dim)|$($a.Reset)  $($a.Soft)axiom-help$($a.Reset)"
    Write-Host ""
}

# -----------------------------
# Prompt
# -----------------------------
# Short by design.
#
# Examples:
#   axiom>
#   logs>
#   tools>
#   security>
#
# Detailed state stays available through:
#   axiom-env
#   axiom-guard
#   axiom-preflight
# -----------------------------

function global:prompt {
    if ($env:AXIOM_PROMPT_ENGINE -eq "oh-my-posh") {
        return "axiom> "
    }

    $leaf = Get-AxiomPromptLeaf
    $location = (Get-Location).Path

    if ($location -like "$script:AxiomRoot*") {
        return "$leaf> "
    }

    return "ps:$leaf> "
}   

# -----------------------------
# Optional visual helper
# -----------------------------

function axiom-visual {
    Write-AxiomStartupBanner
}

# -----------------------------
# One-time startup display
# -----------------------------

if ($env:AXIOM_STARTUP_BANNER -ne "0") {
    if (-not $global:AXIOM_VISUAL_BANNER_SHOWN) {
        $global:AXIOM_VISUAL_BANNER_SHOWN = $true
        Write-AxiomStartupBanner
    }
}
