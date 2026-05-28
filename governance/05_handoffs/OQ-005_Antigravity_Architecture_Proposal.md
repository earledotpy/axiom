# OQ-005: AXIOM Architecture Proposal — Shared Pool Implementation Model

**Date**: 2026-05-27  
**Author**: Antigravity (Chief Architect and Researcher)  
**Topic**: Shared Pool implementation and build responsibilities to resolve Codex rate limits.  
**Question ID**: OQ-005  
**Disposition**: Draft / Panel Review  

---

## 1. Context & Rationale

During active construction of the AXIOM codebase, Codex has hit API rate limits, halting implementation. While the current panel charter specifies Codex as the sole implementation agent, the AXIOM governance model does not restrict other capable agents from participating in builds when resource conservation is necessary. 

We propose **Option C (Shared Pool)** as the operational model. Under Option C, all active panel agents (Codex, Claude Code, and Antigravity) are authorized to implement changes and execute local builds across the repository, serving as an operational fallback to distribute load and bypass rate limits.

---

## 2. Technical and Operational Constraints

To prevent chaos, code duplication, and overlapping changes under a Shared Pool model, we define the following constraints:

1. **Local-First, Fail-Closed Safety Boundary (Unchanged)**:
   - Shared build authority **does not** change AXIOM's runtime constraints (`autonomous_allowed = False`, `safe_pass_enabled = False`).
   - Every agent must adhere to the 7-step policy evaluation engine and SQLite schema invariants.
2. **Governance Changes Remain Bounded**:
   - Although all agents may edit implementation code, changes to the live spine (`governance/01_live_spine/`), CLI surfaces (`governance/02_cli_surfaces/`), and root files (`AGENTS.md`, `CLAUDE.md`, `.antigravity.md`) **must still go through the standard governance cycle** (review by Antigravity and Claude Code, approved by Jeremy).
3. **Audit Separation**:
   - Claude Code serves as the Governance Auditor. When Claude Code implements a change, its audit of its own code must be double-checked by Antigravity or verified with a comprehensive test run before the Operator approves the decision.
4. **Coordination Protocols**:
   - Before starting a multi-file implementation task, the active agent must check the git history and `governance/05_handoffs/` to verify no other agent is editing the same module.

---

## 3. Proposed Live Spine & Surface Updates

### A. AXIOM_Active_Bindings.md
Update bindings to expand implementation authority:
- **AB-003**: Codex serves as an Implementation Specialist and Troubleshooter.
- **AB-004**: Claude Code serves as a Governance Auditor, Specification Critic, and Implementation Specialist.
- **AB-005**: Antigravity serves as Chief Architect, Researcher, and Implementation Specialist.

### B. AXIOM_Panel_Role_Charter.md
Modify the charter to document shared implementation limits:
- **Codex**: Maintain focus on persistence, gateways, and script troubleshooting, but may edit any files.
- **Claude Code**: Focus on security, policies, and test suites, but may edit any files.
- **Antigravity**: Focus on core orchestration and validation, but may edit any files.

### C. CLI Surfaces and Root Developer Guidelines
Update `AGENTS.md`, `CLAUDE.md`, and `.antigravity.md` to inform each agent of their shared implementation privileges and rules.

---

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Code Style Discrepancies** | Medium | Maintain the surrounding style (4-space indentation, explicit absolute imports, type hints). |
| **Overlapping Edits / Conflicts** | High | Use the handoffs folder to signal lock states on long-running tasks. |
| **Bypassing Audits** | High | The Operator remains the final approval authority. No change is merged without complete test verification. |
