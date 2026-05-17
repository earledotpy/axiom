# AXIOM — Constraints Register
## Hard Constraints for the Multi-Agent Autonomous System Design Initiative

**Document Type:** Constraints Reference  
**Status:** Active — Ratified  
**Version:** 1.1  
**Supersedes:** v1.0 (May 2026)  
**Scope:** Hardware, budget, interface, environment constraints, active-binding crosswalk, and runtime-governance constraints  
**Ratification:** Ratified Cycle 3, 2026-05-10 by `AXIOM_Synthesis_Governance_v3.md`.

---

## Purpose

Every proposal produced by the AXIOM design panel is evaluated against this register. Constraints marked **HARD** are non-negotiable. Constraints marked **OBSERVED** reflect current real-world measurements that inform feasibility analysis.

This v1.1 register also mirrors the active binding crosswalk using the original `AB-*`, `CB-*`, and `GB-*` IDs. Mirroring does not supersede the active binding source text.

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

---

## Software Environment — OBSERVED

| Component | Current State |
|---|---|
| Language runtime | Python 3.12 |
| Virtual environment | venv at C:\toontown\venv\ (legacy path — rebuild may relocate) |
| Local model server | Ollama |
| Local embedding model | nomic-embed-text |
| Local language model | qwen3:4b (thinking disabled) |
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

---

## Web Search Constraint — OBSERVED

DuckDuckGo via the duckduckgo_search Python package was used in the legacy build and failed due to structural rate-limiting. A replacement is required. Brave Search API was selected in pre-rebuild planning (free tier, ~1,000 queries/month). The panel may evaluate alternatives.

---

## Constraints That Are Open to Challenge

The following are constraints from the legacy build that the panel may propose to revise with supporting rationale:

- Local model assignment (qwen3:4b) — panel may propose a different model if RAM and capability justify it
- Telegram as interface — panel may propose an additional interface channel if it can be justified without hardware changes
- SQLite as persistence layer — panel may propose an alternative if it improves capability without increasing complexity or RAM overhead

---

---

## 8. Constraints Register and Active Bindings Corrections

### 8.1 Supersession Rule

`AXIOM_Active_Bindings_v1_0.md` remains authoritative for active binding text and status.

A Constraints Register mirror, Charter reference, Core Values note, proposal crosswalk, or Synthesis summary does not supersede an active binding. Supersession requires a later panel ruling that explicitly cites the prior binding ID and states the replacement or supersession rationale.

### 8.2 Rejection of B1–B22 as Canonical Binding IDs

The proposed Constraints Register's `B1–B22` numbering must be withdrawn as a canonical binding scheme. The Constraints Register may mirror active bindings, but the canonical IDs remain:

- `AB-001` through `AB-007`;
- `CB-001` through `CB-022`;
- `GB-001` through `GB-004`.

### 8.3 Verbatim Active Binding Crosswalk

The following rows are restated verbatim from `AXIOM_Active_Bindings_v1_0.md`. They are not renamed, shortened, silently corrected, or superseded.

---

*AXIOM Constraints Register — Version 1.1 — Ratified Cycle 3, 2026-05-10 by AXIOM_Synthesis_Governance_v3.md*
