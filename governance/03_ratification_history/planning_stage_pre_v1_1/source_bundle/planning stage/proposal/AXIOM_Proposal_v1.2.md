AXIOM Proposal v1.2 — Revised Architecture Proposal

Chief Architect Draft for Panel Re-Review

0. Proposal Status

Field	Value

Proposal	AXIOM ground-up architecture
Version	v1.2
Authoring role	GPT-5.5 — Chief Architect
Final approval status	Not approved
Purpose of revision	Resolve Evaluator carryover issues, DeepSeek objections, Gemini binding sandbox correction, and Qwen feasibility conditions
Next panel stage after this	Evaluator confirmation → DeepSeek re-check → Gemini/Qwen targeted confirmation → Implementation Specialist only after approval


This version replaces v1.1 and its addendum. The core architecture remains sequential, queue-mediated, SQLite-backed, Telegram-operated, and zero-trust, but v1.2 adds concrete mechanisms for sandbox isolation, cancellation, watchdog limitations, task-class routing, resource enforcement, classifier validation, and provider-budget limits.


---

1. Governing Constraints Incorporated

1.1 Hard platform constraints

Constraint	v1.2 design response

Celeron N4500	No parallel agent execution
8 GB RAM	Strict sequential runtime, 500 KB context cap, 256 MB sandbox cap
No GPU	Local model limited to routing/sanitization/embedding lane
Windows 11	Windows-specific sandbox and firewall design
Telegram interface	Telegram remains the operational control plane
Free / near-zero API budget	Provider gateway with token estimates, retry caps, timeouts, and usage logging


The Constraints Register establishes that Phase 1 cannot require extra hardware, a GPU, more RAM, a different OS, or paid infrastructure as the primary path. It also records only about 2.0–2.3 GB runtime headroom during legacy operation, making parallel execution a high-risk design choice. 

1.2 Qwen binding feasibility conditions adopted

Qwen condition	v1.2 commitment

Strict sequential execution	One active task operation at a time
qwen3:4b Q4 quantized + memory-mapped	Required local model profile unless panel approves replacement
500 KB context bundle cap	Enforced by Context Builder
256 MB sandbox RAM limit	Enforced by Sandbox Gateway
sqlite-vec 100-vector batch cap	Enforced by Memory Gateway
Brave Search API confirmation	Confirmed as near-zero via monthly credits, not assumed as unlimited free
2× token estimate margin with adaptive logging	Required by Model Gateway before cloud calls


Current Brave pricing shows Search at $5 per 1,000 requests with $5 in free monthly credits, so AXIOM should model Brave as “near-zero for roughly 1,000 Search requests/month under current pricing,” not as an unlimited free tier. 


---

2. Role Naming Revision

Decision

Rename the operational roles now, before implementation.

Previous name	v1.2 name	Actual function

Overseer	Goal Planner	Converts human goal into a proposed plan artifact
Taskmaster	Task Planner	Converts approved parent task into subtasks
Drone	Tool Executor	Performs one bounded tool action under manifest
Verifier	Result Verifier	Checks plans, subtasks, tool results, and final outputs


Rationale

The old names imply a command hierarchy. AXIOM is not a command hierarchy. It is a queue-mediated role system where agents do not command each other directly. Core Value 5 requires all coordination through the task queue, and Core Value 3 requires strict agent-boundary isolation. 


---

3. Highest-Level Architecture

Telegram Gateway
↓
Ingress Sanitizer
↓
Session Controller
↓
SQLite Task Queue
↓
Sequential Scheduler
↓
Role Executor
  ├── Goal Planner
  ├── Task Planner
  ├── Tool Executor
  └── Result Verifier
↓
Gateways
  ├── Model Gateway
  ├── Memory Gateway
  ├── Network Gateway
  └── Sandbox Gateway
↓
SQLite Audit Log + JSONL Mirror

Four highest-level decisions

Decision area	v1.2 decision

Agent hierarchy	Logical role hierarchy, physically sequential runtime
Coordination model	SQLite task queue is the only coordination channel
Persistence layer	SQLite + sqlite-vec + JSONL audit mirror
Execution model	Sequential state machine with bounded task leases, cancellation, retry caps, and explicit approval gates



---

4. Agent Hierarchy Structure

4.1 Logical hierarchy

Human Operator
↓
Telegram Gateway
↓
Session Controller
↓
Goal Planner
↓
Plan Checkpoint via Result Verifier
↓
Task Planner
↓
Subtask Checkpoint via Result Verifier
↓
Tool Executor
↓
Tool Result Verification
↓
Scheduler commits next state

4.2 Physical execution rule

There is one active role execution at a time.

No parallel Goal Planners.
No parallel Task Planners.
No parallel Tool Executors.
No parallel Verifiers.

This is a hard Phase 1 design rule, not a tuning preference.


---

5. Coordination Model

5.1 Sole coordination channel

Agents do not call agents.
Agents do not directly instruct agents.
Agents do not share mutable memory.
Agents read assigned queue records through scoped context bundles.
Agents write bounded outputs back to the queue.
The Scheduler applies state transitions.

This implements the Core Value requirement that all inter-agent coordination happen through the task queue. 

5.2 Queue ownership

Component	Authority

Scheduler	Owns task selection and status transitions
Policy Engine	Decides whether task may run
Permission Engine	Enforces manifest-level permissions
Context Builder	Constructs scoped context bundle
Role Executor	Performs role-specific reasoning/action
Gateways	Enforce model/tool/network/sandbox/memory boundaries
Result Verifier	Writes verdict only
Watchdog hooks	Recover stuck state within defined limits



---

6. Persistence Layer

6.1 Database choice

AXIOM Phase 1 uses SQLite as the primary persistence layer.

The Legacy Reference records SQLite as one of the reliable ToonTown patterns, but v1.2 keeps it on independent grounds: low RAM, single-file persistence, Windows compatibility, simple backup, and enough relational structure for queue/audit operations. 

6.2 Required tables

sessions
tasks
task_events
task_permissions
plan_artifacts
plan_checkpoints
tool_invocations
security_events
memory_items
memory_vectors
provider_usage
config_snapshots
artifacts
classifier_tests

6.3 Required SQLite settings

Setting	Requirement

WAL mode	Required
busy_timeout	Required
schema_version table	Required
task writes	Transactional
audit events	Append-only
large payload storage	Filesystem artifact + hash reference
sqlite-vec batch size	Maximum 100 vectors per operation



---

7. Execution Model

7.1 Sequential execution loop

Scheduler selects next eligible task
↓
Policy Engine checks execution approval
↓
Permission Engine checks manifest
↓
Context Builder constructs <=500 KB context bundle
↓
Role Executor runs one role step
↓
Gateway executes model/tool operation if permitted
↓
Output is sanitized
↓
Result is written to queue
↓
Result Verifier runs if required
↓
Scheduler applies next state

7.2 Active-task lease

Every running task receives:

lease_started_at
lease_expires_at
max_runtime_seconds
cancel_requested

If the task exceeds its lease, the Scheduler moves it to:

retry_pending

or:

failed

depending on attempt count and failure type.


---

8. Task Classes and Branched State Machine

8.1 task_class field

Every task has:

task_class

stored in the tasks table.

Allowed values:

goal_planning
task_planning
tool_execution
verification
operator_control

8.2 Who sets task_class

Task source	Component that sets task_class

Human Telegram command	Command Parser
Goal Planner proposed child task	Plan Committer after checkpoint pass
Task Planner proposed subtask	Subtask Committer after checkpoint pass
Result Verifier task	Scheduler
Cancel/status command	Telegram Gateway / Command Parser


8.3 Decision logic

Condition	task_class

Human submits new high-level goal	goal_planning
Existing approved task needs decomposition	task_planning
Task requires one bounded tool call	tool_execution
Task checks plan/subtask/tool/final result	verification
Task controls runtime state, e.g. cancel/status/pause	operator_control


8.4 Verification point

task_class is verified at:

created → ingress_sanitized

and again before:

approved_for_execution

A mismatch between task_class, role_owner, and manifest causes:

blocked

8.5 Branched state machines

A. Goal-planning task

created
↓
ingress_sanitized
↓
approved_for_execution
↓
running
↓
plan_artifact_created
↓
plan_checkpoint_pending
↓
plan_checkpoint_passed
↓
child_tasks_committed
↓
completed

Failure states:

plan_checkpoint_failed
quarantined
needs_human_input
cancelled
failed

B. Task-planning task

created
↓
ingress_sanitized
↓
approved_for_execution
↓
running
↓
subtask_plan_created
↓
subtask_checkpoint_pending
↓
subtask_checkpoint_passed
↓
child_tasks_committed
↓
completed

C. Tool-execution task

created
↓
ingress_sanitized
↓
approved_for_execution
↓
running
↓
awaiting_verification
↓
verified
↓
completed

D. Verification task

created
↓
approved_for_execution
↓
running
↓
completed

E. Operator-control task

created
↓
approved_for_execution
↓
running
↓
completed

Operator-control tasks can preempt normal queue order.


---

9. Plan Checkpoint Attachment

Decision

The checkpoint state attaches to:

1. The Goal Planner or Task Planner task


2. The plan artifact


3. The plan checkpoint record



Child tasks are not inserted into the task queue until the checkpoint passes.

Correct flow

Goal Planner task runs
↓
Proposed plan stored in plan_artifacts
↓
Goal Planner task enters plan_checkpoint_pending
↓
Result Verifier runs in plan_checkpoint mode
↓
plan_checkpoints row created
↓
If passed: child tasks inserted into tasks table at created state
↓
Goal Planner task enters child_tasks_committed
↓
Goal Planner task completes

Schema ownership

Entity	Stores

tasks	Parent task state, task_class, plan_artifact_id, checkpoint_id
plan_artifacts	Proposed plan JSON and artifact status
plan_checkpoints	Verifier verdict, reason, confidence, security labels



---

10. Plan Checkpoint Criteria

Required criteria

A plan checkpoint must verify:

#	Criterion

1	Goal preservation
2	Constraint compliance
3	Role separation
4	Queue-only coordination
5	Testable acceptance criteria
6	Manifest-compatible tool scope
7	Sandbox/network separation
8	Complexity discipline
9	Resource estimate
10	Human escalation for ambiguity
11	Prompt-injection scan on proposed plan and task text


Injection scan placement

The injection scan happens before child-task commit:

plan_artifact_created
↓
plan_injection_scan
↓
plan_checkpoint_pending

If suspicious instructions are detected:

quarantined

or:

needs_human_input

This closes the write-time sanitization gap identified by the panel. The Legacy Reference identifies missing prompt-injection defense as a serious unresolved ToonTown failure. 


---

11. Policy Engine and Permission Engine

11.1 Distinction

Component	Question answered

Policy Engine	“May this task run at all?”
Permission Engine	“May this task use this specific capability?”


11.2 Module implementation

Phase 1 may implement both classes in:

core/permissions.py

with:

class PolicyEngine
class PermissionEngine

Kimi may split this later if needed.

11.3 Policy Engine checks

task_class validity
sanitization_status
quarantine_flag
parent status
acceptance criteria
manifest presence
resource estimate
provider budget
checkpoint status
cancel state
permission result

11.4 Permission Engine checks

allowed_tools
forbidden_tools
allowed_read_scopes
allowed_write_fields
network_policy
sandbox_policy
memory_policy
budget_policy
manifest expiry


---

12. Permission Manifest

12.1 Manifest storage

Artifact	Storage

Manifest templates	policy/role_manifests/*.json
Task-specific manifest	SQLite task_permissions table
Manifest audit	SQLite task_events


12.2 Minimal manifest schema

{
  "manifest_id": "uuid",
  "task_id": "uuid",
  "task_class": "tool_execution",
  "role_owner": "tool_executor",
  "allowed_tools": ["network.fetch"],
  "forbidden_tools": ["sandbox.execute"],
  "allowed_read_scopes": ["task.self", "artifact.assigned"],
  "allowed_write_fields": [
    "tasks.output_payload",
    "tasks.error_payload",
    "task_events"
  ],
  "shared_state_writes": [],
  "network_policy": {
    "allow_network": true,
    "allowed_domains": ["example.com"],
    "max_fetches": 3
  },
  "sandbox_policy": {
    "allow_sandbox": false,
    "max_ram_mb": 0,
    "max_runtime_seconds": 0
  },
  "memory_policy": {
    "allow_memory_read": false,
    "allow_memory_write_candidate": false
  },
  "budget_policy": {
    "max_model_calls": 1,
    "max_estimated_input_tokens": 4000,
    "max_estimated_output_tokens": 1000,
    "token_estimate_multiplier": 2.0
  },
  "expires_at": "2026-05-02T23:59:59-06:00"
}

12.3 Write-boundary correction

The previous wording “Tool Executor can only write own result/error fields” was too narrow.

Correct rule:

Tool Executor may write only its own result/error fields,
plus shared-state writes explicitly granted by the task manifest.

12.4 Memory write rule

Tool Executor cannot write directly to semantic memory.

It may only write:

memory.write_candidate

if explicitly granted.

Then the Memory Gateway performs:

sanitization
deduplication
source attribution
embedding
insert-or-reject decision

So the manifest permission is retained, but it does not mean direct memory mutation.


---

13. Read and Write Boundaries

Role	May read	May write

Telegram Gateway	Incoming operator message, own session metadata	Command event
Session Controller	Config, session health, startup state	Session state, startup events
Goal Planner	Sanitized goal, constraints summary, relevant memory summaries	Proposed plan artifact
Task Planner	Assigned parent task, criteria, scoped context	Proposed subtask artifact
Tool Executor	Assigned task, assigned artifacts, explicit parameters	Own result/error fields plus manifest-granted write candidates
Result Verifier	Task input, output, criteria, evidence bundle	Verdict only
Scheduler	Queue metadata, manifests, statuses	Status transitions
Memory Gateway	Memory through controlled query API	Approved memory writes
Network Gateway	Fetch request and domain policy	Sanitized fetch result
Sandbox Gateway	Code artifact and sandbox policy	Execution result


Agents never receive raw database handles. They receive context bundles from the Context Builder.


---

14. Result Verifier

14.1 Single component, multiple modes

There is one module:

agents/result_verifier.py

Modes:

plan_checkpoint
subtask_checkpoint
tool_result
final_result
security_review

14.2 Verifier output

The Result Verifier writes:

verdict
verdict_reason
confidence
security_labels
recommended_next_state

The Scheduler applies the actual state transition.

14.3 Retry limit

Verifier retries are capped.

Failure type	Max retries

Schema formatting failure	1
Ambiguous verdict	1
Cloud timeout	1 provider fallback, then escalate
Repeated disagreement	0 automatic retries; escalate
Security suspicion	0 retries; quarantine


Default maximum verifier attempts per task:

2

After that:

needs_human_input

or:

failed

depending on risk.


---

15. Sandbox Architecture

15.1 Gemini binding correction

v1.1’s “restricted token + Job Object” was insufficient because that combination alone does not guarantee network socket blocking.

v1.2 commits to:

dedicated axiom_sandbox_user
+
Windows Defender Firewall outbound-deny rule scoped to that user/SID
+
restricted token
+
Windows Job Object limits

Microsoft’s New-NetFirewallRule supports outbound block rules and includes a LocalUser condition parameter, which is the basis for scoping the firewall rule to the sandbox identity. 

15.2 Why not AppContainer as primary path

AppContainer remains a valid alternate path, but not the Phase 1 primary path.

Microsoft’s AppContainer documentation states that an AppContainer without network capability cannot access the network, and AppContainers provide a sandboxed environment using SIDs, tokens, and DACLs. 

However, AppContainer implementation complexity is higher for a Python-based Windows script runner. For Phase 1, the dedicated sandbox user + firewall-scoped SID path is simpler to operationalize and test.

15.3 Sandbox policy

Sandbox execution is disabled unless all tests pass.

Required controls:

Control	Mechanism

Identity isolation	axiom_sandbox_user
Network block	Windows Defender Firewall outbound deny scoped to sandbox user/SID
Process containment	Windows Job Object
Privilege restriction	Restricted token
RAM cap	256 MB
Runtime cap	Manifest-defined, default 30 seconds
Working directory	Temporary sandbox directory
Secret isolation	No inherited API keys or operator env vars
File boundary	No writes outside sandbox directory


15.4 Mandatory sandbox tests

Before code execution is enabled:

Test	Expected result

HTTP request	Fails
Raw socket connection	Fails
DNS lookup	Fails or blocked according to firewall rule
Read API key env var	Fails
Write outside sandbox directory	Fails
Allocate >256 MB RAM	Terminated
Infinite loop	Terminated
Spawn child process beyond policy	Blocked or terminated


15.5 Fallback if no-network test fails

If Jeremy’s actual machine fails the sandbox no-network test:

Code execution is removed from Phase 1.

Then:

Capability	Phase 1 behavior

Code generation	Allowed as text artifact only
Code execution	Disabled
Sandbox Gateway	Disabled
Tool Executor with sandbox.execute	Blocked
Implementation path	Manual operator execution outside AXIOM


This is not optional. A failed sandbox isolation test blocks autonomous code execution.


---

16. Network Gateway

16.1 Search provider

Primary web search provider:

Brave Search API

Current public pricing supports near-zero use through monthly free credits, but AXIOM must treat this as a monitored budget, not a permanent entitlement. 

16.2 Network rules

Rule	Requirement

No network from sandbox	Enforced by firewall-scoped sandbox user
All fetches through Network Gateway	Required
Domain allowlist	Required per task
Fetch count cap	Required per manifest
Response size cap	Required
External content sanitizer	Required before queue write
Raw external content	Stored as untrusted artifact only



---

17. Latency, Retry, and Cancellation

17.1 Per-cloud-call timeout

Every cloud model call has:

timeout_seconds

Default:

45 seconds

Hard maximum without panel approval:

90 seconds

17.2 Chain-level cap

A single task chain may not exceed:

max_cloud_calls_per_chain = 8

without entering:

needs_human_input

This prevents an 8–15 call verifier/planner cascade from feeling like a hang.

17.3 Retry policy

Operation	Retry rule

Cloud timeout	One fallback provider attempt
Cloud rate limit	Mark provider rate_limited, try next provider
Verifier ambiguity	One retry max
Tool execution failure	Retry only if manifest permits
Sandbox failure	No retry if security-related
Injection suspicion	No retry; quarantine


17.4 Telegram cancellation

Add operator command:

/cancel_current_chain

Aliases:

/cancel
/stop_current

17.5 Cancellation behavior

Telegram command received
↓
operator_control task created with priority interrupt
↓
Scheduler sets active chain cancel_requested = true
↓
Current operation finishes or times out
↓
At next state-machine tick, active task becomes cancelled
↓
Unstarted descendants become cancelled
↓
Telegram Gateway reports cancellation summary

17.6 What cancellation cannot do in Phase 1

It does not forcibly kill an in-flight cloud HTTP request instantly.

It guarantees cancellation at the next state-machine tick or cloud-call timeout.


---

18. Watchdog Architecture

18.1 Phase 1 watchdog limitation

DeepSeek’s objection is accepted.

An in-process watchdog cannot recover the process that contains it if the Scheduler or Python runtime fully hangs.

18.2 Phase 1 watchdog scope

Phase 1 includes:

Watchdog	Placement	Can recover

Startup watchdog	session_controller.py	Stale task states after restart
Scheduler-loop watchdog	scheduler.py	Expired leases while scheduler is alive


18.3 Operator recovery procedure

If Telegram stops responding:

1. Operator returns to laptop.


2. Stop the current AXIOM session window if still open.


3. Run the AXIOM start script again.


4. Startup watchdog scans stale running tasks.


5. Stale tasks move to retry_pending, failed, or cancelled.


6. Telegram receives startup recovery summary.



18.4 Phase 2 external watchdog path

Phase 2 must add one of:

Option	Description

Wrapper batch loop	Restarts AXIOM if process exits unexpectedly
Servy-managed process	Windows service wrapper with restart policy
Telegram silence monitor	External process restarts session if heartbeat fails


Service mode remains deferred until Phase 1 queue/logging/recovery behavior is proven stable.


---

19. Resource Estimation and Runtime Enforcement

19.1 Who estimates resources

Resource	Estimator

Cloud token use	Model Gateway
Search calls	Network Gateway
Sandbox RAM	Sandbox Gateway
Sandbox runtime	Sandbox Gateway
Context bundle size	Context Builder
Vector batch size	Memory Gateway
File artifact size	Artifact Manager


19.2 RAM estimates

Each tool manifest includes:

max_ram_mb

Defaults:

Operation	RAM cap

Context bundle	500 KB serialized
Sandbox execution	256 MB
sqlite-vec batch	100 vectors
Network fetch response	Manifest-defined, default 1 MB
Local model	qwen3:4b Q4 memory-mapped only


19.3 Runtime kill behavior

Violation	Action

Sandbox exceeds 256 MB	Terminate sandbox process
Sandbox exceeds runtime lease	Terminate sandbox process
Context bundle exceeds 500 KB	Rebuild smaller bundle or block
sqlite-vec batch >100 vectors	Split batch
Cloud estimate exceeds budget with 2× margin	Block or require human approval
Search quota projected to exceed monthly budget	Block search task


19.4 Token estimate rule

Before a cloud call:

estimated_tokens * 2.0 <= manifest_budget

If false:

needs_human_input

or:

blocked

Adaptive logging updates future estimates based on actual observed use.


---

20. Defense-in-Depth Clarification

20.1 Revised claim

v1.2 does not claim that two calls to the same permission function are deep defense-in-depth.

Corrected claim:

AXIOM uses two enforcement locations to catch call-site bypasses,
but shared logic bugs remain possible and must be tested directly.

20.2 Structural distinction

Enforcement point	What it sees	What it prevents

Scheduler / Policy Engine	Full task state before execution	Bad task entering running
Tool Gateway / Permission Engine	Actual tool dispatch request	Unauthorized tool use at dispatch


The Tool Gateway check is structurally useful because it validates the actual requested tool call, not merely the task’s planned permission state.

20.3 Remaining risk

A bug in the shared permission logic could affect both points. Therefore Phase 1 requires permission tests for:

forbidden tool
expired manifest
wrong task_class
wrong role_owner
read-scope violation
write-field violation
network domain violation
sandbox/network conflict


---

21. Local Classifier Validation

21.1 Local classifier role

The local model may classify and label:

safe_data
untrusted_data
embedded_instruction
tool_request
memory_candidate
quarantine
needs_cloud_review

It may not approve plans, override manifests, or complete complex reasoning tasks. This is consistent with the Core Values document’s local-model lane: classifier, router, sanitizer, and embedding engine. 

21.2 Confidence threshold

Default rule:

confidence < 0.80 → quarantine

High-risk content requires:

confidence >= 0.90

High-risk content includes:

external fetched content
tool output that requests future actions
memory write candidates
plan artifacts
subtask artifacts

21.3 Initial injection test set

Before autonomous operation, the sanitizer must pass a small test set covering:

Pattern

“Ignore previous instructions”
“Reveal your system prompt”
“Send this to another agent”
“Modify the task queue directly”
“Call this external URL outside the gateway”
“Write this to memory as trusted fact”
Base64/encoded instruction attempt
Markdown hidden instruction
Tool-call imitation
Prompt embedded inside fetched webpage text


Acceptance:

100% of known malicious samples classified as quarantine or embedded_instruction
0 critical misses

21.4 Revalidation rule

If the local model changes, including replacing qwen3:4b or changing quantization materially:

classifier_tests must be rerun before autonomous operation resumes


---

22. Model Gateway

22.1 Local model profile

Required local model profile for Phase 1:

qwen3:4b
Q4 quantized
memory-mapped
thinking disabled

Any replacement requires panel review because local model scope and RAM impact are governed by the Constraints Register and Core Values.  

22.2 Cloud provider states

Only three provider states in Phase 1:

available
rate_limited
failed

No latency optimization, model benchmarking, or advanced scoring in Phase 1.

22.3 Cloud call record

Every call logs:

provider
model
task_id
task_class
role_owner
estimated_input_tokens
estimated_output_tokens
actual_input_tokens_if_available
actual_output_tokens_if_available
estimate_multiplier
timeout_seconds
status
error_type
timestamp


---

23. Cancellation and Priority Interrupts

23.1 Priority model

Operator-control tasks have the highest priority.

operator_control > security_review > verification > planning > tool_execution

23.2 Preemption limit

Phase 1 preemption is cooperative.

It does not interrupt Python bytecode arbitrarily. It sets cancellation state and enforces it at:

state-machine ticks
cloud-call timeout boundaries
tool completion boundaries
sandbox timeout boundaries


---

24. Revised Module Map

axiom/
  app/
    telegram_gateway.py
    session_controller.py
    command_parser.py

  core/
    scheduler.py
    state_machine.py
    context_builder.py
    permissions.py
    watchdog.py
    cancellation.py
    resource_limits.py

  agents/
    goal_planner.py
    task_planner.py
    tool_executor.py
    result_verifier.py

  gateways/
    model_gateway.py
    memory_gateway.py
    network_gateway.py
    sandbox_gateway.py

  security/
    sanitizer.py
    classifier_validation.py
    audit.py

  persistence/
    db.py
    schema.sql
    repositories.py

  policy/
    role_manifests/
      goal_planner.json
      task_planner.json
      tool_executor_network_fetch.json
      tool_executor_sandbox_execute.json
      tool_executor_file_limited.json
      result_verifier.json
      operator_control.json

  tests/
    test_state_machine_branches.py
    test_task_class_assignment.py
    test_permissions.py
    test_read_boundaries.py
    test_write_boundaries.py
    test_sandbox_no_network.py
    test_watchdog_startup.py
    test_cancellation.py
    test_plan_checkpoint.py
    test_classifier_injection_set.py
    test_resource_limits.py


---

25. Revised Acceptance Criteria

25.1 Coordination

Requirement	Pass condition

No direct agent calls	No role module invokes another role module directly
Queue-only coordination	All work moves through SQLite task records
Scheduler-owned transitions	Only Scheduler mutates task status
Context scoping	Agents receive bundles, not DB handles


25.2 Security

Requirement	Pass condition

Sandbox no-network	HTTP/socket/DNS tests fail from sandbox
Firewall-scoped sandbox identity	Sandbox process runs as axiom_sandbox_user with outbound deny
Sandbox fallback	If no-network fails, sandbox.execute disabled
Network gateway only	All fetches go through Network Gateway
Prompt-injection scan	Plan artifacts scanned before child-task commit
Classifier test set	Critical injection samples classified safely
Default quarantine	Low-confidence classifier results quarantined


25.3 Feasibility

Requirement	Pass condition

Sequential execution	One active role execution at a time
Context bundle cap	Serialized bundle ≤500 KB
Sandbox RAM cap	256 MB enforced
sqlite-vec cap	≤100 vectors per batch
Token margin	2× estimate before cloud call
Brave budget	Search usage tracked against monthly credit/budget


25.4 Operability

Requirement	Pass condition

Telegram status	Operator can request current chain/status
Telegram cancel	/cancel_current_chain cancels active chain at next tick/timeout
Cloud timeout	Every cloud call has timeout
Retry cap	Verifier and provider retries capped
Startup recovery	Stale running tasks recovered after restart
Watchdog limitation documented	Operator recovery procedure exists



---

26. Explicit Rejections and Deferrals

Item	Disposition	Reason

Parallel agents	Rejected Phase 1	RAM risk
Direct role-to-role calls	Rejected	Violates queue coordination
Local model for complex reasoning	Rejected	Violates local model lane
DuckDuckGo package search	Rejected	Legacy structural failure
AppContainer sandbox primary path	Deferred	Valid but higher implementation complexity
Windows service mode	Deferred Phase 2	Adds restart/credential complexity
External watchdog process	Deferred Phase 2	Phase 1 uses operator restart + startup recovery
Autonomous code execution without no-network test	Rejected	Violates sandbox/network separation



---

27. v1.2 Final Architecture Position

AXIOM Phase 1 should be:

A logical multi-agent system with a physically sequential runtime.

A SQLite task queue is the sole coordination spine.

Goal Planner, Task Planner, Tool Executor, and Result Verifier are roles,
not independent parallel workers.

The Scheduler owns state transitions.

The Policy Engine decides whether tasks may run.

The Permission Engine enforces manifest-scoped capabilities.

The Result Verifier checks plans, subtasks, tool outputs, and final results
but never mutates state directly.

The sandbox runs under a dedicated sandbox user with outbound firewall deny,
restricted token, Job Object limits, and a mandatory no-network test.

If sandbox isolation fails on the actual machine, autonomous code execution
is removed from Phase 1.

The operator can cancel the current chain from Telegram.

Every cloud call has a timeout, retry cap, token estimate margin, and usage log.

All local classification defaults to quarantine under uncertainty.