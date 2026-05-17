# Evaluator Review — AXIOM Proposal v1.9

**Bottom line:** v1.9 resolves all ten items from the v1 synthesis substantively. The architecture spine is unchanged, no Core Value conflicts are introduced, and Arbiter and Constraints bindings are carried forward verbatim. **Approve to advance to delta-confirmation panel cycle** (Critic / Arbiter / Constraints — bounded to v1.9 changes only) and then to Kimi for implementation planning.

I have four minor coherence clarifications worth tightening, but they are clarifications, not failures. None block advancement.

---

## What Holds — Item-by-Item Verification

| # | Synthesis Item | v1.9 Resolution | Verdict |
|---|---|---|---|
| 1 | Heartbeat field semantics | `last_freshness_at` field introduced; canonical rule that **every** heartbeat write updates it; supervisor stale check uses **only** that field; math re-audited and 120s threshold preserved | ✓ Resolved |
| 2 | Sandbox wall-clock enforcement | `subprocess.run(timeout=60)` + Job Object; explicit 10s termination overhead budget; explicit heartbeat ordering with halt-on-write-failure rule | ✓ Resolved |
| 3 | Calibration test set ownership | DeepSeek author / Gemini factual review / Claude coherence review / Qwen feasibility / Kimi packaging / Operator file-creation only; safe-pass disabled until calibration passes; maintenance triggers enumerated | ✓ Resolved |
| 4 | TaskCommitter validation scope | Bounded to deterministic checks (schema, vocabulary, manifests, ID generation); semantic consistency owned by Result Verifier in checkpoint mode; chain of responsibility documented | ✓ Resolved |
| 5 | Operator-control manifest role | Manifests are enforced but only **after** capability-token authorization; relocated to `policy/operator_control_manifests/`; explicit rule that the manifest is a capability-minimization step, not the primary authorization boundary | ✓ Resolved |
| 6 | Token-counting mechanism | TokenEstimator with provider/tiktoken/conservative-approximation hierarchy; `ceil(char_count / 3)` fallback; dispatch-time gate `actual * 2 ≤ manifest.max`; six-row exceedance behavior table | ✓ Resolved |
| 7 | Model profile change detection | `model_profile_fingerprints` table; boot-time verification; weak-fingerprint fallback (mtime + size + show-JSON hash) when digest unavailable; explicit "no silent drift" rule | ✓ Resolved |
| 8 | Orphan provider-call reconciliation | Conservative immediate charging + manual `/reconcile_provider_usage` + `provider_usage_reconciliations` table + monthly reset cadence with audit retained | ✓ Resolved |
| 9 | Supervisor liveness limitation | Explicit acknowledgement that whole-system hangs cannot be self-detected; Phase 1 mitigation = Telegram keepalive every 15 min + 30-min operator-side rule; Phase 2 watchdog deferred with Core Value 4 rationale | ✓ Resolved |
| 10 | MVP module subset | Three-tier split: MVP-required, MVP-test-required, Deferred Phase 2; deferred list excludes scalability/convenience features; MVP defended in §12.4 against the productive tension between Core Value 1 and Core Value 4 | ✓ Resolved |

### Math audit — heartbeat threshold

I re-traced the worst-case freshness gap under the new field semantics:

- Cloud call (worst case): 90s gap. Threshold 120s. Margin 30s. Safe.
- Sandbox + termination overhead: 60s + 10s = 70s gap. Threshold 120s. Margin 50s. Safe.
- Sequential sandbox → heartbeat write → cloud call: each blocking op individually within bounds, freshness write between them. Max single-op gap = 90s. Safe.

The architect's binding constraint is the 90s cloud call (not the sandbox), so margin = 30s. Correct.

### Core Value compliance

- **CV1 (security baked in):** Strengthened across multiple items — heartbeat semantics, sandbox wall-clock, calibration ownership, manifest enforcement chain, model fingerprint detection, operator-side keepalive.
- **CV2 (local model in lane):** Unchanged.
- **CV3 (zero-trust at boundaries):** Manifest enforcement and capability-token sequencing reinforce this.
- **CV4 (build simple, prove concept, iterate):** Productive tension with CV1 explicitly addressed in §12.4. The architect's defense — that the MVP must include security boundaries because they cannot be bolted on later — is correct. The deferred Phase 2 list (external watchdog, Servy mode, parallel execution, advanced provider scoring, additional UI) excludes scope creep, not security.
- **CV5 (queue-mediated coordination):** Unchanged.
- **CV6 (sandbox/network separation):** Wall-clock enforcement closes the bypass that Gemini flagged (CPU-only Job Object timing).

No conflicts.

---

## What Could Be Tightened — Non-Blocking Clarifications

These are not failures. The proposal can advance with them outstanding, and Kimi can absorb them during implementation planning. But the architect should consider folding them in as footnotes or §16 entries before v1.9 is treated as final.

**Clarification A — Two test lists need reconciliation.** §12.3 lists 12 MVP-test-required tests and §14 lists 12 revised acceptance tests. Four tests appear in both (`test_scheduler_heartbeat_freshness`, `test_sandbox_wall_clock_timeout`, `test_token_estimator_dispatch_gate`, `test_provider_usage_reconciliation`). The relationship between the two lists is undefined: are §14 tests a superset that adds eight v1.9-specific tests to the MVP set? Are some §12.3 tests deferred? Kimi will need to reconcile. The architect should state explicitly that §14 = §12.3 + new v1.9-delta tests, or specify the actual relationship.

**Clarification B — Supervisor stale-check logic location.** With `watchdog.py` absorbed, the v1.9 module map has no module explicitly owning the supervisor's stale-check loop. The "main supervisor" thread is named in §1.2 thread cap, but no module is identified as its home. By process of elimination, this likely lives in `app/session_controller.py` (main thread). The architect should make this explicit. If the supervisor logic is split across modules, that needs to be called out — fragmenting fail-closed logic across modules is a maintainability risk per Core Value 1.

**Clarification C — Token-budget interpretation.** The dispatch-time check `actual_dispatch_estimate * 2.0 ≤ manifest.max_estimated_input_tokens` is the conservative interpretation of "2× safety margin": actuals are capped at half the manifest ceiling. This is correct, but it has a planning-side implication that should be stated explicitly: **the Task Planner must size manifest `max_estimated_input_tokens` at ≥2× the expected actual prompt size**, otherwise the gate will fire on legitimate dispatches. Without this rule, planners under-sizing manifests will produce systematic blocked-budget failures.

**Clarification D — Operator-control enforcement-order ownership.** The seven-step authorization sequence in §7 (Telegram whitelist → thread identity → capability token → command table → manifest exists → ManifestBinder binds → PolicyEngine approves) is well-ordered, but doesn't say which component performs each step. By inference: steps 1–2 are in `telegram_gateway.py`, steps 3–5 in `operator_control_inserter.py`, step 6 in `manifest_binder.py`, step 7 in `policy_engine.py`. Making this explicit would prevent Kimi from placing checks in the wrong module.