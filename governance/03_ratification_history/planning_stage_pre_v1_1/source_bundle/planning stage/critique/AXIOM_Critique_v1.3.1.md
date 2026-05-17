I've read v1.3.1 in full. The patch resolves the five flagged coherence issues cleanly, but it introduces new problems, leaves critical security components undefined, and carries forward several unresolved failure modes from earlier versions. Below are my objections.

---

OBJECTION 1 — PlanInjectionScanner Is Security-Critical and Completely Undefined

What the proposal says:
A new component called PlanInjectionScanner appears in the deterministic chain. The Scheduler invokes it after plan artifact creation. It writes a scan verdict. If the scan passes, checkpoint verification proceeds. If it fails, the Scheduler does not create a checkpoint task. A manifest file internal_plan_injection_scan.json is listed in the module map. A test test_plan_injection_scan_owner.py is specified.

What the proposal does not say:

· What PlanInjectionScanner is. Is it a rule-based scanner? A local model classifier? A cloud model check? A regex pass?
· What its detection mechanism is. What injection patterns does it recognize? What is its false negative rate?
· What its verdict schema looks like. Does it return a boolean? Confidence score? Labels?
· Who builds it. It's not in agents/ (so not a role module), not in security/ (where sanitizer.py and classifier_validation.py live), and not in core/. It appears only as a name in the chain and a manifest in policy/role_manifests/.
· Why it has a role manifest at all. The proposal states "deterministic components are not role modules" and "The Scheduler may call deterministic components directly." If PlanInjectionScanner is a deterministic component called directly by the Scheduler, it should not need a role manifest. If it's an internal role invoked through RoleExecutor, it violates the deterministic component pattern stated in F5.

Why this matters:
This component is the sole injection defense between an untrusted cloud model's output (the Goal Planner's proposed plan) and the task queue. The Legacy Reference identifies prompt injection via the task queue as a real unresolved failure and records pre-rebuild consensus that sanitization must happen at write time. The plan checkpoint is the write-time gate for Goal Planner output. If the injection scanner is undefined, the injection defense is a labeled box with no contents.

The proposal effectively defers the entire injection defense design while claiming the architecture is complete enough to proceed to implementation. It is not.

---

OBJECTION 2 — Cooperative Cancellation Leaves the Human Powerless During Cloud Calls

What the proposal says:
"interrupt = prioritized request handling at the next Scheduler tick. It does not mean mid-flight preemption. Phase 1 cancellation remains cooperative."

What this means in operational reality:
The Scheduler runs a tick, selects a Goal Planner task, sets status = running, and calls RoleExecutor, which calls GoalPlanner, which makes a cloud call to Cerebras. The cloud call takes 18 seconds. The Goal Planner streams tokens back. During those 18 seconds, the Scheduler is blocked inside RoleExecutor. No tick occurs. The human sends /cancel_current_chain. The Telegram Gateway creates an operator_control task with priority interrupt and sets cancel_requested = true on the active task. Absolutely nothing happens until the Goal Planner's cloud call returns and the Scheduler resumes its loop.

Worse case: The cloud call times out or hangs. The Constraints Register notes Cerebras is the primary provider. If Cerebras has an outage or rate-limits, the call could block for 30–60 seconds before a timeout fires—if a timeout is even configured. The proposal specifies no cloud call timeout. The Legacy Reference documents Groq daily limit exhaustion during testing; cloud unreliability is not hypothetical.

During this entire window:

· The human's command is acknowledged (it's a Telegram message, the bot receives it) but not acted on.
· The human sees the bot continue processing the wrong goal.
· The human cannot distinguish "my cancel will be processed soon" from "the system ignored me."
· If the human sends multiple cancel commands, they stack as multiple operator_control tasks in the queue.

The proposal's assumption:
That Scheduler ticks are frequent enough that "next tick" feels responsive. With serial cloud calls for planning, checkpoint verification, and result verification, a single chain can spend 30–90 seconds blocked on cloud I/O. "Next tick" can mean "in 90 seconds." That is not a usable interruption model for a human operator on a mobile messaging interface.

---

OBJECTION 3 — Scheduler Is Now a God Module Carrying Single-Point-of-Failure Risk

What the proposal says (F5):
The Scheduler now owns:

· Task selection and prioritization
· Policy engine invocation
· Plan injection scanner invocation
· Checkpoint verification task creation
· Verdict interpretation through StateMachine
· TaskCommitter invocation
· All task status transitions (F1)
· Watchdog invocation
· Cancel request observation and state mutation
· Pause/shutdown state enforcement
· "Scheduler continues sequential task loop"

What was already the Scheduler's responsibility:

· Queue metadata, statuses, manifests, status transitions (from v1.1 Section 8 boundary table)

Combined, the Scheduler is now responsible for:
Approximately 12 distinct responsibilities across task lifecycle, security gating, orchestration, and recovery.

Failure mode:
A bug in any one of these responsibilities can corrupt the task queue, skip security checks, or hang the entire system. The Scheduler runs in the main Python process. There is no separate watchdog process (Objection 5 from v1.1 review, still unresolved). If the Scheduler's code hits an unhandled exception during the deterministic chain—say, TaskCommitter raises because the plan schema is malformed in a way validation didn't catch—the entire loop stops. No tasks advance. The Telegram bot goes silent. The human has no indication of what failed.

The proposal's module map shows:

· core/scheduler.py
· core/watchdog.py
· core/cancellation.py
· core/state_machine.py
· core/policy_engine.py
· core/task_committer.py

All are separate files, but the Scheduler is the sole caller and integrator. The watchdog is called by the Scheduler loop; it cannot watch the Scheduler itself. The architecture has no component that monitors the Scheduler for liveness. A Scheduler crash is unrecoverable without human restart.

---

OBJECTION 4 — Resource Limits Enforcement Is Named but Not Operationalized

What the proposal says:

· core/resource_limits.py appears in the module map.
· The Policy Engine checks "resource limits" and "provider budget."
· Manifest's budget_policy fields include max_model_calls, max_estimated_input_tokens, max_estimated_output_tokens.
· A test test_resource_limits.py is specified.

What is not specified:

· How resource limits are tracked at runtime. Is there a per-task token counter? A session-level API call counter? A RAM monitor?
· Who produces the budget estimate that the Policy Engine evaluates before approval. The proposal doesn't say. If it's the Task Planner or Goal Planner (a cloud model), the estimate is synthetic and unvalidated (Objection 3 from v1.1 review, still unresolved).
· What happens when a task exceeds its budget mid-execution. The sandbox has CPU/memory limits enforced by Job Objects. Cloud model calls have no equivalent runtime kill switch. If a Task Planner is authorized for max_model_calls: 1 but makes 3 calls because the cloud model hallucinates additional calls, who intercepts that? The Model Gateway? The Scheduler? Neither has a specified enforcement mechanism.
· How resource_limits.py relates to provider_usage tracking in the persistence layer. The persistence section mentions a provider_usage table, but resource_limits.py is described nowhere except its filename.

Why this matters:
The Constraints Register gives 2.0–2.3 GB RAM headroom and requires free-tier API access. The Legacy Reference documents that Groq's daily limit was exhausted during testing. Resource overrun is a demonstrated failure mode, not a theoretical one. A resource limits module that exists only as a filename and a test name is not a resource limits mechanism. It's a placeholder.

---

OBJECTION 5 — PlanInjectionScanner's Role Manifest Blurs the Agent/Deterministic Boundary

What the proposal says:

· "deterministic components are not role modules"
· "The Scheduler may call deterministic components directly."
· But the policy manifest directory includes internal_plan_injection_scan.json.

The contradiction:
Role manifests exist to constrain what a role module can do when invoked through RoleExecutor. If PlanInjectionScanner is a deterministic component called directly by the Scheduler, it doesn't go through RoleExecutor, doesn't get a context bundle from ContextBuilder, and shouldn't need a role manifest. If it does need a manifest, it is being treated as a role—meaning it goes through RoleExecutor, gets a context bundle, and is subject to manifest enforcement. The proposal states both things and cannot have both.

If it's a role:
Then it's subject to the same manifest/permission/verification machinery as Goal Planner and Tool Executor. It must be invoked through RoleExecutor. The Scheduler cannot call it directly. The deterministic chain description in F5 is wrong.

If it's a deterministic component:
Then it doesn't need a manifest, doesn't need a file in policy/role_manifests/, and the internal_plan_injection_scan.json file should not exist. Its behavior should be specified directly in code, not constrained by a manifest.

This ambiguity matters because:
It affects whether the injection scanner's behavior is configurable through manifest changes (which could be a security risk if manifests can be modified) or hardcoded in the module (which is safer but less flexible). It also affects the implementation path—Kimi needs to know whether to write a role module or a utility function.

---

OBJECTION 6 — No Specified Recovery for Mid-Deterministic-Chain Failures

What the proposal specifies:
The happy path through the deterministic chain is detailed step by step. Each step has an owner. The chain ends with child tasks inserted at status = created.

What the proposal does not specify:
What happens when any step fails mid-chain.

Specific failure scenarios:

1. PlanInjectionScanner raises an exception. Is the plan artifact quarantined? Does the parent planning task go to failed? Is the human notified?
2. ResultVerifier in checkpoint mode returns verdict = failed. The proposal says the parent task can retry or escalate to needs_human_input. But where is that decision made? The Scheduler? The Policy Engine? What's the retry count limit?
3. TaskCommitter receives a plan that passes checkpoint verification but fails schema validation. This is a contradiction: the checkpoint was supposed to verify the plan. If it still fails schema validation, something is broken. Does the plan get re-quarantined? Does the system alert?
4. ManifestBinder cannot bind a manifest because the plan requests a tool that has no matching manifest template. The task tree is partially committed? The entire commit is rolled back? SQLite supports transactions, but the proposal doesn't mention a transactional boundary around the commit step.
5. TaskCommitter inserts 4 of 7 child tasks successfully, then hits a constraint violation on the 5th (e.g., duplicate task ID). The first 4 tasks are now live in the queue with status = created and no siblings. Partial task trees violate the plan's integrity. The Scheduler might pick up orphaned child tasks.

The proposal's implicit assumption:
That deterministic components don't fail, or that their failure modes are obvious enough to not require specification. The Legacy Reference documents multiple cascading failures from unhandled edge cases. Mid-chain failure in a multi-step task commitment sequence is exactly the kind of edge case that creates corrupt queue state requiring manual database cleanup by the human operator.

---

OBJECTION 7 — Boot and Crash Recovery Logic Is Tested but Not Specified

What the proposal lists as tests:

· test_boot_sequence.py
· test_startup_recovery_rules.py

What the proposal does not contain:
A specification of the boot sequence. A specification of startup recovery rules. These tests reference behavior that isn't described in v1.3.1 (or, to my reading, in any prior version of the architecture proposal).

The closest prior specification is in v1.1:
The startup watchdog runs once at session start and moves tasks based on status. But v1.3.1 has a significantly revised status space (removing approved_for_execution, adding cancelled, adding injection scan statuses). The startup watchdog logic from v1.1 cannot be applied unchanged to the v1.3.1 status space.

What the boot sequence needs to cover and doesn't:

· What order modules initialize in.
· How the database schema is verified or migrated.
· How the Scheduler determines whether it's resuming a prior session or starting fresh.
· How running tasks from a crashed session are handled (the v1.1 startup watchdog covered this, but v1.3.1 doesn't confirm or revise that logic).
· How policy_approved = 1 tasks from a crashed session are handled—since policy_approved is now separate from status.
· How partially-committed task trees from a mid-chain crash (Objection 6) are detected and cleaned up.

A test without a specification is testing an implementation decision, not a design requirement. The architecture proposal should specify recovery behavior; the test verifies it. Here the tests exist but the specification doesn't.

---

OBJECTION 8 — Classifier Validation Is Still Unoperationalized

What v1.3.1 carries forward from earlier versions:

· The local model classifies content into safety labels (safe_data, embedded_instruction, etc.).
· core/classifier_validation.py appears in the module map (moved to security/? Actually it's now security/classifier_validation.py per the module map).
· test_classifier_injection_set.py and test_classifier_validation_runtime_contract.py are specified.

What is still not specified:

· What accuracy threshold the classifier must meet to be trusted as a security boundary.
· What the injection test set contains. Who curates it? How many samples? What attack vectors are covered?
· What happens when classifier_validation_status indicates the classifier is unreliable. Does the system refuse to run? Fall back to cloud classification (which costs API budget)? Run with degraded security?
· How the validation is performed at runtime vs. at build time. The module is in security/, suggesting it runs during operation, but the tests suggest a one-time validation pass.

This was Objection 10 from v1.1 review. The proposal has added a module file and test names but has not added any specification of the validation criteria, threshold, or remediation. The attack surface is unchanged.

---

OBJECTION 9 — Memory Write Candidate Is Unverified Before Promotion

What the proposal says about shared-state writes:
A Tool Executor with memory.write_candidate permission may write to the Memory Gateway. This is in the "allowed Phase 1 shared-state write candidates" whitelist.

What the legacy reference says:
"Duplicate memory entries. Multiple test writes created duplicate records. No deduplication logic existed at insert level. Memory database was in a degraded state at handoff." Pre-rebuild consensus: "Add pre-insertion cosine similarity check to memory writes (~0.92 threshold)."

What v1.3.1 specifies:
A test test_memory_dedup_threshold.py confirms the dedup threshold exists. But the deterministic chain shows no step where memory.write_candidate entries are verified or deduplicated before insertion. The Tool Executor writes to the Memory Gateway. The Memory Gateway presumably applies dedup at insert time. But the Memory Gateway is not part of the deterministic chain F5 describes. It's a gateway called by the Tool Executor during the running state.

The gap:
If a Tool Executor with memory.write_candidate permission writes a memory item that is a near-duplicate, the Memory Gateway should reject it via cosine similarity check. That rejection needs to be surfaced to the Result Verifier. But the Result Verifier checks the task's output_payload against acceptance criteria. If the memory write was the intended output, and the Memory Gateway silently deduplicates (returning "this already exists"), is that a task success or failure? The Tool Executor wrote successfully—the memory just wasn't new. The acceptance criteria need to account for this, and the Result Verifier needs access to the Memory Gateway's response, not just the Tool Executor's output payload.

The architecture doesn't specify how Memory Gateway responses are routed to the Result Verifier for memory.write_candidate actions. The context bundle for verification would need to include the gateway's dedup decision, which means the Context Builder needs to know about gateway-level responses, not just task-level outputs.

---

OBJECTION 10 — operator_control Task Creation Is an Unprotected Path

What the proposal says:
Human sends /cancel_current_chain → operator_control task is created with priority = interrupt → Telegram Gateway sets cancel_requested = true on the active task.

What's not specified:

· Who creates the operator_control task. The Command Parser? The Session Controller? The Telegram Gateway?
· Whether the operator_control task goes through the same ingress sanitization and Policy Engine approval as other tasks. If not, it's a bypass of the execution gate. If yes, the Policy Engine could theoretically block a cancel request, and the human's explicit command is ignored.
· Whether the operator_control manifest can be modified. If the manifest file on disk is corrupted or deleted, does the cancel path break entirely?
· What prevents a compromised Task Planner from generating a task with task_class = operator_control and priority = interrupt. If task class is determined by the component that creates the task, and a Task Planner has task.create equivalent capability via TaskCommitter, the path for creating control tasks needs explicit restriction.

The security boundary:
Human control commands (/cancel, /pause, /resume, /shutdown) must be the exclusive privilege of the human operator via the Telegram Gateway. No agent-generated task should be able to spoof an operator_control task. The architecture doesn't specify how this exclusivity is enforced. The operator_control manifest exists in the manifest directory alongside agent manifests, implying it's just another role—but it shouldn't be. It should be a privileged path that only the Telegram Gateway can initiate.

---

Summary of Objections

# Category Core Issue
1 Security Gap PlanInjectionScanner is a named placeholder with no mechanism, no location, and an ambiguous role/manifest status
2 Operational Failure Cooperative cancellation means up to 90+ seconds of unresponsiveness to human commands during cloud calls
3 Failure Mode Scheduler owns 12+ responsibilities with no external liveness monitor; scheduler crash = silent system death
4 Unvalidated Placeholder Resource limits module and enforcement exist only as filenames and test names; no runtime mechanism specified
5 Contradiction PlanInjectionScanner has a role manifest but is described as a deterministic component called directly by the Scheduler
6 Failure Mode No specified recovery or rollback behavior for failures mid-deterministic-chain; partial task tree commits are possible
7 Missing Specification Boot sequence and startup recovery tests reference behavior not specified in the architecture
8 Unresolved v1.1 Objection Classifier validation still has no accuracy threshold, test set specification, or remediation path
9 Design Gap Memory Gateway dedup responses are not routed to Result Verifier; verification of memory.write_candidate actions is underspecified
10 Security Boundary operator_control task creation path is unspecified; no stated mechanism to prevent agent-spoofed control commands