# AXIOM

**Status: Legacy Reference — Project on hold indefinitely as of 2026-06-10.**

This repository is preserved as a reference artifact. It is not actively maintained. See [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md) for a complete current-state description.

---

## What This Was

AXIOM was an experiment in building a **locally-hosted, operator-governed, fail-closed AI agent runtime** on a Windows workstation.

The core premise: a human operator retains complete, auditable authority over every AI action — while still delegating planning, implementation, review, and verification work to a panel of specialized AI agents. The system was the opposite of "AI doing things autonomously." It was a governance harness that forces every operation through an explicit operator decision, a fail-closed policy engine, and a two-key autonomy gate before anything can execute.

### What it was trying to do

- Run a bounded, local AI agent that could help with software engineering tasks.
- Keep a local `qwen3:4b` model (via Ollama) in a sanitizer/router/classifier lane.
- Delegate planning and synthesis to cloud models through an explicit, auditable cascade.
- Make every authority boundary legible — to the human operator, to auditing agents, and to the code itself.
- Build on Windows natively: PowerShell + Python 3.12 + SQLite + tmux.

### What it was not

- An autonomous agent system.
- A production tool.
- A framework for general-purpose agent deployment.

---

## Architecture Summary

```
Operator (Jeremy)
  └─ Governance Layer (mandate acceptance, authority boundary, fail-closed posture)
       └─ Policy Engine (manifest binding, tool capability map, injection scanner)
            └─ Scheduler / State Machine (one task at a time, heartbeat enforcement)
                 └─ Executors (no-op → manual_noop → bounded agent task types)
                      └─ Gateways (Model, Network, Sandbox, Memory, Telegram)
                           └─ Agents (GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier)
```

Every layer only activates when the layer above it explicitly authorizes it. The system remained in `fail_closed_non_autonomous` mode for its entire lifetime.

### Multi-agent governance panel

| Agent | Role | Process |
|-------|------|---------|
| Antigravity | Chief Architect and Researcher | `architect` / `plan` |
| Codex | Implementation Specialist and Troubleshooter | `implement` / `build` |
| Claude Code | Governance Auditor and Specification Critic | `audit` / `verify` |
| Cursor | Synthesis and summarization | `synthesize` / `summarize` |

All agent output was advisory. Only the operator (Jeremy) could convert agent output into binding governance.

---

## Implementation Status at Suspension

| Component | Status |
|-----------|--------|
| SQLite persistence layer | Complete |
| Canonical schema + manifest schema | Complete |
| State machine + scheduler | Complete |
| Policy engine + manifest binder | Complete |
| Plan injection scanner | Complete |
| Bootstrap validation | Complete |
| Supervisor monitor | Complete |
| Operator command ledger | Complete |
| Operator console (read-only) | Complete |
| JSON governance record schemas | Complete |
| Governance cycle coordinator | Complete |
| Gateway scaffolding (Model/Network/Sandbox/Memory/Telegram) | Scaffolded, never activated |
| Agent scaffolding (GoalPlanner/TaskPlanner/ToolExecutor/ResultVerifier) | Scaffolded, never activated |
| Automatic scheduler→executor (manual_noop only) | Complete (Phase 9) |
| Governance redesign (Mandates 1–8) | Complete |
| IPC freeze (Level 2A Phase 0) | Complete |
| Terminal UI / PSMUX dashboard | Complete |
| Classifier calibration | Never reached |
| Model fingerprint registration | Never reached |
| Runtime autonomy | Never activated |
| Cloud cascade | Never activated |

---

## What Worked Well

- **Fail-closed design** — the system genuinely refused unauthorized execution at every layer.
- **Phase-gated implementation with proof requirements** — strict sequential phases prevented scope creep.
- **Multi-agent panel with distinct roles** — genuine checks; audit caught real specification drift.
- **JSON-first governance records** — machine-readable schema approach was more auditable than markdown governance.
- **Mandate acceptance workflow** — requiring explicit operator acceptance before implementation prevented authority drift.
- **The two-key autonomy gate design** — the right model for bounded AI autonomy: technical gate + operator mandate, neither alone sufficient.

## What Didn't Work / Lessons Learned

- **Governance overhead outpaced implementation** — the scaffold produced more governance artifacts than code by the later mandates.
- **The advisory council of external models** (Kimi, Qwen, DeepSeek) added coordination cost without proportional value; the simpler four-agent panel was better.
- **IPC as execution channel was unsafe by design** — should have been designed out from the start rather than incrementally frozen.
- **The most interesting part was never reached** — the two-key autonomy gate, cloud cascade, and bounded runtime execution were never cleared because earlier phases took longer than expected.
- **Windows-native complexity** added friction at every layer that wouldn't exist on Linux.

---

## What to Build Upon

If revisiting this work:

1. **The governance doctrine pattern** — `governance/00_doctrine/AXIOM_DOCTRINE.md` — operator-governed, fail-closed, autonomy-gated by design. This is the right mental model.
2. **The JSON governance record schemas** — `governance/80_records/schemas/` — encode what accepted governance state looks like.
3. **The two-key autonomy gate** — `governance/70_autonomy_gate/AXIOM_AUTONOMY_GATE.md` — technical readiness + explicit operator mandate.
4. **The manifest-bound task model** — every agent execution requires a pre-registered manifest with SHA256 verification.
5. **The phase-gated implementation pattern** — each phase closes only when specific verification commands pass.

---

## Repository Layout

```
axiom/           Python runtime package (core, agents, gateways, persistence, security)
governance/      Governance scaffold (00_doctrine through 80_records)
tools/           CLI tools for governance record ops, audits, verification
tests/           pytest test suite
docs/            Phase closeout documents (phases 2–9)
ipc/             Frozen IPC channel (inert historical evidence)
ui/terminal/     PowerShell TUI dashboard (PSMUX)
logs/            Handoff and operator command index logs

DESIGN_DOCUMENT.md              Complete current-state design reference
AXIOM_Implementation_v1.13.md  Canonical implementation specification
CLAUDE.md                       Claude Code agent entrypoint
AGENTS.md                       Codex agent entrypoint
.antigravity.md                 Antigravity agent entrypoint
requirements.txt                Python dependencies
pytest.ini                      Test configuration
launch-workspace.ps1            Workspace launcher
```

---

## Runtime State at Suspension

```
operational_mode:      fail_closed_non_autonomous
autonomous_allowed:    False
safe_pass_enabled:     False
fail_closed_coherent:  True
```

The system was never in any mode other than `fail_closed_non_autonomous`.

---

## Stack

- Python 3.12 (Windows)
- SQLite + sqlite-vec
- Ollama (qwen3:4b local model)
- PowerShell + psmux (TUI)
- pytest
- jsonschema, cryptography, python-telegram-bot (scaffolded dependencies)

---

*Project suspended 2026-06-10. Preserved as legacy reference.*
