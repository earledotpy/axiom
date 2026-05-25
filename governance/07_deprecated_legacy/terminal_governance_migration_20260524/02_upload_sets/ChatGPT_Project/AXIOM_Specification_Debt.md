# AXIOM Specification Debt Ledger

Canonical specification-debt registry per Charter v1.2 §5.2.  
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

---

## Governance v2 Cycle 1 Items — SD-045 through SD-061

| Debt ID | Source | Subject | Severity | Cycle Count | Status | Closure Section/Artifact | Notes |
|---|---|---|---|---|---|---|---|
| SD-045 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §10.1 | Working draft version-control procedure for continuous-layer drafts | LOW | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. Advances to cycle 2 of 2 at next governance cycle. |
| SD-046 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §10.2 | Simultaneous edit conflict resolution authority for shared working drafts | LOW | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. Advances to cycle 2 of 2 at next governance cycle. |
| SD-047 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §10.4 + Kimi K-CLOSURE-3 | Drive access failure fallback + mobile-device compatibility (partially addressed by Q-CB-023) | LOW-MEDIUM | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. Partially addressed by Charter v1.2 §12.7 and CB-023. |
| SD-048 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §1.1 (E-C1) | §7.5 "all six panel members" clarification for post-ratification amendment proposals | LOW | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §7.5; promoted into Charter v1.2 | Closed per Cycle 2 Synthesis §12.4. |
| SD-049 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §1.3 (E-C2) | Maintaining Authority field transition recording (pre- vs. post-ratification) | LOW | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §10.3 and §15.3; AXIOM_Active_Bindings_v1_2.md | Closed per Cycle 2 Synthesis §12.4. |
| SD-050 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §5.1 (E-C5) | §11.4 "Current Binding Text Preserved?" requires verbatim quote or hash | LOW | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §11.4 | Closed per Cycle 2 Synthesis §12.4. |
| SD-051 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §7.1 | §15.3 file-swap sample row template for extended registry schema (AB, CB, GB one each) | LOW | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §10.9 | Closed per Cycle 2 Synthesis §12.4. |
| SD-052 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Evaluation Cycle 1 §Risk 2 | Advisory retry cadence / maximum wait before escalation for rate-limited consultations | LOW | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. |
| SD-053 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §2.1 (K-CLOSURE-1) | Tier membership reference document (`AXIOM_Panel_Tier_Membership.md`) and update mechanism | LOW-MEDIUM | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §15.5 and §15.9; AXIOM_Panel_Tier_Membership.md | Closed per Cycle 2 Synthesis §12.4. |
| SD-054 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §3.1 (K-CLOSURE-2) | Trigger-detection operator checklist with keyword/pattern examples | MEDIUM | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §7.7 | Closed per Cycle 2 Synthesis §12.4. |
| SD-055 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §5.4 (K-CLOSURE-4) | Operator-executable dispute resolution procedure for Arbiter-elect disputed bindings | MEDIUM | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §11.7 | Closed per Cycle 2 Synthesis §12.4. |
| SD-056 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §7.2 (K-CLOSURE-5) | PDR mark omission detection mechanism and cross-document query capability | LOW-MEDIUM | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §8.7 | Closed per Cycle 2 Synthesis §12.4. |
| SD-057 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §8.1 (K-CLOSURE-6) | Knowledge-transfer mechanism for Implementation Specialist operational responsibilities (Kimi → Gemini) | LOW | Closed | Closed | AXIOM_Proposal_Governance_v2_1.md §13.5 | Closed per Cycle 2 Synthesis §12.4. |
| SD-058 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Kimi IS Review §3.3 and §7.1 | PDR automated extraction tool (Python or PowerShell script) | LOW | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. |
| SD-059 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / DeepSeek Critique §10 SD-Proposal-V2-Cycle1-001 | Continuous-layer model-behavior baseline for re-verification on model updates | MEDIUM | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. |
| SD-060 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / DeepSeek Critique §10 SD-Proposal-V2-Cycle1-002 | PDR syntax validation tooling (closure required at implementation stage) | LOW-MEDIUM | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4. |
| SD-061 | AXIOM_Synthesis_Governance_v2_Cycle1.md §9.2 / Arbiter-Elect Affirmation §3.3 (AB-004 qualification) | AB-004 regex pattern operational verification against actual `qwen3:4b` `/api/show` output | LOW | 1 of 2 | Open |  | Remains open per Cycle 2 Synthesis §12.4; carries forward at cycle 1 of 2. |

---

## Governance v2 Cycle 2 Items — SD-062 through SD-067

| Debt ID | Source | Subject | Severity | Cycle Count | Status | Closure Section/Artifact | Notes |
|---|---|---|---|---|---|---|---|
| SD-062 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §12.6 sanitization pipeline — output format, mechanism, file naming convention, failure handling | LOW-MEDIUM | 1 of 2 | Deferred to implementation-stage closure | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.2 | Not blocking for panel cycles before AXIOM runtime work commences; closure-required when runtime work exercises the mechanism. |
| SD-063 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §7.8 architectural trigger — procedural declaration timing; Constraints Register documentation of panel-work/desktop-access distinction | LOW | 1 of 2 | Deferred to implementation-stage closure | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.2 | Not blocking for panel cycles before AXIOM runtime work commences; closure-required when runtime work exercises the mechanism. |
| SD-064 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §7.9 advisory draft-chain delivery — scope, timer start point, delivery format, operator packaging procedure | LOW | 1 of 2 | Deferred to implementation-stage closure | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.2 | Not blocking for panel cycles before AXIOM runtime work commences; closure-required when runtime work exercises the mechanism. |
| SD-065 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §8.5 constrained Evaluator clearance — operational test for "demonstrably outside all advisory domains" | LOW | 1 of 2 | Open |  | Remains live ledger item per Cycle 2 Synthesis §12.3. |
| SD-066 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §7.6 / §10.8 CB-024 paraphrase coexisting with verbatim restatement — clarify controlling version | LOW | 1 of 2 | Open |  | Remains live ledger item per Cycle 2 Synthesis §12.3. |
| SD-067 | AXIOM_Synthesis_Governance_v2_Cycle2.md §12.1 | §13.6 / §12.4 DeepSeek early-touchpoint scope inconsistency (Core Value inclusion) | LOW | 1 of 2 | Open |  | Remains live ledger item per Cycle 2 Synthesis §12.3. |

---

## PDR Summary

This section accumulates Pending-Domain-Review marks that have been formally deferred under Charter v1.1 §5.4, escalated to binding/factual disputes, or converted into specification debt. Ordinary local PDR marks remain confined to their originating artifacts and do not migrate here.

Initial state: empty. No PDR marks have entered this state during the v1.0 → v1.1 or v1.1 → v1.2 amendment cycles.

| PDR Mark ID | Source Artifact | Subject | Disposition | Disposition Date | Notes |
|---|---|---|---|---|---|
| (none) | — | — | — | — | — |

---

*AXIOM Specification Debt Ledger — Updated 2026-05-15 for Charter v1.2 file-swap. SD-045 through SD-067 added/updated per AXIOM_Synthesis_Governance_v2_Cycle1.md §9 and AXIOM_Synthesis_Governance_v2_Cycle2.md §12.*
