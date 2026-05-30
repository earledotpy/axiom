# TUI Design Language: Antigravity Ratification Review

**From**: Antigravity (Chief Architect)  
**To**: Jeremy (Operator), Claude Code (Auditor), Codex (Implementation Specialist)  
**Date**: 2026-05-28  
**Handoff Document**: `20260528_ClaudeCode_TUI_Ratification_Brief.md`  

---

## 1. Architectural Review of Core Items

This document records Antigravity's architectural evaluation and ratification of the Terminal UI (TUI) design changes implemented on branch `claude/axiom-terminal-cleanup-fW6tR`.

### Item 1: `[IDLE]` vs `[WARN]` State Representation
* **Decision**: **RATIFIED** (with notes).
* **Rationale**: Reserving `[WARN]` strictly for unexpected, active degradations or safety violations (e.g. heartbeat loss, database write failures) is correct. Displaying a permanent, active `[WARN]` warning for the system's baseline, healthy fail-closed state (`autonomous_disabled`, `safe_pass_disabled`, `no_current_trusted_model`) induces warning fatigue. Transitioning the display state to `[IDLE]` in dim color, annotated with `(expected — fail-closed by design)`, accurately represents the posture state and improves Operator situational awareness.

---

## 2. Review of Specific Design Language Questions

### Question 1: Binary categorization of "expected" vs "unexpected" blockers
* **Verdict**: **RATIFIED**.
* **Detail**: Separating expected containment constraints from unexpected system errors is appropriate. However, if any expected blocker fails its integrity checks (e.g. a manifest integrity mismatch or fingerprint validation failure), it must escalate immediately to `[WARN]` or `[ERROR]` status.

### Question 2: Color Palette and Gold (`#FFD36E`) Semantics
* **Verdict**: **AMENDED**.
* **Detail**: Assigning gold to *all* intentionally-contained conditions creates a color collision with warning semantics.
  * **Amendment**: 
    * Use **Dim Gray or Dark Blue** for standard "by-design" containment blocks that represent steady-state idle safety (such as `LOCK` or `INIT`).
    * Reserve **Gold/Yellow** (`#FFD36E`) strictly for states that require operator attention or signify active processing gates, such as `PEND` (waiting for human input), `GATE` (evaluation in progress), or `QRNT` (active quarantine following an audit violation).

### Question 3: Sigil Assignments (`◆◇◈`)
* **Verdict**: **RATIFIED**.
* **Detail**: The sigil assignments and left-to-right order are approved. 
  * `◆` Claude (Anthropic / Governance Auditor)
  * `◇` GPT/Codex (OpenAI / Implementation Specialist)
  * `◈` Gemini/Antigravity (Google / Chief Architect)
  This order visually balances the console header and correctly identifies the provenance of panel operations.

---

## 3. Future Autonomous Panel Architecture (Variant B Layout)

### Question 1: Trigger surface for the Approval Gate Panel
* **Verdict**: **RATIFIED**.
* **Detail**: The Approval Gate panel must trigger on tasks transitioning to `needs_human_input` status in the database (`tasks.status`). This is the canonical representation of a task blocked on Operator authorization.

### Question 2: Pipeline Trace Alignment
* **Verdict**: **RATIFIED**.
* **Detail**: The trace stages (plan → dispatch → run → verify) map directly to AXIOM's database task classes (`goal_planning` / `task_planning` → `dispatched` → `running` → `result_verification`). This trace aligns with the multi-agent execution model planned for OQ-001.

### Question 3: Visibility of Safety Boundaries in Variant B
* **Verdict**: **AMENDED**.
* **Detail**: When Variant B (autonomous layout) is active, replacing the Manifest Integrity and Live Event Stream panels must not hide resource caps or boundary state.
  * **Amendment**: The console footer or status line in Variant B must include real-time summaries of **Resource Budget Limits** (remaining tokens, sandbox CPU/RAM usage, and active policy denials) so that the Operator retains complete, un-obscured visibility of containment margins.

---

## 4. Next Steps in Loop

1. **Codex** to implement the color and panel footer amendments specified in sections 2.2 and 3.3 as part of its terminal cleanups.
2. **Claude Code** to verify the uncommitted changes on `claude/axiom-terminal-cleanup-fW6tR` before Jeremy merges the branch.
