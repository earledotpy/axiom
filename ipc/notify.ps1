param(
    [string]$Message = "Axiom notification",
    [string]$Title   = "Axiom",
    [int]   $Timeout = 10
)
$shell = New-Object -ComObject WScript.Shell
$shell.Popup($Message, $Timeout, $Title, 0x40) | Out-Null
