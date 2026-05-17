AXIOM Proposal v1.8.1 — Chief Architect Patch

Resolution of Final Approval Conditions

0. Patch Status

Field	Value

Proposal version	v1.8.1
Type	Small approval patch to v1.8
Scope	Two requested changes only
Architecture spine changed?	No
Status after patch	Ready for targeted confirmation


v1.8 was approved subject to two small patches: sandbox execution duration must be capped relative to the 120-second scheduler-stale threshold, and §11 must be aligned with the canonical scanner rule table in §16. The evaluator identified these as the only remaining issues. 


---

1. Patch 1 — Per-Sandbox-Execution Duration Cap

Decision

Add a hard per-sandbox-execution duration cap:

max_sandbox_execution_seconds = 60

This is enforced through the Sandbox Gateway using the Windows Job Object timeout mechanism, parallel to the existing 256 MB sandbox RAM cap.

Binding sandbox limits

Sandbox resource	Phase 1 limit	Enforcement

RAM	256 MB	Windows Job Object memory limit
Execution duration	60 seconds maximum	Windows Job Object timeout / process termination
Network access	None	Dedicated sandbox user + outbound firewall deny
Filesystem access	Sandbox working directory only	Restricted token + directory ACLs


Why 60 seconds

The scheduler-stale threshold remains:

120 seconds = 90-second max provider-call ceiling + 30-second margin

Sandbox execution now fits safely inside that threshold:

60-second sandbox cap + 30-second margin = 90 seconds

So a legitimate sandbox task should not falsely trigger the 120-second stale-scheduler fail-closed path.

Heartbeat interaction

The Scheduler still writes heartbeat records:

immediately before sandbox execution
immediately after sandbox execution returns, fails, or is terminated

If sandbox execution reaches 60 seconds:

Sandbox Gateway terminates sandbox process
↓
gateway_response.status = failed_resource_limit
↓
task.status = failed_resource_limit
↓
Scheduler heartbeat updates immediately after termination

v1.8 §2 binding condition update

Replace the sandbox binding condition:

Sandbox execution capped at 256 MB via Windows Job Object.

with:

Sandbox execution capped at 256 MB RAM and 60 seconds wall-clock duration via Windows Job Object.

v1.8 §12 resource limits update

Add:

Resource	Pre-dispatch gate	Runtime/post-dispatch action

Sandbox duration	Check manifest timeout ≤60 seconds	Job Object terminates overrun; task → failed_resource_limit


Acceptance test addition

tests/test_sandbox_duration_cap.py

Required assertions:

sandbox manifest cannot request >60 seconds
sandbox process exceeding 60 seconds is terminated
sandbox timeout writes gateway_response.status = failed_resource_limit
scheduler heartbeat does not falsely stale during compliant sandbox execution

This closes the heartbeat/sandbox-duration gap identified in the v1.8 review. 


---

2. Patch 2 — §11 Scanner Prose Aligned to §16

Decision

Remove §11’s independent prose rule description.

§16 is the canonical PlanInjectionScanner ordered rule set.

Replacement for v1.8 §11

Replace §11 with:

# 11. Classifier-Only Injection Signals

The canonical PlanInjectionScanner decision logic is the ordered table in §16. That table is the only implementable rule source.

Classifier-only suspicious labels are handled by §16 Rules 5A–5C:

- Rule 5A: No rule hit + classifier label = quarantine → quarantined.
- Rule 5B: No rule hit + classifier label in {embedded_instruction, tool_request} + risk_class = high_risk → quarantined.
- Rule 5C: No rule hit + classifier label in {embedded_instruction, tool_request} + risk_class = ordinary → needs_human_input.

The `needs_cloud_review` label does not safe-pass. If no earlier rule handles it, it falls through to §16 Rule 12: any unclassified remainder → needs_human_input.

Do not implement scanner behavior from prose summaries. Implement §16 only.

Canonicality rule

If any prose summary conflicts with §16, §16 wins.

Acceptance test update

tests/test_plan_injection_scanner_ordered_rules.py

Add assertions:

quarantine label with no rule hit → quarantined
embedded_instruction + high_risk + no rule hit → quarantined
embedded_instruction + ordinary + no rule hit → needs_human_input
tool_request + high_risk + no rule hit → quarantined
tool_request + ordinary + no rule hit → needs_human_input
needs_cloud_review with no earlier match → needs_human_input via Rule 12

This removes the documentation inconsistency between §11 and §16 noted in the evaluator review. 


---

3. Final v1.8.1 Patch Position

v1.8.1 changes only two things:

1. Sandbox execution now has a 60-second hard duration cap.
2. §16 is explicitly canonical for PlanInjectionScanner rules; §11 no longer contains conflicting rule prose.

All prior v1.8 architectural decisions remain unchanged.