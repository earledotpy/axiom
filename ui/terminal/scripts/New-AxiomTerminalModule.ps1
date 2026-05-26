param([Parameter(Mandatory=$true)][string]$Name)
. 'C:\axiom\ui\terminal\profile\profile-axiom.ps1'
axiom-new-terminal-module $Name
