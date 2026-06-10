# AXIOM Governance Cycle Simplification

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Mandate: MND-ACCEPTED-2026-0018-GOVERNANCE-CYCLE-SIMPLIFICATION
Purpose: Define how the redesigned governance scaffold reduces routine documentation while preserving authority boundaries.

## 1. Purpose

This document defines a simplified governance cycle for routine AXIOM work.

The redesign must reduce per-cycle documentation burden. The standing layer documents should be reused as rules, not recreated for every feature.

Root rule:

```text
Use the smallest governance artifact that preserves authority boundaries, evidence, and Operator decision clarity.
```

## 2. Two Paths

AXIOM should use two governance paths:

```text
1. Lightweight Task Card Path
2. Full Mandate Path
```

The Task Card Path handles low-risk work. The Full Mandate Path handles authority-sensitive work.

## 3. Lightweight Task Card Path

Task cards replace full mandate documents for routine low-risk work.

Task card records belong under:

```text
governance/80_records/tasks/
```

Use task cards for:

- draft governance documents
- schema proposals
- command design proposals
- review requests
- synthesis summaries
- non-runtime research
- read-only visibility design
- documentation cleanup inside approved draft areas
- generated console summaries

Task cards are advisory by default. They do not authorize binding governance, runtime behavior, protected file edits, parser changes, IPC changes, autonomy, or active binding updates.

## 4. Full Mandate Path

Full mandates remain required for:

- doctrine change
- binding record update
- scaffold root replacement or promotion
- accepted decision record creation under `governance/80_records/decisions/`
- parser implementation
- `/axiom:*` command implementation
- operator command manifest changes
- ledger behavior changes
- runtime code changes
- IPC reactivation or transport changes
- scheduler or executor behavior changes
- model, network, sandbox, memory, or security changes
- autonomy grant creation or autonomy enablement
- protected file edits outside already accepted scope

If work can alter authority, active governance, runtime behavior, or protected surfaces, it requires a full mandate.

## 5. Minimal Cycle

Routine low-risk work should use this minimal cycle:

```text
1. Operator goal
2. Task card
3. Agent work
4. Evidence or review JSON
5. Console summary
6. Operator decision or closeout
```

This replaces repeated long-form mandate candidates for low-risk design/review tasks.

## 6. Task Card Schema

Minimum task-card schema:

```json
{
  "schema": "axiom.task_card.v0.1",
  "task_card_id": "",
  "created_utc": "",
  "operator_goal": "",
  "scope": "",
  "authority_status": "advisory_only",
  "risk_class": "low",
  "path": "lightweight_task_card",
  "allowed_actions": [],
  "forbidden_actions": [],
  "inputs_read": [],
  "required_outputs": [],
  "stop_conditions": [],
  "evidence_required": [],
  "recommended_next_action": ""
}
```

Task cards should be JSON-first, concise, and console-readable.

## 7. Required Task Card Fields

Required fields:

- `task_card_id`
- `created_utc`
- `operator_goal`
- `scope`
- `authority_status`
- `risk_class`
- `allowed_actions`
- `forbidden_actions`
- `required_outputs`
- `stop_conditions`

The default `authority_status` is:

```text
advisory_only
```

## 8. Escalation Rules

A task card must escalate to a full mandate when:

- scope becomes authority-sensitive
- binding records may change
- scaffold root may change
- decision records may be created or modified
- parser, manifest, or ledger behavior may change
- runtime code may change
- IPC may reactivate or change transport behavior
- scheduler or executor behavior may change
- model, network, sandbox, memory, or security behavior may change
- autonomy grant or autonomy enablement is involved
- protected file edits are required outside accepted scope
- Operator authority is ambiguous
- evidence is insufficient for closeout
- any blocking objection remains unresolved

Escalation must fail closed. The task card should stop and recommend a full mandate.

## 9. Documentation Reduction Rules

Routine low-risk cycles should not produce long mandate candidates.

Use:

```text
1 task card
1 output artifact
1 evidence/review JSON
1 console summary
```

Avoid duplicating the same state across:

- mandate candidate
- accepted mandate
- review request
- review response
- synthesis markdown
- decision log
- operator chronicle

The Operator Console should summarize active state from structured artifacts instead of requiring Jeremy to read all artifacts manually.

## 10. Evidence Requirements

Task-card evidence should be proportionate to risk.

Minimum evidence:

- files read
- files changed
- outputs produced
- checks run, if any
- skipped checks and reason
- assumptions
- blockers
- recommended next action

Low-risk documentation or schema work may use JSON validation and file existence checks as evidence. Runtime or authority-sensitive evidence requires a full mandate.

## 11. Console Integration

Task cards should appear in the Operator Console as:

```text
active_state
decision_queue
blockers
evidence
```

Console summaries should show:

- task goal
- scope
- current status
- blockers
- evidence quality
- next action
- whether escalation is required

Console summaries remain advisory view state.

Mandate 8 adds a non-executing governance cycle coordinator for this flow:

```text
python tools\governance_cycle.py show --json
python tools\governance_cycle.py summary
python tools\governance_cycle.py next-actions --json
python tools\governance_cycle.py file-roadmap --title "..." --scope "..." --item "..."
```

The coordinator reads JSON records and derives cycle state, blockers, evidence status, pending decision state, and next valid actions. It does not route agents, run commands, execute patches, write ledger rows, alter runtime state, reactivate IPC, start scheduler or executor loops, enable autonomy, or emit `VERIFIED_COMMIT`.

Future mandate plans created with Antigravity should be filed as advisory records when they need to persist beyond a terminal session. A roadmap record is durable planning context only; it is not an accepted mandate.

## 12. Review Requirements

Low-risk task cards may proceed without full AUD/ARCH review when the Operator directly scopes the work and no protected surface is affected.

AUD review is required when:

- authority boundary is unclear
- task card might be mistaken for mandate authority
- lifecycle state or authority status is ambiguous
- evidence is insufficient

ARCH review is required when:

- layer structure changes
- implementation direction changes
- future autonomy, parser, or console architecture is affected

Terminal-only review output is not durable governance state. Reviews that affect blockers, decision readiness, or closeout should be filed through:

```text
python tools\review_ingest.py create --target-artifact "..." --scope "..." --review-file "..."
```

Ingested reviews remain advisory evaluation records until Jeremy records a separate Operator decision.

## 13. Forbidden Task Card Uses

Task cards must not be used to authorize:

- binding governance
- mandate acceptance
- doctrine change
- active binding update
- runtime change
- parser or manifest change
- ledger behavior change
- IPC reactivation
- autonomy grant or autonomy enablement
- scheduler or executor integration
- model, network, sandbox, memory, or security change

## 14. Review Questions

Reviewers should answer:

- Does the task-card path preserve Operator authority?
- Are full-mandate thresholds strict enough?
- Could a task card be mistaken for an accepted mandate?
- Are escalation rules sufficiently fail-closed?
- Does this actually reduce documentation burden?
- Is the minimal cycle compatible with the Operator Console design?
