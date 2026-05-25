I've read v1.8 and the v1.8.1 patch in full. This is the most substantially complete version of the architecture yet—many prior objections have been resolved with real specification, not placeholders. However, the increased detail exposes new interaction surfaces, edge cases, and unstated assumptions that didn't exist when components were vague. My objections follow.

---

OBJECTION 1 — The 120-Second Scheduler-Stale Threshold Creates a Cascading False-Positive Risk Under Realistic Load

What v1.8 specifies:

· Cloud calls capped at 90 seconds absolute hard ceiling.
· Scheduler heartbeat threshold: 120 seconds (90s + 30s margin).
· Heartbeat is written before/after blocking calls.
· Heartbeat becomes stale if last_tick_at > 120s and scheduler not in clean_shutdown/paused.
· Supervisor action: fail closed, disable autonomous operation, require manual restart.

What v1.8.1 adds:

· Sandbox execution capped at 60 seconds.
· Scheduler writes heartbeat immediately before and after sandbox execution.

The interaction failure:
The heartbeat threshold is derived from the provider-call hard ceiling, but the stale condition checks last_tick_at, not last_blocking_operation_started_at. Consider this sequence:

1. Scheduler writes heartbeat at start of tick. last_tick_at = T0.
2. Scheduler prepares sandbox execution, writes heartbeat immediately before. But last_tick_at is not updated—v1.8 only says the heartbeat is written, it doesn't say last_tick_at is set to now. The heartbeat record is written, but what field does the supervisor check? Section 6 says: now - scheduler_heartbeat.last_tick_at > 120 seconds.
3. The sandbox runs for 58 seconds (compliant, under 60s cap).
4. Scheduler writes heartbeat after sandbox. Again, does this update last_tick_at? If not, last_tick_at remains at T0.

Now the scheduler picks the next task, which requires a Goal Planner cloud call. Primary call takes 28 seconds. Fallback is needed, takes 42 seconds. Total provider time = 70 seconds (under 90s ceiling). But last_tick_at hasn't been updated since T0. The sandbox (58s) + cloud cascade (70s) = 128 seconds since the last last_tick_at update at T0. The supervisor declares the scheduler stale and kills autonomous operation—despite everything running within spec.

The unstated assumption:
That heartbeat writes always update last_tick_at, or that the supervisor uses a different freshness signal. The specification doesn't say "last_tick_at is updated on every heartbeat write." It says "Scheduler writes scheduler_heartbeat" at various points and separately defines the stale check as now - scheduler_heartbeat.last_tick_at. If the heartbeat write updates last_tick_at, the field name is misleading—it's no longer "last tick" but "last heartbeat." If it doesn't, the supervisor can't distinguish a hang from a legitimate sequence of bounded operations.

What's needed:
Either last_tick_at must be updated on every heartbeat write, or the supervisor must check GREATEST(last_tick_at, last_heartbeat_at) where last_heartbeat_at is the timestamp of the most recent heartbeat row. The current text is ambiguous enough to produce false-positive shutdowns on the exact hardware this system targets.

---

OBJECTION 2 — Calibration Requires a 120-Sample Test Set That Does Not Exist and Has No Curator

What v1.8 specifies (Section 10):
"Use the existing 120-sample validation set plus confidence buckets." The set composition is specified: 90 malicious, 30 benign, 40 critical malicious, with ten attack-vector categories. Required accuracy thresholds and calibration thresholds are defined. Calibration failure behaviors are enumerated. A test test_classifier_calibration_thresholds.py is required.

What is not stated:
Who creates this 120-sample test set. The human operator's role is execution, not design judgment. The panel's role is architecture, not test-set authoring. The set requires:

· Expert knowledge of prompt injection techniques across 9 attack vectors.
· Carefully crafted adversarial examples that stress the classifier's boundaries.
· Benign controls that are realistic but not trivially distinguishable.
· Maintenance as injection techniques evolve.

The unstated assumption:
That one of the panel AIs (or the human) will produce 120 high-quality labeled samples as part of Phase 1 implementation. The Legacy Reference documents that prompt injection was structurally unaddressed, and the entire sanitization architecture depends on classifier validation succeeding. If the test set doesn't exist, calibration cannot run, and if calibration cannot run, the classifier thresholds are unvalidated. If the thresholds are unvalidated, either the system operates with an unverified security boundary (violating the Core Values' requirement for tested isolation) or it must disable classifier safe-pass and default to quarantining/escalating—crippling autonomous throughput.

This is not a theoretical concern. Curating an injection test set is specialist work. A poorly constructed set produces calibration that looks good on paper but misses real attacks. The architecture now has a beautifully specified calibration process that depends on an artifact nobody has committed to producing.

---

OBJECTION 3 — TaskCommitter Atomic Batch Validation Step 4 Is Impossible Without Executing Goal Planner Logic

What v1.8 specifies (Section 8):
Atomic commit sequence, Step 4: "Validate every child task before inserting any child task."

What this validation entails is undefined, but the context implies:
Checking that each child task is well-formed, has valid fields, has a permissible role assignment, has testable acceptance criteria, etc. These are schema-level and policy-level checks that are implementable.

But consider the broader context:
The Goal Planner produces child tasks. The PlanInjectionScanner checks the plan artifact for injection. The Result Verifier checks the plan for architectural coherence. TaskCommitter then validates every child task before insertion.

The edge case:
What if a child task is internally inconsistent in a way that the plan-level verifier missed because the verifier checks the plan's architecture, not each task's internal logic? For example, a child task specifies tool_execution with sandbox.execute but the acceptance criteria require a network fetch. The plan checkpoint verifier might pass this because the plan structure is sound. The TaskCommitter's Step 4 validation would need to catch it—but TaskCommitter is not an AI agent. It's a deterministic component. It can check schema validity, capability vocabulary membership, manifest compatibility. It cannot check semantic consistency between a task's tool assignment and its acceptance criteria.

The implicit assumption:
That all semantic validation happens upstream (PlanInjectionScanner, Result Verifier in checkpoint mode) and TaskCommitter only does structural checks. But Step 4 is worded broadly: "Validate every child task." If TaskCommitter does structural-only validation, semantically flawed tasks enter the queue. If it attempts semantic validation, it's overreaching its deterministic role and will either produce false positives (blocking valid tasks) or false negatives (passing broken tasks).

The specification debt:
The validation scope for each component in the chain needs to be explicitly bounded. The overlapping checks between PlanInjectionScanner, Result Verifier (checkpoint mode), and TaskCommitter create the illusion of triple-validation while potentially containing a gap where no component owns semantic task-level consistency.

---

OBJECTION 4 — Stale Scheduler Recovery Requires Manual Restart, but the Operator Has No Runtime Awareness

What v1.8 specifies (Section 6):
When the supervisor detects a stale scheduler, it sets a shutdown flag, sends a Telegram alert "if available," and disables autonomous operation. The operator must restart AXIOM manually.

The failure scenario:
The scheduler goes stale. The supervisor sets shutdown_requested = true. It attempts to send a Telegram message. But why would the Telegram thread be available? The two most likely causes of scheduler staleness are:

1. A hung provider call blocking the scheduler thread. The supervisor thread and Telegram thread are separate and still alive—Telegram message goes through. Operator gets notified. Good.
2. A whole-process hang (e.g., SATA SSD paging storm, Windows memory pressure, Python GIL contention from a native extension, system sleep/hibernate). In this case, the supervisor thread is also hung. No Telegram message is sent. The operator sees the bot go silent with no explanation.

In case 2, the operator has no way to distinguish "legitimate long task" from "system hung requiring restart." The 120-second threshold means the operator could wait 2 minutes before concluding something is wrong—but only if they're actively monitoring. The system was designed for mobile messaging where the operator sends a command and checks back later. If they send a goal, put the phone down, and the system hangs 30 seconds later, they return hours later to find the system silently dead with no notification.

The architecture assumes the supervisor thread remains alive during scheduler failures. The Constraints Register explicitly warns that SATA SSD paging "degrades performance severely." Severe paging is a whole-system event, not a single-thread event. The supervisor's liveness is coupled to the same hardware as the scheduler's.

---

OBJECTION 5 — Per-Command Operator Control Manifests Multiply the Attack Surface

What v1.8's module map shows (new since v1.3.1):
The policy/role_manifests/ directory now contains six operator-control manifest files:

· operator_control_status.json
· operator_control_cancel_current_chain.json
· operator_control_pause_after_current.json
· operator_control_resume.json
· operator_control_shutdown_after_current.json
· operator_control_run_classifier_validation.json
· operator_control_enable_autonomous.json

Plus the earlier operator_control.json (now likely superseded but still present? Unclear).

What's changed conceptually:
Previously, operator control was one logical capability. Now each operator command has its own manifest file. These are JSON files on disk, in a directory with other role manifests.

The security concern:
The operator-control security model in v1.7 established that capability is enforced through object identity (OperatorControlCapability token) and thread identity—not through manifest files on disk. The manifests existed for audit/documentation, not as enforcement. But v1.8 now has per-command manifests that look like enforcement artifacts. If the Permission Engine or ManifestBinder ever reads these manifests and uses them as an enforcement source—even as a secondary check—a bug that allows manifest file modification could grant or deny operator commands. More files = more attack surface, more potential for confusion about what enforces what.

The specification doesn't clarify:
Whether these per-command manifests are enforced at runtime or are documentation-only. If enforced, they create a second path for operator-control authorization that bypasses the capability token. If documentation-only, they shouldn't be in policy/role_manifests/ alongside enforced manifests, because Kimi will assume they're load-bearing.

---

OBJECTION 6 — Resource Limits Enforcement for Cloud Calls Is Specified but Not Feasible with Current Provider APIs

What v1.8 specifies (Section 12):
Resource limits enforce a pre-dispatch gate for cloud calls: "Check max_model_calls, 2× token margin." The token budget uses estimated_input_tokens and estimated_output_tokens from the manifest, with a 2× safety margin.

What's unstated and likely infeasible:
The pre-dispatch gate needs to know the actual token count of the prompt being sent to decide if the 2× margin holds. The manifest specifies max_estimated_input_tokens and max_estimated_output_tokens. But who produces the estimate for a given call? The Context Builder builds the prompt. The Model Gateway dispatches it. The ResourceEstimator is supposed to check before dispatch.

The gap:
At dispatch time, the actual input token count may differ from the manifest's estimate. Context Builder includes retrieved memory, task context, and other variable-length content. The manifest's max_estimated_input_tokens is a bound set by the Task Planner at plan time—but the Task Planner is a cloud model that doesn't know how many tokens the memory retrieval will return. The actual input could exceed the estimate. If the ResourceEstimator uses the manifest estimate for the pre-dispatch check, it might approve a call that actually exceeds budget. If it tokenizes the actual prompt to get a real count, it's adding a local tokenization step (using the local model's tokenizer? a separate library?) that wasn't part of the architecture.

The silence on token counting mechanism:
The proposal says "2× safety margin in budget_policy before cloud dispatch" as a binding condition (Section 2). It doesn't say how the dispatch-time token count is obtained. This is an implementation detail that can't be hand-waved—different tokenizers give different counts, and the cloud model's actual token count is only known after the API responds with usage data. Pre-dispatch token estimation requires a local token-counting mechanism that approximates the cloud model's tokenizer.

---

OBJECTION 7 — The 60-Second Sandbox Cap + Heartbeat Interaction Is Underspecified for the Actual Enforcement Flow

What v1.8.1 specifies:
Sandbox execution capped at 60 seconds via Windows Job Object timeout. Scheduler writes heartbeat immediately before and after sandbox execution. If sandbox reaches 60 seconds, Job Object terminates it, gateway_response.status = failed_resource_limit, Scheduler writes heartbeat after termination.

The edge case:
Windows Job Object timeout termination is asynchronous. The parent process calls WaitForSingleObject or equivalent on the child process handle. If the Job Object terminates the child at 60 seconds, the parent's wait call returns with an exit code indicating termination. The Sandbox Gateway code then needs to:

1. Detect that termination was due to timeout (not normal exit).
2. Write the gateway response.
3. Return control to the Scheduler.

What's not specified:

· How long step 1–3 takes. It's probably milliseconds, but on a memory-constrained system under SATA SSD paging, disk I/O for writing the gateway response could add seconds.
· Whether the Scheduler heartbeat after sandbox termination includes the time spent writing the gateway response and updating task status. If the sandbox hits exactly 60 seconds, then the termination handling takes 5 seconds (paging), then the heartbeat is written at T+65. Combined with the next cloud call (up to 90 seconds), the interval between the pre-sandbox heartbeat and the post-cloud-call heartbeat is 60 + 5 + 90 = 155 seconds, exceeding the 120-second threshold.
· The 60-second cap is enforced by the Job Object, but the Job Object's timer starts when the process is created. The parent's wait call includes both the sandbox execution time and the termination handling time. The 60-second cap doesn't include the termination overhead.

The risk: Legitimate sandbox executions that hit the timeout cap could, when combined with post-termination overhead and a subsequent cloud call, trigger a false-positive stale-scheduler detection. The margin analysis (90s ceiling + 30s margin = 120s) didn't account for sandbox termination overhead, gateway response writing, and task status updates on a paging system.

---

OBJECTION 8 — Classifier Calibration "Model Profile Changes" Trigger Is a Runtime Check with No Monitoring

What v1.8 specifies (Section 10):
"Model profile changes → Calibration invalidated; rerun required."

What's unstated:
What constitutes a "model profile change." The local model is qwen3:4b served via Ollama. Does a model profile change mean:

· Ollama pulls an updated version of the qwen3:4b model?
· The human operator changes the Ollama model file?
· The model's quantization changes?
· The model file's checksum changes?

And critically: who or what detects this change and triggers recalibration? The architecture has no component that monitors the model file for changes. The classification happens at runtime inside the local model's inference path. If Ollama silently updates the model (which it might, depending on how the model is pinned), the calibration silently invalidates, and the security boundary degrades.

The gap:
A calibration invalidation rule without a detection mechanism is a paper protection. The system needs either:

· A model checksum stored at calibration time and verified at boot.
· A human-triggered recalibration command (there's already operator_control_run_classifier_validation, but it's manual).
· Or acceptance that calibration is static and model changes require explicit operator action, with a boot check that warns if the model file has changed.

None of these are specified. The calibration section is otherwise rigorous—this "model profile changes" clause stands out as an unoperationalized requirement.

---

OBJECTION 9 — The Enlarged Module Map Exceeds Phase 1 Feasibility

What v1.8's module map specifies:

· app/: 4 modules
· core/: 11 modules
· agents/: 4 modules
· gateways/: 4 modules
· security/: 4 modules plus a test set file
· persistence/: 3 modules
· policy/role_manifests/: 12+ manifest files
· tests/: 12 named tests plus unstated additional tests

That's roughly 30 Python modules, plus 12+ JSON manifests, plus a full SQL schema, plus a calibration test set, all to be implemented by the human operator following Kimi's execution plan.

The Legacy Reference reality:
The ToonTown build took 9 phases to reach a functional state. The AXIOM architecture specifies more components with stricter boundaries. The human operator is a single person with a Celeron N4500 laptop. The Panel Charter says Kimi "produces step-by-step specifications the human operator can execute." The scale of this module map implies weeks of implementation work. During that time, no autonomous system is running—the operator is hand-building infrastructure.

The unstated assumption:
That Phase 1 implementation is achievable in a reasonable number of operator sessions before fatigue, errors, or scope creep set in. The Core Values say "build simple, prove the concept, iterate into complexity." The current module count suggests complexity has been iterated into the initial build. If Kimi consolidates modules (as the panel charter allows), the implementation plan might reduce this. But the architecture as specified is the full blueprint, and its size is a risk factor the panel should acknowledge.

---

OBJECTION 10 — The Provider-Usage Orphan Recovery Estimates Tokens Without Provider Confirmation, Creating Silent Budget Drift

What v1.8 specifies (Section 13):
For orphaned provider calls (status = 'started' from non-current sessions), recovery sets charged_input_estimate = estimated_input_tokens and charged_output_estimate = estimated_output_tokens. The rationale is "conservative budget rule: unknown dispatched call = count estimated usage against budget."

What this assumes:
That estimated_input_tokens and estimated_output_tokens are populated at dispatch time. The provider_usage row lifecycle (v1.7 Section 4) says the row is inserted with status = started and estimated_input_tokens and estimated_output_tokens are part of the initial INSERT. So the estimates are available.

But the real-world behavior:
The orphaned call might have been:

1. Dispatched but never reached the provider (network failure before connection) → no tokens consumed.
2. Dispatched, provider processed it, response was in flight when process crashed → tokens consumed.
3. Dispatched, provider rejected it immediately (rate limit, auth error) → no tokens consumed.

Charging estimated tokens in all cases is conservative for budget safety but means the system's free-tier usage tracking permanently overestimates consumption. Over many crash-recovery cycles (and the Legacy Reference documents multiple stability issues), the budget ledger accumulates phantom usage. The actuals_unavailable = true flag records that these are estimates, but the budget enforcement logic presumably reads charged_input_estimate and charged_output_estimate as the values to count against limits. Over time, the system might refuse to dispatch tasks because its phantom budget consumption says the free tier is exhausted.

The gap:
There's no provision for later reconciliation. If the provider's usage dashboard (accessible to the human operator via web browser) shows actual consumption is lower than the AXIOM ledger, there's no reconcile_provider_usage mechanism to correct the drift. The conservative rule is correct for immediate safety but accumulates permanent error.

---

Summary of Objections

# Category Core Issue
1 Interaction Failure Scheduler heartbeat last_tick_at semantics are ambiguous; legitimate sequential bounded operations can accumulate >120s without a scheduler hang, triggering false-positive stale detection
2 Missing Artifact Calibration requires a 120-sample injection test set that no panel role is assigned to create; security boundary depends on an artifact without a creator
3 Specification Debt TaskCommitter Step 4 "validate every child task" has no bounded scope; semantic validation responsibility across the chain has a potential gap
4 Operational Failure Supervisor liveness is coupled to the same hardware as the scheduler; whole-system paging/freeze prevents Telegram alert and leaves operator with silent dead bot
5 Security Surface Per-command operator control manifests blur the line between documentation and enforcement; if enforced, they create a secondary authorization path around the capability token
6 Feasibility Gap Cloud-call token budget pre-dispatch check requires a token-counting mechanism not specified; manifest estimates are insufficient for actual dispatch-time token counts
7 Interaction Failure Sandbox timeout termination overhead + subsequent cloud call can exceed the 120s heartbeat threshold; margin analysis didn't account for post-termination processing time
8 Unoperationalized Requirement Classifier calibration invalidation on "model profile changes" has no detection mechanism; calibration can silently invalidate
9 Scope Risk Module count (~30 Python files + manifests + schema + test set) may exceed reasonable Phase 1 implementation scope on a single-operator constrained build
10 Budget Drift Orphan provider-call recovery permanently charges estimated tokens without reconciliation path; phantom consumption accumulates over crash-recovery cycles

None of these are bare assertions. Each cites specific sections of v1.8 or v1.8.1 and identifies a specific interaction, gap, or assumption that could cause failure on the target hardware or during the build process. I await the Research Arbiter's factual verification and the Constraints Reviewer's feasibility assessment.