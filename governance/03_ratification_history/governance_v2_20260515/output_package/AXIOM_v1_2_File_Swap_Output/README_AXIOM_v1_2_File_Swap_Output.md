# AXIOM v1.2 File-Swap Output Package

Generated from `AXIOM_v1_2_File_Swap_Source.zip` on 2026-05-15.

## Contents

- `AXIOM_Panel_Charter.md` — updated Charter v1.2
- `AXIOM_Panel_Tier_Membership.md` — new tier membership reference
- `AXIOM_Active_Bindings_v1_2.md` — new versioned bindings registry
- `AXIOM_Active_Bindings.md` — alias copy of v1.2 bindings
- `AXIOM_Specification_Debt.md` — updated with Governance v2 SD items and PDR Summary
- `AXIOM_Project_Instructions.md` — v1.2-derived Claude Project Instructions
- `AXIOM_Operator_Guide.md` — v1.2-derived Operator Guide
- `AXIOM_Canonical_Filenames.md` — updated canonical filename registry
- `AXIOM_Ratification_Confirmation_20260515.md` — ratification confirmation artifact
- `IS_Handoff_Kimi_to_Gemini_20260515/` — handoff package for Gemini
- `AXIOM_Archive/20260515_063423_Governance_v2_Ratification/` — archive of source files with `MANIFEST.sha256`
- `AXIOM_Ratification_File_Swap_Runbook_Governance_v2.md` — operator runbook used for this package
- `verify_axiom_v1_2_file_swap.ps1` — verification script

## Required Manual Actions Remaining

1. Review `AXIOM_Panel_Charter.md` once end-to-end before replacing your live copy.
2. Replace the Claude AXIOM Project Instructions with `AXIOM_Project_Instructions.md`.
3. Set the 30-day audit reminder for 2026-06-14.
4. Upload the updated files to the Claude AXIOM Project knowledge base.
5. Deliver `IS_Handoff_Kimi_to_Gemini_20260515/` to Gemini.
6. Run panel smoke tests per the runbook.

## Verification

From PowerShell in this directory:

```powershell
.erify_axiom_v1_2_file_swap.ps1
```
