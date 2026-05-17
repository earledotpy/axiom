I’ve read the full v1.1 proposal and the addendum. As Adversarial Critic, I’m required to challenge every proposal that reaches me, with supporting reasoning. Below are my objections—organized by severity, not volume. Each identifies a specific failure mode, edge case, unstated assumption, or security weakness. I’m not offering architectural alternatives; that’s the Architect’s job.

---

OBJECTION 1 — Verifier-Induced Latency Spiral (Failure Mode)

What the proposal says:
The Result Verifier runs after every state-changing Tool Executor action. The verifier may use the cloud cascade. The scheduler is strictly sequential.

What will happen under real work:
A single human goal will decompose into multiple subtasks. Each subtask may involve: Task Planner → Tool Executor → Result Verifier → possibly retry. If the Tool Executor makes a state change and the Result Verifier requires cloud cognition to verify it, you’re looking at a minimum of two cloud round-trips per state-changing action—more if the verifier fails and triggers a retry loop. Multiply by the number of subtasks in a plan. Add the Goal Planner’s initial cloud call and the final verification pass. You can easily stack 8–15 sequential cloud calls for one human goal.

Why this is a failure mode, not just a performance concern:
The Constraints Register gives ~2.0–2.3 GB runtime headroom and explicitly warns that SATA SSD paging will degrade performance severely if RAM is exhausted. Long-running sessions with many queued tasks mean the SQLite database grows, memory structures accumulate, and the process sits in memory for extended periods. A task that takes 15 cloud round-trips to complete is not just slow—it’s holding the scheduler hostage. No other task advances. The human operator on Telegram sees silence during the entire chain. If the human sends a follow-up message, it sits in the queue behind the current task. If the current task is in a cloud retry loop, that follow-up is blocked indefinitely.

What the proposal assumes and doesn’t verify:

· That cloud cascade latency is consistently low enough for serial verification to be tolerable.
· That the human operator will accept arbitrary response latency without intervention.
· That the memory footprint of the scheduler + queue + context builder + gateways stays static during long-running sequential chains (it won’t—accumulated state, open handles, and un-vacuumed SQLite will grow).

The proposal does not specify:

· A maximum number of verifier retries before escalation.
· A timeout for any single cloud call.
· A mechanism for the human to preempt, cancel, or check status of a running chain from Telegram.
· A memory budget for the scheduler process over time.

---

OBJECTION 2 — Sandbox Isolation Depends on an Unverified Mechanism (Unstated Assumption / Critical Dependency)

What the proposal says:
“Commit to Windows Job Objects + restricted Windows token via pywin32. This is the named mechanism for sandbox isolation. It is not deferred.”
It then immediately says: “This mechanism still requires Gemini factual verification before implementation.”

What this means in practice:
The entire Core Value 6 enforcement—no direct connection between sandbox and network—rests on a single technical claim that has not been verified on the target hardware. If Gemini’s factual review finds that pywin32 restricted tokens on Windows 11 Home (which the Celeron N4500 laptop likely runs) do not actually provide network isolation for subprocesses, or that Job Objects cannot enforce per-process network deny rules without Group Policy that doesn’t exist on a standalone laptop, then the sandbox mechanism collapses.

The proposal contains no fallback:
There is no Plan B sandbox mechanism. There is no acknowledgment that if Windows Job Objects + restricted tokens fail factual review, the project has no sandbox isolation path in Phase 1. Core Value 6 cannot be satisfied. Code execution would need to be disabled entirely, reducing the Tool Executor to read-only operations. That is a single-point-of-failure dependency on an external factual determination.

What the proposal should have addressed but didn’t:

· What is the fallback mechanism if Gemini rules the pywin32 approach insufficient?
· Who verifies the sandbox tests on the actual target hardware, and what is the pass/fail threshold for proceeding?
· What happens to the architecture if code execution must be removed from Phase 1 scope?

---

OBJECTION 3 — Resource Estimation Is Undefined but Gates Execution (Edge Case / Unstated Assumption)

What the proposal says:
The Execution Approval Gate requires: “Resource estimate: Task does not exceed Phase 1 RAM/API policy.”

The proposal does not say:

· Who produces the resource estimate for a given task.
· What the estimate is based on (token count? tool type? historical data?).
· How the estimate is validated before the task is approved.
· What happens when the estimate is wrong and the task exceeds budget at runtime.

If the Goal Planner or Task Planner provides the estimate:
You are asking a cloud model to estimate resource consumption of a task it just designed. Cloud models routinely miscount tokens, misunderstand their own context window constraints, and cannot introspect into local RAM usage. The estimate will be synthetic—a generated number, not a measured one.

If the estimate is wrong at runtime:
The task has already been approved. It runs. It exceeds the RAM budget. The system pages to SATA SSD. The Constraints Register explicitly warns that this “degrades performance severely.” This is not a theoretical edge case—it’s the direct consequence of an unvalidated gating criterion.

What’s missing:

· A deterministic resource estimator based on tool type and known payload bounds, not model-generated guesses.
· A runtime enforcement mechanism that kills a task if it exceeds its approved resource budget, rather than letting it degrade the whole system.
· Integration with the sandbox memory limit and the provider budget policy in the manifest—the manifest has budget fields, but the approval gate doesn’t explain how it reads or enforces them at decision time.

---

OBJECTION 4 — The Perceived “Defense in Depth” Is Architecture Theater (Security Weakness)

What the proposal says:
The Permission Engine enforces manifests at the Scheduler. Then: “The Tool Gateway performs a second check. This prevents a bug in the Scheduler from becoming unrestricted tool access.”

What’s assumed but not stated:
That the Tool Gateway’s permission check implementation is independent enough from the Scheduler’s Permission Engine that a bug in one won’t replicate in the other.

What will actually happen in Phase 1 implementation:
The Scheduler and all four Tool Gateways live in the same Python process. The Policy Engine and Permission Engine share one implementation file: core/permissions.py. The Tool Gateway’s “second check” will almost certainly call the same PermissionEngine.check() method, or a thin wrapper around it. If PermissionEngine.check() has a logic error—say, it mishandles manifest expiry, or a forbidden_tools list isn’t checked when allowed_tools is non-empty—that error exists in both enforcement points. You have not added defense in depth. You have added the same defense twice at different call sites.

What would make this real defense in depth:

· The Tool Gateway check uses a different code path, written to be minimal and verifiable, that doesn’t share logic with the Policy/Permission Engine.
· Or: the Tool Gateway check is structural (e.g., OS-level token restrictions on the gateway process itself) rather than another Python function call.
· The proposal claims neither.

Risk: A single permission bug allows a Tool Executor to call a tool it shouldn’t, and both enforcement points miss it identically. The Core Value 3 requirement—explicit, enforced tool access—is satisfied only on paper.

---

OBJECTION 5 — Watchdogs Run Inside the Process They’re Watching (Failure Mode)

What the proposal says:
“No separate watchdog process in Phase 1.” Both the startup watchdog and the scheduler-loop watchdog run inside session_controller.py and scheduler.py respectively.

Failure mode:
The scheduler calls sandbox_gateway.execute(), which subprocess-launches sandboxed code with CPU and memory limits. If the subprocess behaves badly in a way that blocks the parent—say, it fills a pipe, or the Job Object termination doesn’t fire correctly, or the subprocess enters an uninterruptible I/O state against the temporary working directory on the SATA SSD—the entire Python process blocks. The scheduler-loop watchdog never fires because the interpreter isn’t advancing. The startup watchdog is irrelevant because the session is already started. The system is hung with no recovery mechanism.

The proposal says the scheduler-loop watchdog checks:

· “running task exceeds lease timeout”
· “Sandbox process exceeds limit → Terminate process, write security event”

The watchdog cannot enforce either check if it cannot run. A lease timeout is meaningless if the scheduler thread is blocked on a subprocess call. A sandbox limit can’t be enforced if the enforcement code never executes.

What’s missing:

· An explicit acknowledgment that in-process watchdogs cannot recover from full-process hangs.
· A plan for what the human operator should do when the bot stops responding (restart batch file? check logs?).
· A Phase 2 path to an external keepalive mechanism (even a simple batch file wrapper that restarts the Python process if the Telegram bot stops responding for N seconds).

---

OBJECTION 6 — Plan Checkpoint Criteria Miss Injection Scanning (Security Gap)

What the proposal says:
The sanitization map (Section 5) lists “Overseer-generated plan” as going through: “Plan Checkpoint + schema validation + injection scan.”
The Plan Checkpoint criteria (Section 11) lists 10 items: goal preservation, constraint compliance, role separation, queue compliance, acceptance criteria, tool scope, security boundary, complexity discipline, resource estimate, human escalation.

What’s missing from the checkpoint criteria:
Injection scanning. The 10 criteria check for architectural validity. They don’t check whether the proposed plan contains embedded instructions that will be executed by downstream agents when the task tree is committed and task input payloads are populated.

Why this matters:
The Legacy Reference explicitly identifies prompt injection via the task queue as a real threat and records pre-rebuild consensus that sanitization must occur at write time. The plan checkpoint is the write-time gate for Goal Planner output. If injection scanning isn’t in the checkpoint criteria, a plan that passes all 10 checks could still contain injected instructions in task descriptions, acceptance criteria, or parameter values. Those injected instructions become task input payloads for Task Planners and Tool Executors. The downstream sanitization paths (tool output, memory write) don’t catch injection that’s already embedded in the task itself.

The proposal claims “injection scan” in the sanitization map but doesn’t operationalize it in the checkpoint. That’s a gap between stated intent and specified mechanism.

---

OBJECTION 7 — Write Boundary Claim Contradicts Memory Gateway Permission (Internal Contradiction)

What the proposal says about write boundaries (Section 8):
Tool Executor → May write: “Own result/error fields only” → Cannot read/write: “Full queue, parent/sibling context, manifest expansion.”

What the proposal says about drone manifests (Section 6):
A Tool Executor with memory.write_candidate permission can write to the Memory Gateway. The manifest schema includes memory_policy.allow_memory_write.

The contradiction:
A Tool Executor writing a memory item via the Memory Gateway is writing to the memory_items table—not its own tasks.output_payload or tasks.error_payload field. That violates the “own result/error fields only” boundary stated in Section 8. If memory writes are considered part of “own result,” then the boundary is poorly defined; “own result fields” should be read as “any table the manifest permits,” which collapses the entire concept of bounded write scopes. If memory writes are not part of own result fields, then the manifest grants a permission that the read/write boundary table says the role cannot exercise.

Why this matters:
Core Value 3 requires: “An agent cannot instruct another agent directly. Coordination happens through authenticated, logged shared state only.” A memory write is shared state. If a Tool Executor can write to shared memory, the write boundary is more permissive than the table implies. The proposal needs to reconcile the boundary table with the manifest-based memory write path, or the boundary table is misleading and should not be used as a design reference by implementers.

---

OBJECTION 8 — Task Class Determination Is Undefined (Unstated Assumption)

What the proposal says (Addendum, Clarification 2):
There are four task classes: Goal-planning, Task-planning, Tool-execution, Verification. Each follows a different branched lifecycle.

What the proposal doesn’t say:
Who or what determines the task class when a task is created, and where that classification is stored.

If the Ingress Sanitizer determines it:
The Ingress Sanitizer is described as a “command parser + local classifier/sanitizer.” Determining whether an incoming message requires a Goal Planner, a Task Planner, or a direct Tool Executor is a routing decision that requires understanding the intent and scope of the request. That’s classification work that edges into goal decomposition—which Core Value 2 reserves for cloud models. The proposal doesn’t clarify whether task class routing is local classification (permitted) or goal analysis (cloud only).

If the Session Controller determines it:
The Session Controller’s scope is “config, session table, startup health checks.” Task classification is not in its described responsibilities.

If the task class is stored incorrectly:
A task that should go through a Goal Planner is classified as Tool-execution. It skips planning, skip checkpoint, runs a tool directly with no decomposed plan. The task output is garbage or a side effect that violates Core Values. The system has no mechanism to detect mid-chain that task classification was wrong.

What’s missing:

· A task_class field in the task schema.
· An explicit statement of who sets it and what decision logic they use.
· A verification step that the task class is appropriate before the task advances to approved_for_execution.

---

OBJECTION 9 — Sequential Scheduler + Human Responsiveness (Edge Case / Operational Failure)

What the proposal says:
The scheduler is sequential. The human interface is Telegram. Messages from the human become tasks in the queue.

Scenario:

1. Human sends: “Research the latest on X and summarize.”
2. Goal Planner runs (cloud call, ~10-30s).
3. Plan checkpoint verifier runs (cloud call, ~10-30s).
4. Task Planner runs for subtask 1.
5. Tool Executor runs (network fetch).
6. Result Verifier runs.
7. Task Planner runs for subtask 2… and so on.

During step 2, the human realizes they made a typo: they meant Y, not X. They send: “Wait, I meant Y not X.”

What happens:
The human’s correction is a new Telegram message. It becomes a new task at the bottom of the queue. The current chain continues uninterrupted for several more minutes. The Tool Executor fetches data for X. The Result Verifier verifies X-related output. All of this is wasted work. The human watches the bot ignore their correction. From the human’s perspective, the system appears broken or unresponsive.

The proposal addresses preemption nowhere.
There is no cancel signal, no priority interrupt, no mechanism for the human to say “stop and replace current goal.” The human’s role is execution and reporting, but the architecture gives them no tool to abort a running chain that they know is wrong. The only recourse is to kill the process, which is a crash, not a controlled operation.

---

OBJECTION 10 — No Verification That the Local Model Can Perform the Assigned Classification Task (Unvalidated Assumption)

What the proposal says (Core Value 2 clarification):
The local model classifies content into one of seven labels: safe_data, untrusted_data, embedded_instruction, tool_request, memory_candidate, quarantine, needs_cloud_review.

What’s assumed:
That qwen3:4b (or whatever local model is selected) can perform this classification with sufficient accuracy for a security boundary.

What’s not addressed:

· No accuracy threshold is specified. Is 90% acceptable? 99%? What’s the false negative rate budget for the embedded_instruction label?
· No calibration dataset or test plan exists. How do we know the model doesn’t classify adversarial inputs as safe_data?
· The Legacy Reference identifies prompt injection as an unresolved failure and proposes the local model as the semantic firewall—but that’s a capability claim, not a verified fact. The pre-rebuild research reached consensus that the local model “is the natural semantic firewall” for write-time sanitization, but consensus among AIs is not the same as empirical testing on real injection payloads.
· If the local model is replaced (as the Constraints Register allows), the classification behavior changes. The architecture doesn’t require revalidation of the new model’s classification accuracy.

Risk: The system relies on a local model classifier for a security-critical function with no acceptance criteria for the classifier’s performance. A false negative on embedded_instruction means prompt injection enters the task queue. From there, downstream agents execute it. This is the exact failure mode the Legacy Reference flagged as unresolved.

---

Summary of Objections

# Category Core Issue
1 Failure Mode Verifier-induced cloud call latency spirals; scheduler blocks; human gets silence
2 Critical Dependency Sandbox isolation relies on unverified pywin32 mechanism; no fallback specified
3 Unstated Assumption Resource estimation gates execution but is undefined/unvalidated; wrong estimate = RAM exhaustion
4 Security Weakness Dual enforcement shares code path; defense-in-depth is illusory
5 Failure Mode In-process watchdogs cannot recover from process hangs
6 Security Gap Plan checkpoint criteria omit injection scan despite sanitization map claiming it
7 Contradiction Write boundary table contradicts memory.write manifest permission
8 Unstated Assumption Task class determination is not assigned to any component
9 Operational Failure No preemption mechanism; human corrections are queued behind active chain
10 Unvalidated Assumption Local model classifier accepted as security boundary with no accuracy threshold

None of these objections are bare assertions. Each cites specific sections of the proposal and connects to hard constraints, Core Values, or documented legacy failures. I await the factual review from the Research Arbiter and the feasibility review from the Constraints Reviewer on each of these points.