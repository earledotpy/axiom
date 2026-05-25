# AXIOM — Constraints Register
## Hard Constraints for the Multi-Agent Autonomous System Design Initiative

**Document Type:** Constraints Reference
**Status:** Proposed Amendment — Awaiting Panel Consensus
**Version:** 1.1 (proposed)
**Supersedes:** v1.0 (May 2026)
**Scope:** Hardware, budget, interface, environment, and runtime constraints

---

## Purpose

Every proposal produced by the AXIOM design panel is evaluated against this register. Constraints marked **HARD** are non-negotiable. Constraints marked **OBSERVED** reflect current real-world measurements that inform feasibility analysis. Constraints marked **BINDING** are runtime invariants established through panel rulings during the build, now promoted to canonical status (new in v1.1).

---

## Hardware Constraints — HARD

| Component | Specification |
|---|---|
| Device | HP laptop |
| Processor | Intel Celeron N4500 |
| RAM | 8 GB total system memory |
| Storage | SATA SSD |
| GPU | None |
| Operating System | Windows 11 |
| Network | Standard home internet connection |

**No proposal may require hardware not listed above.**
Proposals that require a GPU, additional RAM, a different operating system, or a second machine are out of scope for Phase 1 of the build. Such proposals may be flagged as future-state options but cannot be the primary implementation path.

---

## Memory Headroom — OBSERVED

**Baseline RAM consumption during ToonTown operation (legacy reference):** approximately 5.7 GB
**Available headroom at runtime:** approximately 2.0–2.3 GB

This is the working memory budget for all agent processes, schedulers, tools, and model inference. Proposals that require concurrent processes must account for this ceiling explicitly. RAM accounting is required for any proposal involving:

- Local model loading (Ollama)
- Multiple concurrent agent processes
- Sandbox execution
- Database operations with large result sets

**Parallel execution warning:** Gemini's analysis of the legacy build identified that concurrent agent subprocess execution on this hardware will exhaust available RAM and drive the system into SATA SSD paging, degrading performance severely. Any proposal involving parallel execution must address this constraint with explicit RAM accounting.

---

## Runtime Invariants — BINDING (NEW IN v1.1)

The following runtime invariants were established as binding conditions through the v1.7 → v1.11.3 panel cycles. They have been carried forward across multiple revisions and are now promoted to canonical status in this register.

### Execution Model

| # | Constraint | Source |
|---|---|---|
| B1 | Execution is sequential. No two cognitive tasks run concurrently. | Qwen v1.7 ruling |
| B2 | Maximum four threads: main supervisor, Telegram gateway, Scheduler, Bootstrap worker. No fifth thread without panel consensus. | Qwen v1.7 ruling |
| B3 | The Scheduler is the sole owner of `tasks.status` mutations during normal operation. Operator interrupts route through the Scheduler via intent flags (`cancel_requested`, `pause_requested`, `shutdown_requested`). | Architect v1.3.1 §F1 |

### Local Model

| # | Constraint | Source |
|---|---|---|
| B4 | Local model is `qwen3:4b` with thinking disabled, Q4 quantization, memory-mapped via Ollama. | Qwen v1.7, Arbiter v1.11 (qwen3:4b thinking-mode inference) |
| B5 | ModelGateway must include `"think": false` in every local Ollama `/api/chat` and `/api/generate` request. ModelGateway must reject any caller attempting to override this. | Arbiter v1.11.4 |
| B6 | Thinking-mode inference uses the `parameters` field of `/api/show` only — not `template`, not `system`. Pattern: `(?i)^\s*think\s+false\s*$`. | Arbiter v1.11 ruling |

### Sandbox

| # | Constraint | Source |
|---|---|---|
| B7 | Sandbox execution is capped at 256 MB RAM and 60 seconds wall clock. | Qwen v1.7 (RAM), v1.8.1 (wall clock) |
| B8 | Sandbox network isolation requires a dedicated Windows user account with firewall outbound-deny scoped to that SID, OR AppContainer with `internetClient` capability dropped. `subprocess.Popen` alone does not isolate. | Arbiter v1.2 |
| B9 | Sandbox wall-clock enforcement requires `subprocess.run(timeout=60)` (or thread timer) alongside the Windows Job Object. | Arbiter v1.9 |

### Persistence

| # | Constraint | Source |
|---|---|---|
| B10 | SQLite uses WAL journal mode with explicit `busy_timeout` of 5–10 seconds and `PRAGMA synchronous=FULL`. | Arbiter v1.4, Evaluator v1.4 |
| B11 | SQLite cache_size is 32 MiB (`PRAGMA cache_size = -32768`). | Qwen v1.11.3 binding condition 11 |
| B12 | sqlite-vec batch limit is 100 vectors per query. | Qwen v1.7 |
| B13 | Memory dedup uses pre-insertion cosine similarity check at threshold ≈0.92. | Pre-rebuild research consensus |

### Coordination and Budgets

| # | Constraint | Source |
|---|---|---|
| B14 | Context bundles capped at 500 KB serialized. | Qwen v1.7 |
| B15 | Token estimation includes tiered safety margin: 2.0× for calibrated paths, 1.5× for fallback paths. Manifest `max_estimated_input_tokens` must be sized at ≥2× expected actual prompt size, otherwise the dispatch gate produces systematic false blocks. | Qwen v1.7, Evaluator v1.9 clarification C |
| B16 | PolicyEngine is stateless — no per-task or per-session mutable state in the engine itself. | Qwen v1.10 binding condition |

### Security Gates

| # | Constraint | Source |
|---|---|---|
| B17 | Calibration test set must be authored before the PlanInjectionScanner safe-pass path is enabled. Safe-pass is disabled until calibration passes acceptance thresholds. | Qwen v1.10 |
| B18 | Model fingerprint mismatch immediately disables safe-pass for the remainder of the session. | Qwen v1.10 |
| B19 | Pre-decision (not periodic) fingerprint verification is required immediately before any classifier-dependent safe-pass decision. | Architect v1.10, Evaluator approval |
| B20 | Tool capability map is SHA256-fingerprinted at boot; modification blocks autonomous operation. | DeepSeek v1.11.3, Evaluator v1.11.4 |
| B21 | NetworkGateway must disable automatic HTTP redirect following (`allow_redirects=False` for Python `requests`, equivalent for other clients) and traverse redirect chains manually. | Arbiter v1.11.3 |

### Cross-Cutting Artifact Ownership

| # | Constraint | Source |
|---|---|---|
| B22 | Calibration test set workflow: Gemini primary author / DeepSeek adversarial reviewer / Claude coherence / Qwen feasibility / Kimi packaging / operator file creation. | Charter §Cross-Cutting Artifact Protocol, Evaluator v1.9 |

**Modification of any binding constraint requires full panel consensus with written rationale, per Charter §Conflict Resolution.**

---

## Budget Constraints — HARD

**API spend:** Free or near-zero. The system must be operable on free-tier API access across all cloud providers.
**Software:** Free and open-source only, unless a specific paid tool provides capability unavailable elsewhere and can be justified to the panel.
**Hardware:** No new hardware purchases are in scope.

---

## Interface Constraints — HARD

| Interface | Specification |
|---|---|
| Mobile device | Google Pixel 8a (Android) |
| Interface protocol | Telegram bot |
| Human access method | Mobile messaging only during autonomous operation |

The Telegram bot is the sole interface between the human operator and the running system during autonomous operation. Any interface proposal must work through this channel.

**Telegram operator whitelist is the recovery-of-last-resort and may not be deactivated, made empty, or modified without full panel consent and a recorded session_event.** (Added v1.1, derived from v1.11.4 DeepSeek #6 disposition.)

---

## Software Environment — OBSERVED

| Component | Current State |
|---|---|
| Language runtime | Python 3.12 |
| Virtual environment | venv at C:\toontown\venv\ (legacy path — rebuild may relocate) |
| Local model server | Ollama |
| Local embedding model | nomic-embed-text |
| Local language model | qwen3:4b (thinking disabled — see B4–B6) |
| Database | SQLite via toontown_memory.db (legacy — rebuild may rename) |
| Vector search | sqlite-vec extension |

These are observed starting conditions from the legacy build. The rebuild may change any of these. Changes must be evaluated for RAM impact and dependency complexity.

---

## Cloud Cascade — OBSERVED

The legacy build established this cascade. It is a starting point, not a requirement.

| Priority | Provider | Model | Notes |
|---|---|---|---|
| 1 | Cerebras | qwen-3-235b-a22b-instruct-2507 | Free tier, fast |
| 2 | Groq | — | 10K daily token limit — exhausted during testing |
| 3 | OpenRouter | — | Fallback |
| 4 | SambaNova | — | Fallback |

**Known issue:** Groq's daily token limit was exhausted during legacy Phase 9 testing. The cascade needs a more resilient fallback strategy.

**Per-call timeout:** 30 seconds for Cerebras, with cascade fallback on timeout. (Added v1.1 from Evaluator v1.3 synthesis recommendation.)

---

## Web Search — OBSERVED

DuckDuckGo via the duckduckgo_search Python package was used in the legacy build and failed due to structural rate-limiting. A replacement is required. Brave Search API was selected in pre-rebuild planning (free tier, ~1,000 queries/month).

**Status:** Brave Search API confirmed as the chosen replacement. Per Qwen binding condition (v1.11.3): web search remains disabled until Brave Search API access is operationally confirmed.

---

## Constraints That Are Open to Challenge

The following are constraints from the legacy build that the panel may propose to revise with supporting rationale:

- Local model assignment (qwen3:4b) — panel may propose a different model if RAM and capability justify it. Note: any swap requires re-running calibration per B17 and refreshing the fingerprint per B19.
- Telegram as interface — panel may propose an additional interface channel if it can be justified without hardware changes
- SQLite as persistence layer — panel may propose an alternative if it improves capability without increasing complexity or RAM overhead

**Constraints that are NOT open to challenge without full panel consensus:** B1–B22 above. These were established through panel ruling and require a Charter-grade amendment process to modify.

---

## Amendment Log

| Version | Date | Section | Amendment | Rationale | Panel Consensus |
|---|---|---|---|---|---|
| 1.0 | May 2026 | — | Initial register | Pre-build founding document | Pre-panel |
| 1.1 | May 2026 (proposed) | §Runtime Invariants — BINDING | Promoted 22 binding conditions to canonical status | Conditions accumulated across v1.7–v1.11.3 with no canonical home | **Pending** |
| 1.1 | May 2026 (proposed) | §Cloud Cascade | Added per-call timeout (30s Cerebras) | Evaluator v1.3 cancellation discussion | **Pending** |
| 1.1 | May 2026 (proposed) | §Web Search | Updated status to Brave confirmed, pending operational test | Qwen v1.11.3 carry-forward | **Pending** |
| 1.1 | May 2026 (proposed) | §Interface Constraints | Added Telegram whitelist binding | DeepSeek v1.11.4 #6 disposition | **Pending** |
| 1.1 | May 2026 (proposed) | §Constraints That Are Open to Challenge | Excluded B1–B22 from open challenge | Binding conditions require Charter-grade amendment process | **Pending** |

---

*AXIOM Constraints Register — Version 1.1 (proposed) — May 2026*
