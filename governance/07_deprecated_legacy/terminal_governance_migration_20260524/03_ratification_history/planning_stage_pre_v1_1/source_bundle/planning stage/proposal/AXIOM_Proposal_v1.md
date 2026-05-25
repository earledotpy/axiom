AXIOM Initial Ground-Up Architecture Proposal

Chief Architect Draft — Not Yet Panel-Approved

0. Proposal Status

Field	Value

Proposal type	Initial architecture proposal
Authority	Chief Architect draft only
Final decision?	No
Required next review	Claude coherence review → DeepSeek adversarial review → Gemini factual verification → Qwen feasibility review → Kimi implementation plan
Governing documents	Panel Charter, Constraints Register, Core Values, Legacy Reference


This proposal follows the AXIOM role structure: the Chief Architect originates the design but does not make the final decision unilaterally. The full panel must review and approve it before implementation. 


---

1. Highest-Level Decision 1 — Agent Hierarchy Structure

Proposal

AXIOM should use a three-tier logical hierarchy implemented as a single sequential runtime, not as concurrent independent agents.

Proposed hierarchy

Human Operator
   ↓
Telegram Gateway
   ↓
Session Controller
   ↓
Overseer
   ↓
Taskmaster
   ↓
Drone
   ↓
Result Verifier
   ↓
Telegram Gateway

Role definitions

Layer	Responsibility	Allowed to do	Not allowed to do

Telegram Gateway	Human interface	Receive commands, return status/results	Make architectural or task decisions
Session Controller	Runtime supervisor	Start session, validate config, load queue, enforce state machine	Perform reasoning work
Overseer	Goal decomposition	Convert human goal into task tree	Execute tools directly
Taskmaster	Task planning	Convert assigned task into executable subtasks	Talk directly to Drones
Drone	Tool execution	Execute one bounded operation	Modify task structure or spawn work
Result Verifier	Completion check	Check outputs against acceptance criteria	Rewrite the goal unless task fails


Core architectural choice

The “agents” are logical roles, not always separate processes.

For Phase 1, AXIOM should not run multiple autonomous agent processes in parallel. The hardware constraint is too tight: only about 2.0–2.3 GB runtime headroom is available after baseline operation, and concurrent subprocess execution risks forcing SATA SSD paging. 

Why this structure

Criterion	Assessment

Fits hardware	Yes — sequential execution avoids RAM spikes
Fits security model	Yes — each role has a bounded permission envelope
Fits auditability	Yes — each state transition can be logged
Fits core values	Yes — simple first, no direct agent-to-agent communication
Avoids ToonTown inheritance	Yes — keeps the useful hierarchy concept but redesigns execution semantics


Explicit rejection

Rejected: fully parallel multi-agent swarm

Reason: It violates the current hardware envelope. Parallel Taskmasters or Drones would likely exhaust available RAM and degrade into paging. The Constraints Register explicitly warns against unaccounted parallel subprocess execution. 

Rejected: single monolithic “super-agent”

Reason: It is simpler at first glance but worse for auditability, zero-trust boundaries, and task attribution. It would blur planning, execution, and verification into one opaque step.


---

2. Highest-Level Decision 2 — Coordination Model

Proposal

AXIOM should use a SQLite-backed task queue as the only coordination channel.

No direct agent-to-agent calls.
No shared mutable memory outside the queue.
No event bus in Phase 1.
No background autonomous side channels.

Coordination rule

Agents do not call agents.
Agents read assigned queue records.
Agents write bounded outputs back to the queue.
The scheduler advances task state.

Required task states

created
↓
sanitized
↓
planned
↓
approved_for_execution
↓
running
↓
awaiting_verification
↓
completed

failure states:
blocked
failed
needs_human_input
quarantined

Minimal task record

Field	Purpose

task_id	Stable unique task identifier
parent_task_id	Enables task tree
session_id	Links task to operating session
role_owner	Overseer, Taskmaster, Drone, Verifier
status	Queue state
priority	Execution ordering
input_payload	Sanitized task input
output_payload	Bounded result
tool_scope	Explicit allowed tools
created_at	Auditability
updated_at	Auditability
started_at	Watchdog support
completed_at	Runtime measurement
error_payload	Failure evidence
attempt_count	Retry control
quarantine_reason	Prompt-injection/security handling


Coordination invariants

Invariant	Reason

Only scheduler changes global task status	Prevents agents from advancing themselves
Drones can only write result fields	Limits blast radius
Taskmasters can create subtasks but cannot execute tools	Separates planning from action
Overseer can create task trees but cannot run code or fetch network data	Prevents top-level planner from becoming an unchecked actor
All writes pass through sanitizer	Prompt-injection control at the queue boundary


Why this model

This directly implements the AXIOM value that all inter-agent coordination goes through the task queue, and avoids the ToonTown weakness where the hierarchy existed mostly as routing intent rather than enforceable boundaries.  

Explicit rejection

Rejected: direct function calls between Overseer → Taskmaster → Drone

Reason: This violates the zero-trust coordination model. A compromised or confused upstream agent could directly influence downstream behavior without a durable audit boundary.

Rejected: in-memory queue only

Reason: It is simpler, but it fails recovery. AXIOM needs session restart safety, stuck-task recovery, and audit trails.


---

3. Highest-Level Decision 3 — Persistence Layer

Proposal

AXIOM should use SQLite as the primary persistence layer for Phase 1.

It should contain separate logical tables for:

sessions
tasks
task_events
memory_items
memory_vectors
tool_invocations
security_events
provider_usage
config_snapshots

Persistence decision

Component	Proposed storage

Task queue	SQLite tables
Audit log	SQLite append-only event table + JSONL log mirror
Semantic memory	SQLite + sqlite-vec
Provider usage	SQLite accounting table
Runtime config snapshot	SQLite table per session
Long artifacts	Filesystem, referenced from SQLite


Why SQLite

Criterion	Assessment

RAM footprint	Low
Operational complexity	Low
Windows compatibility	Strong
Single-human maintainability	Strong
Recovery after crash	Good with WAL + startup watchdog
Fits free/open-source constraint	Yes


The Legacy Reference records SQLite as one of the proven reliable ToonTown components, but this proposal does not inherit the old memory database blindly. It keeps SQLite because it fits AXIOM’s constraints on its own merits: single-file persistence, low dependency cost, and acceptable reliability on constrained hardware. 

Required database properties

Property	Requirement

Journal mode	WAL
Busy timeout	Required
Schema migrations	Explicit version table
Task writes	Transactional
Memory writes	Deduplicated before insert
Audit events	Append-only
Large payloads	Stored as files with hash references
Startup recovery	Reset stale running tasks to pending or blocked based on policy


Memory model

AXIOM should maintain two separate concepts:

Operational State ≠ Semantic Memory

Type	Purpose	Example

Operational state	Current task execution	pending task, running task, tool output
Semantic memory	Long-term knowledge	architecture decision, user instruction, project fact


Memory insertion should require:

1. Sanitization


2. Deduplication check


3. Source attribution


4. Embedding model metadata


5. Write audit event



The legacy build suffered duplicate memory entries and degraded memory quality. AXIOM should fix this at insert time rather than by cleanup later. 

Explicit rejection

Rejected: ChromaDB or heavier vector database for Phase 1

Reason: The system does not need a heavier service-oriented vector stack yet. It adds dependency and RAM complexity before the simple SQLite/sqlite-vec path fails.

Rejected: filesystem-only persistence

Reason: Simple file logs are not enough for task state transitions, retries, queue queries, and recovery.


---

4. Highest-Level Decision 4 — Execution Model

Proposal

AXIOM should use a sequential state-machine execution model.

Phase 1 should run one active task operation at a time.

load next eligible task
↓
validate permissions
↓
prepare bounded context
↓
call model or tool
↓
write result
↓
verify result
↓
advance queue

Execution layers

Layer	Responsibility

Scheduler	Chooses next task
Permission Gate	Confirms role/tool access
Context Builder	Provides only required context
Model Gateway	Routes cognitive work to cloud/local model
Tool Gateway	Executes approved tools
Sandbox Runner	Executes code with no direct network
Network Gateway	Performs allowlisted external fetches
Verifier	Checks result against acceptance criteria
Logger	Records every transition


Local/cloud model split

Work type	Proposed destination

Routing	Local model
Sanitization	Local model
Embeddings	Local embedding model
Private/local memory handling	Local
Complex reasoning	Cloud cascade
Goal decomposition	Cloud cascade
Synthesis	Cloud cascade
Verification	Prefer cloud when budget allows; local only for narrow checks


This follows the AXIOM value that the local model stays in its lane: routing, private data, sanitization, and embeddings. Complex cognitive work should not be pushed onto the local model merely to save API usage. 

Sandbox/network separation

The execution model must enforce this hard boundary:

Sandboxed code execution cannot access the network.
Network access cannot execute arbitrary code.

Required Phase 1 design:

Component	Rule

Sandbox Runner	No network permissions
Network Gateway	Allowlisted fetch only
Code Drone	Cannot call network directly
Web Drone	Cannot execute generated code
Tool result	Sanitized before queue write


The Core Values explicitly state that sandbox and network must never be directly connected, and the Legacy Reference confirms that subprocess.Popen alone does not provide network isolation on Windows.  

Explicit rejection

Rejected: autonomous continuous loop with broad permissions

Reason: Too dangerous for Phase 1. AXIOM should operate autonomously only through bounded queue steps, explicit permissions, and logged state transitions.

Rejected: agent framework first, architecture second

Reason: AXIOM should not choose a framework before defining the security, queue, persistence, and execution boundaries. A framework may be evaluated later, but it should not define the architecture.


---

5. Proposed Phase 1 System Shape

Minimal viable AXIOM

Telegram Bot
   ↓
Command Parser
   ↓
Session Controller
   ↓
SQLite Task Queue
   ↓
Sequential Scheduler
   ↓
Role Executor
   ├── Overseer mode
   ├── Taskmaster mode
   ├── Drone mode
   └── Verifier mode
   ↓
Tool Gateways
   ├── Model Gateway
   ├── Memory Gateway
   ├── Network Gateway
   └── Sandbox Gateway
   ↓
SQLite Audit + JSONL Logs

Core runtime services

Service	Phase 1 status	Notes

Telegram Gateway	Required	Sole autonomous-operation interface
Session Controller	Required	Validates environment before launch
SQLite Queue	Required	Central coordination mechanism
Sequential Scheduler	Required	No parallel task execution
Model Gateway	Required	Cloud cascade + local routing
Memory Gateway	Required	SQLite/sqlite-vec with dedup
Network Gateway	Required	Replaces broken DuckDuckGo path
Sandbox Gateway	Required before code execution	No direct network
Audit Logger	Required	JSONL + SQLite events
Watchdog	Required	Recovers stale running tasks



---

6. Provider and Model Policy

Proposal

AXIOM should use a provider-agnostic model gateway rather than hardcoding the cloud cascade into agent logic.

Agent role requests capability
   ↓
Model Gateway checks policy
   ↓
Provider selected
   ↓
Usage logged
   ↓
Response normalized
   ↓
Result returned to queue

Provider policy table

Capability	Preferred source	Fallback behavior

Fast decomposition	Free-tier cloud model	Try next provider
Large-context synthesis	Large-context provider	Defer or split task
Verification	Cloud if budget available	Narrow local check
Routing	Local model	Deterministic rules fallback
Embeddings	Local embedding model	Block memory write if unavailable


Required usage accounting

Every model call writes:

provider
model
task_id
agent_role
estimated_input_tokens
estimated_output_tokens
success/failure
error_type
timestamp

Reason: the legacy build exhausted Groq’s daily token limit during testing, so AXIOM needs budget-aware routing from the beginning. 


---

7. Security Boundaries

Required boundaries

Boundary	Enforcement

Human → Telegram Gateway	Whitelisted user ID
Telegram → Queue	Command parser + sanitizer
Queue → Agent role	Assigned task only
Agent → Tool	Permission manifest
Tool → Queue	Sanitized result write
Code → Network	Forbidden
Network → Code	Forbidden
Memory write	Dedup + source + sanitizer
Model output → Task mutation	Verifier or scheduler mediation


Prompt injection defense

Prompt injection should be handled at write time, not read time.

external content fetched
↓
sanitizer labels unsafe instructions/data
↓
safe representation written to queue
↓
agent reads sanitized version only

The Legacy Reference identifies lack of prompt-injection defense as a major unresolved failure and records pre-rebuild consensus that sanitization should occur at the task queue write boundary. 


---

8. Component Evaluation Against Constraints

Component	Accept / Reject / Defer	Reason

Telegram interface	Accept	Hard interface constraint
SQLite queue	Accept	Low RAM, durable, auditable
sqlite-vec memory	Accept	Fits local persistence model
Sequential scheduler	Accept	Required by RAM envelope
Parallel Taskmasters	Reject for Phase 1	RAM risk
Direct agent calls	Reject	Violates queue-mediated coordination
Local model for complex reasoning	Reject	Violates local-model lane
Cloud cascade	Accept with redesign	Must be provider-agnostic and budget-aware
DuckDuckGo package search	Reject	Legacy structural failure
Network gateway	Accept	Required for controlled fetch
Sandbox execution	Accept only with isolation	Must not inherit network permissions
Full autonomous daemon/service	Defer	Start with session model first
Agent framework dependency	Defer	Evaluate after core boundaries are implemented



---

9. First Architectural Specification Draft

AXIOM Phase 1 should implement these modules

axiom/
  app/
    telegram_gateway.py
    session_controller.py
    command_parser.py

  core/
    scheduler.py
    state_machine.py
    permissions.py
    context_builder.py

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

  persistence/
    db.py
    schema.sql
    migrations/
    repositories.py

  security/
    sanitizer.py
    prompt_injection_labels.py
    auth.py
    audit.py

  tools/
    file_tools.py
    search_tools.py
    code_tools.py

  logs/
    jsonl_logger.py

  tests/
    test_queue_boundaries.py
    test_sandbox_no_network.py
    test_task_state_machine.py
    test_memory_dedup.py

This is not yet an implementation plan. It is the proposed architectural decomposition for panel review.


---

10. Acceptance Criteria for Phase 1 Architecture

AXIOM Phase 1 is architecturally acceptable only if these pass:

Test	Acceptance criterion

Queue mediation	No agent can call another agent directly
Role isolation	Drone cannot modify task structure
Scheduler control	Only scheduler advances task lifecycle
RAM discipline	No parallel agent execution required
Telegram operation	Human can start, submit, inspect, and stop through Telegram
Cloud budget control	Provider usage is logged per task
Memory dedup	Duplicate semantic writes are blocked or linked
Prompt injection handling	External text is sanitized before queue insertion
Sandbox isolation	Code execution cannot reach the network
Network control	Fetches go through allowlisted gateway
Crash recovery	Stale running tasks are detected on startup
Auditability	Every task transition has task_id, role, timestamp, and event type



---

11. Known Design Tensions for Panel Review

Tension 1 — Verifier placement

Option	Tradeoff

Verifier after every Drone result	Safer, slower, more API usage
Verifier only after task completion	Cheaper, weaker containment
Local verifier for narrow checks	Cheap, lower reasoning quality


Architect recommendation: Use verifier after every state-changing Drone action, but allow deterministic verification where possible.


---

Tension 2 — Local sanitization reliability

The local model is proposed as a semantic firewall, but this needs panel scrutiny. It fits the budget and privacy constraints, but it may miss subtle prompt injection. The fallback should be rule-based labels plus conservative quarantine.

Architect recommendation: Local sanitizer first; quarantine uncertain inputs rather than passing them through.


---

Tension 3 — Cloud cascade complexity

A provider-agnostic gateway is necessary, but overbuilding it risks violating the simplicity value.

Architect recommendation: Implement only three provider states in Phase 1:

available
rate_limited
failed

Do not build advanced scoring, latency optimization, or model benchmarking yet.


---

Tension 4 — Service mode versus session mode

Legacy ToonTown’s session model was stable. A Windows service may improve autonomy but adds credential, startup, and debugging complexity.

Architect recommendation: Phase 1 should use session mode. Service mode should be deferred until the queue, logs, and watchdog are proven stable.


---

12. Initial Chief Architect Recommendation

AXIOM should begin as a sequential, queue-mediated, SQLite-backed, Telegram-operated autonomous system with strict role boundaries and no parallel agent execution.

The core architectural stance is:

Logical multi-agent system.
Physical single-process/sequential runtime at first.
SQLite task queue as the coordination spine.
Cloud models for cognition.
Local model for routing, sanitization, private data, and embeddings.
Sandbox and network separated by design.

This is the smallest architecture that still preserves AXIOM’s non-negotiables: autonomy, auditability, security boundaries, hardware feasibility, and single-human operability.