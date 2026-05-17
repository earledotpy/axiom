# AXIOM v1.2 File-Swap Verification Script
# Run from the directory containing the updated AXIOM files.

Write-Host "== AXIOM v1.2 Verification =="

$content = Get-Content "AXIOM_Active_Bindings_v1_2.md"
$abCount = ($content | Select-String -Pattern "^\| AB-\d{3} \|").Count
$cbCount = ($content | Select-String -Pattern "^\| CB-\d{3} \|").Count
$gbCount = ($content | Select-String -Pattern "^\| GB-\d{3} \|").Count
$total = $abCount + $cbCount + $gbCount
Write-Host "AB: $abCount, CB: $cbCount, GB: $gbCount, Total: $total"
if ($abCount -eq 7 -and $cbCount -eq 25 -and $gbCount -eq 4 -and $total -eq 36) { Write-Host "PASS: Binding count" } else { Write-Host "FAIL: Binding count" }

$hashAlias = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings.md").Hash
$hashV12 = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings_v1_2.md").Hash
if ($hashAlias -eq $hashV12) { Write-Host "PASS: Active Bindings alias matches v1.2" } else { Write-Host "FAIL: Active Bindings alias does not match v1.2" }

$charter = Get-Content "AXIOM_Panel_Charter.md" -Raw
if ($charter -match "\*\*Version:\*\* v1\.2") { Write-Host "PASS: Charter version v1.2" } else { Write-Host "FAIL: Charter version not v1.2" }

$sd = Get-Content "AXIOM_Specification_Debt.md" -Raw
if ($sd -match "## PDR Summary") { Write-Host "PASS: PDR Summary present" } else { Write-Host "FAIL: PDR Summary missing" }

if (Test-Path "AXIOM_Panel_Tier_Membership.md") { Write-Host "PASS: Panel Tier Membership exists" } else { Write-Host "FAIL: Panel Tier Membership missing" }
if (Test-Path "AXIOM_Ratification_Confirmation_20260515.md") { Write-Host "PASS: Ratification Confirmation exists" } else { Write-Host "FAIL: Ratification Confirmation missing" }
if (Test-Path "AXIOM_Archive/20260515_063423_Governance_v2_Ratification/MANIFEST.sha256") { Write-Host "PASS: Archive manifest exists" } else { Write-Host "FAIL: Archive manifest missing" }
