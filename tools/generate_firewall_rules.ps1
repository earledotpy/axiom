param(
    [string[]]$Principals = @("axiom_builder", "axiom_reviewer", "axiom_verifier"),
    [string]$LoopbackProxy = "127.0.0.1",
    [int]$LoopbackPort = 8765
)

$ErrorActionPreference = "Stop"

foreach ($Principal in $Principals) {
    [pscustomobject]@{
        principal = $Principal
        action = "Allow"
        direction = "Outbound"
        remoteAddress = $LoopbackProxy
        remotePort = $LoopbackPort
        dryRun = $true
        rule = "Allow $Principal outbound only to $LoopbackProxy`:$LoopbackPort"
    }
    [pscustomobject]@{
        principal = $Principal
        action = "Block"
        direction = "Outbound"
        remoteAddress = "0.0.0.0/0"
        remotePort = "Any"
        dryRun = $true
        rule = "Block $Principal direct raw outbound egress"
    }
}
