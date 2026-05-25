# AXIOM Governance Operating Model

Status: Active
Owner: Jeremy, Operator
Effective date: 2026-05-24

## Purpose

AXIOM governance is now terminal-native. The active governance surface exists to give Codex, Claude Code, Antigravity, and the external advisory council enough shared context to make clear judgement calls without carrying the full legacy chat-era file set.

The live spine is the current source of authority. Legacy chat-era materials are preserved under `governance/07_deprecated_legacy/` and historical archives remain under `governance/06_archives/`.

## Authority Model

Jeremy is the Operator and final authority for AXIOM direction.

Panel members may advise, critique, implement, verify, or research within their assigned roles. No panel member may independently expand AXIOM runtime authority, enable autonomous operation, approve model promotion, alter fail-closed posture, or convert advice into binding governance without Operator approval.

## Active Governance Surface

The active terminal governance system is:

- `AXIOM_Governance_Operating_Model.md` - operating authority and process.
- `AXIOM_Panel_Role_Charter.md` - panel roles, duties, and limits.
- `AXIOM_Active_Bindings.md` - binding rules currently in force.
- `AXIOM_Current_Context_Packet.md` - concise context for panel and advisory review.
- `AXIOM_Decision_Log.md` - index of accepted, rejected, or deferred decisions.
- `AXIOM_Governance_Runbook.md` - procedure for running governance cycles.
- `AXIOM_Open_Questions.md` - unresolved questions requiring research, review, or Operator judgement.

CLI adapters live under `governance/02_cli_surfaces/`. External advisory packets and responses live under `governance/03_advisory_council/`. Formal decision records live under `governance/04_decision_records/`. Active panel draft reviews and handoffs live under `governance/05_handoffs/`.

## Decision Workflow

1. A panel member or the Operator raises a proposal.
2. Antigravity evaluates architecture, research, external context, and strategic fit.
3. Claude Code evaluates governance coherence, ambiguity, safety posture, and policy consistency.
4. Codex evaluates implementation feasibility, local risks, and verification path.
5. Jeremy approves, rejects, defers, or sends the proposal to the external advisory council.
6. Approved decisions are recorded in `governance/04_decision_records/` and summarized in `AXIOM_Decision_Log.md`.
7. Binding changes are reflected in `AXIOM_Active_Bindings.md`.

## Advisory Council Handling

Kimi, Qwen, and DeepSeek are advisory-only because access is through online chat sessions mediated by Jeremy. Advisory council members do not receive direct terminal access. Jeremy copies the advisory packet files into each new chat when outside review is needed.

Every advisory response must be returned as a markdown document. Advisory responses should distinguish recommendations from assumptions and should state whether the recommendation should become binding, remain advisory, or require further evidence.

## Runtime Safety Boundary

AXIOM remains local-first, fail-closed, and non-autonomous by design. Governance changes must not weaken runtime safeguards. Implementation work must report live verification evidence separately from claims, assumptions, or memory-derived context.
