# ============================================================
# AXIOM Terminal Oh My Posh Dashboard Prompt
# File: C:\axiom\ui\terminal\modules\06-oh-my-posh.ps1
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

$script:AxiomOmpThemePath = Join-Path $script:AxiomRoot "ui\terminal\themes\axiom-dashboard.omp.json"

function Test-AxiomOhMyPosh {
    $omp = Get-Command oh-my-posh -ErrorAction SilentlyContinue

    if (-not $omp) {
        Write-Host "[AXIOM] Oh My Posh not found. Install with: winget install JanDeDobbeleer.OhMyPosh -s winget" -ForegroundColor Yellow
        return $false
    }

    if (-not (Test-Path $script:AxiomOmpThemePath)) {
        Write-Host "[AXIOM] Oh My Posh theme missing: $script:AxiomOmpThemePath" -ForegroundColor Yellow
        return $false
    }

    return $true
}

function Enable-AxiomDashboardPrompt {
    param([switch]$Quiet)

    $env:AXIOM_PROMPT_ENGINE = "oh-my-posh"

    if (-not (Test-AxiomOhMyPosh)) {
        return
    }

    $initScript = @(oh-my-posh init pwsh --config $script:AxiomOmpThemePath 2>$null)

    if ($LASTEXITCODE -ne 0 -or -not $initScript -or $initScript.Count -eq 0) {
        $env:AXIOM_PROMPT_ENGINE = "native"
        if (-not $Quiet) {
            Write-Host "[AXIOM] Oh My Posh could not initialize. Native prompt remains active." -ForegroundColor Yellow
        }
        return
    }

    $initScript | Invoke-Expression
}

function Disable-AxiomDashboardPrompt {
    $env:AXIOM_PROMPT_ENGINE = "native"
    Write-Host "[AXIOM] Dashboard prompt disabled for this session. Reload terminal for native prompt." -ForegroundColor Yellow
}

function axiom-posh-on {
    Enable-AxiomDashboardPrompt
}

function axiom-posh-off {
    Disable-AxiomDashboardPrompt
}

function axiom-posh-test {
    Write-Host ""
    Write-Host "AXIOM Oh My Posh check" -ForegroundColor Green
    Write-Host "theme: $script:AxiomOmpThemePath"

    $omp = Get-Command oh-my-posh -ErrorAction SilentlyContinue
    if ($omp) {
        Write-Host "oh-my-posh: $($omp.Source)" -ForegroundColor Green
        oh-my-posh version
    }
    else {
        Write-Host "oh-my-posh: missing" -ForegroundColor Red
    }

    if (Test-Path $script:AxiomOmpThemePath) {
        Write-Host "theme file: present" -ForegroundColor Green
    }
    else {
        Write-Host "theme file: missing" -ForegroundColor Red
    }

    Write-Host "AXIOM_PROMPT_ENGINE: $env:AXIOM_PROMPT_ENGINE"
    Write-Host ""
}

# Dashboard prompt is opt-in. Profile load must stay quiet and deterministic;
# use axiom-posh-on when an interactive dashboard prompt is desired.
if ($env:AXIOM_PROMPT_ENGINE -eq "oh-my-posh") {
    $env:AXIOM_PROMPT_ENGINE = "native"
}
