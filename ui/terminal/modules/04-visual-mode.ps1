# ============================================================
# AXIOM Terminal Visual Mode Control
# File: C:\axiom\ui\terminal\modules\43-visual-mode.ps1
#
# Purpose:
#   Centralize AXIOM Terminal visual mode selection.
#
# Boundary:
#   This module changes terminal/profile UX only.
#   It does not mutate AXIOM runtime state.
#   It does not query AXIOM database.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
$script:AxiomVisualConfigPath = Join-Path $script:AxiomTerminalRoot "profile\visual-mode.json"
$script:AxiomDashboardThemePath = Join-Path $script:AxiomTerminalRoot "themes\axiom-dashboard.omp.json"
$script:AxiomNativePromptMode = "native"
$script:AxiomDashboardPromptMode = "dashboard"

function Get-AxiomVisualDefaultConfig {
    [pscustomobject]@{
        schema_version = "axiom.terminal.visual_mode.v1"
        prompt_mode = "dashboard"
        startup_banner = $true
        theme = "axiom-dashboard"
        notes = "AXIOM Terminal visual settings only. Does not affect AXIOM runtime state."
    }
}

function Read-AxiomVisualConfig {
    if (-not (Test-Path $script:AxiomVisualConfigPath)) {
        $config = Get-AxiomVisualDefaultConfig
        Write-AxiomVisualConfig -Config $config
        return $config
    }

    try {
        $config = Get-Content $script:AxiomVisualConfigPath -Raw | ConvertFrom-Json

        if (-not $config.prompt_mode) {
            $config | Add-Member -NotePropertyName prompt_mode -NotePropertyValue "dashboard" -Force
        }

        if (-not ($config.PSObject.Properties.Name -contains "startup_banner")) {
            $config | Add-Member -NotePropertyName startup_banner -NotePropertyValue $true -Force
        }

        if (-not $config.theme) {
            $config | Add-Member -NotePropertyName theme -NotePropertyValue "axiom-dashboard" -Force
        }

        return $config
    }
    catch {
        Write-Host "[AXIOM] Visual config invalid; using defaults for this session." -ForegroundColor Yellow
        return Get-AxiomVisualDefaultConfig
    }
}

function Write-AxiomVisualConfig {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config
    )

    $dir = Split-Path -Parent $script:AxiomVisualConfigPath
    New-Item -ItemType Directory -Force $dir | Out-Null

    $Config | ConvertTo-Json -Depth 8 | Set-Content $script:AxiomVisualConfigPath -Encoding UTF8
}

function Set-AxiomVisualMode {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("native", "dashboard")]
        [string]$Mode
    )

    $config = Read-AxiomVisualConfig
    $config.prompt_mode = $Mode
    Write-AxiomVisualConfig -Config $config

    $env:AXIOM_PROMPT_ENGINE = if ($Mode -eq "dashboard") { "oh-my-posh" } else { "native" }

    Write-Host "[AXIOM] Visual prompt mode set to: $Mode" -ForegroundColor Green
    Write-Host "[AXIOM] Reload with: . `$PROFILE" -ForegroundColor Gray
}

function Set-AxiomStartupBanner {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Enabled
    )

    $config = Read-AxiomVisualConfig
    $config.startup_banner = $Enabled
    Write-AxiomVisualConfig -Config $config

    if ($Enabled) {
        Write-Host "[AXIOM] Startup banner enabled." -ForegroundColor Green
    }
    else {
        Write-Host "[AXIOM] Startup banner disabled." -ForegroundColor Yellow
    }

    Write-Host "[AXIOM] Reload with: . `$PROFILE" -ForegroundColor Gray
}

function Initialize-AxiomVisualMode {
    $config = Read-AxiomVisualConfig

    if ($config.prompt_mode -eq "dashboard") {
        $env:AXIOM_PROMPT_ENGINE = "oh-my-posh"
    }
    else {
        $env:AXIOM_PROMPT_ENGINE = "native"
    }

    $env:AXIOM_STARTUP_BANNER = if ($config.startup_banner) { "1" } else { "0" }
    $env:AXIOM_THEME_NAME = [string]$config.theme
}

function axiom-visual-mode {
    $config = Read-AxiomVisualConfig

    Write-Host ""
    Write-Host "AXIOM VISUAL MODE" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  config:          $script:AxiomVisualConfigPath" -ForegroundColor Gray
    Write-Host "  prompt_mode:     $($config.prompt_mode)" -ForegroundColor Cyan
    Write-Host "  startup_banner:  $($config.startup_banner)" -ForegroundColor Cyan
    Write-Host "  theme:           $($config.theme)" -ForegroundColor Cyan
    Write-Host "  env prompt:      $env:AXIOM_PROMPT_ENGINE" -ForegroundColor DarkGray
    Write-Host "  env banner:      $env:AXIOM_STARTUP_BANNER" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor DarkGreen
    Write-Host "  axiom-visual-native       Use compact native prompt"
    Write-Host "  axiom-visual-dashboard    Use Oh My Posh dashboard prompt"
    Write-Host "  axiom-banner-on           Show startup status panel"
    Write-Host "  axiom-banner-off          Hide startup status panel"
    Write-Host "  axiom-theme               Show theme resources"
    Write-Host ""
}

function axiom-visual-native {
    Set-AxiomVisualMode -Mode "native"
}

function axiom-visual-dashboard {
    Set-AxiomVisualMode -Mode "dashboard"
}

function axiom-banner-on {
    Set-AxiomStartupBanner -Enabled $true
}

function axiom-banner-off {
    Set-AxiomStartupBanner -Enabled $false
}

function axiom-visual-reset {
    $config = Get-AxiomVisualDefaultConfig
    Write-AxiomVisualConfig -Config $config
    Initialize-AxiomVisualMode

    Write-Host "[AXIOM] Visual config reset to defaults." -ForegroundColor Green
    Write-Host "[AXIOM] Reload with: . `$PROFILE" -ForegroundColor Gray
}

Initialize-AxiomVisualMode
