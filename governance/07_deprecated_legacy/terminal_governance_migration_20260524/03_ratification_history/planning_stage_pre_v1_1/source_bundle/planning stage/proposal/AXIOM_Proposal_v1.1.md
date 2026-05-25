AXIOM Proposal v1.1 — Chief Architect Revision

Response to Claude Coherence Return A–J

0. Revision Status

Field	Status

Proposal version	v1.1
Originator	GPT-5.5 — Chief Architect
Authority	Draft only
Can proceed to DeepSeek after this?	Yes, if Claude accepts that A–J are resolved
What changed	State gate, Drone model, sanitization map, permission manifest, verifier integration, read boundaries, sandbox mechanism, watchdog, Overseer checkpoint, Core Value 2 clarification


This revision preserves the v1 spine: sequential logical multi-agent system, SQLite queue coordination, SQLite persistence, cloud cognition, local routing/sanitization/embedding, and strict sandbox/network separation. It tightens the missing mechanisms instead of redesigning the architecture.


---

1. Resolution Matrix

Claude item	Resolution

A — Define approved_for_execution gate	Added Execution Approval Gate, owned by Scheduler + Policy Engine
B — Drone inconsistency	Committed to one Drone executor with permission-scoped tool manifests
C — Sanitization scope	Added source-by-source sanitization map
D — Permission manifest	Added manifest schema, storage, and enforcement point
E — Verifier integration	Integrated verifier into state machine after state-changing Drone actions
F — Read boundaries	Added read/write boundary table by role
G — Sandbox mechanism	Committed to Windows Job Objects + restricted token via pywin32, subject to Gemini factual verification
H — Watchdog	Added startup watchdog + scheduler-loop watchdog
I — Overseer checkpoint	Added Plan Checkpoint before task tree commit
J — Core Value 2 scope	No amendment required; Core Values already list the local model as classifier/router/sanitizer/embedding engine



---

2. Revised Highest-Level Architecture

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
    ├── Overseer Mode
    ├── Taskmaster Mode
    ├── Drone Mode
    └── Verifier Mode
  ↓
Tool Gateways
    ├── Model Gateway
    ├── Memory Gateway
    ├── Network Gateway
    └── Sandbox Gateway
  ↓
SQLite Audit Log + JSONL Mirror

The architecture remains sequential because the constraints register gives only about 2.0–2.3 GB runtime headroom and warns that concurrent agent subprocesses risk exhausting RAM and forcing SATA SSD paging. 


---

3. A — approved_for_execution Gate

Decision

approved_for_execution is produced by the Execution Approval Gate, not by the human operator and not by the agent itself.

Gate owner

Component	Authority

Scheduler	Invokes the gate
Policy Engine	Evaluates manifest, state, risk, and resource rules
Verifier	Supplies plan/check evidence where applicable
Human operator	Only resolves needs_human_input; does not normally approve routine tasks


Approval criteria

A task can enter approved_for_execution only if all conditions pass:

Criterion	Requirement

Sanitization	sanitization_status = passed
Quarantine	quarantine_flag = false
Role assignment	role_owner is valid
Tool scope	Requested tool is listed in the task’s permission manifest
Read scope	Task can only access records allowed by role policy
Write scope	Task can only write fields allowed by role policy
Acceptance criteria	Task has explicit success condition
Resource estimate	Task does not exceed Phase 1 RAM/API policy
Parent status	Parent task is active and not failed/quarantined
Plan checkpoint	If task came from Overseer plan, the plan has passed checkpoint verification


Revised lifecycle

created
↓
ingress_sanitized
↓
planned
↓
plan_checkpoint_pending
↓
plan_checkpoint_passed
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

Failure states:

blocked
failed
needs_human_input
quarantined
retry_pending

Why this is not human approval

AXIOM’s autonomous operation would be weakened if every task required human approval. The human operator’s role is execution and reporting, not design judgment or routine task approval. 


---

4. B — Drone Architecture

Decision

Use one Drone executor with permission-scoped manifests.

Do not create separate WebDrone, CodeDrone, FileDrone, and MemoryDrone classes in Phase 1.

Corrected terminology

Old wording	Revised wording

Code Drone	Drone executor with sandbox.execute permission
Web Drone	Drone executor with network.fetch permission
File Drone	Drone executor with file.read / file.write_limited permission
Memory Drone	Drone executor with memory.query / memory.write_candidate permission


Revised module structure

agents/
  overseer.py
  taskmaster.py
  drone.py
  verifier.py

core/
  permission_manifest.py
  permission_engine.py

Rationale

Typed Drone classes create premature implementation complexity. The simpler architecture is a single executor whose behavior is determined by the manifest attached to the task. This preserves zero-trust boundaries while avoiding class sprawl.


---

5. C — Sanitization Map

Decision

Sanitization is not one generic step. AXIOM uses four source-specific sanitization paths.

Input source	Sanitization placement	Mechanism	Output

Human Telegram input	Before task creation	Command parser + local classifier/sanitizer	created task or needs_human_input
Overseer-generated plan	Before task tree commit	Plan Checkpoint + schema validation + injection scan	plan_checkpoint_passed or quarantined
External fetched content	Before queue write	Network Gateway sanitizer + instruction/data separation	Sanitized evidence object
Tool outputs	Before result write	Tool Gateway sanitizer + result schema validation	Safe output_payload or quarantine
Memory writes	Before insertion	Sanitizer + dedup + source attribution	Stored memory or rejected duplicate
Model outputs	Before state mutation	JSON schema validation + policy check	Accepted structured result or retry


Sanitization mechanisms

Mechanism	Purpose

Deterministic schema validation	Reject malformed or overbroad payloads
Rule-based injection scan	Catch obvious prompt-injection patterns
Local model classifier	Classify ambiguous instruction/data boundaries
Conservative quarantine	Block uncertain inputs rather than passing them through


Important distinction

Sanitization does not mean “make the content true.” It means:

Separate data from instructions.
Label untrusted content.
Reject or quarantine unsafe state-changing instructions.
Ensure only structured, bounded payloads enter the queue.

The Legacy Reference identifies prompt injection at the task queue boundary as a real unresolved failure and records pre-rebuild consensus that sanitization should happen at write time. 


---

6. D — Permission Manifest

Decision

Every executable task must include a Permission Manifest. The Scheduler refuses to run a task without one.

Storage

Artifact	Storage

Manifest template	policy/role_manifests/*.json
Task-specific manifest	SQLite task_permissions table
Manifest audit	SQLite task_events table


Minimal manifest schema

{
  "manifest_id": "uuid",
  "task_id": "uuid",
  "role_owner": "drone",
  "allowed_tools": [
    "network.fetch"
  ],
  "allowed_read_scopes": [
    "task.self",
    "artifact.assigned"
  ],
  "allowed_write_fields": [
    "tasks.output_payload",
    "tasks.error_payload",
    "task_events"
  ],
  "forbidden_tools": [
    "sandbox.execute",
    "memory.write",
    "task.create"
  ],
  "network_policy": {
    "allow_network": true,
    "allowed_domains": ["example.com"],
    "max_fetches": 3
  },
  "sandbox_policy": {
    "allow_sandbox": false
  },
  "memory_policy": {
    "allow_memory_read": false,
    "allow_memory_write": false
  },
  "budget_policy": {
    "max_model_calls": 1,
    "max_estimated_input_tokens": 4000,
    "max_estimated_output_tokens": 1000
  },
  "expires_at": "2026-05-02T23:59:59-06:00"
}

Enforcement point

Scheduler
  ↓
Permission Engine
  ↓
Context Builder
  ↓
Tool Gateway

The Tool Gateway performs a second check. This prevents a bug in the Scheduler from becoming unrestricted tool access.

Non-negotiable rule

An agent cannot self-expand its manifest. Any request for additional permissions becomes a new task with status:

needs_human_input

or

blocked

depending on severity.

This directly enforces zero-trust boundaries: tool access must be explicit, agents cannot read full context, and inter-agent work is logged by agent ID and task ID. 


---

7. E — Verifier Integration

Decision

Verifier is Phase 1 scope.

Verifier runs after:

1. Overseer plan generation


2. Taskmaster subtask generation


3. Every state-changing Drone action


4. Final parent-task completion



Revised state machine with verifier

created
↓
ingress_sanitized
↓
planned
↓
plan_checkpoint_pending
↓
plan_checkpoint_passed
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

If verification fails:

awaiting_verification
↓
retry_pending
↓
approved_for_execution

or:

awaiting_verification
↓
failed

or:

awaiting_verification
↓
needs_human_input

Verifier types

Verification type	Used for	Model/tool requirement

Deterministic verifier	Schema, file existence, status transition validity	No model
Local classifier verifier	Sanitization confidence, narrow classification	Local model
Cloud verifier	Plan coherence, task decomposition quality, complex result review	Cloud cascade
Human escalation	Irreducible ambiguity or unsafe permission request	Telegram prompt


State-changing Drone actions

A Drone action is state-changing if it:

Action	Example

Writes a file	Creates/edits code or artifact
Writes memory	Adds semantic memory
Calls external network	Fetches web content
Runs sandboxed code	Executes generated code
Mutates queue result	Writes task output
Creates artifact reference	Stores file path/hash in DB


Read-only local inspection can use deterministic verification only.


---

8. F — Read and Write Boundaries

Decision

Every role receives a scoped context bundle. No role can query raw tables directly.

Read/write boundary table

Role	May read	May write	Cannot read/write

Telegram Gateway	Incoming user message, own session metadata	New command event	Task internals outside status summaries
Session Controller	Config, session table, startup health checks	Session state, startup events	Agent reasoning payloads
Overseer	Sanitized human goal, relevant retrieved memory summaries, constraints summary	Proposed plan artifact only	Raw full memory DB, full task table, tool outputs from unrelated tasks
Plan Checkpoint Verifier	Proposed plan, constraints summary, manifest templates	Checkpoint verdict	Execute tools, mutate plan directly
Taskmaster	Assigned parent task, acceptance criteria, allowed context bundle	Proposed subtasks	Sibling task internals, full task tree outside assigned branch
Drone	Assigned task, assigned artifacts, explicit tool parameters	Own result/error fields only	Full queue, parent/sibling context, manifest expansion
Result Verifier	Task input, output, acceptance criteria, relevant evidence	Verification verdict	Tool execution, unrelated memory
Scheduler	Queue metadata, statuses, manifests	Status transitions	Model/tool content generation
Memory Gateway	Memory records through query API only	Memory insert/update according to policy	Direct task mutation
Network Gateway	Fetch request, domain policy	Sanitized fetch result	Sandbox execution
Sandbox Gateway	Code artifact, sandbox policy	Execution result	Network access


Context Builder rule

Agents never receive database handles. They receive serialized context bundles constructed by context_builder.py.

Database → Repository → Context Builder → Agent

This closes the gap Claude identified: write controls alone are insufficient if read access exposes the full system.


---

9. G — Sandbox Isolation Mechanism

Decision

Phase 1 sandbox architecture commits to:

Windows Job Objects + restricted Windows token via pywin32

This is the named mechanism for sandbox isolation. It is not deferred.

Sandbox boundary

Sandbox Runner
  ├── restricted OS token
  ├── Job Object limits
  ├── temporary working directory
  ├── no inherited secrets
  ├── no direct network permission
  ├── CPU/time limit
  ├── memory limit
  └── stdout/stderr capture

Required tests before enabling code execution

Test	Expected result

Attempt HTTP request from sandbox	Fails
Attempt socket connection from sandbox	Fails
Attempt environment variable read for API keys	Fails
Attempt write outside sandbox directory	Fails
Infinite loop	Terminated
Excess memory allocation	Terminated
Child process spawn attempt	Blocked or terminated


The Core Values require sandbox isolation to be verified by test, not assumed, and explicitly reject relying on subprocess.Popen for isolation.  The Legacy Reference also records that subprocess.Popen inherited parent network permissions and that Windows Job Objects plus restricted token were identified in pre-rebuild research as required for genuine Windows isolation. 

Important limitation

This mechanism still requires Gemini factual verification before implementation. The architectural commitment is now explicit; the factual sufficiency of the Windows mechanism belongs to Gemini.


---

10. H — Watchdog Architecture

Decision

Use two watchdog modes:

1. Startup watchdog


2. Scheduler-loop watchdog



No separate watchdog process in Phase 1.

Placement

session_controller.py
  └── startup_watchdog()

scheduler.py
  └── scheduler_loop_watchdog()

Startup watchdog

Runs once at session start.

Condition	Action

Task status = running and session is dead	Move to retry_pending
Task status = awaiting_verification	Move to awaiting_verification unchanged
Task has exceeded max attempts	Move to failed
Task has missing manifest	Move to blocked
Task has quarantine flag	Move to quarantined


Scheduler-loop watchdog

Runs every scheduler tick before selecting the next task.

Condition	Action

running task exceeds lease timeout	Mark retry_pending or failed
Provider marked failed for too long	Recheck provider state
Task stuck in planned without checkpoint	Move to blocked
Task waiting on human too long	Leave unchanged; send Telegram reminder only if configured
Sandbox process exceeds limit	Terminate process, write security event


Watchdog authority

The watchdog may mutate only:

status
error_payload
attempt_count
updated_at
task_events

It cannot rewrite:

input_payload
output_payload
tool_scope
acceptance_criteria
parent_task_id
role_owner


---

11. I — Overseer Plan Checkpoint

Decision

Overseer output does not directly become executable queue reality.

It first becomes a proposed plan artifact.

Plan flow

Human goal
↓
Ingress Sanitizer
↓
Overseer generates proposed plan
↓
Plan Checkpoint Verifier reviews proposed plan
↓
If passed: task tree committed to queue
↓
If failed: retry, revise, or needs_human_input

Plan checkpoint criteria

Criterion	Requirement

Goal preservation	Plan still matches original human goal
Constraint compliance	No GPU/new hardware/paid requirement unless explicitly future-state
Role separation	Overseer does not assign itself tool execution
Queue compliance	No direct agent-to-agent calls
Acceptance criteria	Each task has testable completion condition
Tool scope	Each executable task has manifest-compatible tool request
Security boundary	No sandbox/network bypass
Complexity discipline	No speculative future-phase work
Resource estimate	No parallel execution unless specifically approved later
Human escalation	Ambiguity is surfaced, not guessed into execution


Storage model

Artifact	Storage

Proposed plan	plan_artifacts table
Checkpoint verdict	plan_checkpoints table
Committed task tree	tasks table
Rejected plan	Kept for audit, not executed


The Legacy Reference explicitly identifies Overseer decomposition reliability as the weakest link and recommends a verification/checker step before committing a task tree. 


---

12. J — Core Value 2 Clarification

Decision

No Core Value amendment is required.

Claude’s concern is directionally useful but the current Core Values already include sanitization inside the local model lane. The document states the local model is a classifier, router, sanitizer, and embedding engine, while complex reasoning, goal decomposition, and synthesis go to cloud models. 

Architectural interpretation

Sanitization is permitted local-model work only when framed as:

classification + boundary labeling + quarantine recommendation

It is not permitted to become:

complex reasoning
goal decomposition
semantic synthesis
policy invention

Rule

The local model may classify content as:

safe_data
untrusted_data
embedded_instruction
tool_request
memory_candidate
quarantine
needs_cloud_review

The local model may not decide:

whether the overall plan is good
whether the task should be executed despite policy conflict
whether to override a manifest
whether to complete a task using its own reasoning

This keeps sanitization inside Core Value 2 rather than expanding the local model’s role.


---

13. Revised Persistence Tables

Required tables

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

Key task fields

task_id
parent_task_id
session_id
role_owner
status
priority
input_payload
output_payload
error_payload
acceptance_criteria
manifest_id
sanitization_status
quarantine_flag
checkpoint_id
attempt_count
lease_expires_at
created_at
updated_at
started_at
completed_at


---

14. Revised Phase 1 Module Decomposition

Claude is right that v1 risked over-decomposition. v1.1 consolidates the module map.

axiom/
  app/
    telegram_gateway.py
    session_controller.py

  core/
    scheduler.py
    state_machine.py
    context_builder.py
    permissions.py
    watchdog.py

  agents/
    overseer.py
    taskmaster.py
    drone.py
    verifier.py

  gateways/
    model_gateway.py
    memory_gateway.py
    network_gateway.py
    sandbox_gateway.py

  security/
    sanitizer.py
    audit.py

  persistence/
    db.py
    schema.sql
    repositories.py

  policy/
    role_manifests/
      overseer.json
      taskmaster.json
      drone_network_fetch.json
      drone_sandbox_execute.json
      drone_file_limited.json
      verifier.json

  tests/
    test_state_machine.py
    test_permissions.py
    test_read_boundaries.py
    test_sandbox_no_network.py
    test_watchdog.py
    test_plan_checkpoint.py

Kimi may consolidate further during implementation if behavior remains equivalent.


---

15. Revised Acceptance Criteria

AXIOM Phase 1 architecture passes only if:

Area	Acceptance criterion

Queue coordination	No agent directly calls another agent
Execution approval	No task runs without approved_for_execution produced by Scheduler + Policy Engine
Drone architecture	Single Drone executor obeys task manifest
Permission manifest	Every executable task has a manifest
Read boundaries	Agents receive context bundles, not raw DB access
Write boundaries	Drones can only write own result/error fields
Plan checkpoint	Overseer plans are verified before task tree commit
Verifier	State-changing Drone actions enter awaiting_verification
Sanitization	Human input, Overseer output, fetched content, tool output, and memory writes each pass source-appropriate sanitization
Sandbox isolation	Windows Job Object + restricted token mechanism passes no-network test
Network separation	Sandbox cannot fetch; Network Gateway cannot execute code
Watchdog	Startup and scheduler-loop watchdog recover stale tasks
Provider accounting	Every model call logs provider/model/task/role/token estimate/status
Crash recovery	Interrupted running task becomes retry_pending, failed, or quarantined according to policy
Core Value 2	Local model remains classifier/router/sanitizer/embedding engine only



---

16. Final v1.1 Architecture Position

AXIOM should proceed as:

Logical three-tier multi-agent system.
Single sequential physical runtime.
SQLite queue as sole coordination spine.
One Drone executor controlled by manifests.
Scheduler-owned execution approval gate.
Plan checkpoint before task tree commit.
Verifier after every state-changing Drone action.
Context bundles instead of raw database reads.
Windows Job Objects + restricted token for sandbox isolation.
Startup and scheduler-loop watchdogs.
Local model for routing, sanitization, private classification, and embeddings.
Cloud cascade for decomposition, synthesis, and complex reasoning.

This revision closes the coherence gaps without weakening the original design. The next correct move is to return this v1.1 proposal to Claude for coherence re-check before DeepSeek adversarial review.

AXIOM Proposal v1.1 — Chief Architect Addendum

Coherence Clarifications for Advancement to DeepSeek

0. Addendum Status

Field	Value

Document type	Clarifying addendum
Applies to	AXIOM Proposal v1.1
Creates new architecture version?	No
Purpose	Resolve Claude residual Issues 1–4
Advancement recommendation	Advance to DeepSeek after this addendum is attached


This addendum does not redesign v1.1. It resolves naming, state-machine, checkpoint-attachment, and verifier-mode ambiguity.


---

1. Clarification 1 — Policy Engine vs. Permission Engine

Decision

There are two distinct concepts, but Phase 1 may implement them in one module.

Concept	Responsibility	Scope

Policy Engine	Decides whether a task may advance to approved_for_execution	Broad execution gate
Permission Engine	Enforces manifest-level tool/read/write permissions	Narrow zero-trust enforcement


Relationship

Policy Engine asks:
“May this task run at all?”

Permission Engine asks:
“May this task use this specific tool/read/write capability?”

Policy Engine checks

The Policy Engine evaluates:

sanitization_status
quarantine_flag
role_owner
parent_task_status
acceptance_criteria
resource_estimate
provider_budget_policy
checkpoint_status
manifest_presence
permission_engine_result

Permission Engine checks

The Permission Engine evaluates:

allowed_tools
forbidden_tools
allowed_read_scopes
allowed_write_fields
network_policy
sandbox_policy
memory_policy
budget_policy
manifest_expiry

Module map clarification

To avoid premature module sprawl, Phase 1 uses one implementation file:

core/
  permissions.py

Inside that module:

class PolicyEngine
class PermissionEngine

If implementation becomes too large, Kimi may split it later into:

core/policy_engine.py
core/permission_engine.py

but the architectural distinction remains.


---

2. Clarification 2 — Conditional State Machine

Decision

The lifecycle is branched, not universal.

Not every task traverses plan_checkpoint_pending or plan_checkpoint_passed.

Task classes

AXIOM has three task classes in Phase 1:

Task class	Description	Checkpoint required?

Goal-planning task	Converts human goal into proposed plan artifact	Yes
Planning task	Converts approved parent task into subtasks	Yes, but lighter subtask checkpoint
Execution task	Performs bounded tool action	No plan checkpoint; requires execution approval
Verification task	Checks output against criteria	No plan checkpoint; requires verifier policy approval


Revised branched lifecycle

A. Goal-planning task lifecycle

created
↓
ingress_sanitized
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

Failure branches:

plan_checkpoint_failed
quarantined
needs_human_input
failed

B. Task-planning lifecycle

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

C. Tool-execution lifecycle

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

D. Verification task lifecycle

created
↓
approved_for_execution
↓
running
↓
completed

Why branching is correct

Using no-op checkpoint states for every task would pollute the audit trail and make the system look more uniform than it really is. Branching better reflects actual responsibility while preserving queue-mediated coordination.


---

3. Clarification 3 — Plan Checkpoint State Attachment

Decision

Use option (a) from Claude’s review:

> The Goal Planner task transitions through checkpoint states. Child tasks are not committed to the task queue until the plan checkpoint passes.



Entity ownership

Entity	Carries checkpoint state?	Explanation

Goal Planner task	Yes	The task that generated the plan owns the checkpoint lifecycle
Plan artifact	Yes, but as artifact status	Stores proposed plan and checkpoint verdict
Child tasks	No	They do not exist in the task queue until the plan passes


Correct flow

Human goal
↓
Goal Planner task created
↓
Goal Planner produces proposed plan artifact
↓
Plan artifact stored in plan_artifacts
↓
Goal Planner task enters plan_checkpoint_pending
↓
Result Verifier runs in plan_checkpoint mode
↓
plan_checkpoints row created
↓
If passed: child tasks are committed to tasks table
↓
Goal Planner task marked child_tasks_committed/completed

Schema clarification

tasks table

The Goal Planner task contains:

task_id
status = plan_checkpoint_pending | plan_checkpoint_passed | child_tasks_committed | completed
checkpoint_id
plan_artifact_id

plan_artifacts table

The plan artifact contains:

plan_artifact_id
created_by_task_id
artifact_status = proposed | checkpoint_pending | checkpoint_passed | checkpoint_failed | quarantined
plan_json
created_at
updated_at

plan_checkpoints table

The checkpoint row contains:

checkpoint_id
plan_artifact_id
verifier_task_id
verdict = passed | failed | needs_revision | quarantine
verdict_reason
created_at

Child task creation rule

Child tasks are inserted only after:

plan_artifacts.artifact_status = checkpoint_passed
AND
plan_checkpoints.verdict = passed
AND
parent Goal Planner task status = plan_checkpoint_passed

Then child tasks enter:

created

They do not enter:

plan_checkpoint_pending

unless they later generate their own subtask plan.

Why this is the correct attachment point

The proposed plan is not execution reality. It is an artifact awaiting verification. The task queue should not contain executable child tasks until the plan is accepted. This prevents a bad Goal Planner output from becoming partially live system state.

This also aligns with the legacy finding that decomposition reliability was the weakest link and needed a checker before committing the task tree. 


---

4. Clarification 4 — Plan Checkpoint Verifier vs. Result Verifier

Decision

There is one verifier component operating in multiple modes.

The canonical role name is:

Result Verifier

But it has these modes:

Verifier mode	Used for	Output

plan_checkpoint	Goal Planner proposed plans	checkpoint verdict
subtask_checkpoint	Task Planner proposed subtasks	checkpoint verdict
tool_result	Tool Executor outputs	verification verdict
final_result	Parent-task completion	completion verdict
security_review	Quarantined or suspicious payloads	release/block/escalate verdict


Module map

agents/
  result_verifier.py

No separate plan_checkpoint_verifier.py is required in Phase 1.

Invocation pattern

Scheduler creates verifier task
↓
Context Builder supplies scoped evidence bundle
↓
Result Verifier runs in declared mode
↓
Verifier writes verdict only
↓
Scheduler applies state transition

Important boundary

The Result Verifier does not mutate the plan, child tasks, or tool output directly.

It writes:

verdict
verdict_reason
confidence
recommended_next_state

The Scheduler applies the actual transition.

This preserves the queue-mediated coordination model required by AXIOM Core Value 5 and the zero-trust boundary model in Core Value 3. 


---

5. Terminology Alignment Note

The operator has raised a valid nomenclature concern: Overseer / Taskmaster / Drone imply a command hierarchy, while AXIOM is a queue-mediated role system.

This addendum therefore uses the proposed role names:

Previous term	Preferred term

Overseer	Goal Planner
Taskmaster	Task Planner
Drone	Tool Executor
Verifier	Result Verifier


This naming change should be folded into the next full proposal revision, but it does not alter the architecture. It makes the architecture clearer.


---

6. Updated Architecture Summary After Addendum

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
Tool Gateways
  ├── Model Gateway
  ├── Memory Gateway
  ├── Network Gateway
  └── Sandbox Gateway
↓
SQLite Audit Log + JSONL Mirror

Final clarified position

Policy Engine = broad approval gate.
Permission Engine = manifest enforcement.
State machine = branched, not universal.
Plan checkpoint state belongs to the planning task and plan artifact.
Child tasks are committed only after checkpoint pass.
Result Verifier is one component with multiple modes.

7. Chief Architect Recommendation

Attach this addendum to AXIOM Proposal v1.1 and advance to DeepSeek V4 — Adversarial Critic.

The remaining questions are no longer coherence blockers. They are adversarial, factual, feasibility, and implementation questions, which belong to the next panel stages.

