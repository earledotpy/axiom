# AXIOM — Legacy Reference
## ToonTown Build Retrospective · Phases 0–9

**Document Type:** Legacy Artifact — Read-Only Reference  
**Status:** Archived  
**Version:** 1.0  
**Scope:** Complete retrospective of the ToonTown build that preceded AXIOM  

---

## How to Use This Document

This document is a legacy artifact. It describes a prior build called ToonTown that ran from mid-March 2026 through April 7, 2026 across nine phases. It is provided as historical context — a record of what was tried, what worked, and what failed.

**It is not a specification.** Nothing in this document is inherited by default. The AXIOM panel evaluates every component independently. This document informs that evaluation — it does not replace it.

Read it once. Reference specific sections when evaluating proposals that touch the same problem space.

---

## What ToonTown Was

ToonTown was a local-first autonomous multi-agent AI system built on a single constrained laptop, operated and built by one human, with a Telegram bot as its sole interface. Its goal was to accept high-level goals, decompose them into executable work, and carry out that work autonomously using a hierarchy of specialized AI agents.

It was built on top of the smolagents framework. It used SQLite for persistence, Ollama for local model serving, nomic-embed-text for embeddings, and a cloud cascade (Cerebras → Groq → OpenRouter → SambaNova) for cognitive work.

---

## Build History — Phases 0 Through 9

**Phases 0–3 — Foundation**  
Core runtime established: Python venv, Telegram bot, Ollama, SQLite memory database (toontown_memory.db), Open Brain memory tool. Session model defined: human starts session via batch file, bot activates, agents respond to messages.

**Phase 4 — Memory and Retrieval**  
sqlite-vec integrated for vector search. Semantic memory storage and retrieval implemented using nomic-embed-text. Memory commands (REMEMBER, RECALL, BACKUP) established and tested.

**Phases 5–6 — Agent Hierarchy**  
Multi-agent structure introduced using smolagents. Telegram agent established as primary interface layer with routing logic to: Overseer, Taskmasters (Research, Coding, Analysis), and Drones (Web, Search, Code, File, Memory). Routing instructions appended to default system prompt.

**Phases 7–8 — Cloud Cascade and Model Routing**  
Cloud cascade established: Cerebras primary, Groq first fallback, OpenRouter second, SambaNova third. Local model (qwen3:4b) assigned strictly to routing, private data, embeddings. Extended thinking disabled on qwen3:4b.

**Phase 9 — Stability and Hardening**  
Critical failures resolved:
- asyncio and concurrent.futures import order caused runtime conflicts — fixed by moving to top-level imports in agent.py
- smolagents 1.12.0 removed LiteLLMRouterModel — manual cascade written as replacement
- Telegram bot required monkey-patch on sat on_message for correct message handling
- PromptTemplates replaced with prompt_templates append
- ROUTING_INSTRUCTIONS appended to default system prompt
- final_answer("done") added to routing instructions to prevent infinite loops
- BRAIN_TOKEN validation added to start_session.bat before bot launch
- icacls requires literal username, not %USERNAME% environment variable
- sc.exe must be called as `& "$env:SystemRoot\System32\sc.exe"` in PowerShell

Phase 9 acceptance testing passed all criteria on April 7, 2026.

---

## What Worked

These elements functioned reliably. They represent proven patterns worth evaluating for reuse.

**SQLite as persistence layer.** Single-file, reliable, no dependency issues on constrained hardware. sqlite-vec extension integrated cleanly for vector search.

**nomic-embed-text via Ollama.** Ran locally without GPU. Adequate embedding quality. Low RAM overhead.

**Cerebras as primary cloud model.** Fast, capable, free tier. Became primary after Groq daily limits were exhausted.

**Telegram interface.** Python Telegram Bot library integrated cleanly. Mobile-first, session-started (not webhook) model worked reliably on constrained network.

**The session model.** Start via batch file, validate credentials, launch bot, run until manually stopped. Stable and debuggable.

**Cloud cascade pattern.** Routing through multiple free-tier providers in priority order proved resilient. When one provider hit limits, the next picked up.

**Routing instructions via system prompt.** Appending structured routing instructions to the default system prompt was the correct pattern for directing agent behavior.

---

## What Failed or Was Never Completed

These elements failed, partially failed, or were identified as requiring redesign before the build was retired.

**Web search was structurally broken.** duckduckgo_search blocks automated traffic. This is not fixable — DDG has no official API. A replacement (Brave Search API) was selected in pre-rebuild planning but never implemented.

**The Overseer had no system context.** The Overseer (ask_overseer tool via Cerebras) was invoked with no system prompt. It answered as a generic AI with no awareness of ToonTown, its architecture, its constraints, or its purpose. During Phase 9 testing it confused ToonTown with an unrelated product.

**Duplicate memory entries.** Multiple test writes created duplicate records. No deduplication logic existed at insert level. Memory database was in a degraded state at handoff.

**Groq daily limit exhausted during testing.** The cascade was vulnerable when both Cerebras and Groq were unavailable simultaneously.

**The three-tier agent hierarchy was intent, not function.** Phase 9 had routing logic and named roles, but Taskmasters and Drones did not operate with distinct tool boundaries or genuine context blindness. The hierarchy was architectural aspiration, not implemented reality.

**NSSM selected without evaluation.** The Phase 10 plan specified NSSM as the Windows service wrapper before comparing alternatives. Post-planning research identified that NSSM has not been actively maintained since 2017 and has documented credential access problems in Windows Session 0. Servy was identified as the better option but never implemented.

**No sandboxed code execution.** subprocess.Popen inherits parent process network permissions on Windows. Generated code could make outbound network calls without restriction. No isolation existed.

**No prompt injection defense.** No sanitization at the task queue write boundary. External content fetched by agents could carry embedded instructions that downstream agents would execute.

---

## Decisions Made at the Pivot Point

The following decisions were reached in pre-rebuild planning. They are inputs to the AXIOM design process, not binding decisions.

- Replace NSSM with Servy for Windows service management
- Replace duckduckgo_search with Brave Search API
- Add stuck-task watchdog to scheduler startup (reset status = 'running' to 'pending' on startup)
- Add structured JSON logging with task ID correlation from initial implementation
- Write an Overseer system prompt reflecting the full three-tier architecture vision
- Add pre-insertion cosine similarity check to memory writes (~0.92 threshold)
- Implement LLM Tagging — prefix agent outputs with agent ID and task ID markers
- Add sanitization at write time to the task queue, not read time

The AXIOM panel evaluates each of these independently.

---

## Key Technical Details for Reference

**Username on target machine:** ashto  
**Primary working directory:** C:\toontown\ (legacy — AXIOM may relocate)  
**Virtual environment:** C:\toontown\venv\  
**Logs:** C:\toontown\logs\  

**Known Windows-specific behaviors:**
- sc.exe must be called as `& "$env:SystemRoot\System32\sc.exe"` in PowerShell
- icacls requires literal username (ashto), not %USERNAME% variable
- subprocess.Popen does NOT provide network isolation — inherits parent permissions

---

## Research Conducted Before Rebuild

Five AI systems conducted independent research on the Phase 10–12 build plan before the rebuild decision was made. Key findings consensus across all five:

- Windows Job Objects + restricted token (pywin32) are required for genuine sandbox network isolation on Windows
- Prompt injection via the task queue is a real threat — sanitization must occur at write time, not read time
- The local model (qwen3:4b) is the natural semantic firewall for write-time sanitization — zero API cost, already in the architecture
- sqlite-vec deduplication via cosine threshold (~0.92) is confirmed as the correct approach for memory deduplication
- Overseer decomposition reliability is the acknowledged weakest link — a verification/checker step before committing a task tree is recommended
- Gemini specifically flagged that parallel Taskmaster execution on 8GB RAM is likely infeasible — sequential state machine may be the permanent architecture, not a temporary constraint

---

*ToonTown Legacy Reference — Archived May 2026 — Superseded by AXIOM*
