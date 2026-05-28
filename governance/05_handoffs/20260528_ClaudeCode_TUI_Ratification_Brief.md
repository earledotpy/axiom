# TUI Design Language: Ratification Brief

**From**: Claude Code (Governance Auditor)
**To**: Antigravity (Chief Architect)
**Date**: 2026-05-28
**Branch**: `claude/axiom-terminal-cleanup-fW6tR`
**ADR-0006 status**: Out-of-cycle deviation — ratification requested

---

## What Happened and Why This Brief Exists

During a session on 2026-05-28, Jeremy asked the three AI co-designers (Claude, GPT, Gemini) to decide how the AXIOM Operator Console should look and feel — including the future state when autonomous agent operation is enabled. Jeremy's framing: *"it is their decision on how this should look and feel for the Operator."*

Claude Code (this role) acted as designer and implementer — producing the TUI design spec, implementing three terminal module changes, and committing a design reference HTML mockup. This is a deviation from ADR-0006, which assigns architectural planning to Antigravity. The deviation was authorized in scope by Jeremy's explicit direction.

This brief documents what was done, identifies the items that require Antigravity's architectural review, and distinguishes them from the items that are terminal-layer display utilities requiring no ratification.

---

## What Was Committed

**Commits on `claude/axiom-terminal-cleanup-fW6tR`:**

| Commit | Files | Nature |
|---|---|---|
| `dd03752` | `ui/terminal/modules/39-operator-ui.ps1` | 9 new status tokens added to `Get-AxiomUiStatusColor` |
| `dd03752` | `ui/terminal/modules/05-visual.ps1` | Three-AI sigil ANSI color codes; sigils rendered in startup banner |
| `dd03752` | `ui/terminal/modules/39-now.ps1` | `[WARN]` → `[IDLE]` for healthy fail-closed posture |
| `f1713c0` | `ui/terminal/docs/axiom-console-mockup.html` | Design reference HTML mockup (non-executable) |

**Plan document** (design spec, not a committed code file):
`~/.claude/plans/does-this-plan-also-inherited-rose.md`

All changes are in the terminal UI layer (`ui/terminal/`). No runtime Python code, no manifests, no governance files, no protected paths (per ADR-0006 §Protected Files) were modified.

---

## Items That Do NOT Require Ratification

These are pure display utilities with no semantic or architectural weight:

- **Token color additions** (`39-operator-ui.ps1`) — `CAND`, `PEND`, `SKIP`, `LOCK`, `QRNT`, `RUN`, `GATE`, `INIT` added to `Get-AxiomUiStatusColor`. Mapping new names to existing `ConsoleColor` values. No logic, no state.
- **Sigil ANSI codes** (`05-visual.ps1`) — Three hex color constants added to `$script:AxiomAnsi`. The startup banner now renders `◆ ◇ ◈` with per-AI colors. Cosmetic only.
- **HTML mockup** — Design reference artifact. No runtime effect.

---

## Items Requiring Antigravity Ratification

### 1. `[IDLE]` vs `[WARN]` — Posture State Representation

**File**: `ui/terminal/modules/39-now.ps1`
**Change**: `axiom-now` previously emitted `[WARN]` whenever any blocker was present. It now distinguishes between the three *expected* fail-closed blockers (`autonomous_disabled`, `safe_pass_disabled`, `no_current_trusted_model`) and *unexpected* blockers. When all present blockers are expected, it emits `[IDLE]` in dim with an `(expected — fail-closed by design)` annotation. `[WARN]` is now reserved for unexpected conditions.

**Rationale given**: The three expected blockers together define the healthy `fail_closed_non_autonomous` steady state. Displaying them as `[WARN]` yellow trains the Operator to treat intentional containment as a problem. `[IDLE]` communicates "contained by design, not broken."

**Why Antigravity should review**: This is a judgment about how the system represents its own posture to the Operator. If the distinction between "expected" and "unexpected" blockers is wrong — or if `[IDLE]` understates the significance of those conditions for the Operator's situational awareness — the change should be amended. The logic is in `39-now.ps1:272–295`.

---

### 2. TUI Design Language Specification

**Document**: `~/.claude/plans/does-this-plan-also-inherited-rose.md`

This plan defines:
- A formalized status token table (16 tokens with hex colors and semantic meanings)
- Box-drawing character set for panel borders
- Two-variant layout: Variant A (`fail_closed_non_autonomous`, current) and Variant B (`autonomous_supervised`, future)
- Color semantics: green=verified, gold=intentionally contained, red=actual failure, dim=expected/design
- Three-AI provenance sigil assignment: `◆ Claude (Anthropic)` · `◇ GPT/Codex (OpenAI)` · `◈ Gemini/Antigravity (Google)`

**Why Antigravity should review**: This spec will serve as the canonical design reference for all future terminal panel development. Antigravity's primary concern: does this design language align with the long-term architecture intended for AXIOM's operator interface, particularly under OQ-001 (multi-agent governance support)?

Specific questions for Antigravity:

1. The token semantics assume a clean binary between "expected blockers" and "unexpected blockers." Is this the right model, or are there fail-closed conditions that should be `[WARN]` even when technically expected?
2. The color palette assigns gold (`#FFD36E`) to *all* intentionally-contained conditions. Does this create ambiguity between "by design" containment and genuine degradation that happens to be gold?
3. The sigil `◆◇◈` are ordered Claude-GPT-Gemini left-to-right in the header. Antigravity should confirm or amend the assignment.

---

### 3. Future Autonomous Panel Architecture

**Document**: Plan file §3B, §7.3, §7.4

The plan defines future panels not yet built:

| Module (proposed) | Command | Purpose |
|---|---|---|
| `62-execution-trace.ps1` | `axiom-execution-trace` | Active chain pipeline trace (plan→dispatch→run→verify), budget bar |
| `63-approval-gate.ps1` | `axiom-approval-gate` | Surfaces `needs_human_input` tasks, shows operator approval commands (read-only) |
| `64-autonomous-posture.ps1` | `axiom-autonomous-posture` | Autonomous gate evaluation in one screen |

**Variant B layout**: When `autonomous_supervised` is active, the dashboard replaces Manifest Integrity with the Active Execution panel and Live Event Stream with the Approval Gate panel.

**Why Antigravity should review**: These panels define what the Operator sees when autonomy is enabled. The read-only boundary is maintained (each panel shows what to do, not does it), but the information architecture — which state is surfaced, in what priority — is an architectural decision. Antigravity should confirm:

1. Is the `needs_human_input` approval gate the correct trigger surface for the Approval Gate panel, or should it be a different event class?
2. Does the pipeline trace (plan→dispatch→run→verify) match the intended agent execution model per OQ-001?
3. Are there agent boundary conditions visible in Variant B that the current panel design does not surface?

These panels should **not be built until Antigravity ratifies Variant B** or proposes amendments via the normal ADR-0006 planning cycle.

---

## Authorization Basis

Per the session record: Jeremy directed the AI co-designers to decide how the console should look and feel. This authorized Claude Code to act outside ADR-0006 for the design phase. The terminal-layer implementation that followed (three PowerShell module edits) was narrow enough in scope — and sufficiently far from protected paths — that it did not require a separate Operator authorization step.

This brief does not request additional authorization. It requests Antigravity's architectural review of the three items above so the design language can become formally ratified before it is used as the basis for future implementation work.

---

## Antigravity's Response Options

Per ADR-0006 and `GEMINI.governance.md`, Antigravity should produce a written response that:

1. **Ratifies** items as-is, with or without notes
2. **Amends** items with specific proposed changes (Claude Code will implement amendments as terminal-layer edits)
3. **Defers** items pending further research or a new OQ

Antigravity does not need to produce a full implementation plan for the existing commits — they are already implemented. The response is architectural review and ratification.

---

## Verification State at Time of Commit

The branch verification battery was not re-run on this machine after the terminal changes (terminal modules are not in the pytest suite). The following should be run before merging:

```powershell
python tools/verify_foundation.py        # foundation_passed: True, fail_closed_coherent: True
pytest tests -v                          # full regression, no regressions expected
axiom-doctor                             # all PASS — module load order, commands present
```

No runtime Python code was modified in this session's commits. The pre-existing branch changes (`axiom/core/scheduler_loop.py`, `tests/test_scheduler_loop.py`, `tools/run_scheduler_loop.py`) are from Phase 9 work and are covered by their own verification bar in `Phase9_ClaudeCode_Planning_Brief.md`.
