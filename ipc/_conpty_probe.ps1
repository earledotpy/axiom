$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

. C:\axiom\ipc\conpty_capture.ps1
$r = Invoke-ConPtyCapture -Command (Get-Command pwsh).Source -Arguments @("-NoProfile","-c","Write-Host 'colored_text' -ForegroundColor Cyan") -TimeoutMs 8000
"RESULT=[$r]" | Out-File C:\axiom\ipc\_conpty_probe.txt -Encoding UTF8
