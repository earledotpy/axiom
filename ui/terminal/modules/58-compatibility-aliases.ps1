# AXIOM Terminal compatibility aliases.
# Preferred command names remain documented in the registry.

function axiom-open {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Path
    )

    Write-Host "[AXIOM] compatibility alias: use axiom-edit." -ForegroundColor Yellow
    axiom-edit $Path
}

function np {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Path
    )

    Write-Host "[AXIOM] compatibility alias: use ae or axiom-edit." -ForegroundColor Yellow
    axiom-edit $Path
}

function axiom-terminal-logs {
    if (Get-Command axiom-logs -ErrorAction SilentlyContinue) {
        axiom-logs
        return
    }

    $logPath = Join-Path $env:AXIOM_ROOT 'logs'
    if (-not (Test-Path $logPath)) {
        Write-Host "No logs directory." -ForegroundColor Yellow
        return
    }

    Get-ChildItem $logPath -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 25 Name, LastWriteTime, Length |
        Format-Table -AutoSize
}
