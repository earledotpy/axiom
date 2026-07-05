# AXIOM Governance Workflow

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define the redesigned governance workflow layer below Doctrine.

## 1. Workflow Purpose

The Workflow layer defines how a governance item moves from idea to accepted decision, implementation, verification, and archive.

Doctrine defines what must always be true. Workflow defines the allowed lifecycle states and transitions that preserve doctrine.

The root workflow rule is:

```text
No artifact advances into accepted, binding, executable, or autonomous state without explicit Operator decision.
```

## 2. Lifecycle States

The default governance lifecycle is:

```text
proposal
  -> architecture_review
  -> governance_audit
  -> implementation_plan
  -> mandate_candidate
  -> operator_decision
  -> implementation_evidence
  -> verification_audit
  -> decision_record
  -> binding_update
  -> archive
```

Not every governance item needs every state. Skipped states must be intentional, scoped, and recorded when the item affects authority, runtime behavior, protected files, IPC, scheduler/executor behavior, model promotion, network/tool access, autonomy, or binding records.

## 3. State Definitions

| State | Purpose | Authority status |
| --- | --- | --- |
| proposal | Defines the change, question, or problem. | advisory_only |
| architecture_review | Evaluates design fit, system tradeoffs, and external context. | advisory_only |
| governance_audit | Evaluates policy consistency, ambiguity, safety posture, and authority risk. | advisory_only |
| implementation_plan | Defines scoped implementation steps and verification path. | advisory_only |
| mandate_candidate | Drafts a proposed mandate for Operator decision. | advisory_only |
| operator_decision | Records Jeremy's approve, reject, defer, or narrow-scope decision. | operator_accepted |
| implementation_evidence | Reports changed files, commands run, results, and remaining risks. | evidence_only |
| verification_audit | Independently reviews implementation evidence and unresolved risk. | advisory_only |
| decision_record | Preserves the accepted decision and final status. | operator_accepted when based on OP decision |
| binding_update | Updates active binding state when authorized. | binding |
| archive | Retires non-active artifacts as historical evidence. | historical_evidence |

## 4. Transition Rules

- Agent-created artifacts enter the workflow as `advisory_only`.
- Only Jeremy may transition an item into `operator_accepted`.
- A mandate candidate does not become a mandate until Jeremy accepts it.
- A decision record must cite or contain the Operator decision it records.
- A binding update requires an accepted decision record.
- Implementation evidence must report live evidence separately from assumptions and recommendations.
- Verification audit may recommend acceptance, rejection, remediation, or additional evidence, but remains advisory.
- Archived artifacts must not be treated as active authority without re-ratification.

## 5. Role Responsibilities by Stage

| Stage | OP | SYNTH | ARCH | AUD | IMPL |
| --- | --- | --- | --- | --- | --- |
| proposal | create or assign | structure | advise | critique | feasibility notes |
| architecture_review | review | consolidate | primary | identify risks | feasibility notes |
| governance_audit | review | consolidate | answer design questions | primary | answer implementation questions |
| implementation_plan | approve scope direction | draft or consolidate | review design fit | audit ambiguity | validate feasibility |
| mandate_candidate | accept, reject, defer, narrow | draft | review | audit | feasibility review |
| operator_decision | primary | record only when directed | advisory | advisory | advisory |
| implementation_evidence | review | consolidate | review architecture impact | audit evidence | primary |
| verification_audit | decide closeout path | consolidate | advise | primary | answer findings |
| decision_record | accept or direct recording | record when directed | advisory | audit record consistency | provide evidence |
| binding_update | authorize | apply when directed | advisory | audit authority risk | implement when directed |
| archive | authorize when significant | organize | advisory | audit when significant | preserve evidence |

## 6. Blocking vs Non-Blocking Findings

Workflow artifacts should distinguish blocking objections from non-blocking concerns.

Blocking objections are issues that should prevent acceptance, implementation, or binding update until resolved.

Examples:

- unclear Operator authority
- missing accepted mandate
- authority expansion not reviewed
- autonomy or IPC boundary ambiguity
- protected-file edit outside accepted scope
- missing verification evidence for safety-relevant claims
- conflict with Doctrine

Non-blocking concerns are issues that should be recorded but do not prevent progress by themselves.

Examples:

- documentation polish
- naming inconsistency that does not affect authority
- optional test hardening
- future maintainability concern
- archive organization improvement

## 7. Operator Decision Points

Operator decision points are the only authority-bearing workflow transitions.

Allowed decision forms:

```text
approve
reject
defer
narrow_scope
request_review
archive
```

Recommended future command mapping:

```text
/axiom:approve
/axiom:reject
/axiom:defer
/axiom:narrow-scope
/axiom:request-review
/axiom:archive-cycle
```

Native CLI slash commands may support local workflow, but they do not create Axiom governance authority.

## 8. Workflow Failure Rules

Workflow must fail closed and refuse a transition when:

- lifecycle state is undefined
- lifecycle transition is not allowed
- required Operator decision is absent
- required accepted mandate is absent
- required independent review is absent
- required artifact is missing
- required artifact fields are missing or invalid
- blocking objection remains unresolved
- binding update is attempted without an accepted decision record
- mandate candidate is treated as accepted before Operator decision
- archive artifact is treated as active authority
- agent role attempts an authority-bearing transition
- native CLI approval is mistaken for Axiom governance approval
- authority status conflicts with lifecycle state
- Doctrine conflict is detected

Workflow failure should produce a blocking finding, identify the refused transition, and recommend the next Operator action.

## 9. Evidence Requirements

Evidence must be specific enough for independent review.

Implementation evidence should include:

- files changed
- commands run
- command results
- tests or checks performed
- skipped checks and reason
- known risks
- assumptions
- recommended next action

Evidence claims must not rely on memory, intent, or expected behavior when live verification is possible.

## 10. Archive Rules

Archive is a lifecycle state, not an authority state.

Archived artifacts remain historical evidence only. They do not become active doctrine, binding records, accepted mandates, or current context unless Jeremy explicitly re-ratifies them.

The redesigned scaffold should avoid using archive folders as active working context.

## 11. Design Consequence

The Workflow layer should drive the structure of:

- handoff artifacts
- slash-command output schemas
- operator command manifests
- decision record templates
- binding update procedures
- implementation evidence reports
- verification audit reports
- archive and closeout routines

Any workflow step that conflicts with Doctrine must fail closed until Jeremy resolves the conflict.
