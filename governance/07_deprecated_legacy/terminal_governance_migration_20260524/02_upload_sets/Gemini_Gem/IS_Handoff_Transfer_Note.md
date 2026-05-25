# Implementation Specialist Role Transition — Kimi → Gemini

**Transfer Date:** 2026-05-15  
**Authority:** AXIOM_Synthesis_Governance_v2_Cycle2.md §14 Operation F  
**Outgoing Implementation Specialist:** Kimi K2.6  
**Incoming Implementation Specialist:** Gemini 3.1 Pro

## Files Transferred

| File | Status |
|---|---|
| AXIOM_Ratification_File_Swap_Runbook.md | transferred |
| AXIOM_Governance_Implementability_Review_v1_2.md | transferred |
| AXIOM_Governance_Implementability_Review_v2_Cycle2.md | transferred |
| AXIOM_Diff_Gate_Runbook.md | transferred |
| AXIOM_Canonical_Filenames.md | transferred |

## Implementation-Stage Operational Responsibilities

Per Kimi's Cycle 2 Implementability Review §8, the Implementation Specialist role's operational responsibilities are:

1. Producing implementation plans from approved architecture proposals.
2. Diff Gate operation per Charter v1.1/v1.2 §Integration Discipline.
3. Authorized Change List format per Charter v1.1/v1.2 §Integration Discipline.
4. Binding cross-check during integration verification.
5. Archive directory conventions (`AXIOM_Archive/<YYYYMMDD_HHMMSS>/`) and `MANIFEST.sha256` generation.
6. Specification Debt ledger schema maintenance.
7. Canonical Filenames Registry updates as new artifacts emerge.

## Exception: GB-001 Cross-Cutting Artifact Packaging

Per v2_1 §1.4, GB-001 cross-cutting artifact packaging remains with Kimi as a binding-specific exception, regardless of the Implementation Specialist role transition. If future cross-cutting artifacts arise, Kimi continues packaging them per Charter v1.2 §Cross-Cutting Artifact Protocol until GB-001 is explicitly superseded.

## Knowledge Continuity Notes

Gemini assumes the Implementation Specialist and Troubleshooter role under Charter v1.2. Gemini should treat implementation outputs as operator-executable support only unless a troubleshooting recommendation changes architecture, policy, security boundaries, role authority, runtime constraints, binding interpretation, file conventions, or introduces new dependencies. Those cases must route back through Architect/Evaluator governance.

Jeremy Earle / AXIOM Operator
