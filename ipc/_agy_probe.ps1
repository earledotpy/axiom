. C:\axiom\ipc\conpty_capture.ps1
$r = Invoke-ConPtyCapture -Command "C:\Users\tanne\AppData\Local\agy\bin\agy.exe" -Arguments @("--print","say the word test") -WorkingDir "C:\axiom" -TimeoutMs 45000 -Diagnostic
$r | Out-File C:\axiom\ipc\_agy_probe.txt -Encoding UTF8
