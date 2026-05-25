# AXIOM Evaluation v1.4 — Coherence Review

**Evaluator:** Claude (Quality and Coherence Evaluator)
**Subject:** AXIOM Proposal v1.4 — Resolution of Synthesis Items 1–9
**Verdict:** Cannot proceed to implementation. Return to Architect for v1.5 revision.

---

## What Holds

The architectural spine survives revision intact. Sequential execution, queue-mediated coordination, SQLite-backed persistence, and the sandbox/network separation remain consistent through every section. No Core Value conflict detected.

Specific elements that are now genuinely specified rather than gestured at:

**PlanInjectionScanner (§3).** The hybrid four-layer mechanism (rule scan → schema scan → classifier → conservative decision rule) is concrete enough to implement. The explicit decision to make this deterministic infrastructure rather than an agent role is correct and aligned with Core Value 5 — it isn't agent coordination, so it doesn't need queue mediation.

**TaskCommitter atomicity (§6).** `BEGIN IMMEDIATE` on a single transaction, plus the Scheduler's selection guard (`commit_batch_id IS NOT NULL AND task_permissions row exists`), gives genuine defense in depth. A partial subtree cannot become runnable even if transaction semantics fail unexpectedly.

**Resource estimator as deterministic code (§5.4).** "Planner-provided estimates may be stored as comments but are not trusted for enforcement" correctly applies Core Value 3 (zero-trust) at the resource boundary. A compromised planner cannot inflate its own budget.

**operator_control creator allowlist (§9).** Five enforcement points (Command Parser, TaskCommitter, ManifestBinder, PolicyEngine, static test) is real defense in depth, not labeled boxes.

**Memory Gateway response routing (§8).** The verifier sees `dedup_status` and `write_status` directly. The "silent dedup" ambiguity from the prior round is genuinely closed.

**Scheduler failure visibility (§11).** Heartbeat + session_events + Telegram-readable status correctly resolves the visibility gap without splitting the Scheduler — aligned with Core Value 4.

---

## What Fails

Ten coherence and specification gaps. Items 1–4 are genuine internal contradictions or undefined references. Items 5–8 are gaps that affect whether claimed behavior actually holds at runtime. Items 9–10 are minor but should be cleaned up.

### 1. Verdict schema and decision rules contradict each other (§3.4 vs §3.5)

The verdict schema declares `decision: passed | failed | quarantined | needs_human_input`. The decision rules table in §3.5 never produces `failed` — only `passed`, `quarantined`, `needs_human_input`, or "blocked parent task" on scanner exception. Either remove `failed` from the schema or define the conditions that produce it.

### 2. "High-risk artifact" is undefined (§3.5)

Rule: "High-risk artifact confidence < 0.90 → quarantined." But there is no definition of what makes an artifact "high-risk." Is it determined by rule-layer hits? Classifier label? Both? Without this, the rule cannot be implemented deterministically.

### 3. Critical sample count is unspecified (§4.2 vs §4.3)

§4.2 requires 100% recall on critical malicious samples. §4.3 specifies a 120-sample test set but does not state how many samples are tagged `severity: critical`. The 100% threshold is meaningless without a denominator. Specify the critical sample count in the Phase 1 test set, or define `critical` by category rather than sample tag.

### 4. Two recovery rules for the same condition (§7.4)

Row: `running → If lease expired → retry_pending or failed`.
Row: `policy_approved=1, status=running → Treat as stale running task`.

These describe overlapping or identical states with different treatments. Either the second row is redundant (and should be removed) or "stale running task" needs an explicit definition that distinguishes it from lease-expired running.

### 5. First-boot validation case not handled (§7.1 step 12)

§4.6 says "No validation run → Startup blocks autonomous operation." But step 12 of the boot sequence simply says "Validate classifier profile and last passing validation run." It does not specify the behavior when the system has never been validated — i.e., on first boot before any validation has been performed. The system needs an explicit non-autonomous bootstrap mode for the validation run itself to occur. As written, the system cannot reach the state where it can be validated.

### 6. Sandbox no-network validation mechanism is unspecified (§7.1 step 14)

The legacy reference is explicit: `subprocess.Popen` does not isolate network on Windows. Step 14 says "Validate sandbox no-network status if Sandbox Gateway enabled" without specifying *how* validation occurs. A passing assertion ("the config says no network") is not the same as a verified state ("a test process inside the sandbox cannot resolve DNS"). This is the most safety-critical check in the boot sequence and it cannot be a TODO. Specify the actual validation procedure — at minimum, an in-sandbox connect attempt to a known endpoint with assertion of failure.

### 7. Scheduler/Telegram process model is unspecified (§11.4–§11.5)

§11.4: "notify Telegram Gateway if alive."
§11.5: "Telegram Gateway can answer /status by reading scheduler_heartbeat."

Both presuppose that Telegram Gateway can survive a Scheduler crash. That is only true if Telegram Gateway runs in a separate thread or process from the Scheduler loop. The proposal does not state which. If both run in the same process and the Scheduler raises an unhandled exception that escapes the wrapper, Telegram dies with it — and the entire failure-visibility design is voided. Specify the process/thread model explicitly.

### 8. operator_control has no path through the architecture (§9 vs §12)

§9 says TaskCommitter rejects any artifact with `task_class=operator_control`. The end-to-end chain in §12 shows the chain for goal_planning → planning → tool_execution → verification, all of which flow through TaskCommitter. No path is shown for how operator_control tasks actually enter the system. Presumably Telegram Gateway writes them directly to the `tasks` table, bypassing TaskCommitter — but if so, the atomicity, manifest binding, and creator validation properties of TaskCommitter must be replicated in that direct write path, or operator_control loses those guarantees. Specify the operator_control creation flow as a parallel deterministic chain.

### 9. SQLite `synchronous` PRAGMA not specified (§7.1)

WAL mode and `busy_timeout` are set. `synchronous` is not. On the Celeron N4500 / SATA SSD target, the choice between `NORMAL` and `FULL` materially affects whether TaskCommitter's atomicity claims hold across power loss. Default in Python's sqlite3 is `FULL`, which is correct, but it should be explicit in the boot sequence rather than relying on default.

### 10. Resource accounting on cancelled in-flight calls (§10.5)

When cancellation fires after a cloud call has begun but before its timeout, tokens already consumed by the provider are still consumed. §10.5 says cancellation is cooperative and waits for the timeout. §5.9 (provider_usage) tracks `actual_input_tokens` — but the cancellation flow doesn't say whether `actual_input_tokens` is recorded for cancelled-but-charged calls. Without this, free-tier budget tracking will drift on every cancellation.

---

## What Must Be Resolved

Items 1, 2, 4 are internal contradictions and must be resolved before re-review. Items 3, 5, 6, 8 are specification gaps that affect whether the system can boot safely or behave as claimed. Item 7 affects the validity of the scheduler failure design. Items 9 and 10 are smaller but should be cleaned up in the same revision.

**Recommended path:** Return to Architect for v1.5 addressing items 1–8 explicitly. Items 9 and 10 may be addressed in v1.5 or noted as accepted minor gaps with rationale. After v1.5 lands, re-review can be targeted to the changed sections rather than the full proposal.