# ADR-0006: Staged Implementation-Review Loop

Status: Approved
Date: 2026-05-28
Operator: Jeremy

## Decision

Establish the Staged Implementation-Review Loop as the recognized AXIOM development workflow for implementation tasks. The loop runs in three steps, each owned by a distinct panel role:

1. **Plan** — Antigravity reads the live AXIOM worktree and produces a written task plan. The plan is the handoff artifact passed to Codex. Antigravity does not write implementation code.

2. **Implement** — Codex receives the plan, writes the code changes, and runs local verification (relevant tests, `python tools/register_manifests.py` where applicable). Codex owns the implementation diff.

3. **Review** — Claude Code reviews Codex's uncommitted changes against active bindings and the AXIOM runtime safety posture, runs `pytest`, and reports findings before the change is accepted by Jeremy.

No agent moves to the next step until the current step is complete and its output is visible to Jeremy.

## Reason

OQ-005 identified that relying on Codex as the sole implementation agent created rate-limit stalls during active development. The full Shared Pool proposal (all agents with open write authority) raised blocking audit-independence and governance-coherence concerns reviewed by the advisory council and the Claude Code audit.

The Staged Loop resolves the rate-limit problem without expanding any agent's authority:

- Antigravity's planning function is already chartered. The loop formalizes the plan-to-Codex handoff that the Charter already requires.
- Codex retains sole implementation authority. No change to AB-003.
- Claude Code reviews Codex's work, not its own. Audit independence is preserved structurally. No change to AB-004.
- No active binding (AB-003, AB-004, AB-005) changes. This is a workflow decision, not an authority expansion.

## Impact

Panel members now have an explicit, sequential loop to follow for implementation tasks initiated by Jeremy. Antigravity produces the plan. Codex implements. Claude Code verifies. Jeremy approves.

The loop is the default pattern for non-trivial implementation work. Jeremy may direct a shorter path (Codex directly, without a planning step) for narrow or well-specified tasks.

The loop does not authorize any agent to skip AXIOM's verification battery, modify protected files outside the standard governance cycle, or chain steps without Jeremy's observation at each handoff.

## Protected Files

The following paths are outside routine loop authority for all agents. Changes to these paths require explicit Operator authorization before the implementation step:

- `governance/01_live_spine/`
- `governance/02_cli_surfaces/`
- `AGENTS.md`, `CLAUDE.md`, `.antigravity.md`
- `axiom/security/`
- `axiom/core/state_machine.py`
- `axiom/core/policy_engine.py`
- `axiom/persistence/schema.sql`
- `axiom/policy/`
- `tools/register_manifests.py`

## Resolves

OQ-005: How can AXIOM safely partition implementation and build duties among Codex, Claude Code, and Antigravity to mitigate rate limits?
