# AXIOM — Core Values
## Design Principles for the Multi-Agent Autonomous System Initiative

**Document Type:** Core Values Reference
**Status:** Proposed Amendment — Awaiting Panel Consensus
**Version:** 1.1 (proposed)
**Supersedes:** v1.0 (May 2026)
**Scope:** Design principles governing all architectural decisions

---

## Purpose

These values govern every architectural decision made in AXIOM. They are derived from nine phases of real build experience on constrained hardware. They represent what was learned about what makes an autonomous system trustworthy, maintainable, and operable by a single human.

They are not preferences. They are constraints on the design space.

They may be amended through the process defined in the Panel Charter. They are not deleted — only superseded by more specific versions when a compelling case is established by full panel consensus.

**Note on v1.1:** The six values held intact through 13 architecture revisions and one full implementation cycle. No core value was contradicted by execution. The v1.1 changes are clarifications drawn from how the values were operationalized during the build, not new principles.

---

## The Six Core Values

---

### 1. Autonomy with security baked in, not bolted on

Security is not a restriction on autonomy. It is what makes autonomy trustworthy. A system that operates without supervision must have security designed into its architecture from the first decision, not added afterward.

**What this means in practice:**
- Security boundaries are defined before the components they protect are built
- No component assumes trust from another component
- Audit trails exist before the system operates autonomously
- **Security guarantees verified only at boot are insufficient when the verified property can drift during a session** (added v1.1, derived from the v1.10 mid-session model fingerprint discussion)

**What violates this value:**
- Adding authentication after an agent is already communicating
- Designing an execution pipeline and then asking "how do we secure this?"
- Treating security as a Phase N concern when it is a Day 1 concern
- Naming a security mechanism without specifying how it produces the claimed property — "labeled box" syndrome (added v1.1, derived from PlanInjectionScanner specification gaps in v1.1–v1.3)

---

### 2. Local model stays in its lane

The local model handles routing, private data, embeddings, and **sanitization**. All cognitive work goes to the cloud cascade. The local model is not upgraded to perform tasks beyond its defined scope without explicit architectural justification reviewed by the full panel.

**What this means in practice:**
- The local model is a classifier, a router, a sanitizer (including injection scanning), and an embedding engine
- Complex reasoning, goal decomposition, and synthesis go to cloud models
- Local model scope changes require explicit panel approval
- The local model may classify whether content is safe; it may not decide whether plans are good or whether to override manifests (clarification added v1.1)

**What violates this value:**
- Routing a complex planning task to the local model to save API cost
- Expanding local model responsibilities without RAM accounting
- Treating the local model as a fallback for when cloud models are unavailable
- Allowing the local model's classification output to be the sole gate for high-risk operations without a deterministic backstop (added v1.1)

---

### 3. Zero-trust at every agent boundary

Every agent sees only what it needs for its specific task. No agent can escalate its own permissions. No agent can instruct another agent directly. Coordination happens through authenticated, logged shared state only.

**What this means in practice:**
- Agent tool access is explicitly defined and enforced, not assumed
- No agent reads another agent's full context
- Every inter-agent interaction is logged with agent ID and task ID
- **Permission enforcement is architectural, not by convention** — string-equality checks on a `created_by_component` field do not enforce a trust boundary; thread-identity assertion or structural import-graph isolation does (clarification added v1.1, derived from v1.6 spoof protection review)

**What violates this value:**
- An agent that can read the full task queue rather than its assigned task
- A Drone that can write to task structure fields it does not own
- Any direct agent-to-agent communication channel outside the shared queue
- A capability check that can be bypassed by any caller passing the correct argument string (added v1.1)

---

### 4. Build simple, prove the concept, iterate into complexity

The minimum viable version is built first. Complexity is added only when the simple version demonstrably breaks or cannot achieve the goal. Speculative complexity is not added in advance of the problem it would solve.

**What this means in practice:**
- Phase N is not designed until Phase N-1 passes its acceptance criteria
- Features that "will be needed in Phase 12" are not built in Phase 10
- When two designs both solve the problem, the simpler one is implemented first
- **Specification gaps are debt; they accumulate interest** (added v1.1; see Charter §Specification Debt) — a labeled component without a defined mechanism is not a simple version of that component, it is an absent component

**What violates this value:**
- Adding parallel execution before sequential execution is proven stable
- Building a feature because it will "probably be needed later"
- Designing for scale the hardware cannot support
- Carrying a specification gap across multiple cycles by relabeling it as "future work" without formal deferral (added v1.1)

---

### 5. All inter-agent coordination through the task queue

No direct agent-to-agent channels exist at any tier. Coordination happens through the shared task queue. This is the architectural decision that makes the system auditable and limits blast radius when any single component fails or is compromised.

**What this means in practice:**
- An Overseer writes tasks to the queue; it does not call a Taskmaster directly
- A Taskmaster writes subtasks to the queue; it does not call a Drone directly
- A compromised Drone can only write to its own result field — it cannot instruct other agents
- **Deterministic infrastructure is not agent coordination** (clarification added v1.1) — boot-time validators, schedulers, and policy engines are infrastructure that runs the queue, not participants in it

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
- **On Windows, isolation requires a dedicated user account with a firewall outbound-deny rule scoped to that SID, or AppContainer with `internetClient` capability dropped** (Arbiter binding from v1.2; recorded here for visibility)
- **Network gateway must not follow HTTP redirects automatically; redirect chains must be traversed manually with allowlist enforcement at each hop** (Arbiter binding from v1.11.3)

**What violates this value:**
- A sandbox that inherits the parent process's network permissions
- A fetch gateway with no allowlist enforcement
- Assuming subprocess.Popen provides network isolation on Windows (it does not)
- A sandbox sized only for RAM with no wall-clock cap (added v1.1, derived from v1.8.1 sandbox/heartbeat alignment)

---

## Amendment Log

| Version | Date | Value Amended | Amendment | Rationale | Panel Consensus |
|---|---|---|---|---|---|
| 1.0 | May 2026 | — | Initial values established | Derived from Phases 0–9 legacy build | Pre-panel founding document |
| 1.1 | May 2026 (proposed) | CV1 | Added "verified-only-at-boot is insufficient" clarification | Mid-session fingerprint drift discussion in v1.10 | **Pending** |
| 1.1 | May 2026 (proposed) | CV1 | Added "labeled box" anti-pattern to violations | PlanInjectionScanner gap recurred across v1.1–v1.3 | **Pending** |
| 1.1 | May 2026 (proposed) | CV2 | Made "sanitization" explicit in the lane definition (it was always present in the v1.0 violation list but not the practice list) | Evaluator made an error in v1.1 review treating sanitization as a scope expansion when it was already in the lane | **Pending** |
| 1.1 | May 2026 (proposed) | CV2 | Added "classify safety, not goodness" boundary | v1.1 architect/evaluator scope dispute | **Pending** |
| 1.1 | May 2026 (proposed) | CV3 | Added "architectural, not by convention" enforcement clarification | v1.6 OperatorControlInserter spoof-protection review | **Pending** |
| 1.1 | May 2026 (proposed) | CV4 | Added specification-gap-as-debt clarification | DeepSeek Obj 2/5/8 carried across three cycles | **Pending** |
| 1.1 | May 2026 (proposed) | CV5 | Added "infrastructure vs coordination" clarification | v1.5 bootstrap-mode validation routing question | **Pending** |
| 1.1 | May 2026 (proposed) | CV6 | Added Windows sandbox isolation specifics and HTTP redirect handling as recorded Arbiter bindings | v1.2 sandbox ruling, v1.11.3 redirect ruling | **Pending** |
| 1.1 | May 2026 (proposed) | CV6 | Added wall-clock cap to violations | v1.8.1 sandbox/heartbeat alignment | **Pending** |

*All future amendments are recorded in this log.*

---

## What v1.1 is not

v1.1 does not add a seventh value. The six values held. Several recurring failure patterns (specification debt, integration regression, cross-cutting artifact ownership) are governance issues addressed in the Charter, not value-level principles.

The temptation during a long build is to promote every operational lesson to a Core Value. That temptation is itself a Core Value 4 violation: speculative complexity in the governance layer. The panel resisted it.

---

*AXIOM Core Values — Version 1.1 (proposed) — May 2026*
