# AXIOM Specification Debt Ledger

Canonical specification-debt registry per Charter v1.1 §5.2.  
Append-only. Closures are recorded by updating the Status field, not by removing rows.  
Initial population: 2026-05-10 at v1.0 → v1.1 ratification.

---

## Ledger Schema

| Field | Description |
|---|---|
| Debt ID | `SD-###` unique identifier |
| Source | Synthesis document or review that opened the item |
| Subject | Brief description |
| Severity | `LOW` / `LOW-MEDIUM` / `MEDIUM` / `BLOCKING` |
| Cycle Count | `1 of 2` / `2 of 2` / `Closed` |
| Status | `Open` / `Closed` / `Deferred` / `Superseded` |
| Closure Section/Artifact | Document and section where closure occurred, if closed |
| Notes | Additional context |

---

## Historical Closed Items — Cycle 1 SD-001 through SD-018

| Debt ID | Source | Subject | Severity | Cycle Count | Status | Closure Section/Artifact | Notes |
|---|---|---|---|---|---|---|---|
| SD-001 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Deferral authority for specification-debt items | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §5.4 | Closed in Cycle 2. |
| SD-002 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Authorship provenance of v1.1 PROPOSED drafts | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §10.2 | Closed in Cycle 2. |
| SD-003 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | §4.3 ↔ §7.3 supersession reconciliation | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §8.1 | Closed in Cycle 2. |
| SD-004 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Status of GB-001 protocol extension — proposed vs. ratified | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §6.1 | Closed in Cycle 2. |
| SD-005 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Identity of integration verification role | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §4.2 | Closed in Cycle 2. |
| SD-006 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Self-flagging mechanism for unrecorded specification gaps | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §5.1 | Closed in Cycle 2. |
| SD-007 | AXIOM_Synthesis_Governance_v1_1.md §5.1 | Kimi implementability review of Synthesis structure, Diff Gate, and binding crosswalk | Medium | Closed | Closed | AXIOM_Governance_Implementability_Review.md | Closed procedurally. |
| SD-008 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Objection Disposition Matrix schema | Blocking | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §0.1 | Closed in Cycle 2. |
| SD-009 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Specification debt canonical storage location and format | Blocking | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §5.2–§5.3 | Closed in Cycle 2. |
| SD-010 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Synthesis workflow specification — naming, trigger, storage | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §9.1 | Closed in Cycle 2. |
| SD-011 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | CV2 panel-approval mechanism for sanitization tasks | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §7.1 | Closed in Cycle 2. |
| SD-012 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | CV5 infrastructure guardrail enforcement specifics | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §7.2 | Closed in Cycle 2. |
| SD-013 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Constraints Register crosswalk maintenance and validation | Low-Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §8.5 | Closed in Cycle 2. |
| SD-014 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Active Bindings filename standardization and alias maintenance | Low | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §9.2 | Closed in Cycle 2. |
| SD-015 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Charter amendment 30-day audit operationalization | Low | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §2.2 | Closed in Cycle 2. |
| SD-016 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Cross-cutting protocol artifact-type ownership edges | Low | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §6 | Closed in Cycle 2. |
| SD-017 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Canonical filenames registry build | Low-Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §9.3 | Closed in Cycle 2. |
| SD-018 | AXIOM_Synthesis_Governance_v1_1.md §5.3 | Delta-confirmation criterion #6 ↔ §4.6 Diff Gate dependency | Low | Closed | Closed | AXIOM_Proposal_Governance_v1.1.md §3.5 | Closed in Cycle 2. |

---

## Cycle 2 Items — SD-019 through SD-034

| Debt ID | Source | Subject | Severity | Cycle Count | Status | Closure Section/Artifact | Notes |
|---|---|---|---|---|---|---|---|
| SD-019 | AXIOM_Synthesis_Governance_v2.md §6.1 | Cross-cutting protocol class list shifted between v1 and v1.1 without annotation | Low-Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.2.md §6.5 | Closed in Cycle 3 per Synthesis v3 §8.1. |
| SD-020 | AXIOM_Synthesis_Governance_v2.md §6.1 | Objection window operational mechanics | Medium | 1 of 2 | Open |  | Partially addressed by §3.3; remains open per Synthesis v3 §9.2. |
| SD-021 | AXIOM_Synthesis_Governance_v2.md §6.1 | Diff Gate operator runbook | Medium | 1 of 2 | Open |  | Kimi to produce on first Diff Gate use. |
| SD-022 | AXIOM_Synthesis_Governance_v2.md §6.1 | Debt ledger append protocol | Medium | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-023 | AXIOM_Synthesis_Governance_v2.md §6.1 | Integrator handoff artifact | Medium | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-024 | AXIOM_Synthesis_Governance_v2.md §6.1 | Alternate gatekeeper role tension | Medium | Closed | Closed | AXIOM_Proposal_Governance_v1.2.md §4.2 | Closed in Cycle 3 per Synthesis v3 §8.2. |
| SD-025 | AXIOM_Synthesis_Governance_v2.md §6.1 | Archive directory bootstrap | Low | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-026 | AXIOM_Synthesis_Governance_v2.md §6.1 | Synthesis as mandatory upload | Low-Medium | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-027 | AXIOM_Synthesis_Governance_v2.md §6.1 | Deferral record format | Low | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-028 | AXIOM_Synthesis_Governance_v2.md §6.1 | Canonical Filenames Registry initial population | Low | 1 of 2 | Open |  | Partially addressed by ratification file swap; remains open per Synthesis v3 §9.2. |
| SD-029 | AXIOM_Synthesis_Governance_v2.md §6.1 | Authorized Change List authorship | Low | 1 of 2 | Open |  | Remains open per Synthesis v3 §9.2. |
| SD-030 | AXIOM_Synthesis_Governance_v2.md §6.1 | Windows UTF-8 / line-ending Diff Gate I/O | Low | 1 of 2 | Open |  | Implementation-stage Kimi requirement. |
| SD-031 | AXIOM_Synthesis_Governance_v2.md §6.1 | Sub-second timestamp collision risk | Low | 1 of 2 | Open |  | Implementation-stage Kimi requirement. |
| SD-032 | AXIOM_Synthesis_Governance_v2.md §6.1 | Append-only ledger physical-layer integrity | Low-Medium | 1 of 2 | Open |  | Cross-version comparison dependency. |
| SD-033 | AXIOM_Synthesis_Governance_v2.md §6.1 | DoS via spurious objection filings | Low-Medium | 1 of 2 | Open |  | Partially addressed by §3.3 ground-citation requirement; remains open per Synthesis v3 §9.2. |
| SD-034 | AXIOM_Synthesis_Governance_v2.md §6.1 | Operator-side bottleneck for delta artifact posting | Low | 1 of 2 | Open |  | Reliability risk only. |

---

## Cycle 3 Items — SD-035 through SD-044

| Debt ID | Source | Subject | Severity | Cycle Count | Status | Closure Section/Artifact | Notes |
|---|---|---|---|---|---|---|---|
| SD-035 | AXIOM_Synthesis_Governance_v3.md §9.1 | "One cycle" duration undefined for D2.A trivial-flag dismissal motions (mid-cycle vs. cycle-start variance) | LOW-MEDIUM | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-036 | AXIOM_Synthesis_Governance_v3.md §9.1 | Discrepancy-flag entry recursion in §5.7 — flag mechanism flows through Evaluator (the role being checked) | LOW-MEDIUM | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-037 | AXIOM_Synthesis_Governance_v3.md §9.1 | Arbiter alternate gatekeeper assignment without explicit Arbiter consent in routing scope | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-038 | AXIOM_Synthesis_Governance_v3.md §9.1 | §0.2 Cycle-1 Closure Map D1 and D2 rows not updated to cross-reference §0.3 patch closures (audit-trail completeness) | LOW-MEDIUM | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-039 | AXIOM_Synthesis_Governance_v3.md §9.1 | Identity-reference update policy for scope-bounded patches (§1.3, §11, §13, EOF marker remain v1.1/Cycle-2 identified in v1.2) | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-040 | AXIOM_Synthesis_Governance_v3.md §9.1 | Time-zone and timestamp ambiguity for 72-hour objection window (post timestamp format unspecified) | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-041 | AXIOM_Synthesis_Governance_v3.md §9.1 | "Explicit no-objection" format undefined — does "No objection" message suffice? Substantive commentary without explicit objection? | LOW-MEDIUM | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-042 | AXIOM_Synthesis_Governance_v3.md §9.1 | Ground citation requirement explicit vs. implicit — must objection cite ground number? | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-043 | AXIOM_Synthesis_Governance_v3.md §9.1 | Rapid-fire dismissal motion prevention — no rate limit on dismissal motions | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |
| SD-044 | AXIOM_Synthesis_Governance_v3.md §9.1 | Affirmative statement format for §5.7 Synthesis-vs-ledger cross-check (standalone section vs. paragraph; blanket assertion vs. enumeration) | LOW | 1 of 2 | Open |  | Canonical Cycle 3 SD item. |

---

*AXIOM Specification Debt Ledger — Initial v1.1 population prepared 2026-05-10 from Synthesis v2 and Synthesis v3 canonical SD tables.*
