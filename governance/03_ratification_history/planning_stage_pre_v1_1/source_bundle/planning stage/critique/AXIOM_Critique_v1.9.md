I've read v1.9 in full. The document resolves many prior issues directly and transparently—heartbeat semantics, sandbox wall-clock enforcement, token counting, and the MVP split are genuine improvements. But the increased specificity also reveals new role-boundary, security, and operational concerns. My objections follow.

---

OBJECTION 1 — Calibration Test Set Authorship Violates My Panel Charter Boundaries

What v1.9 specifies (Section 5):
"Primary author: DeepSeek V4 — Adversarial Critic."

What the Panel Charter says about my role:
"Responsibilities: Challenge every proposal that reaches the panel. Identify failure modes, edge cases, and unstated assumptions. Stress-test security claims and trust boundaries. Boundaries: Does not originate design proposals."

The problem:
A 120-sample classifier calibration test set is not an adversarial critique. It is a design artifact that defines the security acceptance envelope of the PlanInjectionScanner. The test set determines what the system considers an injection, what confidence thresholds mean, and what attack vectors are defended against. Authoring it is originating a design proposal—specifically, proposing what constitutes a security-passing classifier behavior. That is design work, not adversarial review.

Practical consequence: If I author the test set, I am both the author of a security boundary definition and the critic who challenges architectures that depend on it. When a future proposal relies on the calibration being adequate, I cannot independently challenge that reliance—I built the thing being relied on. This is a structural conflict of interest that undermines the panel's separation of duties.

The Charter's boundaries exist for this exact reason. The Architect proposes, the Critic challenges. If the Critic builds security artifacts, who challenges the Critic's work? The proposal says Gemini and Claude will review, but review is not adversarial stress-testing. The panel loses its independent adversarial voice on the single most important security component in Phase 1.

If the panel insists I author it, the Charter should record an explicit temporary boundary exception with rationale. I will do the work if directed, but the panel must acknowledge that it is operating outside the Charter and that my subsequent critiques of classifier-dependent architecture will carry an authorship bias.

---

OBJECTION 2 — Mid-Session Model Replacement Is a Silent Security Degradation Vector

What v1.9 specifies (Section 9):
Model profile fingerprint is verified at boot. If fingerprint mismatches, safe-pass is disabled. Calibration is tied to the fingerprint.

What is not specified:
Any mid-session re-check of the model fingerprint.

The attack scenario:

1. System boots. Fingerprint matches. Calibration is valid. Safe-pass is enabled.
2. Autonomous operation begins. The local classifier is actively making safe-pass decisions on plan artifacts.
3. An attacker (or compromised sandbox process that escaped filesystem restrictions—unlikely but not impossible, or the human operator acting under incorrect instructions) replaces the qwen3:4b model file in Ollama's models directory with a poisoned version. The poisoned model always returns safe_data with high confidence for any input.
4. The system continues operating. PlanInjectionScanner uses the poisoned classifier. Injected plans pass through.
5. The fingerprint mismatch is not detected until next boot—potentially hours or days later.

Why this matters:
The Core Values require security baked in, not bolted on. The classifier is a security boundary. Security boundaries require runtime integrity verification, not just boot-time checks. A model file replacement during a long-running autonomous session is a low-probability but high-impact threat. The architecture acknowledges model profile changes but only detects them at boot.

The gap can be partially mitigated by periodic fingerprint re-checking (e.g., every N scheduler ticks, or before any safe-pass decision). The proposal doesn't require this, and the panel should decide whether the threat is in scope for Phase 1 or explicitly deferred with rationale.

---

OBJECTION 3 — Keepalive Mitigation Transfers Failure-Detection Burden to the Operator, Contradicting User Experience Goals

What v1.9 specifies (Section 11):
Telegram keepalive sent every 15 minutes. Operator rule: if no keepalive or status response for 30 minutes, operator must physically check the laptop.

The operational reality:
The AXIOM system is designed for a human operator who sends goals via mobile Telegram and checks back later. That operator is not staring at the Telegram chat waiting for keepalive messages. They might send a goal, put the phone down, and return hours later. If the system hangs 10 minutes into operation, the keepalive stops. Thirty minutes after the last keepalive, the operator should check the laptop—but they're not watching. They return 3 hours later to find the system silently dead with no notification.

The contradiction:
The architecture acknowledges that a whole-system hang "cannot be solved completely inside the same process on the same machine." This is accurate. But the mitigation—operator-side keepalive monitoring—assumes the operator is continuously attentive to a chat window for a 30-minute timer, which contradicts the asynchronous, fire-and-forget interaction model the system is built around.

What actually happens in practice:
The operator sends a goal at 9:00. They check back at 11:30. They see the last keepalive was 9:12. They have no idea whether the task completed, partially completed, or hung. The 30-minute rule was not followed because the operator wasn't present to follow it. The Laptop Check is a retrospective diagnostic, not a real-time recovery.

This is not an architectural defect so much as an honesty gap. The proposal should state plainly: "During whole-system hangs, the operator will not receive notification and may not discover the failure until their next check-in. This is an accepted limitation of single-machine operation." Pretending the 30-minute rule provides real-time protection is misleading.

---

OBJECTION 4 — Manual Provider Reconciliation Introduces Operator Accounting Work with No Error-Proofing

What v1.9 specifies (Section 10):
/reconcile_provider_usage requires the operator to manually copy provider dashboard totals, enter them via Telegram, and the system adjusts the budget ledger.

The Legacy Reference reality:
The human operator's role is execution—reading proposals, writing files, running tests, reporting results. Manual token accounting across multiple cloud providers (Cerebras, Groq, OpenRouter, SambaNova) is not execution. It's financial reconciliation. Each provider has a different dashboard, different reporting formats, different date-range controls. The operator must log into each, extract usage data, and transcribe it into a Telegram chat.

Failure modes:

· Transposition errors: operator copies 123456 as 123465.
· Date-range mismatch: AXIOM's budget window doesn't align with the provider's dashboard reporting period.
· Provider dashboard unavailability: Cerebras free-tier dashboard might not expose granular usage. The Legacy Reference notes Groq limits were discovered by exhaustion, not dashboard monitoring.
· Multiple providers: the operator must reconcile Cerebras, Groq, OpenRouter, and SambaNova separately. Each /reconcile command must be scoped to one provider. Four manual entries per reconciliation cycle.

The architectural implication:
The budget ledger's accuracy depends on error-prone manual data entry. A single significant entry error could cause the system to falsely believe it has exhausted its free-tier budget and disable cloud calls, or conversely, to over-consume and hit provider rate limits during autonomous operation. The Core Values emphasize trustworthiness and verifiability. A manual reconciliation process with no validation of operator-entered data (e.g., sanity-checking that reported tokens are within plausible range of system's own estimates) is a weak link.

Suggested minimum: The reconciliation handler should validate operator-reported totals against AXIOM's own estimated totals for the same period and flag discrepancies exceeding, say, ±50% for confirmation. The proposal doesn't include this.

---

OBJECTION 5 — Conservative Token Estimation May Cripple Legitimate Large-Context Tasks

What v1.9 specifies (Section 8):
Default token estimation fallback: ceil(character_count / 3). This is intentionally conservative. The dispatch gate requires actual_dispatch_estimate * 2.0 <= manifest_budget.max_estimated_input_tokens. If the estimate exceeds the manifest budget, the task is blocked, rebuilt with smaller context, or escalated to human.

The interaction with memory retrieval:
The Task Planner assigns a max_estimated_input_tokens to a task. The Context Builder includes retrieved memory chunks in the final prompt. Memory retrieval is dynamic—it depends on what's in the memory database at runtime. The Task Planner cannot precisely predict the token size of retrieved memories.

Scenario:

· Task Planner creates a research task with max_estimated_input_tokens = 2000.
· At dispatch time, Context Builder retrieves relevant memories that, combined with the task payload and system prompt, produce a prompt of ~1200 characters.
· Using ceil(char_count / 3), the token estimate is 400 tokens.
· The dispatch gate checks: 400 * 2.0 <= 2000 → 800 <= 2000 → passes. Good.

But alternative scenario:

· Same manifest budget of 2000.
· Context Builder retrieves extensive relevant memories. Combined prompt is ~3500 characters.
· Token estimate: ceil(3500 / 3) = 1167 tokens.
· Gate check: 1167 * 2.0 <= 2000 → 2334 <= 2000 → fails.

The task is blocked—not because the actual token count would exceed budget (1167 is well under 2000), but because the 2× safety margin on a conservative estimator produced a phantom overage. The system either strips retrieved memories (losing relevant context) or escalates to the human (who now must manually judge token budgets).

The problem: The 2× margin was designed to prevent underestimation. Combined with an already-conservative estimator, it double-penalizes context size. The effective token limit for a 2000-token manifest budget is ~667 actual tokens (2000 / 2 = 1000, then divided further by the estimator's conservatism). The system may frequently block tasks that are genuinely within budget, reducing autonomous capability.

This is a parameter tuning issue, not a design flaw, but parameter tuning can't happen until the system is running. The MVP will operate with this double-conservatism and may produce excessive blocks. The panel should acknowledge this and consider whether the 2× margin should be reduced when a tokenizer (rather than character estimation) is used, or whether the character divisor should be 3.5 or 4 when combined with the 2× safety margin.

---

OBJECTION 6 — Manifest File Integrity Is Not Verified at Runtime

What v1.9 specifies:
Operator-control manifests are enforced through a 7-layer authorization stack. Per-command manifests are JSON files on disk in policy/operator_control_manifests/. ManifestBinder binds the appropriate manifest. If the manifest is missing or mismatched, the command is rejected—which is safe.

What's not specified:
Integrity verification of the manifest files themselves. If a manifest file is corrupted on disk (partial write, filesystem error, accidental human edit), ManifestBinder might parse it and produce a degraded permission set. For example, cancel_current_chain.json might lose its tasks.cancel_requested write field due to JSON truncation. The command appears to succeed (no manifest mismatch error—the file exists and matches the command type) but the bound manifest silently omits a critical permission. The operator's cancel command is accepted but doesn't actually authorize cancellation.

This applies to all role manifests, not just operator-control. A corrupted tool_executor_sandbox_execute.json could silently drop sandbox_policy.allow_sandbox: true, causing sandbox tasks to fail with permission errors that are logged as policy blocks, not manifest corruption.

The gap: No manifest checksum or hash verification at load time. No boot-time integrity scan of the policy/ directory. The system trusts that files on disk are exactly as written by the Chief Architect and human operator. On a single-machine system with a single operator, the risk of malicious tampering is low, but the risk of accidental corruption or incomplete writes during implementation is real.

---

OBJECTION 7 — The Result Verifier Checkpoint Cloud Call Adds Unaccounted Latency to the Deterministic Chain

What v1.9 cross-references:

· Section 6 assigns semantic consistency to "Result Verifier checkpoint mode."
· The deterministic chain (implied from prior versions) is: PlanInjectionScanner → Result Verifier checkpoint mode → TaskCommitter.
· Section 1.2 binding: "Cloud models for cognitive work." Section 8 specifies per-provider-call timeouts of 30–90 seconds.

What's not accounted for:
The Result Verifier in checkpoint mode is performing semantic consistency checks: "Child task matches parent goal," "Tool assignment fits task intent," "Acceptance criteria are testable and relevant." These are cognitive operations requiring a cloud model call. That cloud call is subject to the 30–90 second timeout and the cascade fallback logic.

This means the deterministic chain includes a blocking cloud call:

1. Goal Planner produces plan (cloud call, up to 90s)
2. PlanInjectionScanner runs (deterministic + local classifier)
3. Checkpoint verification (cloud call, up to 90s)
4. TaskCommitter (deterministic, fast)

A single goal can now consume up to 180 seconds of cloud-call time just in planning and verification, before any subtask executes. The heartbeat freshness accounting handles this (heartbeat before/after each cloud call), but the human operator sees a 3-minute silence between sending a goal and seeing the first subtask start. The Telegram keepalive won't fire during this period if it coincides with a blocking operation (the keepalive is on a separate thread, so it's fine, but the operator's /status query would queue behind the current task).

The unstated assumption: That the human operator will tolerate multi-minute response latency for goal planning. The Legacy Reference's Phase 9 acceptance testing worked with direct model calls; the difference here is the accumulated latency of multiple serial cloud calls in the chain.

---

OBJECTION 8 — Combined Sandbox and Cloud-Call Overhead Risks False-Positive Stale Detection Despite Heartbeat Ordering

What v1.9 specifies (Section 4):
Heartbeat ordering requirement: post-sandbox heartbeat must complete before any subsequent cloud call. Max sandbox overhead: 60s execution + 10s termination = 70s. Max cloud call: 90s. Freshness threshold: 120s. The logic is that only one blocking operation can occur between heartbeats, so the max gap is 90s (cloud call) or 70s (sandbox) + margin.

The edge case:
The heartbeat write itself is a SQLite operation. On the Celeron N4500 with SATA SSD and 2.0–2.3 GB RAM headroom, SQLite writes are normally fast (milliseconds). But if the system is under memory pressure and the SQLite database has grown significantly (as it will during a long autonomous session with many tasks, events, and memory items), a heartbeat write could trigger page cache eviction and SATA SSD paging. The Constraints Register explicitly warns that paging degrades performance severely.

If the heartbeat write takes 5 seconds due to paging, and the subsequent cloud call takes exactly the 90s ceiling, and the cloud-call-response heartbeat also takes 5 seconds, the interval between the pre-cloud-call heartbeat and the post-cloud-call heartbeat is at most ~100 seconds (5 + 90). That's under 120. But combine a worst case: pre-sandbox heartbeat takes 5s, sandbox takes 60s, termination overhead takes 10s, post-sandbox heartbeat takes 8s (paging worse now), then a cloud call is dispatched: pre-cloud heartbeat takes 4s, cloud call takes 90s, post-cloud heartbeat takes 6s. The total from pre-sandbox to post-cloud heartbeat: 5+60+10+8+4+90+6 = 183 seconds. The supervisor sees last_freshness_at from the pre-sandbox heartbeat and declares the scheduler stale at 120s. But the scheduler is not hung—it's been continuously doing work and writing heartbeats. The problem is the heartbeat writes between sandbox and cloud call completed, but last_freshness_at was updated at the post-sandbox heartbeat. Wait, the proposal says "heartbeat after sandbox termination handling" updates last_freshness_at. So the supervisor should see that update and reset its timer. The gap from post-sandbox heartbeat (T+83) to post-cloud heartbeat (T+183) is 100 seconds, which includes the cloud call (90s) + some heartbeat overhead (10s). 100 seconds is under 120s. So it's okay if the post-sandbox heartbeat actually commits before the cloud call starts.

The real risk is if the SQLite write for the post-sandbox heartbeat is delayed by paging and takes, say, 15 seconds. Then the gap from the pre-sandbox heartbeat (which was written at T+5) to the post-sandbox heartbeat (which commits at T+5+60+10+15 = T+90) is 85 seconds. Then the cloud call starts, and the pre-cloud heartbeat is written immediately... wait, the ordering requires a heartbeat before the cloud call too. So the sequence is: pre-sandbox (T+5), sandbox (T+5 to T+65), post-sandbox heartbeat attempts to write at T+65 but takes until T+80 due to paging. At T+80, last_freshness_at is updated. Then pre-cloud heartbeat writes at T+80 (fast, say 1s), last_freshness_at updated to T+81. Cloud call runs T+81 to T+171. Post-cloud heartbeat writes at T+171. The longest gap without a heartbeat update is the cloud call itself: T+81 to T+171 = 90 seconds. That's under 120. The paging delays happen between the heartbeat writes, but the heartbeat writes still happen.

I withdraw this objection as a false-positive risk per the updated heartbeat semantics. The freshness update at each heartbeat boundary adequately segments the delays. However, the human-perceived latency of all these serial operations compounded by paging remains an operational concern (a multi-minute task could take tens of minutes under paging).

---

OBJECTION 9 — No End-to-End Acceptance Test Exists for a Complete Human Goal

What v1.9 lists as tests:
12 unit/integration tests covering heartbeat, sandbox, calibration, operator control, token dispatch, etc. These test individual mechanisms.

What is not tested:
A complete end-to-end chain: human sends a goal → Goal Planner produces plan → PlanInjectionScanner scans → Result Verifier checks → TaskCommitter commits → Task Planner creates subtasks → Tool Executor executes → Result Verifier verifies → Scheduler updates status → Telegram reports completion.

The Legacy Reference documents Phase 9 acceptance testing that verified the full system against specific criteria. v1.9 has no equivalent. The architecture has grown significantly in complexity. A well-functioning PlanInjectionScanner, a perfectly calibrated classifier, and an atomic TaskCommitter can all pass their unit tests but fail when integrated because of an unanticipated interaction (e.g., the Result Verifier's context bundle doesn't include the risk_class field the scanner wrote on the plan artifact).

The Core Values require "build simple, prove the concept, iterate into complexity." Proving the concept means demonstrating that a goal flows from Telegram input to verified completion. Unit tests prove components; an integration/acceptance test proves the architecture. The proposal should specify at least one end-to-end acceptance criterion for MVP, even if it's a trivial goal like "summarize the AXIOM Core Values from memory."

---

Summary of Objections

# Category Core Issue
1 Role Boundary Calibration test set authorship violates Adversarial Critic Charter boundary against originating design proposals; creates conflict of interest
2 Security Gap Model fingerprint checked only at boot; mid-session model replacement would not be detected until restart
3 Honesty Gap 30-minute keepalive rule assumes continuous operator attention, contradicting the fire-and-forget interaction model
4 Operational Risk Manual provider reconciliation introduces error-prone data entry; no validation of operator-reported totals against system estimates
5 Capability Risk Conservative token estimator (÷3) combined with 2× safety margin double-penalizes context size, likely causing excessive blocks
6 Integrity Gap Manifest files on disk have no checksum or integrity verification; corruption could silently degrade permissions
7 Latency Concern Result Verifier checkpoint mode adds second cloud call to deterministic chain; goal-to-first-subtask latency up to 180s
8 (Withdrawn) Heartbeat segmentation resolved this; paging delays don't cause false-positive staleness under v1.9 semantics
9 Testing Gap No end-to-end acceptance test specified; component unit tests don't validate full goal-flow integration.