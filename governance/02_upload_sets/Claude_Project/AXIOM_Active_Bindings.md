# AXIOM — Active Bindings
## Running Registry of Arbiter Factual Rulings and Constraints Feasibility Conditions

**Document Type:** Living Reference — Updated Per Cycle
**Status:** Active — Ratified under Charter v1.2
**Version:** v1.2
**Scope:** All factual rulings and binding conditions currently in force across the AXIOM design
**Ratification Cycle:** Ratified Cycle 2, 2026-05-14 by `AXIOM_Synthesis_Governance_v2_Cycle2.md`

---

## How This Document Is Used

Per Charter v1.2 §Binding Rulings Travel Forward:

- **Every fresh chat with any panel member** must have this document uploaded alongside the four-document spine
- **The Architect** restates relevant bindings in every revision so they are not lost
- **Gemini** encodes every relevant binding into the implementation plan as Implementation Specialist and Troubleshooter
- **The Evaluator** verifies that every active binding is honored in each proposal version

A binding is **superseded** only by a later panel ruling that explicitly cites the prior binding. Mark superseded entries `Superseded by [ID]`. Never delete — the audit trail matters.

Schema extended with `Issuing Authority` and `Maintaining Authority` fields per Charter v1.2 §Active Bindings Authority. Total active bindings: 36 (7 AB + 25 CB + 4 GB).

---

## Arbiter Bindings (Factual)

These are factual rulings originally issued by Gemini and now maintained by Kimi under Charter v1.2. They state how external technology actually behaves on the target environment. They are binding unless contradicted by new evidence.

| ID | Source Cycle | Ruling | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| AB-001 | v1.2 | `subprocess.Popen` does not provide network isolation on Windows. Genuine sandbox network isolation requires a dedicated user account with a Windows Defender Firewall outbound-deny rule scoped to that SID, OR AppContainer with `internetClient` capability dropped. Windows Job Object + restricted token alone does NOT block network sockets. | Gemini | Kimi | Active |
| AB-002 | v1.4 | SQLite must be configured with `PRAGMA journal_mode=WAL` and an explicit `busy_timeout` (5–10 seconds). | Gemini | Kimi | Active |
| AB-003 | v1.9 | Sandbox wall-clock enforcement requires `subprocess.run(timeout=60)` (or thread timer) alongside the Windows Job Object. The Job Object alone enforces only RAM. | Gemini | Kimi | Active |
| AB-004 | v1.11 | Thinking-mode determination for `qwen3:4b` via Ollama must inspect the `parameters` field of `/api/show` response only. The `template` and `system` fields are not authoritative. Pattern: `(?i)^\s*think\s+false\s*$`. Function returns `'disabled'` on match, `'unknown'` on absence. State `'enabled'` is reserved for future Arbiter ruling. | Gemini | Kimi | Active |
| AB-005 | v1.11.3 | NetworkGateway must disable automatic HTTP redirect following (`allow_redirects=False` for Python `requests`, equivalent for other clients) and traverse redirect chains manually, applying allowlist enforcement at each hop. | Gemini | Kimi | Active |
| AB-006 | v1.11.3 | JSON Schema validation for manifest files must use a draft-07-or-later validator with `additionalProperties: false` enforced at every object level. | Gemini | Kimi | Active |
| AB-007 | v1.11.3 | sqlite-vec virtual table declaration uses `vec0` syntax with explicit dimension and distance metric. | Gemini | Kimi | Active |

---

## Constraints Bindings (Feasibility)

These are conditions issued by Qwen as part of feasibility approval. They are binding implementation constraints that the Architect must restate and Gemini must encode as Implementation Specialist and Troubleshooter.

### Execution Model

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-001 | v1.7 | Sequential execution enforced. No two cognitive tasks run concurrently. | Qwen | Qwen | Active |
| CB-002 | v1.7 | Maximum four threads: main supervisor, Telegram gateway, Scheduler, Bootstrap worker. | Qwen | Qwen | Active |

### Local Model

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-003 | v1.7 | `qwen3:4b` remains Q4-quantized and memory-mapped via Ollama. | Qwen | Qwen | Active |
| CB-004 | v1.11.4 | ModelGateway must include `"think": false` in every local Ollama `/api/chat` and `/api/generate` request and reject any caller attempting to override. | Qwen | Qwen | Active |

### Sandbox

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-005 | v1.7 | Sandbox execution capped at 256 MB via Windows Job Object. | Qwen | Qwen | Active |
| CB-006 | v1.8.1 | Sandbox execution capped at 60 seconds wall clock. | Qwen | Qwen | Active |

### Persistence

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-007 | v1.7 | sqlite-vec batch limit of 100 vectors per query. | Qwen | Qwen | Active |
| CB-008 | v1.11.3 | SQLite cache_size = 32 MiB (`PRAGMA cache_size = -32768`). | Qwen | Qwen | Active |
| CB-009 | (pre-rebuild research) | Memory dedup uses pre-insertion cosine similarity check at threshold ≈0.92. | Qwen | Qwen | Active |

### Coordination and Budgets

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-010 | v1.7 | Context bundles capped at 500 KB serialized. | Qwen | Qwen | Active |
| CB-011 | v1.10 | Token estimation: 2.0× safety margin for calibrated paths, 1.5× for fallback paths. Manifest `max_estimated_input_tokens` ≥ 2× expected actual prompt size. | Qwen | Qwen | Active |
| CB-012 | v1.10 | PolicyEngine is stateless. No per-task or per-session mutable state in the engine itself. | Qwen | Qwen | Active |

### Security Gates

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-013 | v1.10 | Calibration test set must be authored before PlanInjectionScanner safe-pass is enabled. Safe-pass disabled until calibration passes. | Qwen | Qwen | Active |
| CB-014 | v1.10 | Model fingerprint mismatch immediately disables safe-pass for the remainder of the session. | Qwen | Qwen | Active |
| CB-015 | v1.10 | Pre-decision (not periodic) fingerprint verification before any classifier-dependent safe-pass decision. | Qwen | Qwen | Active |
| CB-016 | v1.11.4 | Tool capability map SHA256-fingerprinted at boot; modification blocks autonomous operation. | Qwen | Qwen | Active |
| CB-017 | v1.11.4 | Manifest `max_response_bytes` has a schema-level ceiling (5–10 MB recommended). | Qwen | Qwen | Active |
| CB-018 | v1.11.4 | Manifest `allowed_tools` and `forbidden_tools` constrained to canonical tool IDs (schema enum or ManifestBinder validation). | Qwen | Qwen | Active |
| CB-019 | v1.11.4 | PolicyEngine fails closed on missing policy fields (deny-all). | Qwen | Qwen | Active |

### Operator Recovery

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-020 | v1.11.4 | Telegram operator whitelist may not be deactivated, made empty, or modified without full panel consent and a recorded session_event. | Qwen | Qwen | Active |

### Web Search

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-021 | v1.11.3 | Web search remains disabled until Brave Search API access is operationally confirmed. | Qwen | Qwen | Active |

### Cloud Cascade

| ID | Source Cycle | Condition | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| CB-022 | v1.3 (Evaluator-derived from cancellation discussion) | Per-call timeout: 30 seconds for Cerebras, with cascade fallback on timeout. | Qwen | Qwen | Active |
| CB-023 | Governance v2 Cycle 1 | **Drive Unavailability Fallback.** The continuous layer must maintain an explicit operational fallback to local file exchange (copy-paste, local markdown, or offline sync) if Drive access, account authentication, or operator network connectivity is degraded or unavailable for >4 hours. Claims remain `pending domain review` until synchronization is restored. | Qwen | Qwen | Active |
| CB-024 | Governance v2 Cycle 1 | **Advisory Free-Tier Context Pacing.** Advisory council reviews on free tiers must utilize prompt chunking, executive summarization of non-binding context, or sequential review routing to remain within daily message/token quotas. If a quota limit is reached, the operator pauses routing, logs the limit, and resumes within the same cycle window rather than skipping review. | Qwen | Qwen | Active |
| CB-025 | Governance v2 Cycle 1 | **PDR Ledger Isolation.** Pending-Domain-Review markings and local ledgers shall remain confined to the originating artifact. They must not be appended to `AXIOM_Specification_Debt.md` unless formally deferred under Charter v1.1 §5.4 or escalated to a binding/factual dispute. | Qwen | Qwen | Active |

---

## Charter Bindings (Governance)

These are charter-grade rulings about how the panel itself operates. They emerged during the build and are now codified in Charter governance.

| ID | Source Cycle | Ruling | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| GB-001 | v1.9 | Cross-cutting artifact ownership: Gemini primary author / DeepSeek adversarial / Claude coherence / Qwen feasibility / Kimi packaging / operator file creation. Initial assignment of authorship to the Critic violates separation of duties. | Full panel | Full panel | Active (codified in Charter v1.1) |
| GB-002 | v1.7 → v1.13 cumulative | Delta-confirmation cycles are authorized when the revision introduces no new component, factual claim, or runtime impact and touches no Core Value or Constraints entry. | Full panel | Full panel | Active (codified in Charter v1.1) |
| GB-003 | v1.13 | Implementation revisions follow Integration Discipline: restate only authorized sections, preserve panel-ratified content verbatim, integration verification gate before delta-confirmation. | Full panel | Full panel | Active (codified in Charter v1.1) |
| GB-004 | v1.7 cumulative | Specification gaps that carry across two cycles become specification debt and are closure-required for the next revision. | Full panel | Full panel | Active (codified in Charter v1.1) |

---

## Maintenance

**Add a binding** the moment a panel member files it. Don't wait until end-of-cycle.

**Mark superseded** with the new binding's ID and one-line rationale. Never delete.

**Cross-reference** when a binding tightens an earlier one (e.g., CB-006 wall clock alongside CB-005 RAM both apply to sandbox).

**Audit at every full panel cycle** — verify that the Architect's revision restated the relevant active bindings and that no binding was silently dropped.

---

*AXIOM Active Bindings — Version v1.2 — May 2026 — schema extended with Issuing Authority and Maintaining Authority fields per Charter v1.2. Total bindings: 36 (7 AB + 25 CB + 4 GB).*