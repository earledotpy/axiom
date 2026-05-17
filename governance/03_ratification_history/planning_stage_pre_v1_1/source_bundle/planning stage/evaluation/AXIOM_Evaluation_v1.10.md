# Evaluator Review — AXIOM Proposal v1.10

**Bottom line:** v1.10 substantively addresses all twelve items from the v1.9 synthesis. The architecture spine is unchanged, no Core Value conflicts are introduced, and the three security-strengthening additions (mid-session fingerprint check, manifest integrity verification, e2e acceptance test) are coherent with the existing patterns. **Approve to advance to bounded delta-confirmation cycle**, with one required correction noted below that the Architect should patch before Kimi takes the proposal.

The architect chose the stricter option on item 2 (pre-decision rather than periodic fingerprint check) and added a thoughtful defensive rule on item 6 (sandbox-execute + fallback estimator → needs_human_input) that wasn't requested. Both choices reflect good security judgment.

---

## Resolution Verification

| # | Synthesis Requirement | v1.10 Resolution | Verdict |
|---|---|---|---|
| 1 | Reassign calibration test-set authorship | Gemini primary author / DeepSeek adversarial reviewer / Claude coherence / Qwen feasibility / Kimi packaging | ✓ Resolved |
| 2 | Add mid-session model fingerprint verification | Pre-decision check on every classifier-dependent safe-pass; risk-class-tiered mismatch behavior | ✓ Resolved (stricter than asked) |
| 3 | Add manifest integrity verification | `manifest_fingerprints` table; SHA256 boot verification; fail-closed; registration mode for deployment | ✓ Resolved |
| 4 | Add end-to-end acceptance test | `test_full_goal_flow_minimum.py` with 14 boundary assertions; trivial no-network/no-sandbox goal | ✓ Resolved |
| 5 | Add reconciliation sanity check | ±50% discrepancy threshold + operator confirmation flow + storage fields | ✓ Resolved |
| 6 | Add tiered token-margin rule | 2× calibrated / 1.5× fallback + high-risk + sandbox.execute escalation rule | ✓ Resolved |
| 7 | Reframe keepalive honestly | Explicit "retrospective diagnostic, not real-time alert" framing; Phase 2 watchdog deferral acknowledged | ✓ Resolved |
| 8 | Add immediate goal acknowledgement | Telegram template with planning-latency expectation; insertion point specified | ✓ Resolved |
| 9 | Reconcile §12.3 / §14 test lists | Canonical merged suite specified | ✓ Resolved (with caveat — see below) |
| 10 | Locate supervisor stale-check logic | `app/session_controller.py::SupervisorMonitor` with explicit scope and anti-fragmentation rule | ✓ Resolved |
| 11 | Add task-planner manifest-sizing rule | ≤50% / ≤66% rules with Result Verifier checkpoint enforcement closing the loop | ✓ Resolved |
| 12 | Specify operator-control authorization ownership | Seven-step table with owners and failure behaviors; atomic insertion specified | ✓ Resolved |

### Specific verification notes

**Item 2 — pre-decision check is the stricter choice.** Periodic re-check would have left an exposure window between checks. Pre-decision ties the integrity guarantee directly to the security action being taken. Performance cost is bounded — Ollama metadata calls are ~50–200ms and only fire when the scanner would safe-pass on classifier confidence (not on every scan). Acceptable.

**Item 3 — registration mode is the right shape.** The "treat missing fingerprint as mismatch unless in deployment-registration mode" rule prevents silent introduction of new manifests during autonomous operation. The mode-toggle mechanism itself isn't fully specified (who toggles it, how the toggle is verified) — this is a Kimi-level implementation detail that should default to the obvious safe pattern: a CLI/script run only with `autonomous_operation_enabled = false`. Worth flagging to Kimi but not a v1.10 blocker.

**Item 4 — e2e test boundary assertions are well-chosen.** The test exercises the queue-mediation, policy-gating, manifest-binding, and verification boundaries without requiring web search or sandbox infrastructure. The negative assertions ("no direct role-to-role call occurs," "no task bypasses PolicyEngine," "no task runs without a manifest") will require audit-log inspection helpers in the test harness — Kimi should build that infrastructure.

**Item 6 — the high-risk + fallback-estimator + sandbox.execute escalation rule is a good defense addition.** It correctly identifies that running unverified code with an uncalibrated token estimate is a compounded risk and routes those cases to human input. Operational implication worth surfacing to Kimi: in MVP, providers without calibrated tokenizers will produce systematic `needs_human_input` for sandbox tasks until calibrated tokenizers are configured. The architect should consider listing which providers in the cloud cascade have calibrated tokenizers in MVP — this isn't blocking, but it sets operator expectations.

**Item 11 — closing the loop with Result Verifier checkpoint is the right architectural placement.** Catching planner-sized manifests that violate the dispatch gate at checkpoint time prevents systematic false blocks at dispatch. This is consistent with the §6 chain of responsibility (Result Verifier owns semantic consistency; manifest sizing relative to expected prompt is semantic).

---

## Core Value Compliance

| Value | Status |
|---|---|
| CV1 — Security baked in | **Strengthened** — mid-session fingerprint check + manifest integrity verification + reconciliation sanity check |
| CV2 — Local model in lane | Unchanged |
| CV3 — Zero-trust at boundaries | **Strengthened** — operator-control seven-step ownership table makes the trust chain explicit |
| CV4 — Build simple, prove concept, iterate | **Strengthened** — e2e acceptance test gives MVP a "concept proven" criterion |
| CV5 — Queue-mediated coordination | Unchanged |
| CV6 — Sandbox/network separation | Unchanged |

No conflicts.

---

## Issue Found in v1.10 — Required Correction

**Test list reconciliation is incomplete.** The architect committed in §11 to "§14 = full MVP acceptance suite" as the union of §12.3 + v1.9 §14 + v1.10 e2e. The actual canonical suite produced in §11 is missing seven tests that appeared in v1.9 §14:

- `test_sandbox_heartbeat_ordering.py`
- `test_calibration_set_ownership_metadata.py`
- `test_task_committer_validation_scope.py`
- `test_checkpoint_semantic_consistency.py`
- `test_operator_control_manifest_binding.py` (possibly merged into `test_operator_control_authorization_chain.py` or `test_operator_control_capability_boundary.py` — unclear)
- `test_supervisor_liveness_limit_notice.py`
- `test_mvp_module_boundary.py`

Some may be intentional consolidations (e.g., `test_operator_control_manifest_binding` likely consolidates into the new authorization-chain test). Others appear to have been dropped without explanation. `test_checkpoint_semantic_consistency` in particular is the test that proves Result Verifier owns what TaskCommitter doesn't — losing it leaves Item 4 from the original v1.9 synthesis (TaskCommitter validation scope) without verification.

**Required correction:** the Architect should produce a v1.10.1 footnote/patch that either:
(a) restores the missing tests to the canonical suite, or
(b) explicitly maps each missing test to a consolidated successor in the v1.10 list with a one-line rationale per test.

This is a bookkeeping correction, not architectural revision. It does not require restarting the panel cycle. It should be completed before Kimi receives the proposal so that Kimi implements the full intended acceptance surface.

---

## Non-Blocking Observations for Kimi

These are not v1.10 defects but are worth surfacing to the implementation specialist:

- **Manifest registration mode toggle mechanism** — needs an obvious safe pattern (e.g., CLI script only runnable when autonomous operation disabled). Kimi to specify.
- **E2E test audit-log inspection helpers** — required infrastructure for the negative assertions. Kimi to build.
- **MVP calibrated-tokenizer coverage** — which cloud providers in the cascade have calibrated tokenizers in MVP, and which fall back to ÷3? Kimi to enumerate during implementation planning so operator expectations are set.
- **`BootstrapValidationWorker` liveness scope** — SupervisorMonitor's scope includes this, but the worker is bootstrap-only and should terminate. Kimi to clarify whether the liveness check covers post-bootstrap edge cases.

---

## Decision

**v1.10 advances.**

Recommended panel routing for delta confirmation:

1. **Critic (DeepSeek)** — bounded delta review: did v1.10 resolve the eight v1.9 critique items (Obj 1–7, 9; Obj 8 already withdrawn)? Any new issues in the changes themselves? Note that DeepSeek's primary v1.9 objection (Obj 1, Charter conflict on test set authorship) has been resolved by reassignment, not by Charter exception — DeepSeek's panel-boundary concerns should now be satisfied.
2. **Arbiter (Gemini)** — likely skippable. v1.10 introduces no new factual mechanisms beyond what's already verified. The new SHA256 manifest verification is standard cryptography. The pre-decision Ollama metadata call uses the same `/api/show` endpoint already verified in v1.9 §9. If Gemini wishes to confirm, the review is a one-page formality. Note: Gemini also takes on a new operational role (calibration test-set author per Item 1) — Gemini should confirm acceptance of that role.
3. **Constraints (Qwen)** — likely skippable. The v1.10 additions are deterministic logic and small schema additions. RAM impact is negligible. If Qwen wishes to confirm, a one-page delta review covering the new `manifest_fingerprints` table, the pre-decision Ollama metadata call frequency, and the new `SupervisorMonitor` placement is sufficient.
4. **Synthesis (this seat)** — confirm delta cycle clean and the test-list correction patched.
5. **Implementation planning (Kimi)** — produce execution plan against the corrected v1.10 with the four observations above flagged.

The Architect has done the work cleanly. One bookkeeping correction, then advance.

---

*AXIOM Evaluation v1.10 — May 2026 — save as `AXIOM_Evaluation_v1_10.md`*