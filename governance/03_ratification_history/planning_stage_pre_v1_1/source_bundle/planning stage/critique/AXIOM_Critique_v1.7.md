I've read v1.7 in full. The targeted fixes to provider_usage semantics and operator-control thread identity are solid. But the revision tightens four items while leaving multiple critical specifications from prior reviews untouched, and the centerpiece—the PlanInjectionScanner rules—introduces new definitional gaps that prevent implementation.

---

OBJECTION 1 — "High-Risk" vs. "Ordinary" Artifact Is Undefined, and the Scanner Rules Depend on It

What the proposal says:
Rules 6 and 10 reference "high-risk artifact." Rules 7 and 11 reference "ordinary artifact." The worked examples show Non-critical rule hit + classifier safe_data + confidence 0.94 → passed as a "high-risk artifact" case under Rule 10, and No rule hit + classifier safe_data + confidence 0.83 → passed as an "ordinary artifact" case under Rule 11. Identical classifier outputs produce different verdicts depending on this classification.

What is not defined anywhere in v1.7:
What makes a plan artifact "high-risk" vs. "ordinary." Is it:

· Presence of sandbox.execute in any child task's tool list?
· Presence of network.fetch?
· Both in the same plan (but Rule 4 already quarantines that)?
· A task count above some threshold?
· A computed risk score from some upstream component?
· A field in the plan artifact schema that the Goal Planner sets?

Why this matters:
Four of the twelve ordered rules pivot on this distinction. If "high-risk" is undefined, Rules 6, 7, 10, and 11 cannot be implemented. Two implementers reading the same spec would produce different scanner behavior. A Goal Planner doesn't know how to label its own output. The scanner doesn't know how to classify the artifact it receives. This is not a minor ambiguity—it's a missing input variable to a security-critical decision tree.

The worked examples imply but do not define the distinction. The proposal shows the scanner behaving correctly for specific cases but never states the rule by which the scanner determines which case an artifact belongs to. That's exactly the kind of specification gap that produces implementation errors.

---

OBJECTION 2 — Classifier Confidence Thresholds Are a Security Gate with No Calibration Basis

What the proposal specifies:
Rules 6, 7, 10, and 11 all use classifier confidence thresholds: ≥ 0.90 for high-risk artifacts, ≥ 0.80 for ordinary artifacts. The local model (currently qwen3:4b) produces the classifier label and the confidence score. A safe_data label at confidence 0.89 on a high-risk artifact → quarantined. The same label at 0.91 → passed.

What is not specified:

· Whether qwen3:4b's confidence scores are calibrated. Small language models are well-documented as poorly calibrated—a reported 0.90 confidence often does not correspond to a 90% probability of correctness. This is not a hypothetical; it's a known property of LLM output probabilities.
· What test set validates the confidence thresholds. The proposal lists test_classifier_injection_set.py and test_classifier_validation_runtime_contract.py from v1.3.1, but those tests are named, not specified. No sample size, attack vector coverage, or pass criterion exists.
· What happens if the classifier model is changed (the Constraints Register explicitly allows the panel to propose a different local model). Different models have different confidence calibration. Thresholds tuned for qwen3:4b may be meaningless for its replacement.

The security consequence:
The PlanInjectionScanner is the sole injection defense between an untrusted cloud model's output and the task queue. That defense now relies on numerical thresholds from an uncalibrated classifier. If the classifier is overconfident on adversarial inputs—a common failure mode—injected content passes at confidence 0.94 and is committed to the task queue. The scanner rules are formally specified but rest on an unvalidated measurement instrument.

This was Objection 8 from v1.3.1 review and Objection 10 from v1.1 review. Three revisions later, the architecture still treats the local model's confidence scores as a reliable signal without requiring evidence that they are reliable on the target hardware with the target model.

---

OBJECTION 3 — "Privileged Task-Class" Is Referenced but Not Enumerated

What the proposal says:
Rule 3 states: "Privileged task-class request, including operator_control → quarantined."

What is not defined:
What task classes are "privileged" beyond operator_control. The v1.3.1 addendum defined four task classes: goal_planning, task_planning, tool_execution, and verification. v1.3.1 added operator_control as a fifth. Rule 3's phrasing—"including operator_control"—implies there are other privileged classes. Are they:

· bootstrap_validation (for classifier validation commands)?
· Some internal system task class not yet defined?
· None—and the wording is misleading?

Why this matters:
If additional privileged task classes are planned but not specified, the scanner rule is a partial implementation. If no other privileged classes exist, the rule should say "operator_control task-class request" without "including" to avoid implying an open set. Either way, an implementer needs to know the closed list of privileged classes to implement Rule 3. Right now they don't have it.

---

OBJECTION 4 — Cloud Call Timeout Remains Unspecified; Supervisor Can Observe but Not Interrupt

What v1.7 says about the supervisor:
"Main supervisor thread still runs. It can observe the Telegram crash and set the shutdown request. The Scheduler will honor it when the current bounded operation returns or times out."

What v1.7 does not specify:
The timeout on a cloud call. The phrase "or times out" assumes a timeout is configured. It is not stated anywhere in v1.7, v1.3.1, or v1.1 what the ModelGateway's timeout is for a synchronous cloud call. The Constraints Register documents that Groq's daily limit was exhausted during testing and that Cerebras is the primary. Provider latency and reliability are variable by design—that's why the cascade exists.

Operational failure scenario:

1. Cerebras API accepts the connection but streams response tokens at 1 token/second for a long context.
2. The ModelGateway is blocked in a synchronous HTTP call with no timeout configured, or a timeout set to 120 seconds.
3. The human sends /cancel_current_chain at second 15 and then /status at second 30.
4. The main supervisor thread is alive and sets flags. The Telegram thread is alive and acknowledges the command.
5. The Scheduler thread is blocked for up to 120 seconds before it checks any flag.
6. The human receives an acknowledgment that cancel was requested, then silence for two minutes. From the human's perspective, the cancel command was accepted but the system is ignoring it.

The proposal uses "90 seconds" conversationally but never codifies it. Without a specified maximum cloud call duration, "bounded operation" is not bounded. A hung TCP connection with no timeout can block for minutes. The supervisor architecture is an improvement, but it does not solve the interrupt problem—it only ensures the system doesn't crash if Telegram dies during the block.

---

OBJECTION 5 — Telegram Thread Restart Mechanism Is a Hand-Wave

What the proposal says:
"SessionController writes session_events.telegram_thread_exception → SessionController attempts one Telegram thread restart → If restart succeeds: continue session."

What is not specified:

· How a Telegram bot thread is "restarted." The python-telegram-bot library uses an Application object with an async event loop. Restarting a Telegram listener involves tearing down the old Application, cancelling its polling, and creating a new one—or reinitializing the same one. This is not a trivial threading.Thread.start() re-invocation.
· Whether in-flight message processing is preserved during the crash. If the Telegram thread was mid-message when it crashed, does that message get re-delivered on restart? Lost? Duplicated?
· Whether the OperatorControlCapability token survives the crash. The capability is an in-memory object held by the TelegramGateway. If the thread dies and the gateway is reinitialized, the new instance must receive the same capability token from the SessionController. The proposal does not state that the SessionController retains and re-passes the token.

Why this matters:
The operator-control security model (v1.7's strongest addition) depends on the TelegramGateway holding the sole OperatorControlCapability object. If the restart path doesn't explicitly re-establish that, the restarted TelegramGateway cannot issue cancel/pause/shutdown commands. The human's recovery path is broken, and they must kill the entire process—exactly the crash the supervisor is meant to avoid.

---

OBJECTION 6 — PlanInjectionScanner Has No Module Location and No Interface Specification

What the proposal says:
The scanner is invoked by the Scheduler: "Scheduler invokes PlanInjectionScanner." It applies 12 ordered rules and returns a verdict. The scanner is not a role module, not in agents/, and not in security/sanitizer.py.

What is not specified:

· Where the scanner lives. The module map has not been updated since v1.3.1, and it showed no plan_injection_scanner.py at that time. v1.7 doesn't include a revised module map. Is it in security/? core/? Its own module?
· What interface the scanner exposes. Does it have a single function scan(plan_artifact, classifier_result) -> ScanVerdict? A class? Does it access the database directly or receive all data through parameters?
· Whether the scanner uses the classifier inline or receives a pre-computed classifier result. Rules reference classifier labels and confidences, but the Scheduler is the caller. Does the Scheduler call the classifier first, then pass results to the scanner? Or does the scanner call the classifier? This determines whether the scanner has a model dependency.

Why this matters:
The scanner is the most complex security component in Phase 1. Twelve ordered rules with branching sub-rules. It must be testable in isolation. Without a module location and a function signature, Kimi's implementation plan cannot include it, and the acceptance tests in Section 7 cannot be written.

---

OBJECTION 7 — Scheduler Heartbeat Monitoring Has No Liveness Threshold

What the proposal says:
The main supervisor thread monitors: scheduler_heartbeat.last_tick_at. This is listed alongside thread.is_alive() checks.

What is not specified:

· What delta between last_tick_at and current time constitutes a dead scheduler.
· What the supervisor does when it determines the scheduler is dead. "Scheduler safe-stop" is mentioned in the Telegram crash path, but safe-stop is invoked for operator interface failure, not scheduler death. If the scheduler thread is alive but last_tick_at is 5 minutes old, does the supervisor kill it? Restart it? Request human intervention via a session event?
· How last_tick_at is updated. Does the scheduler set it at the top of each loop iteration? After each task transition? The granularity determines what "stale" means. If it's set only at loop start, and a single task takes 90 seconds, the heartbeat is 90 seconds old during normal operation. The supervisor needs to know this is normal, not a hang.

False positive risk:
If the threshold is too short, the supervisor declares the scheduler dead during a legitimate long cloud call and initiates a recovery action that conflicts with the still-running scheduler. If the threshold is too long, a genuinely hung scheduler is not detected for minutes.

---

OBJECTION 8 — Multiple Prior Objections Remain Unaddressed Across Three Versions

The following objections were raised in my v1.3.1 review and have not been resolved in v1.7. They are not new, but their accumulation is itself a risk:

Prior Objection Status in v1.7
Resource limits enforcement has no runtime mechanism (v1.3.1 #4) resource_limits.py is a filename with no specification; budget enforcement at runtime is still undescribed
Mid-deterministic-chain failure recovery is unspecified (v1.3.1 #6) Partial task tree commits remain possible; no transactional boundary or rollback specified for TaskCommitter
Boot sequence and startup recovery are tested but not specified (v1.3.1 #7) Provider usage orphan recovery was added, but the general boot sequence and task recovery logic across the v1.7 status space is not described
Memory write candidate verification path is incomplete (v1.3.1 #9) Memory Gateway dedup responses are still not routed to the Result Verifier; verification of memory.write_candidate tasks is underspecified

The panel should decide whether these are deferred to implementation or require architectural resolution. In their current state, they are gaps between the architecture document and a buildable specification.

---

Summary of Objections

# Category Core Issue
1 Missing Definition "High-risk" vs. "ordinary" artifact classification is undefined; four scanner rules depend on it
2 Unvalidated Assumption Classifier confidence thresholds (0.80, 0.90) are security gates with no calibration evidence for the target model
3 Missing Definition "Privileged task-class" is referenced but not enumerated beyond operator_control
4 Operational Failure Cloud call timeout remains unspecified; supervisor can observe blocks but cannot interrupt them
5 Missing Specification Telegram thread restart mechanism and capability token re-establishment are not described
6 Missing Specification PlanInjectionScanner has no module location or function interface
7 Missing Definition Scheduler heartbeat liveness threshold is not set; false positive risk during legitimate long calls
8 Accumulated Risk Four prior objections (resource limits, mid-chain failure, boot sequence, memory verification) remain unaddressed across three proposal versions.