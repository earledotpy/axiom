# ipc/_inbox_antigravity.ps1
# Phase 2: inbound IPC is review-only. It must not invoke Antigravity.

$IPC_PHASE2_NEUTRALIZE_ACTIVE = $true

Write-Output "[ipc-neutralized] Antigravity IPC inbox auto-invocation is disabled."
Write-Output "[ipc-neutralized] Review ipc/to_antigravity.md manually in the terminal pane."
return
