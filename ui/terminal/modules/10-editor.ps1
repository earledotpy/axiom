# ============================================================
# AXIOM Terminal Editor Integration
#
# Purpose:
#   Terminal-native editor workflow for AXIOM implementation.
#
# Boundary:
#   This module opens/creates files only.
#   It must not mutate AXIOM runtime state directly.
#   It must not fall back to Windows Notepad by default.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

if (-not $script:AxiomTerminalRoot) {
    $script:AxiomTerminalRoot = Join-Path $script:AxiomRoot "ui\terminal"
}

$script:AxiomEditorRoot = Join-Path $script:AxiomTerminalRoot "editor"
$script:AxiomEditorSettingsPath = Join-Path $script:AxiomEditorRoot "settings.json"
$script:AxiomEditorBindingsPath = Join-Path $script:AxiomEditorRoot "bindings.json"

function Initialize-AxiomEditorConfig {
    New-Item -ItemType Directory -Force $script:AxiomEditorRoot | Out-Null

    if (-not (Test-Path $script:AxiomEditorSettingsPath)) {
@'
{
    "autosave": 0,
    "backup": true,
    "clipboard": "terminal",
    "colorscheme": "simple",
    "cursorline": true,
    "diffgutter": true,
    "eofnewline": true,
    "hlsearch": true,
    "ignorecase": true,
    "indentchar": " ",
    "infobar": true,
    "matchbrace": true,
    "mkparents": true,
    "mouse": true,
    "parsecursor": true,
    "paste": false,
    "pluginchannels": [],
    "pluginrepos": [],
    "readonly": false,
    "ruler": true,
    "savecursor": true,
    "savehistory": true,
    "scrollbar": true,
    "softwrap": false,
    "status": true,
    "statusformatl": "$(filename) $(modified)[$(line),$(col)]",
    "statusformatr": "AXIOM",
    "syntax": true,
    "tabsize": 4,
    "tabstospaces": true,
    "termtitle": true,
    "useprimary": true
}
'@ | Set-Content -Path $script:AxiomEditorSettingsPath -Encoding UTF8
    }

    # Keep bindings minimal. Do not define Replace; it is invalid in some micro builds.
    if (-not (Test-Path $script:AxiomEditorBindingsPath)) {
@'
{
    "Ctrl-s": "Save",
    "Ctrl-q": "Quit",
    "Ctrl-f": "Find",
    "Ctrl-g": "FindNext",
    "Ctrl-z": "Undo",
    "Ctrl-y": "Redo"
}
'@ | Set-Content -Path $script:AxiomEditorBindingsPath -Encoding UTF8
    }
}

function Get-AxiomTerminalEditor {
    if ($env:AXIOM_EDITOR) {
        $override = Get-Command $env:AXIOM_EDITOR -ErrorAction SilentlyContinue
        if ($override) {
            return $override.Source
        }

        if (Test-Path $env:AXIOM_EDITOR) {
            return $env:AXIOM_EDITOR
        }

        Write-Host "[AXIOM] AXIOM_EDITOR is set but not found: $env:AXIOM_EDITOR" -ForegroundColor Yellow
    }

    foreach ($name in @("micro", "nvim", "vim", "nano")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }

    return $null
}

function Resolve-AxiomPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }

    if ($env:AXIOM_ROOT) {
        return Join-Path $env:AXIOM_ROOT $Path
    }

    return Join-Path $script:AxiomRoot $Path
}

function Invoke-AxiomTerminalEditor {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    Initialize-AxiomEditorConfig

    $editor = Get-AxiomTerminalEditor

    if (-not $editor) {
        Write-Host "[AXIOM] No terminal editor found." -ForegroundColor Red
        Write-Host "Install micro with:" -ForegroundColor Gray
        Write-Host "  winget install -e --id zyedidia.micro" -ForegroundColor Gray
        Write-Host "" 
        Write-Host "Refusing to fall back to Windows Notepad because AXIOM Terminal is terminal-first." -ForegroundColor Yellow
        return
    }

    $editorName = Split-Path -Leaf $editor

    if ($editorName -like "micro*") {
        $env:MICRO_CONFIG_HOME = $script:AxiomEditorRoot
    }

    & $editor $Path
}

function axiom-edit {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Path
    )

    $resolved = Resolve-AxiomPath $Path

    if (-not (Test-Path $resolved)) {
        $parent = Split-Path -Parent $resolved

        if ($parent) {
            New-Item -ItemType Directory -Force $parent | Out-Null
        }

        New-Item -ItemType File -Force $resolved | Out-Null
    }

    Invoke-AxiomTerminalEditor $resolved
}

function ae {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Path
    )

    axiom-edit $Path
}

function axiom-edit-profile {
    axiom-edit "ui\terminal\profile\profile-axiom.ps1"
}

function axiom-edit-user-profile {
    Invoke-AxiomTerminalEditor $PROFILE
}

function axiom-edit-config {
    axiom-edit "config\axiom.yaml"
}

function axiom-edit-schema {
    axiom-edit "axiom\persistence\schema.sql"
}

function axiom-edit-db {
    axiom-edit "axiom\persistence\db.py"
}

function axiom-edit-scheduler {
    axiom-edit "axiom\core\scheduler.py"
}

function axiom-edit-terminal-module {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name
    )

    if ($Name -notlike "*.ps1") {
        $Name = "$Name.ps1"
    }

    axiom-edit "ui\terminal\modules\$Name"
}

function axiom-install-editor {
    $winget = Get-Command winget -ErrorAction SilentlyContinue

    if (-not $winget) {
        Write-Host "winget not found. Install micro manually from https://micro-editor.github.io/" -ForegroundColor Yellow
        return
    }

    winget install -e --id zyedidia.micro
    Initialize-AxiomEditorConfig

    Write-Host ""
    Write-Host "AXIOM editor configuration initialized locally:" -ForegroundColor Green
    Write-Host "  $script:AxiomEditorRoot" -ForegroundColor Gray
    Write-Host ""
    Write-Host "AXIOM Terminal uses MICRO_CONFIG_HOME for this local config." -ForegroundColor Gray
    Write-Host "It does not need to copy config into your user profile." -ForegroundColor Gray
    Write-Host ""
}

function axiom-editor-info {
    Initialize-AxiomEditorConfig

    $editor = Get-AxiomTerminalEditor

    Write-Host ""
    Write-Host "AXIOM EDITOR INFO" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    Write-Host ""

    if ($editor) {
        Write-Host "  editor:             $editor" -ForegroundColor Green
    }
    else {
        Write-Host "  editor:             none found" -ForegroundColor Yellow
    }

    Write-Host "  editor root:        $script:AxiomEditorRoot" -ForegroundColor Gray
    Write-Host "  settings.json:      $(if (Test-Path $script:AxiomEditorSettingsPath) { 'present' } else { 'missing' })" -ForegroundColor Gray
    Write-Host "  bindings.json:      $(if (Test-Path $script:AxiomEditorBindingsPath) { 'present' } else { 'missing' })" -ForegroundColor Gray
    Write-Host "  MICRO_CONFIG_HOME:  $env:MICRO_CONFIG_HOME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Override editor for this session:" -ForegroundColor DarkGreen
    Write-Host "  `$env:AXIOM_EDITOR = 'micro'" -ForegroundColor Gray
    Write-Host ""
}

function axiom-editor-doctor {
    Initialize-AxiomEditorConfig

    Write-Host ""
    Write-Host "AXIOM EDITOR DOCTOR" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    Write-Host ""

    $editor = Get-AxiomTerminalEditor
    $micro = Get-Command micro -ErrorAction SilentlyContinue

    if ($editor) {
        Write-Host "  selected editor:    $editor" -ForegroundColor Green
    }
    else {
        Write-Host "  selected editor:    missing" -ForegroundColor Red
    }

    if ($micro) {
        Write-Host "  micro:              $($micro.Source)" -ForegroundColor Green
    }
    else {
        Write-Host "  micro:              missing" -ForegroundColor Yellow
    }

    Write-Host "  editor root:        $script:AxiomEditorRoot" -ForegroundColor Gray
    Write-Host "  settings.json:      $(if (Test-Path $script:AxiomEditorSettingsPath) { 'present' } else { 'missing' })" -ForegroundColor Gray
    Write-Host "  bindings.json:      $(if (Test-Path $script:AxiomEditorBindingsPath) { 'present' } else { 'missing' })" -ForegroundColor Gray

    if (Test-Path $script:AxiomEditorBindingsPath) {
        $bad = Select-String -Path $script:AxiomEditorBindingsPath -Pattern "Replace" -SimpleMatch -ErrorAction SilentlyContinue

        if ($bad) {
            Write-Host "  binding issue:      Replace binding found" -ForegroundColor Red
            foreach ($match in $bad) {
                Write-Host "                      $($match.Line)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "  binding issue:      none detected" -ForegroundColor Green
        }
    }

    $userConfigs = @(
        "$env:USERPROFILE\.config\micro\bindings.json",
        "$env:APPDATA\micro\bindings.json"
    )

    Write-Host ""
    Write-Host "  user-level binding files:" -ForegroundColor DarkGreen

    foreach ($p in $userConfigs) {
        if (Test-Path $p) {
            $bad = Select-String -Path $p -Pattern "Replace" -SimpleMatch -ErrorAction SilentlyContinue
            if ($bad) {
                Write-Host "    $p : contains Replace binding" -ForegroundColor Yellow
            }
            else {
                Write-Host "    $p : present" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "    $p : absent" -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    Write-Host "Test:" -ForegroundColor DarkGreen
    Write-Host "  axiom-edit ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md" -ForegroundColor Gray
    Write-Host ""
}