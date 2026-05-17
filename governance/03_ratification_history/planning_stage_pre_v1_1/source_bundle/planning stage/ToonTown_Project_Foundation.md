# ToonTown — Project Foundation Document
## Retrospective Reference and Design Brief for Multi-System Rebuild

**Document Type:** Project Foundation — Cold-Start Reference  
**Status:** Active  
**Version:** 1.0  
**Scope:** Complete retrospective of Phases 0–9, core values, governance model, and rebuild brief  

---

## Purpose of This Document

This document is the authoritative starting point for the ToonTown rebuild. It is written to be fully self-contained. Any capable AI system reading it without prior context should be able to understand what has been built, what worked, what failed, what is being rebuilt, and what rules govern the process.

This is not a technical specification. It is a foundation document. Technical specifications are produced by the design panel working from this foundation.

---

## 1. What ToonTown Is

ToonTown is a local-first autonomous multi-agent AI system. It runs on a single constrained laptop. It is operated and built by one human. Its interface is a mobile messaging app.

The goal of ToonTown is to create a system that can accept high-level goals, decompose them into executable work, carry out that work autonomously using a hierarchy of specialized AI agents, and deliver results — without requiring the human operator to supervise each step.

ToonTown is not a product. It is not a framework built on top of an existing orchestration library. It is a ground-up implementation built to run within specific hardware and budget constraints that most comparable systems do not face.

---

## 2. Physical Constraints

These are permanent hardware constraints, not preferences. All design decisions must be evaluated against them.

**Primary compute device:** HP laptop with Intel Celeron N4500 processor  
**RAM:** 8 GB total system memory  
**Storage:** SATA SSD  
**GPU:** None  
**Operating system:** Windows 11  
**Network:** Standard home internet connection  

**Mobile interface device:** Google Pixel 8a (Android)  
**Interface protocol:** Telegram bot  

**Observed RAM baseline at runtime:** Approximately 5.7 GB consumed during normal ToonTown operation, leaving approximately 2 GB headroom for agent processes.

**Budget:** Free or near-zero API cost. Cloud models used via free tiers and low-cost API providers only.

These constraints are non-negotiable. They are not obstacles to route around — they are the design surface. Any proposal that requires hardware not listed above, or API costs that cannot be sustained on a free or minimal-spend budget, must explicitly account for this.

---

## 3. Build History — Phases 0 Through 9

ToonTown was built across nine phases between mid-March 2026 and April 7, 2026. All phases were completed and accepted before the rebuild decision was made.

### Phase Summary

**Phase 0–3 — Foundation**  
Established the core runtime: Python virtual environment, Telegram bot integration, Ollama local model server, SQLite memory database (toontown_memory.db), and the Open Brain memory tool. The basic session model was defined: the human starts a session via a batch file, the Telegram bot becomes active, and agents respond to messages.

**Phase 4 — Memory and Retrieval**  
Integrated sqlite-vec for vector search. Implemented semantic memory storage and retrieval using nomic-embed-text embeddings via Ollama. Memory commands (REMEMBER, RECALL, BACKUP) established and tested.

**Phase 5–6 — Agent Hierarchy**  
Introduced the multi-agent structure using the smolagents framework. Established the Telegram agent as the primary interface layer, with routing logic to specialized agents: Overseer, Taskmasters (Research, Coding, Analysis), and Drones (Web, Search, Code, File, Memory). Routing instructions appended to the default system prompt.

**Phase 7–8 — Cloud Cascade and Model Routing**  
Established the cloud cascade: Cerebras as primary, Groq as first fallback, OpenRouter as second fallback, SambaNova as third fallback. Local model (qwen3:4b via Ollama) assigned strictly to routing decisions, private data handling, and embeddings. Extended thinking mode disabled on qwen3:4b via extra_body parameter.

**Phase 9 — Stability and Hardening**  
Resolved critical runtime failures:  
- asyncio and concurrent.futures conflicts resolved by moving imports to top-level in agent.py  
- smolagents 1.12.0 removed LiteLLMRouterModel — manual cascade written as replacement  
- Telegram bot monkey-patch applied to sat on_message for correct message handling  
- PromptTemplates replaced with prompt_templates append  
- ROUTING_INSTRUCTIONS appended to default system prompt  
- final_answer("done") added to routing instructions to prevent infinite loops  
- BRAIN_TOKEN validation added to start_session.bat before bot launch  
- icacls permission commands require literal username, not %USERNAME% variable  
- sc.exe must be called as & "$env:SystemRoot\System32\sc.exe" in PowerShell  

Phase 9 acceptance testing passed all criteria on April 7, 2026.

---

## 4. What Worked

The following elements functioned as intended and represent proven patterns worth carrying forward into the rebuild.

**SQLite as the persistence layer.** toontown_memory.db proved reliable for both structured data and vector search via sqlite-vec. The single-file pattern works well on constrained hardware. No dependency issues.

**nomic-embed-text via Ollama for embeddings.** Ran locally without GPU. Adequate quality for semantic memory retrieval. Low RAM overhead.

**Cerebras as primary cloud model.** qwen-3-235b-a22b-instruct-2507 on Cerebras provided fast, capable responses on the free tier. Became the primary after Groq daily token limits were exhausted during Phase 9 testing.

**Telegram as the interface.** Python Telegram Bot library integrated cleanly. Mobile-first interface matched the use case. Session-started bot model (not webhook) worked reliably on the constrained network environment.

**The session model.** Starting ToonTown via start_session.bat, validating credentials, launching the bot, and running until manually stopped — this pattern was stable and debuggable.

**The cloud cascade concept.** Routing through multiple free-tier providers in priority order proved resilient. When one provider hit limits, the next picked up. The cascade pattern should be preserved in the rebuild.

**Routing instructions via system prompt.** Appending ROUTING_INSTRUCTIONS to the default system prompt was the correct pattern for directing agent behavior without hard-coded logic.

---

## 5. What Did Not Work as Intended

The following elements were identified as failing, partially failing, or requiring architectural reconsideration before the rebuild decision was made.

**Web search was broken at Phase 9 acceptance.** The duckduckgo_search package was blocking all requests. DuckDuckGo has no official API and actively rate-limits automated traffic. This is structural, not fixable. Web search was non-functional throughout most of Phase 9 testing.

**The Overseer had no ToonTown system context.** The Overseer (ask_overseer tool via Cerebras) was called with no system prompt. It answered as a generic AI with no awareness of ToonTown, its architecture, its constraints, or its purpose. During Phase 9 testing, it confused ToonTown with an unrelated product. No persistent context was ever written for it.

**Duplicate memory entries from test runs.** Multiple test writes to Open Brain during Phase 9 created duplicate records. No deduplication logic existed at the insert level. This left the memory database in a degraded state.

**Groq daily token limit exhausted during testing.** Groq's 10K daily token limit was hit during Phase 9 acceptance testing. This exposed a vulnerability in the cascade: if Cerebras fails and Groq is at its limit, the system has no cognitive fallback until the limit resets.

**The three-tier agent hierarchy was defined but not fully implemented.** The Phase 9 system had agent routing logic and named roles (Overseer, Taskmasters, Drones), but the actual specialization was incomplete. Taskmasters and Drones did not operate with distinct tool boundaries or genuine context blindness. The hierarchy was architectural intent, not functional reality.

**NSSM was selected for the Phase 10 scheduler service before evaluation.** The Phase 10 plan specified NSSM (Non-Sucking Service Manager) as the Windows service wrapper without comparing alternatives. Post-planning research identified that NSSM has not been actively maintained since 2017 and has documented credential access problems in Windows Session 0 (services cannot access user-level environment variables). Servy was identified as an actively maintained alternative with first-class environment variable support.

**No sandboxed code execution existed.** The Phase 10–12 plan called for a sandboxed execution environment in Phase 11, but no isolation existed in the Phase 9 system. subprocess.Popen inherits parent process network permissions on Windows, which means generated code could make outbound network calls without restriction.

**No prompt injection defense existed.** No sanitization occurred at the task queue write boundary. External content fetched by agents could carry embedded instructions that downstream agents would execute without awareness.

---

## 6. What Was Being Decided at the Pivot Point

When the rebuild decision was made, the following decisions had been reached or were in progress for Phase 10:

- Replace NSSM with Servy for Windows service management
- Replace duckduckgo_search with Brave Search API
- Add stuck-task watchdog to scheduler startup (reset status = 'running' to 'pending')
- Add structured JSON logging with task ID correlation from Phase 10 forward
- Write an Overseer system prompt that reflects the Phase 12 vision (Tier 1 orchestrator, goal decomposer, never executes)
- Defer token-cost estimation flag to Phase 12 scope
- Address LLM Tagging (agent output provenance markers) as Phase 10 or Phase 11 scope
- Add pre-insertion cosine similarity check to memory writes (~0.92 threshold)

These decisions are carried forward as inputs to the rebuild design process. They are not binding. The design panel should evaluate them independently.

---

## 7. Core Values

These values governed the Phase 0–9 build and carry forward into the rebuild. They are treated as the design foundation, not as open questions. They may be amended if a compelling argument is made and consensus among the design panel is reached that an amendment is inherently beneficial to the project as a whole.

**Autonomy with security baked in, not bolted on.**  
Security is not a constraint on autonomy. It is what makes autonomy trustworthy. A system that operates without supervision must have security designed into its architecture from the first decision, not added afterward.

**Local model stays in its lane.**  
The local model handles routing, private data, and embeddings. All cognitive work goes to the cloud cascade. The local model is not upgraded to perform tasks beyond its defined scope without explicit architectural justification.

**Zero-trust at every agent boundary.**  
Every agent sees only what it needs for its specific task. No agent can escalate its own permissions. No agent can instruct another agent directly. Coordination happens through authenticated, logged shared state only.

**Build simple, prove the concept, iterate into complexity.**  
The minimum viable version is built first. Complexity is added only when the simple version breaks or demonstrably cannot achieve the goal. Speculative complexity is not added in advance.

**All inter-agent coordination through the task queue.**  
No direct agent-to-agent channels exist at any tier. Coordination happens through the shared task queue. This is the architectural decision that makes the system auditable and limits blast radius when any single component fails or is compromised.

**The sandbox and the network are never directly connected.**  
Code execution is isolated. Network access goes through a controlled gateway only. An agent cannot bypass the network gateway by writing network code and executing it in the sandbox.

**Proof-driven development.**  
Each phase is proven to work before the next phase begins. Acceptance criteria are defined before implementation begins. A phase is not complete until it passes its criteria.

---

## 8. Design Panel and Governance

ToonTown is rebuilt by a panel of six AI systems working collaboratively. The human operator acts as the physical abstraction layer — reading proposals, executing file operations, writing code to disk, and running tests. The human does not make design decisions. The panel does.

### Panel Members and Roles

**GPT-5.5 — Chief Architect**  
Responsible for producing initial system designs, decomposing goals into architectural proposals, and synthesizing panel input into coherent specifications. First mover on design questions.

**Claude Opus 4.7 — Quality and Coherence Evaluator**  
Responsible for reviewing proposals for logical consistency, internal coherence, and long-horizon correctness. Identifies logical faults in planning before they reach implementation. Final check before a proposal enters the queue.

**Gemini 3.1 Pro — Research and Knowledge Arbiter**  
Responsible for verifying factual claims, evaluating external tools and libraries against current state, and providing grounded real-world context. When the panel needs a factual question settled, Gemini settles it.

**DeepSeek V4 — Adversarial Critic**  
Responsible for challenging every proposal. Finds failure modes, stress-tests assumptions, and identifies what the proposal gets wrong. DeepSeek's objections are overruled only if both Gemini (facts) and Qwen (constraints) find them unsupported by evidence.

**Qwen 3.6 Plus — Constraints and Feasibility Reviewer**  
Responsible for evaluating every proposal against the physical hardware constraints, API budget limits, and RAM accounting on the Celeron N4500. If a proposal cannot run on the hardware or cannot be sustained within the budget, Qwen flags it. Qwen's feasibility verdict on hardware questions is binding unless overturned by panel consensus.

**Kimi K2.6 — Implementation Specialist**  
Responsible for translating approved designs into concrete, executable implementation plans. Produces the step-by-step specifications that the human operator executes. Works at the boundary between architecture and code.

### Decision Flow

Architect proposes → Evaluator checks coherence → Critic challenges → Arbiter verifies facts → Constraints reviewer approves or blocks on feasibility → Implementation Specialist produces the execution plan.

### Conflict Resolution

When panel members disagree, the following hierarchy applies:

1. Factual disputes are resolved by Gemini.
2. Hardware feasibility disputes are resolved by Qwen.
3. Security disputes require consensus between the Evaluator and the Critic.
4. Architectural disputes are resolved by majority panel vote, with the Architect breaking ties.
5. Amendments to Core Values require full panel consensus and a written rationale.

The human operator does not vote. The human operator executes the outcome.

---

## 9. Rebuild Brief

The rebuild starts from a clean slate. Existing code may be referenced and selectively reused, but no component is inherited automatically. Every component is re-evaluated.

**What carries forward by default:**
- SQLite as persistence layer
- Telegram as the interface
- Ollama for local model serving
- nomic-embed-text for embeddings
- The cloud cascade pattern
- The core values listed in Section 7

**What is open for redesign:**
- Agent framework (smolagents was used in Phase 0–9; the panel may propose alternatives or a custom implementation)
- Agent hierarchy structure and tier definitions
- Tool architecture and tool boundaries
- Scheduler implementation
- Memory architecture
- Security and sandboxing approach
- Model assignments across the cascade

**What the rebuild must achieve:**
- A system that operates autonomously between sessions
- A system that accepts high-level goals and decomposes them into executable work
- A system that runs reliably within the hardware constraints defined in Section 2
- A system where every agent boundary is enforced and auditable
- A system where the human operator can read a log and understand exactly what happened and why

**First deliverable from the design panel:**
A ground-up architecture proposal that addresses the failures listed in Section 5, respects the core values in Section 7, and can realistically run on the hardware defined in Section 2. The Architect leads. All other panel members review against their assigned roles before the proposal is accepted.

---

*ToonTown Project Foundation Document — Version 1.0 — May 2026*  
*Reference the original Phase 0–9 build sessions for complete implementation history.*
