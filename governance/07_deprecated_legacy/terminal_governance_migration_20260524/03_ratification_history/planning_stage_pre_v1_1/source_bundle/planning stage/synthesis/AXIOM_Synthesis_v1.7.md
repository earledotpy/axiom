Evaluator Synthesis — AXIOM Proposal v1.7 Panel Review
Bottom line: The proposal must return to the Architect. v1.7's spine is sound and the v1.6→v1.7 delta closures hold, but DeepSeek surfaced eight objections — several of which my prior evaluation should have caught. Six are architectural gaps that block implementation planning. Three are implementation-level or can defer to Kimi. Qwen's nine binding conditions and the two minor touch-ups from my prior evaluation also need to fold into v1.8.
I want to flag the meta-issue plainly before going further: my v1.7 evaluation traced the worked examples through the new ordered rules and confirmed they produced the stated decisions, but I treated the artifact-class labels in those examples ("high-risk artifact", "ordinary artifact") as givens rather than auditing whether the proposal defines them. DeepSeek caught that. The panel cycle did its job; my prior approval was premature.
1. Valid Objections — Must Be Resolved Before Approval
#
Source
Objection
Why valid
Severity
A
DeepSeek Obj 1
"High-risk" vs "ordinary" artifact is undefined; Rules 6, 7, 10, 11 pivot on it
Four security-critical scanner rules cannot be implemented without this definition. Two implementers would produce different scanner behavior. The Goal Planner has no rule for what to label its own output. This is a missing input variable to the decision tree, not a clarification
Blocking — architectural
B
DeepSeek Obj 3
"Privileged task-class" referenced but not enumerated beyond operator_control
Rule 3's wording "including operator_control" implies an open set. An implementer cannot build the rule without the closed list. Trivial to fix but cannot be left ambiguous in a security gate
Blocking — specification
C
DeepSeek Obj 4
Cloud-call timeout unspecified; supervisor can observe blocks but cannot interrupt them
The supervisor architecture solves crash detection but not interrupt latency. Without a maximum bound on a synchronous cloud call, /cancel_current_chain is acknowledged but ignored for an unspecified duration. "Bounded operation" is not bounded if the bound is unset. This is the operational ceiling on operator control responsiveness
Blocking — architectural
D
DeepSeek Obj 7
Scheduler heartbeat has no liveness threshold and no defined supervisor action when stale
Pairs with C. The heartbeat threshold must be derived from the cloud-call timeout (threshold > timeout + margin), or the supervisor produces false positives during legitimate long calls. The supervisor's action on confirmed stale state must also be specified — kill, restart, or human-escalate are all different security postures
Blocking — architectural
E
DeepSeek Obj 5 (capability portion)
Telegram thread restart does not specify how OperatorControlCapability is re-established on the new gateway instance
This is the security-critical sub-issue inside Obj 5. The capability-object identity model only works if SessionController retains the token and re-passes it to the restarted gateway. If not specified, the restart path silently degrades the operator-control security model. Gemini already flagged the related implementation caveat (new Thread object required); the capability handoff is the architectural complement
Blocking — security model
F
DeepSeek Obj 8 (mid-chain failure)
TaskCommitter has no specified transactional boundary for partial deterministic-chain commits
Genuine architectural gap carried from v1.3.1. If the committer writes 3 of 5 child tasks and crashes, the resulting state is undefined. Affects auditability (Core Value 1) and zero-trust accounting
Blocking — architectural
G
DeepSeek Obj 8 (memory verification)
Memory Gateway dedup responses are not routed to the Result Verifier; verification path for memory.write_candidate tasks is incomplete
Carried from v1.3.1. The verification loop is open: memory writes can complete without traversing the verifier that other tool outputs go through. Inconsistent zero-trust treatment across tool classes
Blocking — architectural
H
DeepSeek Obj 2 (partial)
Classifier confidence thresholds (0.80, 0.90) are security gates with no calibration evidence for qwen3:4b
The thresholds themselves don't need to be re-set at architecture stage, but the architecture must require a calibration procedure as an acceptance criterion for the scanner, with a documented behavior when calibration fails (e.g., default to quarantine, raise threshold, etc.). Otherwise the scanner ships on uncalibrated numerical gates — a known LLM failure mode. Three revisions of carry-over makes this overdue
Blocking — acceptance criterion
2. Overruled or Deferred Objections
#
Source
Objection
Disposition
Rationale
I
DeepSeek Obj 5 (mechanics portion)
How a Telegram bot thread is restarted (Application teardown, polling cancellation, in-flight message handling)
Deferred to Kimi
These are implementation mechanics. Gemini has already verified the architectural claim and flagged the new-Thread-object caveat for Kimi. In-flight message handling at the python-telegram-bot library level is implementation-spec. The architectural requirement (capability token re-establishment) is captured in objection E above
J
DeepSeek Obj 6 (interface portion)
PlanInjectionScanner function signature unspecified
Deferred to Kimi
Function signatures are implementation-level. Kimi's plan must produce one; the architecture does not need to
J'
DeepSeek Obj 6 (module location)
PlanInjectionScanner has no module-map entry
Specification clarification, not blocking
The architecture should name where this lives, but it's a one-line addition that doesn't require a new revision cycle. Fold into v1.8 alongside the blocking items
K
DeepSeek Obj 8 (boot sequence breadth)
General boot sequence and task recovery beyond provider_usage orphans
Deferred to Kimi with explicit acknowledgment
v1.7 addressed the most operationally consequential boot recovery (provider_usage / budget integrity). Remaining recovery paths (stuck-task watchdog from legacy notes, in-flight task status reconciliation) are implementation-spec provided the architecture explicitly delegates them. Architect should add a one-paragraph delegation statement
L
DeepSeek Obj 8 (resource limits enforcement)
resource_limits.py filename with no specification of runtime enforcement mechanism
Specification clarification, not blocking
Enforcement mechanism (token-bucket, hard-cap on provider_usage budget table, etc.) needs at minimum a sentence in v1.8. One-paragraph addition; not a structural change
Per Charter §Conflict Resolution, DeepSeek objections are overruled only if both Gemini and Qwen find them unsupported. Neither Gemini nor Qwen addressed DeepSeek's objections directly — they reviewed v1.7 against their own scopes. So the formal override path doesn't apply here. The dispositions above are coherence/scope judgments within the Evaluator's role, ruling on whether an item is architectural-spec (panel) or implementation-spec (Kimi).
3. Required Revisions for v1.8
The Architect must produce v1.8 addressing all of the following. Items A–H are blocking; items I'–L can be folded into the same revision rather than waiting for a separate cycle.
Architectural (blocking):
Define artifact risk class. Add to the plan-artifact schema or scanner spec a deterministic rule for classifying a plan as high-risk vs ordinary. Candidate inputs (in priority order, panel can confirm): presence of sandbox.execute in any child task's tool list, presence of network.fetch in any child task's tool list, total task count threshold, or an explicit field set by the Goal Planner. State the rule once; reference it in Rules 6, 7, 10, 11.
Enumerate privileged task classes. Replace "including operator_control" in Rule 3 with the closed list. Currently identified candidates: operator_control, bootstrap_validation. Architect to confirm and lock the set.
Specify cloud-call maximum duration. Set a numeric ceiling (the v1.7 conversational "90 seconds" is a candidate) on synchronous calls in ModelGateway. State that the timeout is enforced per provider call, not per cascade attempt. Document what happens at timeout (cascade to next provider, or fail the task).
Set scheduler heartbeat liveness threshold and dead-scheduler action. Threshold derived from #3 (e.g., timeout + 30s margin). Specify how last_tick_at is updated (granularity matters). Specify the supervisor's action when threshold is exceeded — kill+restart, kill+human-escalate, or other.
Specify OperatorControlCapability re-establishment on Telegram thread restart. SessionController retains the capability token across restart and passes it to the new TelegramGateway instance. Restart fails closed if re-establishment fails (no degraded gateway operates without capability).
Specify TaskCommitter transactional boundary. Either: all child tasks of a deterministic chain commit atomically (single SQLite transaction), or partial commits are flagged and recovered on next boot via a defined rule. State which.
Close the memory verification loop. Route Memory Gateway dedup responses through the Result Verifier the same way other tool outputs traverse it. Or document explicitly why memory writes are exempt and what compensating control replaces verification.
Add classifier calibration as a scanner acceptance criterion. Specify: a calibration test set (size, attack-vector coverage), a pass criterion (e.g., calibration error below threshold X on the chosen confidence cutoffs), and the fallback behavior if calibration fails (raise thresholds, default to quarantine, swap classifier model). Bind this to v1.7's named test files.
Specification touch-ups (fold in same revision):
Add PlanInjectionScanner to the module map with module location.
Add one paragraph on resource_limits runtime enforcement mechanism.
Add one paragraph delegating remaining boot-sequence recovery (in-flight task reconciliation, stuck-task watchdog) to Kimi's implementation plan.
(From my prior evaluation) Broaden orphan provider_usage recovery scope from session_id = previous_session_id to all non-current sessions.
(From my prior evaluation) Document or close the gap where a confident classifier embedded_instruction label with no rule hit falls through to needs_human_input.
Binding conditions to fold into v1.8 documentation (from Qwen):
Sequential execution enforced; 4-thread cap (main supervisor, Telegram, Scheduler, Bootstrap).
qwen3:4b remains Q4-quantized and memory-mapped via Ollama.
Context bundles capped at 500 KB serialized.
Sandbox execution capped at 256 MB via Windows Job Object.
sqlite-vec batch limit of 100 vectors per query.
Token estimation includes 2× safety margin in budget_policy.
Brave Search API confirmed (or panel-approved free-tier alternative) before web search enabled.