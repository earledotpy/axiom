$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

. C:\axiom\ipc\conpty_capture.ps1
$r = Invoke-ConPtyCapture -Command "C:\Users\tanne\AppData\Local\agy\bin\agy.exe" -Arguments @("--print","say the word test") -WorkingDir "C:\axiom" -TimeoutMs 45000 -Diagnostic
$r | Out-File C:\axiom\ipc\_agy_probe.txt -Encoding UTF8
