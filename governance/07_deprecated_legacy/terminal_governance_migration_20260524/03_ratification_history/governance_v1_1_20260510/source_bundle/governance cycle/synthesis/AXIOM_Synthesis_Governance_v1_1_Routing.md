# AXIOM_Synthesis_Governance_v1_1_Routing.md
## Cycle 2 Per-Role Re-Review Routing for `AXIOM_Proposal_Governance_v1.1.md`

**Document Type:** Synthesis Routing Addendum (companion to `AXIOM_Synthesis_Governance_v1_1.md` §6)
**Status:** Issued — to be included in Architect's v1.1 revision instructions
**Authoring Role:** Claude — Quality and Coherence Evaluator
**Date:** 2026-05-08
**Cycle:** Full panel cycle (NOT delta-confirmation, per `AXIOM_Synthesis_Governance_v1_1.md` §7)

---

## Standing Routing Rules

1. **Full panel cycle in force.** Every role re-reviews v1.1. Delta-confirmation is unavailable for this revision. No role is skipped.
2. **Charter v1.0 §Decision Flow sequence preserved.** Architect → Evaluator → Critic → Arbiter → Constraints → Implementation, then Evaluator synthesizes (v1.2 or v2).
3. **Scope is per-role tailored.** "Full panel cycle" means every role reviews; it does not mean every role re-evaluates everything from scratch. Each role's scope below specifies what is *in* and what *carries forward unchanged*.
4. **Closure verification is the focus, not re-litigation.** v1 review findings that have already settled stand. Re-review scope is closure of v1 objections + scrutiny of new content introduced by closures + new gaps the closures themselves may create.
5. **Any role may escalate.** If during re-review a role discovers a new substantive issue not covered by their prior findings, they may file it. Closures that introduce new defects do not get a free pass because they are "fixes."

---

## Adversarial Critic — DeepSeek V4

### (1) Re-reviews v1.1?
**YES — substantively.** v1.1 is closing the five DeepSeek objections (D1–D5). Closures can introduce new vulnerabilities, especially when they add procedural mechanisms. Adversarial scrutiny of the closures themselves is the core re-review activity.

### (2) In-scope sections of v1.1
- **Closure of D1** (delta self-certification): does the objection window + Critic/Qwen escalation right actually close the loophole, or can it be circumvented by silent timing, coordinated subset action, or ambiguous content classification? Does "delta-flagged but unobjected" become a new attack vector?
- **Closure of D2** (specification debt hiding): does the open-flagging mechanism prevent silent gaps, or does it create flag-spam / flag-suppression dynamics? Is the Evaluator's open-issue-list responsibility itself a single point of failure?
- **Closure of D3 + C6** (Diff Gate operationalization, restoration coupling): is the chosen tool tamper-resistant? Can the integrator be bypassed via tool selection? Does the prior-version retrieval mechanism have integrity guarantees, or can a corrupted "prior" be substituted?
- **Closure of D4** (integrator identity): does the chosen role (Evaluator-gatekeeper-with-operator-executor per Kimi GAP-19, or Kimi-as-integrator per DeepSeek's earlier recommendation, or alternative) preserve zero-trust? Can the integrator collude with the author? Is there a structural verification of non-collusion or only convention?
- **Closure of D5** (retroactive-reopening loophole): is the prospective-only replacement language watertight? Any escape hatch via "substantive equivalence" or "spirit of the rule" reasoning?
- **Closure of K1 / SD-008** (Matrix schema): does the schema admit any column that could be weaponized to bury or misclassify objections?
- **Closure of K2 / SD-009** (debt storage location): is the chosen storage tamper-resistant? Append-only? Auditable?

### (3) Carries forward unchanged
- v1 binding-crosswalk completeness — Gemini and Qwen settled binding-level questions. DeepSeek's adversarial focus remains on governance mechanisms, not bindings.
- Cross-Cutting Artifact Protocol basic ownership split (GB-001) — already accepted. Only the C5 + K9 panel motion declaring the six-class extension is in scope.
- Core Values v1 substantive content (CV1, CV4) — DeepSeek did not object; not re-opened.
- DeepSeek does NOT need to stress-test the binding text itself; only governance mechanism closures.

---

## Research and Knowledge Arbiter — Gemini 3.1 Pro

### (1) Re-reviews v1.1?
**YES — narrowly.** Gemini's re-review is the lightest of the four reviewing roles because v1.1 is governance content, not architecture. Re-review focuses only on factual claims about external technology that v1.1 introduces.

### (2) In-scope sections of v1.1
- **Tooling claims introduced by D3 closure** (if Architect adopts Kimi's recommendations or proposes alternatives):
  - If Python `difflib`: confirm Windows 11 + Python 3.12 compatibility for document-comparison use, including line-ending and encoding behavior.
  - If `git init`: confirm Windows compatibility, line-ending normalization (CRLF/LF), binary-file handling for any non-text artifacts, and behavior when no remote is configured.
  - If timestamped file backups: confirm Windows file-system semantics for atomic snapshots and naming collision behavior.
  - Any alternative tooling: full factual verification.
- **Any new claims about Ollama, SQLite, sqlite-vec, Brave Search, Cerebras, Telegram, Windows process/file semantics** that v1.1 introduces incidentally. None are expected, but Gemini should scan.
- **Any factual claim attached to closures of K4 (CV2 mechanism) or K5 (CV5 enforcement)** if the Architect's closure references specific external technology behavior.

### (3) Carries forward unchanged
- All AB-001 through AB-007 factual rulings — already verified; no re-verification.
- Brave Search 1,000-queries/month free tier ruling — already verified.
- PRAGMA synchronous=FULL ruling — technically accurate, I/O risk on Celeron N4500/SATA SSD noted; remains PROPOSED unless v1.1 elevates it (Gemini is not asked to re-rule).
- Canonical filename change rule — already verified at system level.
- "No factual inaccuracies" verdict on v1's external-technology claims — stands.

If v1.1 introduces zero new external-technology claims (the expected case), Gemini's re-review is a one-paragraph affirmation that nothing in factual scope changed.

---

## Constraints and Feasibility Reviewer — Qwen 3.6 Plus

### (1) Re-reviews v1.1?
**YES — focused.** Qwen confirms (a) no new runtime infrastructure leaked in, (b) the four binding conditions from v1 are preserved.

### (2) In-scope sections of v1.1
- **Closure of K4 (CV2 mechanism)**: if the Architect implements panel approval as a *runtime* registry (rather than a documentation artifact), Qwen rules on RAM, thread, and persistence cost. If it is a documentation/process artifact only, no feasibility burden — confirm and move on.
- **Closure of K5 (CV5 enforcement)**: if per-write schema validation, structured logging, or a field-assignment registry are implemented as runtime infrastructure, Qwen rules on cost. If specified as Kimi-implementation-stage requirements only, no feasibility burden at governance ratification — confirm and move on.
- **Closure of D3 + SD-005 (Diff Gate tooling)**: confirm that the tooling sits in the *pre-implementation governance path*, not the runtime path. If a Python script using `difflib`, execution cost is negligible. If anything heavier (e.g., a continuously-running diff service), Qwen rules.
- **Verification that v1's four binding conditions are preserved verbatim in v1.1:**
  - B1–B22 numbering discarded
  - Complete crosswalk uses original `AB-*` / `CB-*` / `GB-*` IDs
  - PROPOSED runtime invariants isolated from active bindings
  - Supersession clause preserved (mirroring does not supersede)
- **Any new "PROPOSED" runtime invariants introduced by v1.1.** None expected (governance content). Scan and confirm.

### (3) Carries forward unchanged
- All 22 CB feasibility rulings — no re-evaluation needed.
- All 7 AB feasibility implications — no re-evaluation needed.
- All 4 GB rulings — no re-evaluation needed.
- Cross-Cutting Artifact Protocol zero-runtime-burden finding — established.
- Charter v1.1 §4.1 / §4.2 / §4.6 zero-runtime-burden finding — established.
- Kimi's broader zero-runtime-burden assessment across all governance mechanisms — established and concurring with Qwen v1.
- The 2.0–2.3 GB runtime headroom remains untouched by this amendment.

If the Architect's closures preserve governance-as-process-only (no runtime infrastructure leak), Qwen's re-review is a focused confirmation, not a fresh feasibility ruling.

---

## Implementation Specialist — Kimi K2.6

### (1) Re-reviews v1.1?
**YES — heaviest re-review.** Most v1.1 closures operationalize gaps Kimi itself flagged. Kimi is the role best positioned to know whether the closures are implementable as specified.

### (2) In-scope sections of v1.1
- **Verify each of the 7 blocking gaps is closed:**
  - GAP-4 (Matrix schema) — closure provides operator-executable column structure
  - GAP-5 (delta-confirmation enforcement) — closure assigns enforcing role and procedure
  - GAP-11 (debt storage canonical location) — closure designates single canonical location and format
  - GAP-15 (Diff Gate tooling) — closure specifies the tool
  - GAP-16 (prior-version retrieval) — closure specifies the mechanism
  - GAP-17 (binding cross-check operationalization) — closure assigns the role and method (semantic check, not just ID-existence)
  - GAP-19 (integrator identity) — closure assigns the role explicitly
- **Verify each of the 19 non-blocking gaps either closes or is formally deferred** per §4.4 with a five-element record (recommendation: most close in this revision; LOW-severity items may defer with proper records).
- **Identify new gaps introduced by the closures themselves.** Closures often raise their own implementation-detail questions (e.g., "objection window" — how does the operator post a revision for a 24h window? what notifies panel members? what counts as a "filed" objection?).
- **Verify the §0 Closure Map (per `AXIOM_Synthesis_Governance_v1_1.md` §6) follows the matrix schema specified by the SD-008 closure.** This is a self-consistency check: v1.1 must use its own newly-defined schema for its own Closure Map.
- **Implementability of any new mechanism** introduced (objection window mechanics, integrator handoff procedure, debt-ledger append protocol, etc.).
- **Closure of K-items reinforcing prior objections (D1, D3, D4, C3, C5)** — confirm the operationalization details are sufficient for the operator to execute.

### (3) Carries forward unchanged
- Directional "implementable" finding for the broad mechanism set — stands unless v1.1 introduces a non-implementable mechanism, which is unexpected.
- Zero-runtime-cost finding across all governance mechanisms — stands unless v1.1 leaks runtime infrastructure (Qwen will flag separately if so).
- Kimi's tooling recommendations from the v1 review (Python `difflib`, timestamped backups or `git init`, Evaluator-as-gatekeeper, etc.) remain on the table as defaults if the Architect did not displace them. If displaced, Kimi re-reviews the alternative.

Kimi's re-review is the gating step before the next Synthesis. If Kimi's blockers do not close in v1.1, ratification is impossible regardless of other roles' positions.

---

## Evaluator — Claude (for completeness)

### (1) Re-reviews v1.1?
**YES — first in sequence per Charter §Decision Flow.** Coherence + binding-carry-forward + Core Value conflict check, as in v1.

### (2) In-scope sections of v1.1
- All v1.1 content — coherence and Core Value conflict review is whole-document by definition.
- Closure verification of v1 objections (D1–D5, C1–C5, Q1–Q4, K1–K11) and v1 SD ledger items.
- Verification that no active binding has been silently dropped or modified.
- Verification that the §0 Closure Map is complete and consistent with the SD-008-mandated matrix schema.
- Identification of new specification debt opened by v1.1 closures.

### (3) Carries forward unchanged
- v1 active-bindings carry-forward audit (33 bindings present) — re-verify briefly that v1.1 preserves all 33; this is mechanical, not substantive re-review.
- v1 Core Values conflict check verdict — stands unless v1.1 modifies CV text further.

---

## Architect's v1.1 Revision Instructions — Routing Citation

The Architect should include the following statement in `AXIOM_Proposal_Governance_v1.1.md` §11 (Required Next Panel Reviews):

> Cycle 2 review scope is governed by `AXIOM_Synthesis_Governance_v1_1_Routing.md`. Each role reviews per the scope specified for that role. Items marked "carries forward unchanged" in the Routing document are not re-litigated in this cycle.

This citation closes the routing loop and ensures each panel member reviews the correct scope when v1.1 reaches them.

---

## What This Routing Does NOT Do

- Does not authorize any role to skip review (this is full panel cycle, not delta).
- Does not bind a role to a narrow scope if that role discovers a new substantive issue. Any role may escalate beyond its assigned scope on filed reasoning.
- Does not pre-decide closure adequacy. Each role independently determines whether v1.1 closes their prior objections.
- Does not substitute for the next Synthesis. After Cycle 2 panel review completes, the Evaluator produces `AXIOM_Synthesis_Governance_v2.md` (or `v1_2.md`) ruling on closure status and consensus.

---

*End of AXIOM_Synthesis_Governance_v1_1_Routing.md*
*Companion to `AXIOM_Synthesis_Governance_v1_1.md`. To be cited in the Architect's v1.1 revision instructions.*
