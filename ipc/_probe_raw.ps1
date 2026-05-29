. C:\axiom\ipc\conpty_capture.ps1
$session = [ConPty.ConPtySession]::new()
$cmdLine = Format-CommandLine -Exe "C:\Windows\System32\cmd.exe" -Args @("/c","echo hello_from_conpty")
"CMDLINE=[$cmdLine]" | Out-File C:\axiom\ipc\_probe_raw.txt -Encoding UTF8
$session.Start($cmdLine, 'C:\axiom')
$null = $session.WaitForExit(8000)
$session.Dispose()
$bytes = $session.GetRawBytes()
$raw = [System.Text.Encoding]::UTF8.GetString($bytes)
"BYTES=$($bytes.Length)" | Out-File C:\axiom\ipc\_probe_raw.txt -Append -Encoding UTF8
"RAW=[$raw]" | Out-File C:\axiom\ipc\_probe_raw.txt -Append -Encoding UTF8
$stripped = Strip-Ansi -Raw $raw
"STRIPPED=[$stripped]" | Out-File C:\axiom\ipc\_probe_raw.txt -Append -Encoding UTF8
