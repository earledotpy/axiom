# ipc/_inbox_codex.ps1
# Phase 2: inbound IPC is review-only. It must not invoke Codex.

$IPC_PHASE2_NEUTRALIZE_ACTIVE = $true

Write-Output "[ipc-neutralized] Codex IPC inbox auto-invocation is disabled."
Write-Output "[ipc-neutralized] Review ipc/to_codex.md manually in the terminal pane."
return
