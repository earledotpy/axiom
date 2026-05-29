# ============================================================
# AXIOM Terminal Profile
# Path: C:\axiom\ui\terminal\profile\profile-axiom.ps1
#
# Purpose:
#   Deterministic AXIOM Terminal loader.
#
# Boundary:
#   This profile loads terminal modules only.
#   It must not mutate AXIOM runtime state.
#   Runtime checks, dashboards, audits, and tools live in modules.
# ============================================================

$script:AxiomRoot = 'C:\axiom'
$script:AxiomMode = 'fail_closed_non_autonomous'
$script:AxiomTerminalRoot = Join-Path $script:AxiomRoot 'ui\terminal'
$script:AxiomTerminalModules = Join-Path $script:AxiomTerminalRoot 'modules'
$script:AxiomTerminalProfile = Join-Path $script:AxiomTerminalRoot 'profile\profile-axiom.ps1'
$script:AxiomTerminalRegistry = Join-Path $script:AxiomTerminalRoot 'registry\axiom-terminal-command-registry.json'

$env:AXIOM_ROOT = $script:AxiomRoot
$env:AXIOM_TERMINAL_ROOT = $script:AxiomTerminalRoot
$env:AXIOM_PROFILE_MODE = $script:AxiomMode

# ------------------------------------------------------------
# Minimal loader diagnostics
# ------------------------------------------------------------

function Write-AxiomProfileWarning {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[AXIOM Terminal] $Message" -ForegroundColor Yellow
}

function Write-AxiomProfileError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[AXIOM Terminal] $Message" -ForegroundColor Red
}

# ------------------------------------------------------------
# Preflight path checks for terminal layer only
# ------------------------------------------------------------

if (-not (Test-Path $script:AxiomRoot)) {
    Write-AxiomProfileWarning "AXIOM root missing: $script:AxiomRoot"
}

if (-not (Test-Path $script:AxiomTerminalRoot)) {
    Write-AxiomProfileWarning "AXIOM Terminal root missing: $script:AxiomTerminalRoot"
}

if (-not (Test-Path $script:AxiomTerminalModules)) {
    Write-AxiomProfileWarning "Module directory missing: $script:AxiomTerminalModules"
    return
}

# ------------------------------------------------------------
# Load numbered AXIOM Terminal modules from organized subdirectories.
#
# Load order: core → foundation → utilities → shared → operators → diagnostics → phase10 → safety
#
# Important intra-order dependencies:
#   04-visual-mode.ps1 must load before 05-visual.ps1
#   05-visual.ps1 must load before 06-oh-my-posh.ps1
# ------------------------------------------------------------

$moduleGroups = @('core', 'foundation', 'utilities', 'shared', 'operators', 'diagnostics', 'phase10', 'safety')
$moduleFiles = @()

foreach ($group in $moduleGroups) {
    $groupPath = Join-Path $script:AxiomTerminalModules $group
    if (Test-Path $groupPath) {
        $moduleFiles += @(Get-ChildItem $groupPath -Filter '*.ps1' -ErrorAction SilentlyContinue | Sort-Object Name)
    }
}

foreach ($module in $moduleFiles) {
    try {
        . $module.FullName
    }
    catch {
        Write-AxiomProfileError "Failed loading module: $($module.Name) from $($module.Directory.Name)/"
        Write-AxiomProfileError $_.Exception.Message
    }
}

# ------------------------------------------------------------
# Loader sanity hints.
# These are warnings only. They do not block terminal startup.
# ------------------------------------------------------------

$visualModeOldPath = Join-Path $script:AxiomTerminalModules '43-visual-mode.ps1'
$visualModeFoundationPath = Join-Path $script:AxiomTerminalModules 'foundation' '04-visual-mode.ps1'

if ((Test-Path $visualModeOldPath) -and -not (Test-Path $visualModeFoundationPath)) {
    Write-AxiomProfileWarning "visual-mode module is named 43-visual-mode.ps1. Rename to 04-visual-mode.ps1 under foundation/ subdirectory."
}

if (-not (Get-Command axiom-help -ErrorAction SilentlyContinue)) {
    Write-AxiomProfileWarning "axiom-help is not loaded. Check modules under $script:AxiomTerminalModules subdirectories (core, foundation, utilities, shared, operators, diagnostics, phase10, safety)."
}

if (-not (Get-Command axiom-edit -ErrorAction SilentlyContinue)) {
    Write-AxiomProfileWarning "axiom-edit is not loaded. Check editor module."
}
