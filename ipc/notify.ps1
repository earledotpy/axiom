param(
    [string]$Message = "Axiom notification",
    [string]$Title   = "Axiom",
    [int]   $Timeout = 10
)

$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}

$shell = New-Object -ComObject WScript.Shell
$shell.Popup($Message, $Timeout, $Title, 0x40) | Out-Null
