# AXIOM Governance Runbook

Status: Active
Owner: Jeremy, Operator
Effective date: 2026-05-24

## Purpose

This runbook defines how AXIOM governance is executed in the terminal-native system. It is the procedural companion to the operating model, panel role charter, active bindings, current context packet, decision log, and open questions register.

## Standard Governance Cycle

1. Intake the question, proposal, defect, role change, architecture concern, or policy issue.
2. Classify the item as implementation, governance, architecture, advisory, or mixed.
3. Assign the primary reviewer by role.
4. Gather the minimum context needed from the live spine, repository files, current evidence, and any relevant archived legacy material.
5. Produce a recommendation with explicit assumptions, risks, and expected impact.
6. Jeremy decides whether to approve, reject, defer, narrow, or send to advisory council review.
7. Approved decisions are recorded as decision records and reflected in active bindings when binding authority changes.
8. Codex implements approved file changes when implementation is needed.
9. Verification is performed and reported.
10. The decision log, context packet, and open questions are updated if the decision changes future operating context.

## Intake Classification

Use this classification before deciding who leads:

| Type | Lead | Examples |
| --- | --- | --- |
| Implementation | Codex | File edits, debugging, tests, verification, local migration work. |
| Governance | Claude Code | Binding changes, role boundaries, authority questions, policy consistency. |
| Architecture | Antigravity | System design, long-range structure, research, strategic tradeoffs. |
| Advisory | Jeremy | Kimi, Qwen, or DeepSeek review through online chat. |
| Mixed | Jeremy | Any proposal that changes both governance and implementation behavior. |

## Proposal Format

Every substantive proposal should answer:

- What decision is being requested?
- What files, roles, bindings, or runtime behavior are affected?
- Is this binding governance, advisory guidance, documentation, or implementation?
- What evidence supports the proposal?
- What risks or unresolved assumptions remain?
- Which panel member owns the next step?

## Panel Review Sequence

Use the default sequence when a proposal changes direction, governance, architecture, or runtime posture:

1. Antigravity reviews architecture, research, and strategic fit.
2. Claude Code reviews governance coherence, role authority, ambiguity, and safety consistency.
3. Codex reviews implementation feasibility, local file impact, test path, and likely failure modes.
4. Jeremy decides the disposition.

Active panel members write their draft reviews and pass state using `governance/05_handoffs/`. Files must be named according to the convention: `<QuestionID>_<PanelMember>_<DocType>.md` (e.g., `OQ-001_Antigravity_Architecture_Proposal.md`).

For narrow implementation fixes, Jeremy may direct Codex to act first and request later review only if the change touches governance, architecture, safety posture, or active bindings.

## Advisory Council Trigger

Jeremy should consider Kimi, Qwen, or DeepSeek review when:

- A decision changes panel roles, authority, or binding governance.
- A decision changes AXIOM architecture direction.
- A decision has unclear safety impact.
- The panel disagrees or the tradeoff is not well understood.
- External critique would improve confidence before ratification.

When advisory review is needed, paste the files listed in `governance/03_advisory_council/00_PASTE_SEQUENCE.md` into a new chat, followed by the specific proposal or question.

## Advisory Council Output Rule

Kimi, Qwen, and DeepSeek must return complete markdown documents suitable to save as `.md` files. They must name their response files using the convention `YYYYMMDD_<Advisor>_Response_<Topic/QuestionID>.md` (e.g., `20260524_Kimi_Response_OQ001.md`). Save these response files under `governance/03_advisory_council/`. Their responses are advisory only until Jeremy approves and records a decision.

## Decision Dispositions

Use one of these dispositions:

- Approved: accepted by Jeremy and ready to record or implement.
- Rejected: declined by Jeremy with reason recorded when useful.
- Deferred: not decided; requires more evidence, timing, or review.
- Advisory only: useful guidance but not binding governance.
- Superseded: replaced by a later decision.

## Decision Record Requirements

Create a decision record in `governance/04_decision_records/` when a decision:

- Changes active bindings.
- Changes panel roles or authority.
- Changes the governance process.
- Changes AXIOM architecture direction.
- Changes safety posture or runtime authority.
- Deprecates or replaces a significant governance file.

Decision records should include:

- Title.
- Status.
- Date.
- Operator.
- Decision.
- Reason.
- Impact.

## Active Binding Update Rule

Update `AXIOM_Active_Bindings.md` only when Jeremy approves a rule that should govern future AXIOM behavior. Do not convert advice, drafts, research, or implementation notes into active bindings without explicit approval.

## Verification Requirements

For governance-only changes:

- Verify the expected files exist.
- Verify Jeremy is named as Operator where applicable.
- Verify advisory council files require markdown output when advisory workflow is affected.
- Verify archived or deprecated material was preserved when migration occurs.

For implementation or policy changes:

- Run the relevant local checks.
- Prefer the canonical AXIOM preflight when system health is in scope.
- Report exactly what was and was not tested.
- Do not claim provider credentials, external API calls, cloud model calls, or autonomous behavior were verified unless live output proves it.

## Legacy Material Rule

Use `governance/06_archives/` as historical evidence, not active authority. Pull archived legacy details forward only by creating or updating active live-spine files and recording the decision when the change becomes binding.

Use `governance/06_archives/` as historical evidence. Do not edit archives unless Jeremy explicitly grants that scope.

## Closeout Report

Every governance work session should close with:

- Files changed.
- Files archived or deprecated.
- Decisions recorded.
- Verification performed.
- Verification not performed.
- Open questions or next recommended review.
