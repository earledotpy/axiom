# AXIOM — Core Values
## Design Principles for the Multi-Agent Autonomous System Initiative

**Document Type:** Core Values Reference  
**Status:** Active — Ratified  
**Version:** 1.1  
**Supersedes:** v1.0 (May 2026)  
**Scope:** Design principles governing all architectural decisions  
**Ratification:** Ratified Cycle 3, 2026-05-10 by `AXIOM_Synthesis_Governance_v3.md`.

---

## Purpose

These values govern every architectural decision made in AXIOM. They are derived from nine phases of real build experience on constrained hardware. They represent what was learned about what makes an autonomous system trustworthy, maintainable, and operable by a single human.

They are not preferences. They are constraints on the design space.

They may be amended through the process defined in the Panel Charter. They are not deleted — only superseded by more specific versions when a compelling case is established by full panel consensus.

The v1.1 update adds operational clarifications for CV2, CV3, and CV5 as ratified in `AXIOM_Proposal_Governance_v1.2.md` §7 and §4.2. CV1, CV4, and CV6 carry forward from v1.0 unchanged.

---

## The Six Core Values

---

### 1. Autonomy with security baked in, not bolted on

Security is not a restriction on autonomy. It is what makes autonomy trustworthy. A system that operates without supervision must have security designed into its architecture from the first decision, not added afterward.

**What this means in practice:**
- Security boundaries are defined before the components they protect are built
- No component assumes trust from another component
- Audit trails exist before the system operates autonomously

**What violates this value:**
- Adding authentication after an agent is already communicating
- Designing an execution pipeline and then asking "how do we secure this?"
- Treating security as a Phase N concern when it is a Day 1 concern

---

### 2. Local model stays in its lane

The local model handles routing, private data, embeddings, and sanitization. All cognitive work goes to the cloud cascade. The local model is not upgraded to perform tasks beyond its defined scope without explicit architectural justification reviewed by the full panel.

**What this means in practice:**
- The local model is a classifier, a router, a sanitizer, and an embedding engine
- Complex reasoning, goal decomposition, and synthesis go to cloud models
- Local model scope changes require explicit panel approval
- The local model may classify whether content is safe to pass. It may not decide whether a plan is good, override manifests, expand its own tool permissions, or approve high-risk actions without deterministic policy backstops.

**Panel-approved sanitization mechanism:**

The local model remains in lane when used for routing, private data handling, embeddings, and sanitization. “Panel-approved sanitization task” means a sanitization use that is authorized by at least one of the following:

1. an active binding;
2. a panel-ratified design specification;
3. a Synthesis-authorized revision scope.

No per-task runtime panel approval is required. This is a documentation/process approval mechanism only. It does not add a runtime registry, thread, database table, API call, or model invocation.

The local model may classify whether content is safe to pass. It may not decide whether a plan is good, override manifests, expand its own tool permissions, or approve high-risk actions without deterministic policy backstops.

**What violates this value:**
- Routing a complex planning task to the local model to save API cost
- Expanding local model responsibilities without RAM accounting
- Treating the local model as a fallback for when cloud models are unavailable
- Allowing the local model's classification output to become the sole gate for high-risk operations without a deterministic backstop

---

### 3. Zero-trust at every agent boundary

Every agent sees only what it needs for its specific task. No agent can escalate its own permissions. No agent can instruct another agent directly. Coordination happens through authenticated, logged shared state only.

**What this means in practice:**
- Agent tool access is explicitly defined and enforced, not assumed
- No agent reads another agent's full context
- Every inter-agent interaction is logged with agent ID and task ID
- Governance procedures also follow anti-self-certification. Under the Integration Diff Gate, the author of a candidate revision may not certify that revision's Diff Gate result. If the Evaluator authored the candidate revision, the Research and Knowledge Arbiter serves as alternate Diff Gate gatekeeper for that artifact only.

**What violates this value:**
- An agent that can read the full task queue rather than its assigned task
- A Drone that can write to task structure fields it does not own
- Any direct agent-to-agent communication channel outside the shared queue
- A governance certifier approving its own revision without an independent Diff Gate check

---

### 4. Build simple, prove the concept, iterate into complexity

The minimum viable version is built first. Complexity is added only when the simple version demonstrably breaks or cannot achieve the goal. Speculative complexity is not added in advance of the problem it would solve.

**What this means in practice:**
- Phase N is not designed until Phase N-1 passes its acceptance criteria
- Features that "will be needed in Phase 12" are not built in Phase 10
- When two designs both solve the problem, the simpler one is implemented first

**What violates this value:**
- Adding parallel execution before sequential execution is proven stable
- Building a feature because it will "probably be needed later"
- Designing for scale the hardware cannot support

---

### 5. All inter-agent coordination through the task queue

No direct agent-to-agent channels exist at any tier. Coordination happens through the shared task queue. This is the architectural decision that makes the system auditable and limits blast radius when any single component fails or is compromised.

**What this means in practice:**
- An Overseer writes tasks to the queue; it does not call a Taskmaster directly
- A Taskmaster writes subtasks to the queue; it does not call a Drone directly
- A compromised Drone can only write to its own result field — it cannot instruct other agents
- Deterministic infrastructure is not agent coordination: boot-time validators, schedulers, and policy engines are infrastructure that runs the queue, not participants in it.

**Infrastructure guardrail enforcement:**

The CV5 clarification that deterministic infrastructure is not agent coordination is accepted with an implementation-stage enforcement requirement:

| Guardrail | Required Implementation-Stage Artifact |
|---|---|
| Schema enforcement | Kimi must define the relevant schema validation point before queue-writing implementation proceeds. Manifest-file validation remains subject to AB-006. |
| Structured logging | Kimi must specify structured JSON log fields for queue writes, including task ID, component ID, actor role, field changed, old status when applicable, new status when applicable, and timestamp. |
| Field-assignment registry | Kimi must create or reference `AXIOM_Field_Assignment_Register.md` before implementing task-queue write permissions. |

These requirements are not runtime infrastructure at governance-ratification time. They create no new process, thread, API budget, or model load.

---

**What violates this value:**
- Any function call from one agent to another outside the queue
- Shared memory between agents that is not mediated by the queue
- Event-based triggers that bypass the queue's sequencing logic

---

### 6. The sandbox and the network are never directly connected

Code execution is isolated. Network access goes through a controlled gateway only. An agent cannot bypass the network gateway by writing network code and executing it in the sandbox.

**What this means in practice:**
- The sandbox process runs under a restricted OS-level token with no network permissions
- Network access requires going through the fetch gateway, which enforces allowlisting
- Sandbox isolation is verified by test — not assumed from subprocess configuration

**What violates this value:**
- A sandbox that inherits the parent process's network permissions
- A fetch gateway with no allowlist enforcement
- Assuming subprocess.Popen provides network isolation on Windows (it does not)

---

## Amendment Log

| Version | Date | Value Amended | Amendment | Rationale | Panel Consensus |
|---|---|---|---|---|---|
| 1.0 | May 2026 | — | Initial values established | Derived from Phases 0–9 legacy build | Pre-panel founding document |
| 1.1 | 2026-05-10 | CV2 | Added panel-approved sanitization mechanism and safety/goodness boundary | Operationalizes local-model lane without adding runtime registry | Ratified Cycle 3 |
| 1.1 | 2026-05-10 | CV3 | Added governance anti-self-certification reference for Diff Gate | Applies zero-trust principle to integration verification | Ratified Cycle 3 |
| 1.1 | 2026-05-10 | CV5 | Added infrastructure guardrail enforcement requirements | Clarifies that deterministic infrastructure is not agent coordination while preserving implementation-stage enforcement | Ratified Cycle 3 |

---

*AXIOM Core Values — Version 1.1 — Ratified Cycle 3, 2026-05-10 by AXIOM_Synthesis_Governance_v3.md*
