# Deep Research Report: Autonomous Agent-to-Agent Communication

**Date:** 2026-05-29  
**Subject:** Analysis of `/ipc` and Architecture for Autonomous Agent Messaging

## 1. Analysis of the Current `/ipc` Setup

The current `/ipc` system represents a hybrid manual/event-driven bridge designed to decouple agent execution from manual human routing. 

### How it currently works:
* **Storage & Indexing:** Messages are written to human-readable markdown files (`to_{agent}.md`) via `send.ps1`, which uses an OS-level Mutex to prevent race conditions. Simultaneously, the message is logged into a SQLite database (`ipc_messages.db`) for deduplication and read-state tracking via `ipc_db.py`.
* **Event Loop:** `agent_bridge.ps1` runs a continuous `FileSystemWatcher` on the inbox. When a write occurs, it queries the SQLite DB for unprocessed messages.
* **Execution:** The script extracts the message body and invokes the target agent directly (using standard input for Codex, and a ConPTY capture for Antigravity). 
* **Response Routing:** Once the agent returns output, the bridge marks the message as `processed=1` and fires `send.ps1` to route the answer back to the original sender.

### Shortcomings & Limitations:
1. **Primitive Loop Prevention:** `agent_bridge.ps1` hard-stops execution if the subject starts with `"re: "` or `"re:"`. This forcefully prevents infinite reply loops, but completely breaks conversational state. Agents cannot have a multi-turn back-and-forth dialogue.
2. **Loss of Context:** Agents are invoked from a cold start for every message (via CLI arguments or STDIN). They have no inherent memory of the overarching task.
3. **Unstructured Payloads:** Messages are raw strings. The receiving agent doesn't know if it's receiving a strict command, a request for information, or a status update.

---

## 2. Methodology: How to Research and Plan a Robust System

If we were to build a native, fully autonomous messaging system from the ground up, the methodology requires moving away from shell scripting and towards established distributed systems paradigms.

### Research Vectors
1. **The Actor Model:** Systems like Erlang/OTP or Akka treat agents as isolated actors that communicate strictly through message passing. 
2. **The Blackboard Pattern:** Often used in multi-agent AI, agents observe a shared "blackboard" (a central state or database) and independently decide when they have the expertise to modify it.
3. **Model Context Protocol (MCP):** Researching standardizing how agents expose tools and context to one another, so an agent can natively "query" another agent's state rather than just sending a text prompt.

### Planning the Protocol
A robust system requires designing a **Message Envelope** rather than just a text body. 
* **Intent/Type:** `TASK`, `QUERY`, `RESULT`, `ERROR`, `TERMINATE`.
* **Thread ID:** For tracking multi-turn conversations.
* **TTL (Time To Live):** A budget of how many bounces a message can make before the system forcefully halts it (solving the infinite loop problem without killing legitimate dialogue).

---

## 3. Target Architecture for Autonomous Communication

To build a truly autonomous system, I propose the following architectural evolution:

### A. The Message Broker Daemon (The Router)
Instead of individual `agent_bridge.ps1` scripts polling files, a central Python-based daemon (e.g., `ipc_router.py`) manages the SQLite database. It acts as an asynchronous pub/sub broker. It handles routing, enforces TTLs to prevent infinite loops, and tracks Thread IDs.

### B. Structured JSON Payloads
Transition the backend transport from raw Markdown appending to structured JSON (while still generating Markdown for human readability).
```json
{
  "thread_id": "req-12345",
  "from": "claude",
  "to": "codex",
  "intent": "TASK",
  "ttl": 5,
  "payload": "Implement the API endpoints for Phase 11",
  "context_pointers": ["file:///C:/axiom/governance/05_handoffs/plan.md"]
}
```

### C. Semantic Termination & Handshakes
Instead of preventing replies, we allow multi-turn conversation by establishing a handshake protocol.
* If Codex needs clarification, it replies with `intent: QUERY`.
* Claude responds with `intent: INFO`.
* When the task is done, Codex sends `intent: RESULT`.
* If a thread exceeds its `ttl` budget, the Router suspends it and alerts the Operator (Jeremy).

### D. Persistent Agent Daemons (Warm Starts)
Currently, `agent_bridge.ps1` spins up a new CLI process for every message. Autonomous agents should run as persistent background daemons (or servers) exposing a REST/WebSocket endpoint. When the Router receives a message, it sends an HTTP POST to the agent. This allows the agent to maintain short-term memory and context between messages without re-reading the entire disk state.

---

## 4. Proposed Build Plan

If we were to build this, I would sequence it in three phases:

* **Phase 1: Standardization.** Update `send.ps1` and `ipc_db.py` to require and store `thread_id` and `intent`. Modify agents to understand these headers so they know *why* they are being contacted.
* **Phase 2: The Router.** Deprecate `agent_bridge.ps1`. Build `axiom_router.py`, a central service that uses `asyncio` to monitor the SQLite DB and dispatch messages. Implement TTL budgets to gracefully solve the infinite loop issue.
* **Phase 3: Daemonization.** Transition the agents from cold-boot CLI scripts to persistent WebSocket clients that stay connected to the Router, allowing for instantaneous, context-aware dialogue.

---
*End of Report*
