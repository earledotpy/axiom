# AXIOM — Design Document

**Status:** Legacy Reference (Project on hold indefinitely as of 2026-06-10)
**Operator:** Jeremy Earle
**Branch at close:** `axiom/level-2a-control-plane`

---

## 1. What AXIOM Was

AXIOM was an experiment in building a **locally-hosted, operator-governed, fail-closed AI agent runtime** on a Windows workstation. The core ambition was: a human operator (Jeremy) retains complete, auditable authority over every AI action — while still offloading planning, implementation, review, and verification work to a panel of specialized AI agents.

The system was never intended to be autonomous "AI agents doing things on their own." It was the opposite: a governance harness that forces every autonomous operation to pass through an explicit operator decision, a fail-closed policy engine, and a two-key autonomy gate before anything can actually run.

---

## 2. High-Level Goal

> Run a bounded, local AI agent that can help with software tasks — but only under explicit human operator governance, with every authority boundary documented, audited, and enforced in code.

Secondary goals:

- Use a local `qwen3:4b` model (via Ollama) as a fast sanitizer/router/classifier lane.
- Delegate planning and synthesis to cloud models (Claude, GPT-4, etc.) only through an explicit cascade path.
- Make the entire governance structure legible — to the human operator, to auditing agents, and to the code itself.
- Build on Windows natively (PowerShell, SQLite, Python 3.12).

---

## 3. Architecture Overview

### 3.1 Core Principle Stack

```
Operator (Jeremy)
  └─ Governance Layer (mandate acceptance, authority boundary, fail-closed posture)
       └─ Policy Engine (manifest binding, tool capability map, injection scanner)
            └─ Scheduler / State Machine (one task at a time, heartbeat enforcement)
                 └─ Executors (no-op → manual_noop → bounded agent task types)
                      └─ Gateways (ModelGateway, NetworkGateway, SandboxGateway, MemoryGateway)
                           └─ Agents (GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier)
```

Every layer only activates when the layer above it has explicitly authorized it.

### 3.2 Governance Layer (`governance/`)

The governance structure was redesigned during the project. The final accepted scaffold:

| Directory | Purpose |
|-----------|---------|
| `governance/00_doctrine/` | Root doctrine: operator-governed, fail-closed, autonomy-gated |
| `governance/10_workflow/` | Lifecycle states, artifact transitions, archive rules |
| `governance/20_transport/` | How governance information moves without conferring authority |
| `governance/30_delegation/` | How operator goals become scoped agent work |
| `governance/40_execution/` | How approved work is implemented and evidenced |
| `governance/50_evaluation/` | How work is reviewed, audited, and prepared for operator decision |
| `governance/60_operator_console/` | How Jeremy sees active state, blockers, decisions |
| `governance/70_autonomy_gate/` | Two-key scoped/revocable autonomy grant model |
| `governance/80_records/` | JSON-first machine-readable records (task cards, decisions, evaluations, bindings) |

The legacy `governance/01_live_spine/` structure (advisory panel, handoff files, ADRs, open questions) was retired and replaced by this numbered scaffold.

### 3.3 Runtime Core (`axiom/core/`)

The Python runtime was built in sequential phases. Key components:

| Module | Role |
|--------|------|
| `state_machine.py` | Task lifecycle state machine (pending → running → completed/failed/cancelled) |
| `scheduler.py` | Single-task dispatcher with one-running-task invariant |
| `scheduler_loop.py` | Bounded foreground scheduler loop (Phase 9) |
| `task_lifecycle_service.py` | Lifecycle service composing guard, starter, committer, completer, canceller, failer |
| `task_lifecycle_guard.py` | Enforces pre-transition invariants (manifest bound, no duplicate running tasks) |
| `supervisor_monitor.py` | Heartbeat-based supervisor health |
| `policy_engine.py` | Seven-step stateless tool authorization |
| `manifest_binder.py` | JSON Schema validation + SHA256 verification of role manifests |
| `context_builder.py` | Context bundle assembly with 500 KB size cap |
| `token_estimator.py` | Token estimation with 2.0× calibrated / 1.5× fallback margins |
| `autonomous_gate.py` | Two-key autonomy readiness check (technical gate + operator mandate) |
| `operator_command_parser.py` | Operator command intake (fail-closed on unknown commands) |
| `operator_command_ledger.py` | SQLite ledger of operator command history |
| `operator_console.py` | Read-only console view of active governance state |
| `governance_cycle.py` | Governance cycle coordinator (Mandate 8) |
| `decision.py` / `binding.py` | Operator decision and active binding records |
| `delegation.py` / `evaluation.py` | Delegation packet and evaluation report records |
| `task_card.py` / `handoff.py` / `evidence.py` | JSON-first governance record types |
| `autonomy_grant.py` | Scoped autonomy grant records (not runtime autonomy) |

### 3.4 Security Layer (`axiom/security/`)

| Module | Role |
|--------|------|
| `plan_injection_scanner.py` | Deterministic scanner + classifier-safe-pass path for plan artifacts |
| `model_fingerprint_guard.py` | Model fingerprint mismatch → fail closed |
| `autonomous_gate_panel.py` | Panel-level autonomy readiness review |
| `audit.py` | Security event recording |

### 3.5 Persistence (`axiom/persistence/`)

SQLite-backed via `axiom.db`. Key tables: `tasks`, `sessions`, `events`, `manifest_fingerprints`, `model_profiles`, `resource_usage`, `operator_commands`, `security_events`. Schema in `axiom/persistence/schema.sql`.

### 3.6 Gateways (`axiom/gateways/`)

All gateways were scaffolded but kept inert during the project:

- `ModelGateway` — local Ollama + cloud cascade; `think: false` injected into every local call
- `NetworkGateway` — Brave Search API (not activated; required panel approval)
- `SandboxGateway` — Windows Job Object execution (not activated; required Windows specifics approval)
- `MemoryGateway` — sqlite-vec sparse vector index (not activated; batches capped at 100 vectors)
- `TelegramGateway` / `TelegramBotAdapter` — Telegram control plane (not activated)

### 3.7 Agents (`axiom/agents/`)

Scaffolded manifest-bound executors:

- `GoalPlanner` — decomposes operator goals into task plans
- `TaskPlanner` — refines task-level plans
- `ToolExecutor` — executes manifest-authorized tools
- `ResultVerifier` — verifies task results against acceptance criteria
- `ManualCLI` — bounded manual execution path

None of these were activated in the project; they were scaffolded for future use behind the full policy + autonomy gate stack.

### 3.8 IPC Layer (`ipc/`)

A shared message directory (markdown files + SQLite) for cross-agent communication between Claude Code, Codex, and Antigravity. By Phase 0 of Level 2A, IPC execution paths were frozen:

- `command` frames rejected at `ipc_db.py`
- inbox files treated as inert historical evidence only
- no auto-invocation of any agent via IPC

### 3.9 Terminal UI (`ui/terminal/`)

A PowerShell-based TUI was built during Phases 10-11 using `psmux` (tmux bridging). Features included:

- Multi-panel dashboard (status, task, log, IPC, governance panels)
- Layer 2A operator panel structure
- Color-coded status tokens and fail-closed posture sigils
- Terminal command registry (`axiom-terminal-command-registry.json`)
- `launch-workspace.ps1` — workspace launcher with PSMUX bridging

---

## 4. Multi-Agent Panel

AXIOM used a multi-agent governance panel:

| Agent | Role | Process | Function |
|-------|------|---------|---------|
| **Antigravity** | Chief Architect and Researcher | `architect` | `plan` |
| **Codex** | Implementation Specialist and Troubleshooter | `implement` | `build` |
| **Claude Code** | Governance Auditor and Specification Critic | `audit` | `verify` |
| **Cursor** | Synthesis and summarization | `synthesize` | `summarize` |

All agent output was advisory unless Jeremy explicitly recorded an operator decision. An earlier "advisory council" of external models (Kimi, Qwen, DeepSeek) was retired by the governance redesign.

---

## 5. Implementation Phases Completed

| Phase | Summary | Key Invariant |
|-------|---------|---------------|
| **Foundation** | Directory structure, SQLite schema, manifest schema, tool-capability map, model fingerprint | `init_db()` only after canonical schema on disk |
| **Phase 2** | StateMachine, Scheduler, TaskCommitter, SupervisorMonitor, ContextBuilder, TokenEstimator | One running task at a time; manifest_id non-null before running |
| **Phase 3** | ManifestBinder integrity, PolicyEngine authorization, PlanInjectionScanner contract | Classifier safe-pass disabled; scanner return contract enforced |
| **Phase 4** | Gateway scaffolding (ModelGateway, MemoryGateway, NetworkGateway, SandboxGateway) | All gateways inert; no real calls authorized |
| **Phase 5** | Agent scaffolding (GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier) | Manifest-bound; no activation |
| **Phase 6** | Telegram gateway scaffolding | Not activated; whitelist mechanism unspecified |
| **Phase 7** | Acceptance suite, e2e gate planning | E2E test gated on classifier calibration + model fingerprint |
| **Phase 8** | Repository cleanup, release freeze, documentation reconciliation | Audit/planning only |
| **Phase 9** | Automatic scheduler→executor integration for `manual_noop` tasks | Foreground only; no background daemon |
| **Phase 10** | PSMUX bridging, TUI multi-panel dashboard, UI directory professionalization | Terminal UI only; no runtime authority |
| **Phase 11** | TUI dashboard modernization, IPC panel | Design/ratification only |
| **Governance Redesign (Mandates 1-8)** | Doctrine, workflow, transport, delegation, execution, evaluation, console, autonomy gate scaffold; JSON-first records; operator console; schema validation | All output advisory; no IPC reactivation; no autonomy |
| **Level 2A — Phase 0** | IPC freeze implementation (`MND-ACCEPTED-2026-0001-PHASE0-IPC-FREEZE`) | `command` frames rejected; IPC inert |

---

## 6. What Was Never Activated

The following were explicitly prohibited throughout the project and remain inactive:

- **Autonomous operation** — `autonomous_allowed: False` at all times
- **Classifier safe-pass** — disabled until calibration passes against panel-authored test sets
- **Real model calls** — ModelGateway scaffolded but no real Ollama chat/generate calls made in production
- **Network fetches** — NetworkGateway scaffolded; Brave Search API never confirmed
- **Sandbox execution** — SandboxGateway scaffolded; Windows Job Object specifics never approved
- **Memory writes** — MemoryGateway scaffolded; sqlite-vec writes never authorized
- **Telegram control plane** — gateway scaffolded; operator whitelist mechanism never specified
- **Persistent scheduler daemon** — bounded foreground loop only; no background service
- **IPC auto-invocation** — permanently frozen by Phase 0 IPC Freeze mandate

---

## 7. Safety Invariants (Preserved Throughout)

1. Strict sequential execution — no concurrent agent subprocesses
2. `qwen3:4b` — Q4-or-lower quantized, memory-mapped via Ollama
3. Context bundles capped at 500 KB serialized size
4. Sandbox execution capped at 256 MB RAM and 60 seconds wall-clock
5. sqlite-vec operations capped at 100 vectors per query/batch
6. Token estimation margins: 2.0× calibrated, 1.5× fallback
7. PolicyEngine, ManifestBinder, tool-capability lookups — stateless; boot-time-cached
8. Runtime thread count limited to four: main supervisor, Telegram, Scheduler, BootstrapValidationWorker
9. Classifier safe-pass disabled until calibration passes
10. Model fingerprint mismatch → fail closed
11. Manifest SHA256 mismatch → fail closed
12. SQLite page cache explicitly bounded (`cache_size = -32768`)

---

## 8. Governance Record State at Close

```
governance/80_records/
  decisions/    — 1 decision record (DEC-20260610)
  delegations/  — 1 delegation packet (DLG-20260609)
  evaluations/  — 2 evaluation reports (EVL-20260610 x2)
  evidence/     — IPC Phase 0 freeze evidence JSON + web chat project setup ZIP
  handoffs/     — 1 handoff record (HND-20260609)
  schemas/      — JSON Schemas for all record types
  bindings/     — empty (no active bindings recorded)
  autonomy/     — empty (no autonomy grants)
  command_intents/ — empty
  command_manifests/ — empty
  console/      — empty
  archive/      — empty
```

No active bindings. No autonomy grants. No accepted operator decisions beyond the mandate records in governance docs.

---

## 9. Runtime Posture at Close

```
operational_mode:      fail_closed_non_autonomous
autonomous_allowed:    False
safe_pass_enabled:     False
fail_closed_coherent:  True
```

The system was never in any mode other than `fail_closed_non_autonomous`.

---

## 10. Repository Structure at Close

```
C:\axiom\
  axiom/                — Python runtime package
    agents/             — Agent scaffolding (GoalPlanner, TaskPlanner, etc.)
    app/                — Bootstrap validation, status reporting
    core/               — State machine, scheduler, governance, policy engine
    gateways/           — ModelGateway, NetworkGateway, SandboxGateway, etc.
    persistence/        — SQLite layer (db.py, repositories.py)
    policy/             — Manifest schemas, role manifests, tool capability map
    security/           — Injection scanner, fingerprint guard, audit
    tools/              — tool_capability_map helper
  governance/           — Governance scaffold (00-80 directories)
  tools/                — CLI tools for governance record ops, audits, verification
  tests/                — pytest test suite
  docs/                 — Phase closeout documents (phases 2-9)
  ipc/                  — Frozen IPC channel (inert)
  ui/terminal/          — PowerShell TUI dashboard
  logs/                 — Handoff and operator command index logs
  axiom.db              — SQLite database
  requirements.txt      — Python dependencies
  pytest.ini            — Test configuration
  launch-workspace.ps1  — Workspace launcher (PSMUX/tmux)
  AXIOM_Implementation_v1.13.md — Canonical implementation specification
  CLAUDE.md             — Claude Code agent entrypoint and authority boundary
  AGENTS.md             — Codex agent entrypoint and authority boundary
  .antigravity.md       — Antigravity agent entrypoint and authority boundary
```

---

## 11. What Worked Well

- **Fail-closed design** — every layer genuinely refused to proceed without explicit operator action; the system never "slipped" into unauthorized execution.
- **Multi-agent governance panel** — having distinct agents with distinct roles (architect, implementer, auditor, synthesizer) created genuine checks; Claude Code audits caught real specification drift that Codex implementations would otherwise have silently absorbed.
- **Phase-gated implementation** — strict sequential phases with documented proof requirements prevented scope creep and made rollback straightforward.
- **JSON-first governance records** — the `governance/80_records/` JSON schema approach was significantly more legible and auditable than the earlier markdown-file governance structure.
- **Mandate acceptance workflow** — requiring explicit operator acceptance of each mandate before implementation work began was the right call; it prevented a lot of "agent assumes approval" drift.
- **Terminal UI** — the multi-panel PSMUX dashboard gave Jeremy a useful at-a-glance view of system state during development.
- **The IPC design** — even though IPC was ultimately frozen, the message-passing architecture between agents was a clear, auditable communication channel during the phases it was active.

---

## 12. What Didn't Work / Lessons

- **Governance overhead grew faster than implementation** — by Mandates 5-8, the governance scaffold was producing more governance artifacts than implementation artifacts. A lighter-weight governance model might achieve the same safety guarantees with less ceremony.
- **The "advisory council" (Kimi, Qwen, DeepSeek) was retired** — external AI models contributing governance opinions via paste sequences added coordination cost without proportional value. The simpler four-agent panel was better.
- **IPC as an execution channel was unsafe by design** — the impulse to use IPC message frames as agent dispatch was recognized early and frozen, but the underlying pattern (agents triggering other agents via message files) should have been designed out from the start rather than incrementally restricted.
- **Model gateway was never activated** — the full cloud cascade architecture (local qwen3:4b classifier → cloud planning/synthesis) was scaffolded to high specification but never exercised in production, because the safety gates upstream of it were never all cleared simultaneously. Whether the architecture would have worked in practice remains unknown.
- **The two-key autonomy gate was never cleared** — the most interesting part of the design (bounded runtime autonomy with evidence-bound, revocable grants) was never reached because earlier phases took longer than expected and the project was suspended before activation was attempted.
- **Windows-native complexity** — PowerShell + Python + SQLite + tmux on Windows added friction at every layer (path handling, encoding, process management, PSMUX bridging) that wouldn't exist on Linux/macOS.

---

## 13. Build Upon / Inspiration

If revisiting this work, the highest-value components to carry forward are:

1. **The governance doctrine pattern** — operator-governed, fail-closed, autonomy-gated by design. This is the right mental model for safe AI agent systems.
2. **The JSON-first governance records schema** (`governance/80_records/schemas/`) — these schemas encode what "accepted governance state" looks like in machine-readable form.
3. **The two-key autonomy gate** — technical readiness gate + explicit operator mandate. Neither alone is sufficient.
4. **The phase-gated implementation pattern with proof requirements** — each phase closed only when specific verification commands passed.
5. **The multi-agent panel role separation** — distinct roles with distinct authority boundaries, all advisory unless operator converts output to binding governance.
6. **The manifest-bound task model** — every agent execution requires a pre-registered manifest with SHA256 verification. This prevents drift and makes auditing tractable.

---

*This document was authored at project suspension (2026-06-10) as a legacy reference for future work.*
