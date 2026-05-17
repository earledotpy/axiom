# Evaluator Synthesis — AXIOM Proposal v1.8 / v1.8.1

**Bottom line:** The proposal **returns to the Chief Architect for revision.** Ten objections from the Critic, none overruled by Arbiter or Constraints, identify real specification gaps. The Arbiter has issued one binding factual caveat that requires architectural acknowledgement. The Constraints Reviewer has approved subject to ten binding conditions. The architecture spine is sound — the gaps are in interaction details, ownership of artifacts, and unoperationalised requirements that cannot be safely passed through to Kimi as-is.

This synthesis revises my v1.8.1 "approve to advance" verdict. That earlier verdict was scoped narrowly to whether the two patches resolved what they set out to resolve. The full panel cycle has now surfaced issues those patches did not touch.

---

## (1) Objections That Are Valid and Must Be Resolved

Per the Charter rule, an objection is overruled only if **both** Arbiter and Constraints find it unsupported. None of the ten objections meets that bar. Below, I rank by severity and tag the resolution required.

### Blocking — architectural revision required

**Obj 1 — Heartbeat field semantics ambiguous.** The spec writes heartbeats at multiple points but uses `last_tick_at` as the supervisor's freshness signal. If `last_tick_at` is only updated at the start of a tick, a legitimate sequence of bounded operations (sandbox 60s → cloud call 90s with no tick boundary between them) accumulates ~150s without a hang and trips a false-positive shutdown. The math I audited in my v1.8.1 review implicitly assumed every heartbeat write updates the freshness field — but the spec does not say that. **Must clarify:** either every heartbeat write updates `last_tick_at`, or the supervisor's stale check is `now - GREATEST(last_tick_at, last_heartbeat_at)`, with the field semantics rewritten accordingly.

**Obj 2 — Calibration test set has no creator.** The 120-sample injection set is the security-critical artifact on which classifier safe-pass thresholds depend. No panel role is assigned to author it. The operator does not produce design artifacts. Without a creator, calibration cannot run, and either (a) the system operates with an unverified security boundary (violates Core Value 1) or (b) safe-pass is permanently disabled, crippling autonomous throughput. **Must specify:** which panel role authors the set, what the interim default is until calibrated (I recommend: classifier defaults to quarantine on every flag; safe-pass disabled until calibration passes), and what governs set maintenance as attack vectors evolve.

**Obj 7 + Arbiter binding addition — Sandbox wall-clock enforcement and termination overhead.** The Arbiter ruled that Windows Job Object time limits measure **User-Mode CPU time only**, not wall-clock. A sleeping or socket-waiting process bypasses the Job Object timeout indefinitely. The 60s cap therefore requires `subprocess.run(timeout=60)` or an equivalent wall-clock wrapper alongside the Job Object. This is a binding factual ruling. Compounding this: DeepSeek's worst-case math (60s sandbox + ~5s termination overhead under SATA paging + 90s subsequent cloud call = 155s) exceeds the 120s heartbeat threshold if the post-sandbox heartbeat write is delayed by termination handling. **Must revise:** specify the wall-clock enforcement mechanism explicitly, and specify that the post-sandbox heartbeat write occurs **after** termination handling completes and **before** any subsequent blocking operation. The 30s margin must be re-derived against the new termination-overhead budget.

### Significant — must be specified before approval

**Obj 3 — TaskCommitter validation scope undefined.** "Validate every child task before insertion" is worded broadly enough to imply semantic validation, but TaskCommitter is deterministic and cannot perform semantic-consistency checks. The chain (PlanInjectionScanner → Result Verifier in checkpoint mode → TaskCommitter) creates a triple-validation surface with a possible gap where no component owns child-task-level semantic consistency. **Must specify:** the bounded scope of TaskCommitter's validation (schema, capability vocabulary, manifest compatibility), and which component owns semantic-consistency checking between a task's tool assignment and its acceptance criteria.

**Obj 5 — Per-command operator-control manifests' enforcement role.** Six new per-command operator-control manifests sit alongside enforced role manifests in `policy/role_manifests/`. The v1.7 model said operator capability is enforced through object identity (the capability token), not via manifest files. If these new manifests are enforcement artifacts, they create a second authorisation path; if documentation-only, they should not live alongside enforced manifests because Kimi will treat them as load-bearing. **Must clarify:** enforcement role of these files, and either remove them from the enforced-manifest directory or explicitly bind them to the capability token.

**Obj 6 — Token-counting mechanism for pre-dispatch budget gate.** The 2× safety-margin rule (binding per Constraints condition 7) cannot be enforced without a dispatch-time token count. Manifest estimates are set at plan time and do not account for variable retrieved-memory and context-bundle content at dispatch time. **Must specify:** the local tokenisation mechanism used pre-dispatch (e.g., `tiktoken` for OpenAI-family endpoints, model-specific tokenisers for others, or a documented approximation rule with conservative bias), plus the rule for what happens when the actual prompt exceeds the manifest estimate at dispatch time.

**Obj 8 — Model profile change detection.** The calibration-invalidation rule "model profile changes" has no detection mechanism. Ollama can silently update a model; the security boundary degrades without anyone noticing. **Must specify:** a detection mechanism. The simplest options that satisfy this without architectural creep are (a) store the model file checksum at calibration time and verify at every boot, with classifier safe-pass disabled if mismatched, or (b) accept that calibration is static and require explicit operator recalibration after any Ollama operation, with a boot-time warning if the model file mtime has changed since last calibration.

**Obj 10 — Orphan provider-call recovery accumulates phantom budget consumption.** Conservatively charging estimated tokens for orphaned dispatches is correct for immediate safety but accumulates permanent error across crash-recovery cycles. Constraints binding condition 7 ("actual usage must be logged for adaptive calibration") implies a reconciliation pathway that the architecture does not specify. **Must specify:** either a `reconcile_provider_usage` mechanism (operator-triggered command that ingests the provider's usage dashboard data — likely manual paste, given free-tier APIs typically lack programmatic usage endpoints), or an explicit acknowledgement that drift is permanent until the budget ledger is manually reset, with a recommended reset cadence.

### Lower severity but valid

**Obj 4 — Supervisor liveness coupled to scheduler hardware.** A whole-system paging storm or hibernate event hangs the supervisor thread along with the scheduler thread, defeating the "fail-closed + Telegram alert" pattern. The Constraints Register explicitly warns about SATA SSD paging severity. A pure single-machine system cannot fully self-detect total system hang, but the architecture can do better than silent failure. **Must specify:** at minimum, an explicit acknowledgement of the limit, and an operator-side mitigation (Telegram client-side keepalive, or a documented "if no scheduler heartbeat acknowledgement for X minutes, the operator must check on the system physically"). Bonus credit if the architect specifies an out-of-process watchdog (e.g., a Windows Scheduled Task that pings a health endpoint and notifies the operator if it stops responding) — but this is not required if the limitation is documented honestly.

**Obj 9 — Module map vs. Core Value 4.** ~30 Python modules + 12+ JSON manifests + full SQL schema + 120-sample test set is a large Phase 1 surface for a single human operator on constrained hardware. Core Value 4 ("build simple, prove the concept, iterate into complexity") is at risk. This is partly Kimi's problem — phased implementation plans can sequence delivery. But the architect can help by marking which modules are MVP versus deferred. **Must address:** either (a) defend each module against Core Value 4 (why this is needed in Phase 1, not Phase N), or (b) tag a subset as MVP with the rest explicitly deferred. The architect does not need to choose Kimi's sequencing — only to clarify which parts of the architecture must exist for the system to start versus which can land later.

---

## (2) Objections Overruled

**None.** Per the Charter rule, the Arbiter and Constraints Reviewer would have to find an objection unsupported for it to be overruled. Neither did. The closest case is **Obj 7**, where the Arbiter's ruling actually amplified rather than overruled the concern.

---

## (3) What the Architect Must Revise

The Architect must produce **AXIOM_Proposal_v1.9** addressing the following in order:

1. **Heartbeat field semantics** (Obj 1) — clarify that every heartbeat write updates the freshness field used by the supervisor's stale check, and rename the field if needed to match its new semantics. Re-audit the heartbeat math against the new semantics.
2. **Sandbox wall-clock enforcement** (Obj 7 + Arbiter binding) — specify `subprocess.run(timeout=60)` or equivalent wall-clock wrapper alongside the Job Object. Re-derive the heartbeat math to include termination handling overhead. Specify the heartbeat ordering: post-sandbox heartbeat write completes before any subsequent blocking operation.
3. **Calibration test set ownership** (Obj 2) — assign authorship to a panel role; specify the interim default behaviour (recommended: safe-pass disabled until calibration passes); specify a maintenance owner.
4. **TaskCommitter validation scope** (Obj 3) — bound it explicitly to schema, capability vocabulary, and manifest compatibility. Assign semantic-consistency checking to a named upstream component.
5. **Per-command operator-control manifests** (Obj 5) — clarify enforcement role; relocate documentation-only manifests out of `policy/role_manifests/` if not enforced.
6. **Token-counting mechanism** (Obj 6) — specify the local tokeniser used at dispatch time and the policy when actuals exceed manifest estimates.
7. **Model profile change detection** (Obj 8) — specify the detection mechanism.
8. **Orphan provider-call reconciliation** (Obj 10) — specify either a reconciliation pathway or an explicit budget-reset cadence.
9. **Supervisor liveness limitation** (Obj 4) — document the failure mode honestly; specify mitigation.
10. **MVP module subset** (Obj 9) — tag MVP versus deferred modules, or defend each Phase 1 module against Core Value 4.

The Architect should also explicitly reaffirm that the v1.9 proposal travels under:

- **Arbiter binding:** Sandbox wall-clock enforcement requires `subprocess.run(timeout=60)` (or thread timer) alongside the Windows Job Object. The Arbiter has otherwise factually cleared the proposal.
- **Constraints binding (10 conditions):** sequential execution, qwen3:4b Q4 quantisation + mmap, 500 KB context bundle cap, sandbox 256 MB + 60s, sqlite-vec 100-vector batch cap, Brave Search API confirmation, 2× token margin, stateless PolicyEngine, four-thread cap, calibration before safe-pass.

These are binding rulings that travel forward with the proposal through every subsequent revision and panel pass.