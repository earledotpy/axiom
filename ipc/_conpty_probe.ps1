. C:\axiom\ipc\conpty_capture.ps1
$r = Invoke-ConPtyCapture -Command (Get-Command pwsh).Source -Arguments @("-NoProfile","-c","Write-Host 'colored_text' -ForegroundColor Cyan") -TimeoutMs 8000
"RESULT=[$r]" | Out-File C:\axiom\ipc\_conpty_probe.txt -Encoding UTF8
