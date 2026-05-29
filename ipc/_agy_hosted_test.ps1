. C:\axiom\ipc\conpty_capture.ps1
$r = Invoke-ConPtyCaptureHosted -Command "C:\Users\tanne\AppData\Local\agy\bin\agy.exe" -Arguments @("--print","say the word test") -WorkingDir "C:\axiom" -TimeoutMs 45000
"RESULT=[$r]" | Out-File C:\axiom\ipc\_agy_hosted_test.txt -Encoding UTF8
