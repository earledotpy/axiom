. C:\axiom\ipc\conpty_capture.ps1
Invoke-ConPtyCapture -Command "C:\Windows\System32\cmd.exe" -Arguments @("/c","echo hello_from_conpty") -TimeoutMs 5000 -Diagnostic | Out-Null
