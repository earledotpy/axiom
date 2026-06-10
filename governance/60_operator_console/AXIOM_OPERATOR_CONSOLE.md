# AXIOM Operator Console

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define how Jeremy monitors active governance state, blockers, evidence, recommendations, and decisions.

## 1. Console Purpose

The Operator Console layer defines what Jeremy sees and does day to day when operating the redesigned governance scaffold.

Doctrine defines what must always be true. Workflow defines lifecycle states. Transport defines how information moves. Delegation defines how work is assigned. Execution defines how work is performed. Evaluation defines how work is judged. The Operator Console defines how governed state is presented for Operator awareness and decision.

The root console rule is:

```text
The Operator Console presents governed state; it does not invent governed state.
```

## 2. Console Non-Authority Rule

The console may aggregate, summarize, filter, and present governance state.

The console may not by itself authorize:

- acceptance
- mandate approval
- binding update
- doctrine change
- runtime autonomy
- IPC reactivation
- scheduler or executor integration
- model promotion
- security gate weakening
- network/tool permission expansion
- protected file edits outside accepted scope

The console must not display advisory recommendations as accepted decisions.

## 3. Console State Inputs

The console should read from canonical structured or accepted sources.

Recommended inputs:

- delegation packets
- lifecycle state records
- agent handoff JSON
- evaluation reports
- implementation evidence
- Operator command ledger
- decision records
- binding records
- command manifests and command intents
- autonomy gate status
- archive index

The console should avoid treating unstructured prose as authoritative state unless the prose is an accepted decision record, active binding, or other Operator-accepted governance record.

## 4. Console State Summary

Recommended summary shape:

```json
{
  "schema": "axiom.operator_console_state.v0.1",
  "generated_utc": "",
  "authority_status": "advisory_only",
  "active_cycles": [],
  "active_delegations": [],
  "pending_operator_decisions": [],
  "blocking_objections": [],
  "non_blocking_concerns": [],
  "latest_evidence": [],
  "recommended_next_actions": [],
  "authority_sensitive_items": [],
  "autonomy_status": {}
}
```

Console summaries are views, not source records.

## 5. Console Views

Initial views:

```text
1. Active State View
2. Blockers View
3. Decision Queue View
4. Evidence View
5. Autonomy Status View
```

Additional views may be added when they reduce Operator burden without hiding authority-relevant detail.

## 6. Active State View

The Active State View answers:

```text
What is currently happening?
What goal is active?
Which delegation or cycle is active?
What lifecycle state is each item in?
Who has the next role?
What is the recommended next action?
```

This view should prioritize active and pending items over historical detail.

## 7. Blockers View

The Blockers View answers:

```text
What is blocked?
Why is it blocked?
Who reported it?
What boundary is affected?
What evidence supports the blocker?
What next action is recommended?
```

Blockers should identify the affected layer when possible:

```text
Doctrine
Workflow
Transport
Delegation
Execution
Evaluation
Operator Console
Autonomy Gate
```

Blocking objections must be visually and structurally distinct from non-blocking concerns in future UI or command output.

## 8. Decision Queue View

The Decision Queue View answers:

```text
What requires Jeremy's decision?
What decision options are available?
What evidence supports each option?
What happens if Jeremy defers?
What happens if Jeremy narrows scope?
```

Recommended decision statuses:

```text
ready_for_operator_decision
blocked_pending_evidence
blocked_pending_review
needs_scope_clarification
needs_remediation
deferred
closed
```

The decision queue should be the primary console surface.

## 9. Evidence View

The Evidence View answers:

```text
What changed?
What commands ran?
What passed?
What failed?
What was skipped?
What risks remain?
```

Evidence should separate:

- implementation evidence
- verification evidence
- audit findings
- assumptions
- skipped checks
- known risks

The console should not convert evidence into acceptance.

## 10. Autonomy Status View

The Autonomy Status View answers:

```text
Is runtime autonomy disabled or enabled?
What autonomy gates exist?
What scope, if any, is eligible?
What evidence supports eligibility?
What mandate, if any, authorizes the scope?
What is still missing?
```

Default display should be conservative:

```text
runtime autonomy: disabled unless both required gates are satisfied for a specific scope
```

The console may report readiness state and accepted grant records. It may not enable autonomy. In the governance-only implementation, runtime autonomy remains disabled even when an accepted grant record is visible.

## 11. Command Surface

Recommended future command mapping:

```text
/axiom:show-active-state
/axiom:show-blockers
/axiom:show-delegations
/axiom:show-evaluation
/axiom:show-decisions
/axiom:show-evidence
/axiom:ready-for-decision
/axiom:show-autonomy-status
```

Decision commands remain separate:

```text
/axiom:approve
/axiom:reject
/axiom:defer
/axiom:narrow-scope
/axiom:request-review
/axiom:request-remediation
/axiom:archive-cycle
```

Read-only console commands may be allowed before authority-bearing commands are implemented.

## 12. Presentation Rules

Console output should be concise and action-oriented.

Good console output emphasizes:

- number of active cycles
- pending decisions
- blockers
- latest evidence
- recommended next action
- authority-sensitive items

Console output should avoid:

- long artifact dumps
- ambiguous approval language
- hiding blockers inside summaries
- mixing historical archives with active state
- treating recommendations as accepted decisions

The console must use authority language carefully.

Allowed for advisory records:

```text
recommended_for_operator_acceptance
ready_for_operator_decision
blocked
needs_remediation
insufficient_evidence
out_of_scope
```

Allowed for accepted records only:

```text
operator_accepted
binding
approved
accepted
authorized
```

## 13. Failure Rules

The console must fail closed when:

- source state is inconsistent
- lifecycle state is missing
- authority status is missing
- blocker target is missing
- evidence target is missing
- decision record cannot be traced to Operator decision
- active binding conflicts with draft state
- archive artifact is treated as active state
- native CLI command is mistaken for Axiom command
- autonomy status cannot be determined

Failure should surface as a blocker, not as inferred state.

## 14. Autonomy Alignment

The Operator Console is the layer that lets Jeremy monitor agent work without micromanaging every artifact.

The intended operating model is:

```text
Agents plan, build, evaluate, and summarize.
The console shows active state, blockers, evidence, and decision needs.
Jeremy governs by direction, scope, and decision.
```

The console should make bounded autonomy observable, not automatic.

## 15. Design Consequence

The Operator Console layer should drive:

- read-only `/axiom:*` status commands
- active state summary schema
- blocker summary generation
- decision queue generation
- evidence view generation
- autonomy status reporting
- active vs archived state separation
- future terminal or UI dashboard design

Any console rule that conflicts with Doctrine, Workflow, Transport, Delegation, Execution, or Evaluation must fail closed until Jeremy resolves the conflict.
