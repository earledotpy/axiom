. C:\axiom\ipc\conpty_capture.ps1
$bytes = $null
$raw = $null
$session = [ConPty.ConPtySession]::new()
$session.Start('"C:\Windows\System32\cmd.exe" /c echo hello_from_conpty', 'C:\axiom')
$null = $session.WaitForExit(8000)
$session.Dispose()
$bytes = $session.GetRawBytes()
$raw = [System.Text.Encoding]::UTF8.GetString($bytes)
"BYTES=$($bytes.Length)" | Out-File C:\axiom\ipc\_probe_diag.txt -Encoding UTF8
$raw | Out-File C:\axiom\ipc\_probe_diag.txt -Append -Encoding UTF8
