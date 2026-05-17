I've read v1.10 in full. This is a responsive and careful revision—most of my v1.9 objections are addressed directly, thoughtfully, and without hand-waving. The authorship reassignment (Item 1), mid-session fingerprint check (Item 2), manifest integrity verification (Item 3), end-to-end test (Item 4), tiered token margins (Item 6), and honest keepalive reframing (Item 7) are all genuine improvements.

However, the new specificity introduces several new edge cases and unstated assumptions. My objections follow.

---

OBJECTION 1 — Mid-Session Fingerprint Check Error Handling Is Underspecified

What v1.10 specifies (Item 2):
"Before PlanInjectionScanner applies any rule that would produce decision = passed based on classifier confidence, it calls: ModelFingerprintGuard.verify_current_profile()."

"On mismatch: safe-pass disabled immediately... On match: Safe-pass may proceed."

What is not specified:
What verify_current_profile() does when the Ollama API call fails—timeout, connection refused, HTTP 5xx, malformed response. The guard is making a localhost HTTP request to Ollama's /api/show or equivalent. On a system under memory pressure, localhost calls can time out. On a system where Ollama has crashed (but the Python process survived), the connection is refused. On an Ollama update that changes the API response schema, the digest field might be missing or renamed.

The failure mode:
If the guard treats an API error as anything other than a mismatch, a compromised model can continue to authorize safe-pass decisions. If it treats it as a mismatch, a transient Ollama hiccup can disable safe-pass and quarantine the current artifact unnecessarily. Neither behavior is specified.

The security-critical path is fail-closed: an API error should be treated as a fingerprint mismatch, disabling safe-pass and quarantining/escalating the artifact. The operator should receive an immediate Telegram notification because mid-session loss of fingerprint verification is a security-relevant event. The proposal specifies notification for mismatches implicitly (security event written) but doesn't explicitly require a Telegram alert. A silent security degradation during autonomous operation is a Core Value 1 violation.

Recommended minimum specification:

· verify_current_profile() timeout: 5 seconds.
· On timeout, connection error, or malformed response: treat as mismatch.
· On mismatch or API failure: write security_events.model_fingerprint_verification_failed with failure reason.
· Send immediate Telegram alert: "Classifier safe-pass disabled: model fingerprint verification failed mid-session. Reason: [timeout/connection refused/digest mismatch]. Autonomous execution continues without classifier safe-pass. Operator action may be required."

---

OBJECTION 2 — No Telegram Alert for Mid-Session Fingerprint Mismatch

What v1.10 specifies (Item 2):
On fingerprint mismatch: "safe-pass disabled immediately, security_events.model_fingerprint_mismatch written, session_events.safe_pass_disabled_mid_session written, current artifact → needs_human_input or quarantined according to risk_class."

What is not specified:
A Telegram notification to the operator.

The operational scenario:
The system is running autonomously. The operator sent a goal and put their phone down. Mid-session, the model file changes (operator manually updated Ollama, or a filesystem corruption occurred). The next plan artifact triggers the fingerprint guard, safe-pass is disabled, the current artifact is quarantined. The system continues operating without safe-pass—meaning all subsequent planning artifacts hit the needs_human_input or quarantined path. The task queue fills with blocked tasks. The operator returns hours later to find nothing completed and no explanation in the chat—only in session events they'd have to manually query.

Why this matters:
Mid-session model profile change is a critical security event. It potentially indicates tampering, or at minimum invalidates a security boundary that was verified at boot. The operator should know immediately, not retrospectively. The Telegram Gateway is on a separate thread and can send a message even if the Scheduler is mid-task.

Recommended addition:
On fingerprint mismatch or verification API failure, SessionController (via SupervisorMonitor or directly) must instruct TelegramGateway to send an immediate operator alert with the mismatch reason and the system's current safe-pass status. This does not require a new thread or component—TelegramGateway already has message-sending capability.

---

OBJECTION 3 — Manifest Registration Mode Has No Production Disablement Guard

What v1.10 specifies (Item 3):
"Manifest fingerprints may be registered only during approved implementation/deployment: manifest_registration_mode = true. This mode is not available during autonomous operation."

What is not specified:
How this mode is disabled in production. Is it a configuration flag in a file? An environment variable? A code constant? More importantly, what prevents it from being accidentally or maliciously set to true after deployment?

The failure scenario:
If manifest_registration_mode is a configuration value in a Python file or JSON config that the operator or a compromised sandbox process could modify, an attacker could enable registration mode, replace a manifest file with a malicious version, trigger a reboot or re-registration, and the system would accept the new manifest fingerprint as legitimate. The manifest integrity system that was supposed to protect against corruption becomes a vector for undetected manifest replacement.

Why this matters:
The proposal correctly fingerprints manifests and verifies them at boot. But the registration mode that allows new fingerprints to be recorded is itself a security boundary. It should be enforced by a mechanism that cannot be changed by modifying a config file—e.g., it requires a specific command-line flag passed at process start, or is a compile-time constant, or requires manual database insertion by the operator with a separate tool. The proposal should specify the enforcement mechanism for registration mode, not just state that it exists.

Recommended minimum:
manifest_registration_mode must be a command-line argument (--manifest-registration) to the Python process, not a file-based configuration value. It cannot be enabled at runtime without restarting the process. The boot sequence must log and alert if registration mode is enabled when autonomous operation is expected.

---

OBJECTION 4 — Task-Planner/Result-Verifier Token Estimation vs. Dispatch-Time Token Counting May Diverge Systematically

What v1.10 specifies (Item 6 and Item 11):

· Dispatch-time token counting uses either a calibrated tokenizer (2× margin) or fallback ceil(chars/3) estimator (1.5× margin).
· Task Planner must size child-task manifests so "expected prompt size is no more than the usable budget."
· Result Verifier must reject plans where "expected prompt > manifest_input_cap / safety_margin."

What is unstated:
The Task Planner and Result Verifier are cloud models. They reason about prompts in abstract token terms. They do not have access to the local TokenEstimator. A cloud model's internal concept of "how many tokens is this prompt" may differ materially from the local estimator's output—especially in fallback mode where estimation is character-based.

The coordination gap:

· Task Planner (cloud) creates a task, estimates its prompt will be ~800 tokens, sets max_estimated_input_tokens = 1600 (expecting 2× headroom for calibrated mode).
· At dispatch time, the local TokenEstimator runs in fallback mode (tiktoken not available), estimates the prompt at 1100 tokens, applies 1.5× margin → 1650 > 1600 → dispatch blocked.
· The Task Planner's cloud-model token estimate was ~800; the local character-based estimate was 1100. Neither is "wrong"—they're different estimators. The Result Verifier, also a cloud model, approved the plan because it used cloud-model token reasoning.

This is not a theoretical concern. Cloud models routinely miscount tokens in their own prompts—this is documented behavior. Having cloud models set numeric token budgets that a local estimator enforces creates a coordination gap without an explicit calibration step between the two estimators.

Recommended mitigation:
At calibration/bootstrap time, AXIOM should run a small cross-estimation benchmark: send fixed prompts through both the cloud model's self-reported token count and the local TokenEstimator, and compute a correction factor. The Task Planner should be informed of this correction factor in its system prompt (e.g., "The local token estimator reports ~15% higher counts than you expect; budget accordingly"). This doesn't need to be perfect but should reduce systematic divergence.

Without this, the system will experience blocks at dispatch that the Result Verifier approved, leading to blocked_resource_limit tasks that the operator must manually address. The end-to-end test uses a trivial memory-only goal that likely won't trigger this, so the problem will surface only in more complex autonomous operation.

---

OBJECTION 5 — End-to-End Test Is Gated on Calibration, Which Is Gated on Test-Set Authorship by a Panel That Has No Defined Workflow for This

What v1.10 specifies (Item 4):
test_full_goal_flow_minimum.py exercises the full MVP chain.

What v1.10 specifies (Item 1):
Gemini authors the injection test set. DeepSeek adversarially reviews it. Claude checks coherence. Qwen checks feasibility. Kimi packages it. Operator writes the file.

What is unstated:
The workflow and timeline for this multi-AI, multi-step artifact creation. The panel operates through the human operator as the physical abstraction layer. Gemini produces the test set as a proposal. The operator presents it to DeepSeek for adversarial review. DeepSeek's critique goes back to Gemini. Iterations occur. Claude and Qwen then review. Kimi packages. The operator writes the final file. Then calibration runs. Then the end-to-end test can pass.

This is a multi-session, potentially multi-day workflow. It's not a design flaw—the panel charter defines this process—but v1.10 presents the test set, calibration, and end-to-end test as implementable items without acknowledging the panel-process latency they depend on. The MVP cannot be declared complete until this workflow concludes.

The architectural implication is minor (this is a project-management concern, not a design validity concern), but the proposal should acknowledge that the end-to-end acceptance gate depends on a completed panel artifact workflow, not just on code implementation. Kimi's implementation plan cannot sequence these steps without knowing the dependency.

---

OBJECTION 6 — SupervisorMonitor Stale-Check Runs on Main Thread; A Slow Database Read Could Delay All Supervisor Functions

What v1.10 specifies (Item 10):
SupervisorMonitor lives in app/session_controller.py on the main supervisor thread. It reads scheduler_heartbeat.last_freshness_at and checks liveness.

The edge case:
The main supervisor thread also monitors Telegram liveness and bootstrap worker liveness, and coordinates shutdown. If the SQLite database is under heavy write load from the Scheduler thread (committing task events, provider usage rows, gateway responses), the SELECT last_freshness_at FROM scheduler_heartbeat query could contend with the write lock. SQLite uses database-level locking; a long write transaction on the Scheduler thread could block the supervisor's read. The supervisor's read is simple and fast, but under SATA SSD paging, even simple reads can take seconds.

If the supervisor thread is blocked on this read for several seconds, it's not checking Telegram liveness or processing shutdown requests during that window. This is unlikely to cause a failure (seconds of delay in liveness monitoring is acceptable), but it's a coupling point between the Scheduler's database activity and the supervisor's monitoring loop. The proposal doesn't acknowledge this coupling.

Mitigation:
The supervisor should use a separate SQLite connection in WAL mode for reads, or read last_freshness_at from an in-memory variable updated by the Scheduler (with appropriate thread-safety). SQLite WAL mode allows concurrent reads and writes, which would mitigate this. The proposal's persistence schema doesn't specify journal mode. I recommend WAL mode be required for the AXIOM database.

---

OBJECTION 7 — Operator-Control Authorization Chain (Item 12) Is Specification Without New Mechanism; No Changes to Existing Safeguards

This is not an objection to a flaw—it's an observation on scope.
Item 12 provides an explicit seven-step ownership table for operator-control authorization. It clarifies who owns which check. It does not introduce new authorization mechanisms beyond those already in v1.9. The table is useful for implementation clarity. No objection. I note this for completeness and will not raise it as an issue.

---

OBJECTION 8 — Pre-Decision Fingerprint Check Adds Latency to Every Safe-Pass Decision

What v1.10 specifies (Item 2):
The fingerprint check runs before every classifier-dependent safe-pass decision.

The latency concern:
The check makes an HTTP request to Ollama's localhost API. On a Celeron N4500 system, this is likely 50–200ms if Ollama is responsive. But the check runs once per plan artifact that reaches the safe-pass stage of scanner evaluation. In a session with many planning cycles (a complex goal decomposed into multiple sub-goals, each requiring re-planning), these checks accumulate.

Practical assessment: This is negligible compared to cloud-call latency (30–90 seconds). Even 10 fingerprint checks per session add up to 1–2 seconds total. Not a concern. I note it as considered, not as a blocking objection.

---

Summary of Objections

# Category Core Issue
1 Security Gap Mid-session fingerprint check error handling (API timeout/failure) is unspecified; could fail open if not explicitly fail-closed
2 Operational Gap No Telegram alert on mid-session fingerprint mismatch; operator may not discover security degradation until retrospective check
3 Security Gap Manifest registration mode enablement mechanism is unspecified; if file-based config, a compromised process could silently re-enable it
4 Coordination Gap Cloud-model token estimates and local dispatch-time estimates use different estimators with no calibration step; systematic divergence likely causes dispatch blocks
5 Workflow Dependency End-to-end test is gated on calibration which is gated on panel-authored test set; multi-step panel workflow has unacknowledged timeline
6 Edge Case SupervisorMonitor database read for heartbeat freshness can contend with Scheduler write locks under SQLite default journal mode; WAL mode not specified

Objections 1 and 2 are security/operational concerns I recommend resolving before implementation. Objection 3 is a security mechanism detail. Objection 4 is a coordination gap that will produce operational friction but isn't unsafe. Objection 5 is a project-management dependency. Objection 6 is a database configuration recommendation.

None of these are bare assertions. Each cites specific sections of v1.10 and identifies a concrete gap, assumption, or interaction. I await the Research Arbiter's factual verification and the Constraints Reviewer's feasibility assessment.