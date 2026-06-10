param([Parameter(Mandatory)][string]$Agent)

Write-Output "[ipc-neutralized] watcher_service.ps1 notification automation is disabled for $Agent."
Write-Output "[ipc-neutralized] Check ipc/to_$($Agent.ToLower()).md manually when directed."
return
