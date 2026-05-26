# ============================================================
# AXIOM Terminal Phase 7 Panel
# File: C:\axiom\ui\terminal\modules\60-phase7.ps1
#
# Purpose:
#   Compact read-only Phase 7 acceptance and full-goal E2E status visibility.
#
# Boundary:
#   This module must not mutate AXIOM runtime state.
#   It calls Phase 7 tools in JSON report mode only.
#   Legacy boundary wording: acceptance/gate reports only; no E2E execution.
#   It must not run pytest, enable safe-pass, approve calibration,
#   register model fingerprints, or run full-goal E2E.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

function Get-AxiomPhase7Json {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $raw = Invoke-AxiomPythonCapture $Arguments
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }

    try {
        return $raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Write-AxiomPhase7Blockers {
    param(
        [object[]]$Blockers
    )

    if (-not $Blockers -or $Blockers.Count -eq 0) {
        Write-AxiomUiLine "blockers" "none" "Green"
        return
    }

    $first = $true
    foreach ($blocker in $Blockers) {
        if ($first) {
            Write-AxiomUiLine "blockers" ([string]$blocker) "Yellow"
            $first = $false
        }
        else {
            Write-AxiomUiLine " " ([string]$blocker) "Yellow"
        }
    }
}

function axiom-phase7 {
    Write-AxiomUiTitle "AXIOM PHASE 7"
    Write-AxiomUiStatus "READ" "boundary" "acceptance/status reports only; no E2E execution from terminal"

    $acceptance = Get-AxiomPhase7Json @('tools\run_phase7_acceptance.py', '--json')
    $gate = Get-AxiomPhase7Json @('tools\audit_phase7_e2e_gate.py', '--json')

    Write-AxiomUiSection "Acceptance"
    if ($acceptance) {
        $acceptanceColor = if ($acceptance.acceptance_inventory_passed) { "Green" } else { "Red" }
        Write-AxiomUiLine "inventory" ([string]$acceptance.acceptance_inventory_passed) $acceptanceColor
        Write-AxiomUiLine "mapped tests" ([string]$acceptance.canonical_test_paths.Count) "Cyan"
        Write-AxiomUiLine "runner executed" ([string]$acceptance.executed) $(if ($acceptance.executed) { "Yellow" } else { "Green" })
        Write-AxiomUiLine "runner pass" ([string]$acceptance.passed) $(if ($acceptance.passed) { "Green" } else { "Red" })
    }
    else {
        Write-AxiomUiLine "acceptance" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Full-goal E2E status"
    if ($acceptance) {
        Write-AxiomUiLine "accepted e2e_ready" ([string]$acceptance.e2e_ready) $(if ($acceptance.e2e_ready) { "Green" } else { "Yellow" })
        Write-AxiomPhase7Blockers -Blockers @($acceptance.e2e_blockers)
    }
    else {
        Write-AxiomUiLine "accepted status" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Isolated gate audit"
    if ($gate) {
        $gateColor = if ($gate.gate_status -eq "ready") { "Green" } else { "Yellow" }
        Write-AxiomUiLine "gate_status" ([string]$gate.gate_status) $gateColor
        Write-AxiomUiLine "e2e_ready" ([string]$gate.e2e_ready) $(if ($gate.e2e_ready) { "Green" } else { "Yellow" })
        Write-AxiomUiLine "e2e test" "$($gate.e2e_test_path); present=$($gate.e2e_test_present)" $(if ($gate.e2e_test_present) { "Green" } else { "Yellow" })
        Write-AxiomPhase7Blockers -Blockers @($gate.e2e_blockers)
    }
    else {
        Write-AxiomUiLine "gate" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Prerequisites"
    if ($acceptance -and $acceptance.prerequisites) {
        foreach ($item in @($acceptance.prerequisites)) {
            $color = if ($item.passed) { "Green" } else { "Yellow" }
            Write-AxiomUiLine ([string]$item.name) ([string]$item.detail) $color
        }
    }
    else {
        Write-AxiomUiLine "prerequisites" "unavailable" "Yellow"
    }

    Write-AxiomUiSection "Operator material"
    if ($acceptance -and $acceptance.e2e_ready) {
        Write-Host "  accepted: approved classifier calibration run" -ForegroundColor Green
        Write-Host "  accepted: current model fingerprint tied to approved calibration" -ForegroundColor Green
        Write-Host "  accepted: safe-pass readiness decision" -ForegroundColor Green
        Write-Host "  accepted: explicit operator approval for full-goal E2E" -ForegroundColor Green
        Write-Host "  boundary: no autonomy, scheduler automation, agent execution, or Telegram service" -ForegroundColor Gray
    }
    else {
        Write-Host "  1. approved classifier calibration run" -ForegroundColor Gray
        Write-Host "  2. current model fingerprint tied to approved calibration" -ForegroundColor Gray
        Write-Host "  3. safe-pass readiness decision" -ForegroundColor Gray
        if ($gate -and -not $gate.e2e_test_present) {
            Write-Host "  4. tests\e2e\test_full_goal_flow_minimum.py" -ForegroundColor Gray
            Write-Host "  5. explicit operator approval for full-goal E2E" -ForegroundColor Gray
        }
        else {
            Write-Host "  4. explicit operator approval for full-goal E2E" -ForegroundColor Gray
        }
    }

    Write-AxiomUiSection "Tools"
    Write-Host "  axiom-phase7-acceptance" -ForegroundColor Gray
    Write-Host "  axiom-phase7-e2e-gate" -ForegroundColor Gray
    Write-Host "  axiom-phase7-closeout" -ForegroundColor Gray
    Write-Host "  python tools\run_phase7_acceptance.py --run" -ForegroundColor Gray
    Write-Host ""
}
