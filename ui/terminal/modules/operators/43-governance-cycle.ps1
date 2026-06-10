# ============================================================
# AXIOM Terminal Governance Cycle Commands
# File: C:\axiom\ui\terminal\modules\operators\43-governance-cycle.ps1
#
# Purpose:
#   Clean operator-facing commands for JSON-first governance records.
#
# Boundary:
#   These commands operate through approved governance tools.
#   They do not execute patches, route agents, reactivate IPC, start
#   scheduler/executor loops, enable autonomy, or emit VERIFIED_COMMIT.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

function Invoke-AxiomGovernanceTool {
    param(
        [Parameter(Mandatory = $true)][string]$Tool,
        [string[]]$ToolArguments = @()
    )
    $normalizedToolArguments = @($ToolArguments | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $callArgs = @($Tool) + $normalizedToolArguments
    Invoke-AxiomPython -Arguments $callArgs
}

function Show-AxiomGovernanceToolHelp {
    param(
        [Parameter(Mandatory = $true)][string]$Tool
    )
    Invoke-AxiomGovernanceTool -Tool $Tool -ToolArguments @('--help')
}

function state {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($Args -and $Args.Count -gt 0) {
        Invoke-AxiomGovernanceTool -Tool 'tools\operator_console.py' -ToolArguments $Args
    }
    else {
        Invoke-AxiomGovernanceTool -Tool 'tools\operator_console.py' -ToolArguments @('/axiom:show-active-state', '--json')
    }
}

function cycle {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($Args -and $Args.Count -gt 0) {
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments $Args
    }
    else {
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments @('summary')
    }
}

function next {
    Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments @('next-actions', '--json')
}

function review {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if (-not $Args -or $Args.Count -eq 0) {
        Show-AxiomGovernanceToolHelp -Tool 'tools\review_ingest.py'
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\review_ingest.py' -ToolArguments (@('create') + @($Args))
}

function accept {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($Args -and $Args.Count -gt 0 -and $Args[0] -eq 'record') {
        $remaining = if ($Args.Count -gt 1) { @($Args[1..($Args.Count - 1)]) } else { @() }
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments (@('decision-record') + $remaining)
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments (@('decision-preview', '--decision', 'approve') + @($Args))
}

function decide {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if (-not $Args -or $Args.Count -eq 0) {
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  decide --decision defer --target-id <id> --scope <scope>"
        Write-Host "  decide record --preview-id <DEC-id> --confirm <token>"
        return
    }
    if ($Args[0] -eq 'record') {
        $remaining = if ($Args.Count -gt 1) { @($Args[1..($Args.Count - 1)]) } else { @() }
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments (@('decision-record') + $remaining)
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments (@('decision-preview') + @($Args))
}

function task {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if (-not $Args -or $Args.Count -eq 0) {
        Show-AxiomGovernanceToolHelp -Tool 'tools\task_card.py'
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\task_card.py' -ToolArguments $Args
}

function delegate {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if (-not $Args -or $Args.Count -eq 0) {
        Show-AxiomGovernanceToolHelp -Tool 'tools\delegation.py'
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\delegation.py' -ToolArguments $Args
}

function evidence {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if (-not $Args -or $Args.Count -eq 0) {
        Show-AxiomGovernanceToolHelp -Tool 'tools\evidence.py'
        return
    }
    Invoke-AxiomGovernanceTool -Tool 'tools\evidence.py' -ToolArguments $Args
}

function roadmap {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($Args -and $Args.Count -gt 0) {
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments (@('file-roadmap') + @($Args))
    }
    else {
        Invoke-AxiomGovernanceTool -Tool 'tools\governance_cycle.py' -ToolArguments @('show', '--json')
    }
}

function validate {
    Invoke-AxiomGovernanceTool -Tool 'tools\validate_governance.py' -ToolArguments @('--root', $script:AxiomRoot)
}

function guard {
    axiom-guard
}

function doctor {
    axiom-doctor
}

function registry {
    axiom-registry
}

function axiom-governance {
    cycle
}

function axiom-review {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    review @Args
}

function axiom-accept {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    accept @Args
}
