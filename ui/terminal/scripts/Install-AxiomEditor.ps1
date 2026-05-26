$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "winget not found. Install micro manually from https://micro-editor.github.io/" -ForegroundColor Yellow
    exit 1
}
winget install -e --id zyedidia.micro

$src = 'C:\axiom\ui\terminal\editor\micro'
$dst = Join-Path $HOME '.config\micro'
if (Test-Path $src) {
    New-Item -ItemType Directory -Force $dst | Out-Null
    Copy-Item -Path (Join-Path $src '*') -Destination $dst -Force
    Write-Host "Copied AXIOM micro config to: $dst" -ForegroundColor DarkGreen
}
