# AXIOM git/docs helpers

function Test-AxiomGit { return [bool](Get-Command git -ErrorAction SilentlyContinue) }

function axiom-git-status {
    if (-not (Test-AxiomGit)) { Write-Host "git not found." -ForegroundColor Yellow; return }
    Push-Location $env:AXIOM_ROOT
    try { git status --short --branch }
    finally { Pop-Location }
}

function axiom-git-diff {
    if (-not (Test-AxiomGit)) { Write-Host "git not found." -ForegroundColor Yellow; return }
    Push-Location $env:AXIOM_ROOT
    try { git diff --stat; git diff -- . ':!*.db' ':!logs/*' }
    finally { Pop-Location }
}

function axiom-tree {
    $anchors = @('axiom','axiom\core','axiom\gateways','axiom\persistence','axiom\policy','axiom\security','config','logs','tools','tests','ui\terminal')
    Write-Host ""
    Write-Host "AXIOM project anchors" -ForegroundColor Green
    foreach ($a in $anchors) {
        $p = Join-Path $env:AXIOM_ROOT $a
        if (Test-Path $p) { Write-Host "[ok]      $a" -ForegroundColor DarkGreen }
        else { Write-Host "[missing] $a" -ForegroundColor Yellow }
    }
}

function axiom-files {
    Write-Host ""
    Write-Host "AXIOM key files" -ForegroundColor Green
    Write-Host "profile:                 C:\axiom\ui\terminal\profile\profile-axiom.ps1"
    Write-Host "terminal modules:        C:\axiom\ui\terminal\modules"
    Write-Host "Windows Terminal snippet:C:\axiom\ui\terminal\terminal\windows-terminal-axiom-snippet.jsonc"
    Write-Host "background:              C:\axiom\ui\terminal\assets\axiom-crt-background.png"
    Write-Host "config:                  C:\axiom\config\axiom.yaml"
    Write-Host "database:                C:\axiom\axiom.db"
    Write-Host "schema:                  C:\axiom\axiom\persistence\schema.sql"
}

function axiom-terminal-settings {
    $stable = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
    $preview = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'
    $snippet = 'C:\axiom\ui\terminal\terminal\windows-terminal-axiom-snippet.jsonc'
    Write-Host "Windows Terminal settings candidates:" -ForegroundColor Green
    if (Test-Path $stable) { Write-Host "stable:  $stable" }
    if (Test-Path $preview) { Write-Host "preview: $preview" }
    Write-Host "AXIOM snippet: $snippet" -ForegroundColor DarkGreen
    Write-Host ""
    if (Test-Path $snippet) { Invoke-AxiomTerminalEditor $snippet }
}

function axiom-new-terminal-module {
    param([Parameter(Mandatory=$true)][string]$Name)
    if ($Name -notmatch '^\d{2}-[a-z0-9_-]+\.ps1$') {
        Write-Host "Use a numbered module name like: 50-my-feature.ps1" -ForegroundColor Yellow
        return
    }
    $target = Join-Path 'C:\axiom\ui\terminal\modules' $Name
    if (Test-Path $target) { Write-Host "Module already exists: $target" -ForegroundColor Yellow; return }
    $template = 'C:\axiom\ui\terminal\templates\terminal-module.template.ps1'
    if (Test-Path $template) { Copy-Item $template $target }
    else { New-Item -ItemType File -Force $target | Out-Null }
    axiom-edit $target
}
