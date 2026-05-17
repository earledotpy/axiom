# Evaluator Synthesis — AXIOM Proposal v1.9

**Bottom line:** The proposal **returns to the Chief Architect for a targeted v1.10 revision.** Arbiter has factually cleared all v1.9 mechanisms with no caveats. Constraints has approved with twelve binding conditions, all of which are codifications of v1.9 decisions rather than new blockers. The Critic raised nine objections, withdrew one, and surfaced four that genuinely block advancement plus four addressable specification gaps. The architecture spine is intact and the v1.9 → v1.10 delta should be small.

---

## (1) Objections That Are Valid and Must Be Resolved

Per the Charter rule, an objection is overruled only if **both** Arbiter and Constraints find it unsupported. The Arbiter ruled only on factual mechanisms (and verified all of them); Constraints ruled on hardware/budget feasibility. Neither addressed the Critic's role-boundary, security-gap, or operational-design objections, so none are overruled by that route. I rule on each below.

### Blocking — must be resolved in v1.10

**Obj 1 — Calibration test set authorship violates Charter separation of duties.** This is a genuine governance issue and the Critic is correct. Authoring 120 adversarial samples is design work — it defines the security envelope of the PlanInjectionScanner. The Charter explicitly prohibits the Critic from originating design proposals. Assigning authorship to DeepSeek and asking DeepSeek to subsequently challenge architectures that depend on its own artifact creates a structural conflict.

The clean resolution is reassignment. Gemini is the natural primary author: the Arbiter's existing duty is factual review of attack realism, which already requires deep knowledge of current injection vectors. DeepSeek then performs adversarial review of the set itself — looking for gaps, weak samples, missing vectors, ways an attacker would slip through. That preserves separation: the Arbiter creates the artifact, the Critic attacks it.

**My recommendation to the Architect:** Revise §5 ownership matrix to:

| Responsibility | Owner |
|---|---|
| Primary author | Gemini 3.1 Pro |
| Adversarial review (gap-finding, attack-vector coverage) | DeepSeek V4 |
| Coherence/final acceptance review | Claude Opus 4.7 |
| Feasibility review | Qwen 3.6 Plus |
| Implementation packaging | Kimi K2.6 |
| Physical file creation | Human operator |

If the Architect prefers a different assignment, fine — but DeepSeek as primary author requires either a written Charter exception with rationale or a panel consensus to amend the Charter. The status quo is not acceptable.

**Obj 2 — Mid-session model fingerprint check missing.** Boot-time verification leaves an open window during long autonomous sessions. A model file replacement (whether from accidental Ollama auto-update, human error, or low-probability sandbox escape) goes undetected until next reboot. This is genuinely inconsistent with Core Value 1: a security boundary verified only at boot is bolted on, not baked in.

The fix has two viable shapes:
- **Periodic re-check:** verify fingerprint every N scheduler ticks or every M minutes; on mismatch, disable safe-pass and flag a security event.
- **Pre-decision check:** verify fingerprint immediately before each safe-pass decision (cheaper than a model call but adds an Ollama metadata round-trip per scan).

Either is acceptable. The Architect must specify which, with rationale, or formally defer to Phase 2 with explicit Core Value 1 acknowledgement and a documented residual-risk note.

**Obj 6 — Manifest file integrity not verified at runtime.** Manifest files in `policy/role_manifests/` and `policy/operator_control_manifests/` are security artifacts that authorize tool access and operator commands. v1.9 has fingerprint verification for the local model but no equivalent for these on-disk JSON files. A corrupted, partially-written, or accidentally-edited manifest could silently produce a degraded permission set that ManifestBinder parses without complaint.

The fix is small and architecturally consistent with the v1.9 model fingerprint pattern: add a `manifest_fingerprints` table keyed by relative path, store SHA256 at deployment/calibration time, verify at boot, fail-closed on mismatch. This belongs in `security/audit.py` or `core/manifest_binder.py`. **Must be added.**

**Obj 9 — No end-to-end acceptance test.** The twelve unit tests in §14 prove individual mechanisms in isolation; they do not prove that a goal flows from Telegram input through Goal Planner → PlanInjectionScanner → Result Verifier checkpoint → TaskCommitter → Task Planner → Tool Executor → Result Verifier → completion. ToonTown Phase 9 had end-to-end acceptance criteria; AXIOM v1.9 does not. Without one, the MVP cannot be declared complete with any meaningful confidence — Core Value 4 requires *proving* the concept, not merely testing components.

**Must be added:** at least one e2e test specification, e.g. `test_full_goal_flow_minimum.py` exercising a trivial goal (the Critic's example "summarize the AXIOM Core Values from memory" is reasonable) end-to-end with assertions at each architectural boundary.

### Significant — must be specified but not architecturally heavy

**Obj 4 — Manual reconciliation has no error-proofing.** Valid operational concern. The Critic's suggested minimum — sanity-check operator-reported totals against AXIOM's own estimate for the same period and flag discrepancies exceeding a threshold (the Critic suggested ±50%, which is reasonable for free-tier estimation noise) — should be added to the `/reconcile_provider_usage` flow. On flag, prompt the operator to confirm rather than silently apply. **Must specify** the validation threshold and the on-flag behavior.

**Obj 5 — Conservative ÷3 estimator combined with 2× margin double-penalizes context size.** The Critic's math is correct. The character-divisor of 3 over-estimates real token counts by roughly 33% versus a calibrated tokenizer. Multiplying by 2 then yields an effective utilization ceiling of around 37% of the manifest budget when fallback estimation is in use, versus 50% when a calibrated tokenizer is in use. This will produce excessive blocks on legitimate large-context tasks.

The fix is a tiered margin rule: 2× margin applies when a calibrated tokenizer (provider-supplied or tiktoken) is in use; 1.5× margin applies when the conservative ÷3 fallback is in use, since the divisor already provides ~33% conservatism. **Must specify** the tiered rule, or alternatively defend the existing parameters with an explicit acknowledgement that excessive blocking is accepted MVP behavior pending parameter tuning.

### Lower severity — clarifying revisions

**Obj 3 — Keepalive rule frames a retrospective diagnostic as real-time monitoring.** The Critic is right that the 30-minute laptop-check rule does not provide real-time failure detection — the operator is asynchronous by design. The architect already acknowledged the underlying limitation (whole-system hangs cannot be self-detected). What's needed is honesty in framing.

**Must revise** §11 to state plainly: "During whole-system hangs the operator will not receive notification and may not discover the failure until their next check-in. The keepalive rule is a retrospective diagnostic to help the operator distinguish 'system hung' from 'no work available' upon return, not a real-time alert. Real-time hang detection is deferred to Phase 2 via an out-of-process watchdog."

**Obj 7 — Compounded cloud-call latency in deterministic chain.** The Critic correctly identifies that Goal Planner (≤90s) + Result Verifier checkpoint (≤90s) = up to 180s of cloud time before the first subtask executes. This is a consequence of design decisions already approved (semantic verification before commit, per-call timeouts), not a defect. But the operator will see prolonged silence between sending a goal and seeing activity.

**Should add** to §11 or to the Telegram Gateway specification: an immediate acknowledgement on goal receipt ("Goal received. Planning may take 1–3 minutes.") so that the operator is not parsing silence as a hang during the planning phase. This is a small operational addition, not architectural.

---

## (2) Objections Overruled

**Obj 8 — Withdrawn by the Critic.** DeepSeek's own analysis showed the heartbeat freshness segmentation in v1.9 adequately handles paging delays between heartbeat writes. The withdrawal is correct. No action.

No other objections are overruled. Some are downgraded (Obj 3, 7), but downgrade is not overrule — the underlying observations remain valid and the proposal benefits from addressing them.

---

## (3) What the Architect Must Revise — v1.10 Patch List

The architect produces **AXIOM_Proposal_v1.10** addressing the following:

**Blocking revisions:**
1. **§5 — Reassign calibration test-set authorship.** Gemini as primary author, DeepSeek as adversarial reviewer of the set. Or write a formal Charter exception with rationale.
2. **§9 — Add mid-session model fingerprint verification.** Specify cadence (periodic or pre-decision) and on-mismatch behavior. Or formally defer to Phase 2 with Core Value 1 acknowledgement.
3. **New section — Manifest integrity verification.** SHA256 fingerprints stored at deployment, verified at boot, fail-closed on mismatch. Add `manifest_fingerprints` table to schema. Mirrors the §9 model-fingerprint pattern.
4. **§14 — Add at least one end-to-end acceptance test.** Specify the trivial goal, the boundaries asserted at, and the success criterion.

**Significant specification revisions:**
5. **§10 — Add reconciliation sanity check.** Validation threshold for operator-reported vs system-estimated totals; on-flag behavior.
6. **§8 — Add tiered token-margin rule.** 2× with calibrated tokenizer, 1.5× with ÷3 fallback. Or defend the current uniform 2× with acknowledged blocking behavior.

**Clarifying revisions:**
7. **§11 — Reframe keepalive honestly** as a retrospective diagnostic, not real-time monitoring.
8. **Telegram Gateway / §11 — Add immediate goal-receipt acknowledgement** with planning-latency expectation set.

**Carrying forward from my v1.9 evaluation (still outstanding):**
9. **Reconcile §12.3 and §14 test lists explicitly** — the relationship between the two needs to be stated (likely §14 = §12.3 + v1.9-delta tests, but say so).
10. **Specify supervisor stale-check logic location** — `app/session_controller.py` is the likely home; make it explicit so Kimi doesn't fragment fail-closed logic.
11. **Specify task-planner manifest-sizing rule** for the ≥2× target prompt size, otherwise the dispatch gate produces systematic false blocks.
12. **Specify per-step component ownership** for the seven-step operator-control authorization chain in §7.

Items 9–12 are clarifications I flagged in my v1.9 evaluation that the previous panel cycle didn't pick up. They should fold into v1.10 because they're cheap to address and Kimi will need them.

**Bindings travel forward unchanged:**
- Arbiter: all v1.9 factual mechanisms verified, no caveats.
- Constraints: twelve binding conditions per the v1.9 ruling, including the new safe-pass-disabled-until-calibration and fingerprint-mismatch-disables-safe-pass conditions.

---

## (4) Decision

**The proposal does not advance to Kimi in its current form.** It returns to the Architect for v1.10.

The v1.10 patch is small relative to v1.9. The architecture spine is unchanged. Three of the four blocking items (Obj 2, 6, 9) are additive — small new mechanisms or test specifications that fit cleanly into the existing structure. Obj 1 is a governance rdeassignment, not architecture work.

Routing for v1.10:

1. **v1.10 produced by Architect** addressing items 1–12 above.
2. **Delta-confirmation Evaluator** (this seat) — confirm patches resolve the items and introduce no new conflicts.
3. **Delta-confirmation Critic** (DeepSeek) — bounded review: did v1.10 resolve Obj 1, 2, 3, 4, 5, 6, 7, 9? Any new issues introduced by the changes themselves?
4. **Arbiter** can be skipped on this round unless v1.10 introduces new factual mechanisms (the items above are mostly governance, integrity verification, parameter rules, and test specifications — none require new factual rulings beyond what's already verified).
5. **Constraints** can be skipped on this round unless v1.10 introduces new RAM or thread overhead (none of the items 1–12 should — manifest fingerprint table is negligible, the e2e test is bootstrap-only, the rest are logic/governance).
6. **Synthesis** — confirm delta cycle clean.
7. **Implementation planning** — Kimi.

If the Architect wants to challenge my Obj 1 reassignment recommendation specifically (e.g., proposes a Charter exception instead), that is a panel-consensus question and should be flagged explicitly in v1.10's synthesis matrix rather than buried in the rewrite.

The Architect has been doing the work. Items 2 and 6 are real Core Value 1 gaps; item 9 is a real Core Value 4 gap; item 1 is a governance issue I should have caught in my v1.9 review and didn't. None of these are reasons to lose confidence in the trajectory. Patch and advance.