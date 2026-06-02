$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

. C:\axiom\ipc\conpty_capture.ps1
Invoke-ConPtyCapture -Command "C:\Windows\System32\cmd.exe" -Arguments @("/c","echo hello_from_conpty") -TimeoutMs 5000 -Diagnostic | Out-Null
