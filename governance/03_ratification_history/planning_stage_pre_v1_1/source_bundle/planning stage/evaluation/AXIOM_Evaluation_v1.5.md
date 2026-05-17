# Evaluator Review — AXIOM Proposal v1.5

**Bottom line:** v1.5 closes most of the v1.4 coherence gaps, but introduces or leaves open at least eight items that block approval. The architecture spine is preserved and Core Values 1, 2, 4, and 6 are upheld. Core Values 3 and 5 have unresolved conflicts. **Return to Architect for v1.6 revision before implementation planning.**

---

## What Holds

| Item | Resolution status |
|---|---|
| 3 — Critical sample count | Math is correct (40 critical across 9 categories), critical-miss gate is concrete |
| 4 — Stale-running recovery (ordered rule) | First-match semantics cleanly resolves the v1.4 overlap |
| 6 — Sandbox empirical validation | DNS/TCP/HTTPS/UDP/env/FS tests, pass-condition explicit, fail-mode disables `sandbox.execute` |
| 9 — `PRAGMA synchronous=FULL` | Correctly applied to every connection at boot |
| 10 — Cancelled-call accounting | Status enum, field set, and "actuals_unavailable" flag are coherent for free-tier tracking |

These five items can be considered closed.

---

## What Fails — Items With Internal Gaps

### Item 1 — PlanInjectionScanner verdict semantics: partially resolved

Three sub-gaps remain:

1. **Redundant fields invite desync.** The verdict schema has both `"passed": bool` and `"decision": "passed | failed | quarantined | needs_human_input"`. If `passed=true` and `decision="quarantined"`, behavior is undefined. Specify one as derived from the other (recommend dropping `passed` and treating `decision == "passed"` as the canonical pass signal).
2. **Decision rules table has no precedence ordering.** Multiple rows can match a single artifact (e.g., non-critical rule hit + high-risk-flag-from-Item-2 + classifier confidence 0.85). The rules need explicit ordering, the way Item 4's stale-running recovery now does. Without it, the implementer picks an order, which is precisely the kind of interpretive gap v1.4 was supposed to remove.
3. **Transition logic is vague in two rows.** "retry_pending or failed" and "blocked if deterministic schema error; otherwise retry" don't define the branch condition. Specify the exact condition (presumably `attempt_count < max_attempts` for retry, schema-malformed-vs-semantic for blocked).

### Item 2 — High-risk rule: substantively sound, one residual question

The deterministic flag and 0.90/0.80 thresholds are solid. But the trigger "Artifact contains text matched by any injection rule, even non-critical" combined with Item 1's non-precedence-ordered rules creates the ambiguity above. Resolve in Item 1.

### Item 4 — Stale-running recovery: the policy-approval lifecycle is unspecified

The new ordered rule handles the running-task overlap correctly. The separate `policy_approved=1, status='created'` recovery path clears policy approval and demands fresh evaluation. But:

> What happens to `policy_approved=1` on a task that gets recovered to `retry_pending` or `awaiting_verification` via the stale-running rule?

If approval is retained, a task that was approved under one set of conditions resumes under stale state. If cleared, fresh PolicyEngine evaluation is required on retry. v1.5 doesn't say. The conservative reading (clear and re-evaluate) aligns with Core Value 1; specify it.

### Item 5 ↔ Item 7 — Genuine conflict between bootstrap mode and the thread model

This is the most significant gap in v1.5.

- Item 7 (boot step 15): Scheduler thread starts **only if autonomous operation is enabled**.
- Item 5: bootstrap mode means autonomous = disabled.
- Item 5 also requires `/run_classifier_validation` to invoke `ClassifierValidationRunner`, which loads the local model and runs 120 samples.

**With no Scheduler running, what executes the validation?** Three plausible interpretations, all problematic without explicit choice:

- (A) Telegram thread runs it inline → Telegram blocks for minutes; `/status` becomes unresponsive during validation. Contradicts the Item 7 promise that Telegram remains responsive.
- (B) A limited Scheduler runs in bootstrap mode → directly contradicts Item 7's "scheduler thread only if autonomous enabled."
- (C) A dedicated validation worker thread spawns → not described anywhere.

Pick one and specify it. Without this, bootstrap mode is architecturally undefined.

Related minor gap: `/enable_autonomous` is referenced as a post-validation command but isn't in the bootstrap-allowed-commands table.

### Item 7 — Telegram-thread crash is unhandled

The failure model covers Scheduler crash and full-process death. The third case — Telegram thread crashes while Scheduler keeps running — is missing. In that state, AXIOM continues autonomous operation with **no operator visibility, no `/status`, no `/cancel`**. That violates the spirit of the operator-in-the-loop design. Specify behavior: either kill the process on Telegram crash, or restart the Telegram thread under a top-level handler with a maximum restart count.

### Item 7 ↔ Item 10 — In-flight call resolution path is unspecified

Item 10 says cancelled in-flight calls must be tracked until resolution, with `provider_usage` written on completion. But in the two-thread model (Item 7), where does that response handler live?

- If model calls are synchronous on the Scheduler thread, the Scheduler must wait for the response after cancelling — which defeats the purpose of cancellation.
- If model calls are async with a background completion handler, that infrastructure isn't described.

Specify the model-call lifecycle relative to the thread model. This affects whether Item 10 is implementable as written.

### Item 8 — Spoof protection is not architecturally enforced

> "If any non-Telegram component calls OperatorControlInserter → security_events: operator_control_invalid_creator; task not inserted"

The enforcement mechanism is undefined. If the check is "verify `created_by_component == 'telegram_gateway'`," any compromised component that calls OperatorControlInserter with the right string defeats it. The boundary needs to be **architectural** — at minimum a thread-identity assertion (`assert threading.current_thread() is telegram_thread`) — or, better, structural (only the Telegram thread imports the inserter; the inserter module is not on other components' import path).

This is a Core Value 3 issue. See below.

Secondary gap: ManifestBinder binds an `operator_control` manifest, but the source/scope of that manifest is unspecified — is it a single static manifest for all operator commands, or per-command?

---

## Core Value Conflicts

### Core Value 3 — Zero-trust at every agent boundary

**Conflict with Item 8.** Spoof protection on the OperatorControlInserter is enforced via a string-equality check on `created_by_component`. That is not zero-trust — it is trust-by-convention. A component that can call OperatorControlInserter with the correct argument string passes the check.

Required resolution: enforce the boundary architecturally. Either thread-identity assertion at OperatorControlInserter entry, or structural isolation (the inserter is importable only from the Telegram-gateway module). The doc must name the mechanism.

### Core Value 5 — All inter-agent coordination through the task queue

**Potential conflict with Item 5.** If `ClassifierValidationRunner` is invoked directly from the Telegram thread without writing to and reading from the task queue (because the Scheduler isn't running), bootstrap-mode validation bypasses the queue.

Two acceptable resolutions:
1. State explicitly that bootstrap-mode validation is **not** inter-agent coordination — it is a deterministic infrastructure check run before agents exist — and therefore Core Value 5 does not apply.
2. Or: route the validation through the queue with a limited Scheduler that processes only bootstrap-class tasks.

Either is fine; the proposal must pick one and document the rationale.

---

## Required Resolutions Before v1.6 Can Be Approved

In priority order:

1. **Resolve Item 5 ↔ Item 7 contradiction.** Specify what executes `/run_classifier_validation` when Scheduler is not started. (Blocking — without this, bootstrap mode is undefined.)
2. **Specify architectural enforcement for OperatorControlInserter spoof protection.** (Blocking — Core Value 3.)
3. **State the Core Value 5 position on bootstrap-mode validation.** (Blocking — Core Value 5.)
4. **Order the Item 1 decision rules and resolve the redundant `passed`/`decision` fields.** Specify exact conditions for the two vague transition rows.
5. **Specify Telegram-thread crash handling in Item 7.**
6. **Specify in-flight cloud call lifecycle in the two-thread model** (Item 7 ↔ Item 10).
7. **Specify policy_approved lifecycle for stale-running tasks recovered to retry_pending or awaiting_verification** (Item 4).
8. **Add `/enable_autonomous` to the bootstrap-allowed commands table; specify the operator_control manifest source** (Items 5, 8 — minor).

---

## Out-of-Scope but Worth Flagging

- **Item 3 dataset provenance.** v1.5 specifies validation thresholds against `injection_classifier_v1.jsonl` but doesn't specify who produces this 120-sample dataset, when, or what review process it passes through. Without the dataset, the gate is symbolic. This is downstream of the architecture but should be on the panel's tracking list before Phase 1 implementation.
- **Boot-time cost of sandbox validation on Celeron N4500.** Spinning up a sandbox process to run six tests on every boot has a cost. Not a coherence issue — pass to Constraints Reviewer (Qwen) for feasibility ruling.