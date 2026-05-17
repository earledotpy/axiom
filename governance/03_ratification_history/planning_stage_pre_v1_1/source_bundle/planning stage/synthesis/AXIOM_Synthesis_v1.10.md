# Evaluator Synthesis — AXIOM Proposal v1.10

**Bottom line:** The proposal **returns to the Chief Architect for a small v1.10.1 patch.** Arbiter has factually cleared all v1.10 mechanisms with one minor implementation note for Kimi. Constraints has approved with twelve binding conditions (one new). The Critic raised eight observations, two of which the Critic explicitly noted are not blocking, leaving five valid objections and one project-management note. None require architectural revision — all six are targeted spec additions consistent with the existing architecture. Combined with the test-list reconciliation I flagged in my v1.10 evaluation, this is patch-scale work, not a full revision.

The architect's trajectory is converging cleanly. The remaining items are spec polish, not design re-think.

---

## (1) Objections That Are Valid and Must Be Resolved

Per the Charter rule, an objection is overruled only if **both** Arbiter and Constraints find it unsupported. Arbiter ruled only on factual mechanisms; Constraints ruled on hardware/budget feasibility. Neither addressed the Critic's security-spec, coordination, or operational concerns, so none are overruled by that route.

### Blocking — must be addressed in v1.10.1

**Obj 1 — Mid-session fingerprint verification error handling is underspecified.** v1.10 §4 specifies on-mismatch behavior but is silent on what `ModelFingerprintGuard.verify_current_profile()` does when the underlying Ollama API call fails — timeout, connection refused, malformed response, schema change. A security-boundary check that fails open on infrastructure error is a Core Value 1 violation.

**Required:** specify fail-closed semantics. Critic's minimum specification is sound and should be adopted: 5-second timeout; treat timeout, connection error, and malformed response as mismatch; write `security_events.model_fingerprint_verification_failed` with the failure reason.

**Obj 2 — No Telegram alert on mid-session fingerprint mismatch.** v1.10 §4 writes `security_events` and `session_events` rows but does not push the event to the operator. In the fire-and-forget interaction model, the operator may not discover the security degradation until their next check-in — a retrospective discovery that contradicts the urgency of the event itself. Mid-session model profile change is the highest-criticality security event the system can detect.

**Required:** add Telegram alert on mismatch and on verification failure (per Obj 1). The Telegram Gateway is already on a separate thread; this is mechanism reuse, not new infrastructure.

**Obj 3 — Manifest registration mode lacks production-disablement enforcement.** v1.10 §5 states "registration mode is not available during autonomous operation" but does not specify the enforcement mechanism. If `manifest_registration_mode` is a config file value or environment variable readable at runtime, a compromised process could enable it and silently re-register manifest fingerprints, defeating the integrity check this section is supposed to provide.

**Required:** specify the enforcement mechanism. Critic's recommendation (command-line flag passed at process start, not changeable at runtime) is the cleanest option. Alternative: a separate registration CLI tool, invoked only by the operator during deployment, that writes to `manifest_fingerprints` and is not part of the main AXIOM process. Either works; the architect must pick one.

**Obj 4 — Cloud-model token reasoning and local TokenEstimator have no coordination step.** This is the most substantive remaining gap. v1.10 item 11 specifies that Task Planner must size manifests so prompts fit within the dispatch-time gate, and Result Verifier checkpoint mode must reject plans that violate the gate. But Task Planner and Result Verifier are cloud models reasoning about token counts in their own internal frames. The dispatch gate uses the local TokenEstimator. Cloud models routinely miscount their own prompt tokens — this is documented behavior, not speculation. Without coordination between the two estimators, plans approved by checkpoint mode can systematically fail at dispatch with `blocked_resource_limit`.

**Required:** specify how cloud-model planning reconciles with local-estimator enforcement. Two viable shapes:

- **(a)** Result Verifier checkpoint mode invokes the local TokenEstimator on proposed prompts/contexts as part of its gate check, rather than relying on the cloud model's self-reported token reasoning. This makes checkpoint and dispatch gates use identical estimation, eliminating divergence by construction.
- **(b)** Bootstrap cross-estimation benchmark per Critic's recommendation: at calibration time, send fixed prompts through both the cloud model's self-report and the local TokenEstimator, compute a correction factor, and inject that factor into Task Planner's system prompt.

Option (a) is architecturally cleaner — one source of truth for the gate. Option (b) is more accurate but adds calibration complexity. The architect should pick. I lean (a) because it's deterministic and removes the gap by construction; (b) preserves a residual coordination dependency. But this is the architect's call to defend.

**Obj 6 — SQLite journal mode not specified; SupervisorMonitor reads can contend with Scheduler writes.** Default rollback journal mode uses database-level locking — readers block on writers and vice versa. Under SATA SSD paging, even simple SELECT queries can stall for seconds while a writer holds the lock. The supervisor's freshness-check loop runs on the main thread; if it stalls on a heartbeat read, Telegram-liveness monitoring and shutdown-coordination stall with it.

**Required:** specify SQLite WAL (Write-Ahead Logging) mode for the AXIOM database. WAL allows concurrent readers and writers and is well-supported by sqlite-vec. This is a one-line specification with no architectural impact.

### Project-management note — must be acknowledged but not architecture work

**Obj 5 — E2E test depends on a panel-workflow timeline.** The Critic's own framing is correct: this is a project-management concern, not a design defect. The calibration test set requires Gemini to author, DeepSeek to attack, Claude to review, Qwen to feasibility-check, Kimi to package, and the operator to write — multiple panel sessions before classifier safe-pass becomes operational and the e2e test can run end-to-end with classifier paths exercised.

**Required:** add a one-paragraph acknowledgement to v1.10.1 stating that MVP completion gates on this panel-workflow dependency, so Kimi sequences implementation accordingly. The proposal does not need to schedule the workflow — it needs to flag it so it isn't lost.

---

## (2) Objections Overruled

**Obj 7 (Operator-control authorization chain).** The Critic explicitly noted this is "an observation on scope, not an objection to a flaw" and "will not raise it as an issue." Withdrawn by the Critic on submission.

**Obj 8 (Pre-decision fingerprint check latency).** The Critic explicitly noted "this is negligible compared to cloud-call latency... Not a concern. I note it as considered, not as a blocking objection." Withdrawn by the Critic on submission.

No other objections are overruled. Obj 5 is downgraded to a project-management note, but downgrade is not overrule — the underlying concern remains valid and the proposal benefits from the acknowledgement.

---

## (3) What the Architect Must Revise — v1.10.1 Patch List

The architect produces **AXIOM_Proposal_v1.10.1** addressing the following:

**Blocking spec additions:**
1. **§4 — Fingerprint verification error handling.** Specify 5s timeout; fail-closed treatment of timeout, connection error, malformed response; security event with failure reason.
2. **§4 — Telegram alert on mismatch and on verification failure.** Specify message template and trigger conditions; reuse existing Telegram Gateway path.
3. **§5 — Manifest registration mode enforcement mechanism.** Specify command-line flag, separate CLI tool, or equivalent runtime-immutable mechanism.
4. **§13 — Cloud-model vs local TokenEstimator coordination.** Specify either (a) Result Verifier checkpoint invokes local TokenEstimator for the gate check, or (b) bootstrap cross-estimation calibration with correction factor injected into Task Planner system prompt. Architect selects and defends.
5. **Persistence section — SQLite journal mode.** Specify WAL mode.

**Project-management acknowledgement:**
6. **§3 or §6 — Calibration test-set workflow dependency.** One paragraph noting MVP completion gates on the multi-session panel workflow producing the calibration test set.

**Carry-forward from v1.10 Evaluator review (still outstanding):**
7. **§11 — Test list reconciliation.** Either restore the seven v1.9 §14 tests missing from v1.10's canonical suite, or explicitly map each missing test to a consolidated successor with one-line rationale per test.

**Arbiter implementation note for Kimi (not a revision, just forward-pass):**
- Ollama does not expose a native `thinking_mode` flag. `ModelFingerprintGuard` must parse the `template` or `system` fields returned by `/api/show` to verify thinking-mode state for qwen3:4b. Architect should add this as an inline note in §4 or §9 so Kimi captures it during planning.

**Bindings travel forward unchanged:**
- Arbiter: all v1.10 mechanisms verified (SHA256, Ollama metadata, tiktoken/fallback math, SQLite atomic transactions). One Kimi-facing implementation note on `thinking_mode` parsing.
- Constraints: twelve binding conditions per the v1.10 ruling, including the new combined model-fingerprint-and-manifest-mismatch immediate-disable rule.

---

## (4) Decision

**The proposal does not advance to Kimi yet.** It returns to the Architect for a v1.10.1 patch.

The patch is small relative to the full proposal. None of the seven items above require architectural revision:

- Items 1, 2, 3, 5 are spec sentences clarifying behavior at established boundaries.
- Item 4 is a single architectural clarification (which estimator owns the gate) within an existing section.
- Item 6 is a one-paragraph acknowledgement.
- Item 7 is bookkeeping.

Recommended panel routing for v1.10.1:

1. **v1.10.1 produced by Architect** addressing items 1–7.
2. **Delta-confirmation Evaluator** (this seat) — confirm patches resolve the items and introduce no new conflicts.
3. **Delta-confirmation Critic** (DeepSeek) — bounded review: did v1.10.1 resolve Obj 1, 2, 3, 4, 5, 6? Any new issues introduced by the patches themselves?
4. **Arbiter** can be skipped — no new factual mechanisms are introduced. (The fail-closed timeout, Telegram alert, command-line flag, WAL mode, and TokenEstimator delegation are all standard mechanisms already factually cleared in surrounding context.)
5. **Constraints** can be skipped — no new RAM, thread, or budget impact. WAL mode does change SQLite I/O patterns slightly but is standard practice and reduces contention rather than adding overhead.
6. **Synthesis** (this seat) — confirm delta cycle clean.
7. **Implementation planning (Kimi).**

The architect has been doing the work cleanly across four cycles. v1.10 resolved twelve substantive items from the v1.9 synthesis without introducing architectural drift. v1.10.1 should be the last revision before Kimi takes the proposal — assuming no new issues emerge from the patches themselves, which is unlikely given their narrow scope.

Patch and advance.

---

*AXIOM Synthesis v1.10 — May 2026 — save as `AXIOM_Synthesis_v1_10.md`*