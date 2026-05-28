# OQ-005: Codex Feasibility Check - Shared Pool Implementation Model

**Reviewer**: Codex  
**Date**: 2026-05-27  
**Proposal**: `governance/05_handoffs/OQ-005_Antigravity_Architecture_Proposal.md`  
**Question ID**: OQ-005  
**Role Lens**: Implementation Specialist and Troubleshooter  

---

## Executive Disposition

**Codex recommends deferring OQ-005 as written.**

The operational problem is real: relying on one implementation surface can stall AXIOM work when Codex hits resource limits. A shared implementation model is technically possible, but the current proposal grants broad repository write authority before the repository has the controls needed to absorb multi-agent implementation safely.

The feasible path is a narrower pilot:

1. Preserve Claude Code as the default independent governance auditor.
2. Allow Codex and Antigravity to implement only within explicit, non-overlapping domains.
3. Keep governance live-spine files and safety-critical runtime modules behind separate Operator approval.
4. Require serial task ownership, handoff logging, and a fixed verification gate before any shared-pool result is accepted.

Blanket authority for Codex, Claude Code, and Antigravity to "may edit any files" is not implementation-feasible under the current repo controls.

---

## Feasibility Assessment

| Area | Assessment | Notes |
| --- | --- | --- |
| Operational value | Feasible | Distributing build work can reduce stalls if the agents actually use separate rate-limit pools. |
| Repository safety | Not feasible as written | The current working tree has no technical lock, ownership matrix, branch discipline, or protected-file gate. |
| Audit independence | Not feasible as written | Claude Code cannot remain the normal governance auditor while also freely implementing changes it may later audit. |
| Style and quality control | Feasible with gates | AXIOM already has a strong pytest culture, but no committed formatter or linter configuration. |
| Governance compatibility | Not feasible as written | AB-003, AB-004, AB-005, and the Panel Role Charter would need explicit amendment and decision records. |
| Runtime safety posture | Feasible if carved out | Shared implementation does not inherently weaken fail-closed, local-first, non-autonomous posture, but unsafe modules need elevated handling. |

---

## Local Implementation Risks

### 1. Shared writes will collide without serial ownership

The proposal relies on each agent checking git history and `governance/05_handoffs/` before multi-file work. That is a useful convention, but it is not a collision-control mechanism. AXIOM currently has one local working tree, broad pending changes, and no multi-agent scheduler or merge queue.

Minimum viable control:

- One active implementation owner per task.
- A handoff note before starting any multi-file change.
- No overlapping edits to the same module family unless Jeremy explicitly serializes the work.
- `git status --short` checked before and after every implementation slice.

### 2. Protected files need a separate authorization path

The following paths should not be part of routine shared-pool implementation authority:

- `governance/01_live_spine/`
- `governance/02_cli_surfaces/`
- root agent instruction files: `AGENTS.md`, `CLAUDE.md`, `.antigravity.md`
- `axiom/security/`
- `axiom/core/state_machine.py`
- `axiom/core/policy_engine.py`
- `axiom/persistence/schema.sql`
- `axiom/policy/`
- `tools/register_manifests.py`

These are not impossible to change, but they should require explicit Operator approval for that slice plus cross-agent review before acceptance.

### 3. Claude Code implementation creates an avoidable audit gap

From an implementation standpoint, the simplest safe partition is not a three-agent full pool. It is:

- Codex: default implementer and troubleshooter.
- Antigravity: limited implementation support for architecture-approved, non-governance slices.
- Claude Code: remains default governance auditor and specification critic.

Claude Code can still provide patch suggestions or pseudocode during review, but granting it routine repository write authority forces AXIOM to invent a second independent audit function before the immediate rate-limit problem is solved.

### 4. Quality gates are not yet strong enough for broad shared implementation

The current repo guidance defines style conventions, and the test suite provides useful regression coverage. That is not enough for multiple independent implementation styles. Before a broad shared pool, AXIOM should either add machine-enforced style and import checks or keep the pilot narrow enough that style drift remains manageable by review.

Minimum viable verification gate for a pilot:

- Focused tests for changed behavior.
- Existing audit scripts relevant to the touched area.
- Full `pytest tests -v` before accepting governance-impacting or safety-impacting changes.
- `python tools/register_manifests.py` after policy, schema, or manifest changes.

---

## Recommended Pilot Model

### Authority

Codex remains the primary implementation specialist. Antigravity may implement bounded slices only when Jeremy assigns a task and the slice stays outside protected files unless explicitly approved. Claude Code remains auditor-only by default.

### Domain Partition

Initial pilot ownership should be narrow:

| Domain | Default Owner | Notes |
| --- | --- | --- |
| Persistence, scripts, verification tooling | Codex | Matches current implementation role. |
| Gateway adapters and architecture experiments | Antigravity, with Codex verification | Must avoid binding runtime authority changes without separate approval. |
| Governance review, proposal critique, binding consistency | Claude Code | Should not audit its own authored implementation. |
| Live spine and role bindings | Jeremy-approved governance cycle | No routine shared-pool edits. |
| Security, state machine, policy engine, manifests | Codex only unless Jeremy assigns exception | Requires strongest verification evidence. |

### Coordination Protocol

Every shared-pool implementation task should produce or update a handoff note containing:

- Question or task ID.
- Active owner.
- Files or domains reserved.
- Start time and current status.
- Verification commands run.
- Known remaining risks.

This is not a substitute for git-level isolation, but it is the lowest-friction control compatible with the current repo.

### Acceptance Gate

A shared-pool result should not be accepted unless the final report separates:

- changed files,
- commands run,
- commands not run,
- live failures,
- assumptions,
- whether protected files were touched,
- who is eligible to audit the change.

This matches AB-015 and keeps implementation evidence separate from recommendations.

---

## Decision Options for Jeremy

### Option 1 - Reject Current Draft

Reject the broad "may edit any files" Shared Pool proposal and keep Codex as sole implementer. This preserves clean role separation but does not solve Codex rate-limit stalls.

### Option 2 - Defer and Draft a Narrow Pilot

Defer OQ-005 as written and request a revised proposal for a Codex-plus-Antigravity implementation pilot with Claude Code as auditor. This is the recommended path.

### Option 3 - Approve Full Shared Pool with Preconditions

Approve the direction only after all preconditions are ratified:

- binding amendments for AB-003, AB-004, and AB-005,
- Panel Role Charter updates,
- ADR for the role-authority change,
- protected-file carve-out,
- audit-exclusion rule,
- task-lock or branch convention,
- mandatory verification gate.

This is feasible, but it is a larger governance and tooling project than the current operational bottleneck requires.

---

## Recommended Next Step

Codex recommends that Jeremy **defer OQ-005 as written** and authorize a narrower follow-up artifact:

`OQ-005A_Shared_Implementation_Pilot_Proposal.md`

That proposal should define a limited Codex/Antigravity implementation pilot, preserve Claude Code as independent auditor, list protected paths, and specify the exact verification gate for pilot acceptance.

---

## Verification Performed

Codex reviewed:

- `governance/02_cli_surfaces/codex/AGENTS.governance.md`
- `governance/01_live_spine/AXIOM_Governance_Operating_Model.md`
- `governance/01_live_spine/AXIOM_Panel_Role_Charter.md`
- `governance/01_live_spine/AXIOM_Active_Bindings.md`
- `governance/01_live_spine/AXIOM_Current_Context_Packet.md`
- `governance/01_live_spine/AXIOM_Open_Questions.md`
- `governance/03_advisory_council/OQ-005_Advisory_Packet_Insert.md`
- `governance/05_handoffs/OQ-005_Antigravity_Architecture_Proposal.md`
- `governance/05_handoffs/OQ-005_ClaudeCode_Governance_Audit.md`
- `governance/05_handoffs/20260527_DeepSeek_Response_OQ005.md`
- `governance/05_handoffs/20260527_Kimi_Response_OQ005.md`
- `governance/05_handoffs/20260527_Qwen_Response_OQ005.md`

No runtime tests were run because this task compiled a governance feasibility check and did not change executable code.
