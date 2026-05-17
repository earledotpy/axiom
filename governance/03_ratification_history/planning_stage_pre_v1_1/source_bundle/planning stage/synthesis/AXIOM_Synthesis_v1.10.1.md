# Evaluator Synthesis — AXIOM Proposal v1.10.1

**Bottom line:** The Critic explicitly recommends advancement to Kimi and frames all six objections as non-blocking. I largely agree, with one important caveat: the test-list footnote I required in my v1.10.1 evaluation is still outstanding, and two of the Critic's objections (Obj 2 artifact lifecycle, Obj 6 alert deduplication) are spec gaps that should be closed in proposal text rather than left for Kimi to invent.

**Decision: Return for a small v1.10.2 addendum** combining the outstanding test-list reconciliation with two narrow spec additions. Then advance to Kimi. This is a one-page document, not a new revision cycle.

Note on panel quorum: per my v1.10.1 routing recommendation, only the Critic was required for the delta cycle. Arbiter and Constraints were skipped because v1.10.1 introduced no new factual mechanisms and no new RAM/thread/budget impact. The Critic alone constitutes adequate review for this delta, and the Critic's recommendation is significant.

---

## (1) Objections That Are Valid and Must Be Resolved

The Critic explicitly says: "None of these are blocking for architectural validity. They are edge cases and specification gaps that will become implementation details for Kimi or operational observations for the first autonomous session. None rise to the level of a security boundary violation or a Core Value contradiction."

I treat that framing as the Critic's own ranking. Within that ranking, two items are spec gaps that should be closed in proposal text rather than punted to Kimi — because Kimi inventing them is more friction than the architect specifying them. The other four are properly Kimi-resolvable.

### Spec gaps — must be closed in v1.10.2

**Obj 2 — Artifact lifecycle disposition after fingerprint-related scanner failure.** v1.10.1 §2 specifies the scanner's *output label* (high_risk → quarantined; ordinary → needs_human_input) but not the artifact's *lifecycle state* or the parent task's status transition. The questions the Critic raises — does the artifact receive `injection_scan_failed`? does the parent task go to `blocked` or `needs_human_input`? can a quarantined artifact be re-scanned after recalibration, or is it permanently tainted? — are not implementation details. They are state-machine transitions that the architect owns.

The transient-Ollama-timeout case makes this concrete: an operator hits a paging spike, gets a security alert, recalibrates, and now needs to know whether to resubmit the goal or whether the original quarantined artifact can rehabilitate. The system should have an answer. The architect should write it.

**Required addition:** specify the lifecycle state assigned to the artifact and parent task on fingerprint-related scanner failure, and specify whether quarantined artifacts can rehabilitate after successful recalibration or are session-terminal. 5–10 lines.

**Obj 6 — Alert deduplication via session-state short-circuit.** The Critic's framing assumes the fingerprint guard re-runs on every classifier-dependent safe-pass attempt and produces repeated identical alerts. The cleanest resolution isn't rate-limiting — it's making the architecture self-deduplicating: once safe-pass is disabled mid-session, the scanner short-circuits classifier-dependent rules entirely, so the guard never re-runs. State persists in session memory until session restart or successful recalibration.

This is the same shape as the existing "safe-pass disabled until calibration passes" boot-time rule, just applied to mid-session state. It also resolves a related ambiguity in v1.10 §4 that wasn't explicit: when safe-pass is globally disabled, does the scanner still attempt classifier-dependent rules?

**Required addition:** state explicitly that once safe-pass is disabled mid-session (whether by mismatch or verification failure), the scanner does not re-run the fingerprint guard for subsequent classifier-dependent decisions in that session, and classifier-dependent safe-pass rules are short-circuited. 2–3 lines.

### Carry-forward from prior evaluation — still outstanding

**Test-list reconciliation footnote.** My v1.10.1 evaluation required a footnote addressing the seven specific tests I flagged as missing from v1.10's canonical suite (`test_sandbox_heartbeat_ordering`, `test_calibration_set_ownership_metadata`, `test_task_committer_validation_scope`, `test_checkpoint_semantic_consistency`, `test_operator_control_manifest_binding`, `test_supervisor_liveness_limit_notice`, `test_mvp_module_boundary`). The architect's v1.10.1 §8 mapping table addressed a different set of tests — not the seven I called out. The footnote correction has not been delivered.

This must be in v1.10.2: either the seven tests added (with appropriate renames where v1.10 reassignments make the v1.9 names stale, e.g. `calibration_set_ownership` should reflect Gemini authorship), or each one explicitly mapped to a consolidated successor with a one-line rationale.

### Should be folded — not blocking

**Obj 3 (partial) — CLI database configuration inheritance.** One sentence in §4 stating that `tools/register_manifests.py` uses the same database path and applies the same WAL-mode pragmas as the main runtime. The "what if operator runs concurrently" question is properly Kimi's — SQLite WAL handles multi-writer contention via `busy_timeout`, but the safe-stop sequencing is implementation guidance for the operator playbook.

**Obj 4 — Checkpoint vs realized prompt acknowledgement.** One paragraph in §5 acknowledging that checkpoint estimates a planned prompt shape and dispatch estimates the realized prompt; the planner-sizing rule from v1.10 §11 (≤50% / ≤66% target) provides margin to absorb divergence; on dispatch-time exceedance the existing remediation flow from v1.10 §8 fires. This isn't a fix — the architecture already handles it. It's an explicit label so Kimi doesn't read v1.10.1 §5 as implying identical inputs.

### Properly Kimi-resolvable — flag in implementation plan, not in proposal

**Obj 1 — 5-second Ollama timeout under paging.** Parameter calibration concern. The 5s value is reasonable as a default but should be tunable based on first-session observation. The Critic's suggestion (retry once with shorter timeout, or differentiate timeout vs digest-mismatch in alert wording) is also a Kimi tuning consideration. Architect should add a one-line note that the timeout is operationally tunable; Kimi specifies the tuning mechanism in the implementation plan.

**Obj 5 — WAL checkpointing on SATA SSD.** Critic explicitly notes "low-probability edge case" and "should checkpoint quickly even on SATA SSD." Recommendation is a one-line note that auto-checkpoint threshold and passive-checkpoint mode are tunable if operationally significant. Kimi-facing note.

---

## (2) Objections Overruled

None overruled in the formal Charter sense (which requires both Arbiter and Constraints findings, neither of which were run for this delta). But the Critic's own non-blocking framing on all six objections is the substantive signal. Of the six, four are absorbed into the implementation plan (Obj 1, 3, 4, 5 — with the small architect-side notes above), and two need spec text in v1.10.2 (Obj 2, 6).

---

## (3) What the Architect Must Revise — v1.10.2 Addendum

The architect produces **AXIOM_Proposal_v1.10.2** as a small addendum (single page, footnote-style), addressing:

**From this Critic review:**
1. **§2 — Artifact lifecycle disposition** on fingerprint-related scanner failure. Specify artifact state, parent task state, and rehabilitation rule.
2. **§4 — Alert deduplication via session-state short-circuit.** Once safe-pass is disabled mid-session, scanner short-circuits classifier-dependent rules; guard does not re-run; alert fires once per session.
3. **§4 (one line) — Timeout operationally tunable.** Kimi specifies the tuning mechanism.
4. **§5 (one paragraph) — Checkpoint vs realized prompt acknowledgement.** Planner-sizing margin absorbs divergence; dispatch gate handles exceedance.
5. **§4 (one sentence) — CLI database configuration inheritance.** CLI uses same DB path and WAL pragmas as main runtime.
6. **§6 (one line) — WAL checkpoint tunability note** for Kimi.

**From v1.10.1 Evaluator review (still outstanding):**
7. **§8 — Test-list reconciliation footnote** addressing the seven specific tests flagged in the v1.10.1 evaluation. Either restore (with appropriate renames) or explicitly map each to a consolidated successor with one-line rationale.

This is one document, not a new proposal. The architecture spine is unchanged. No new factual mechanisms, no new RAM/thread impact.

---

## (4) Decision

**Return for v1.10.2 addendum, then advance to Kimi.**

After the addendum is produced:

1. **Delta-confirmation Evaluator** (this seat) — confirm the seven items are addressed; one-page review.
2. **Critic, Arbiter, Constraints — skippable.** No new mechanisms or constraints introduced; v1.10.2 is closing established gaps with already-verified mechanisms. The Critic has already recommended advancement on substance; absent new architectural content, no further adversarial review is needed.
3. **Implementation planning (Kimi).**

This is the same pattern as the v1.8 → v1.8.1 transition: tightly scoped follow-up that completes the proposal. The Critic's explicit "advance to Kimi" recommendation, combined with the small scope of remaining items, makes another full panel cycle unnecessary. The gating concern is just that the spec text be complete before Kimi treats the proposal as canonical.

The architect has converged. One more focused addendum and the proposal is ready.

---

*AXIOM Synthesis v1.10.1 — May 2026 — save as `AXIOM_Synthesis_v1_10_1.md`*