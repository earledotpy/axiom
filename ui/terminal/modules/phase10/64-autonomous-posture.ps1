# ============================================================
# AXIOM Terminal Autonomous Posture
# File: C:\axiom\ui\terminal\modules\64-autonomous-posture.ps1
#
# Purpose:
#   Display 7-step autonomous readiness gate.
#   Shows each step status and overall readiness.
#
# Boundary:
#   Read-only. No runtime state mutations.
# ============================================================

. "C:\axiom\ui\terminal\modules\shared\39-operator-ui.ps1"

function Get-AutonomousGateStatus {
    $python = @'
from axiom.security.autonomous_gate_panel import get_autonomous_gate_status
import json

try:
    data = get_autonomous_gate_status()
    print(json.dumps(data.to_dict(), ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False))
'@

    try {
        $json = $python | python -c $python 2>$null

        if ([string]::IsNullOrWhiteSpace($json)) {
            return $null
        }

        $obj = $json | ConvertFrom-Json
        return $obj
    }
    catch {
        return $null
    }
}

function axiom-autonomous-posture {
    Write-AxiomUiTitle "AUTONOMOUS POSTURE" "7-step readiness gate"

    $gate = Get-AutonomousGateStatus

    if (-not $gate) {
        Write-Host "  (Unable to fetch autonomous gate status)" -ForegroundColor Red
        return
    }

    Write-AxiomUiSection "Readiness Checklist"

    if ($gate.steps) {
        foreach ($step in $gate.steps) {
            $icon = if ($step.passed) { "✓" } else { "✗" }
            $color = if ($step.passed) { "Green" } else { "Red" }

            Write-Host "  " -NoNewline
            Write-Host $icon -NoNewline -ForegroundColor $color
            Write-Host " Step $($step.step_number): " -NoNewline -ForegroundColor Gray
            Write-Host $step.name -ForegroundColor $color
            Write-Host "    $($step.reason)" -ForegroundColor DarkGray
        }
    }

    Write-AxiomUiRule

    # Overall status
    if ($gate.overall_ready) {
        Write-Host "  Overall Status: " -NoNewline -ForegroundColor Gray
        Write-Host "READY" -ForegroundColor Green
    } else {
        Write-Host "  Overall Status: " -NoNewline -ForegroundColor Gray
        Write-Host "BLOCKED" -ForegroundColor Yellow

        if ($gate.blocking_reasons -and $gate.blocking_reasons.Count -gt 0) {
            Write-Host ""
            Write-Host "  Blocking Issues:" -ForegroundColor Yellow
            foreach ($reason in $gate.blocking_reasons) {
                Write-Host "    • $reason" -ForegroundColor Yellow
            }
        }
    }
}

axiom-autonomous-posture
