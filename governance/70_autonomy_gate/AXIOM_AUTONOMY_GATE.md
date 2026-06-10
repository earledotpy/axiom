# AXIOM Autonomy Gate

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define when AXIOM may perform bounded autonomous work without Operator approval for every individual step.

## 1. Autonomy Gate Purpose

The Autonomy Gate layer defines the conditions under which delegated agent work may proceed with reduced Operator intervention.

Doctrine defines what must always be true. Workflow defines lifecycle states. Transport defines how information moves. Delegation defines how work is assigned. Execution defines how work is performed. Evaluation defines how work is judged. The Operator Console defines how governed state is presented. The Autonomy Gate defines when scoped autonomy may operate.

The root autonomy rule is:

```text
Autonomy is scoped, revocable, evidence-bound, and never self-authorizing.
```

## 2. Autonomy Non-Authority Rule

Autonomy may allow agents or deterministic systems to perform bounded work inside an accepted scope.

Autonomy may not by itself authorize:

- doctrine change
- binding update
- mandate acceptance
- scope expansion
- runtime authority expansion
- model promotion
- IPC reactivation
- security gate weakening
- network/tool permission expansion
- scheduler or executor integration outside accepted scope
- final acceptance of agent work

Autonomous work still returns to Jeremy for authority-bearing decisions unless a separate accepted mandate explicitly defines a narrower pre-authorized decision path.

## 3. Two-Key Rule

Runtime autonomy requires both independent keys for the specific scope:

```text
1. Technical readiness gate passes.
2. Jeremy accepts a separate mandate authorizing the specific autonomy scope.
```

Neither key alone is sufficient.

The following are not sufficient by themselves:

- passing tests
- successful implementation
- architecture recommendation
- governance audit recommendation
- CLI-native approval
- model capability
- scheduler availability
- delegation packet
- accepted mandate without technical readiness
- technical readiness without accepted mandate

## 4. Autonomy Levels

Recommended autonomy levels:

| Level | Name | Meaning |
| --- | --- | --- |
| A0 | no_autonomy | Agents act only through direct Operator/session instruction. |
| A1 | advisory_autonomy | Agents may inspect, summarize, and recommend inside scope. |
| A2 | planning_autonomy | Agents may decompose goals into plans, tasks, and delegation packets. |
| A3 | draft_artifact_autonomy | Agents may create draft governance artifacts and handoffs. |
| A4 | bounded_implementation_autonomy | Agents may implement inside a specific accepted mandate. |
| A5 | bounded_remediation_autonomy | Agents may remediate findings inside accepted scope. |
| A6 | bounded_cycle_autonomy | Agents may run a bounded cycle: plan, implement, evaluate, summarize, and return to Jeremy for decision. |

The redesigned scaffold should not define unbounded full autonomy.

## 5. Autonomy Grant Object

An Autonomy Grant is the canonical object that records a proposed, accepted, revoked, or expired scoped autonomy allowance.

Autonomy grant records belong under:

```text
governance/80_records/autonomy/
```

Minimum schema:

```json
{
  "schema": "axiom.autonomy_grant.v0.1",
  "grant_id": "",
  "created_utc": "",
  "operator_decision_id": "",
  "technical_gate_result": "",
  "grant_state": "draft",
  "autonomy_level": "",
  "scope": "",
  "out_of_scope": [],
  "allowed_roles": [],
  "allowed_actions": [],
  "forbidden_actions": [],
  "protected_surfaces": [],
  "required_evidence": [],
  "stop_conditions": [],
  "revocation_conditions": [],
  "expires_utc": "",
  "max_cycles": 1,
  "authority_status": "advisory_only"
}
```

Grant state values:

```text
draft
pending_review
operator_accepted
revoked
expired
```

The default state for a drafted grant is `draft` with `authority_status: advisory_only`.

An Autonomy Grant may carry `authority_status: operator_accepted` only after Jeremy explicitly accepts the grant and the accepted record cites both the technical readiness result and the Operator decision.

No active autonomy exists unless a valid current Autonomy Grant exists for the requested scope with:

- `grant_state: operator_accepted`
- `authority_status: operator_accepted`
- a cited Operator decision
- a passed technical readiness gate result
- unexpired scope and cycle limits

## 6. Scope Requirements

Every autonomy grant must define:

- autonomy level
- scope
- out-of-scope boundaries
- allowed roles
- allowed actions
- forbidden actions
- protected surfaces
- required evidence
- stop conditions
- revocation conditions
- expiration or cycle limit
- Operator decision checkpoints

Ambiguous scope fails closed.

## 7. Required Evidence

Autonomous work must preserve enough evidence for independent review.

Required evidence should include:

- active grant id
- delegation id
- mandate or decision id
- lifecycle state
- files read
- files changed
- commands run
- command results
- tests/checks performed
- skipped checks and reasons
- blockers encountered
- remediation attempted
- final evaluation report
- recommended Operator decision

Evidence must distinguish live verification results from assumptions, recommendations, and memory-derived context.

## 8. Stop Conditions

Autonomy must stop and return to Jeremy when:

- scope ambiguity appears
- protected surface is touched unexpectedly
- required evidence cannot be collected
- required check fails
- required review blocks
- agent disagreement cannot be resolved inside scope
- command or artifact schema is invalid
- cost, time, or cycle limit is reached
- runtime, autonomy, IPC, scheduler, executor, model, network, or security boundary is implicated outside grant scope
- Doctrine conflict is detected
- Workflow transition is not allowed
- Operator decision is required

Scheduled or background work is autonomous behavior. Cron jobs, scheduler loops, executor loops, background workers, timers, or any recurring task runner require a valid current Autonomy Grant when they perform governed work without direct per-step Operator instruction.

Stop conditions should produce a blocking finding, evidence summary, and recommended next action.

## 9. Revocation Conditions

Autonomy should be easy to revoke.

Default revocation conditions:

- Operator revokes grant
- grant expires
- max cycle count reached
- stop condition triggers
- evidence trail breaks
- protected boundary conflict appears
- security or runtime risk is detected
- required review is unavailable
- active binding changes in a way that affects the grant

After revocation, autonomous work must stop and return to Operator-directed mode.

## 10. Forbidden Autonomy

The redesigned scaffold should forbid:

- unbounded autonomy
- self-authorizing autonomy
- hidden autonomy grants
- autonomy without expiration or cycle limit
- autonomy that can approve its own output
- autonomy that bypasses evidence capture
- autonomy that bypasses Operator Console visibility
- autonomy that weakens Doctrine
- autonomy that reactivates IPC execution paths without accepted mandate
- autonomy that expands network, model, sandbox, security, scheduler, executor, or runtime authority outside scope

## 11. Operator UX

Recommended future command mapping:

```text
/axiom:show-autonomy-status
/axiom:request-autonomy-review
/axiom:grant-autonomy
/axiom:stop-autonomy
/axiom:revoke-autonomy
/axiom:show-autonomy-evidence
```

Target operator flow:

```text
Jeremy defines desired bounded autonomy.
Agents evaluate scope, risks, and readiness.
Technical gate reports readiness.
Jeremy accepts or rejects a scoped autonomy grant.
Autonomous work proceeds inside the grant.
Operator Console shows status, blockers, and evidence.
Autonomy stops at decision points, limits, or revocation conditions.
Jeremy accepts, rejects, defers, narrows, or requests remediation.
```

## 12. Autonomy Alignment

The Autonomy Gate directly supports the target operating model:

```text
Jeremy sets goals, boundaries, and accepts results.
Agents plan, build, evaluate, remediate, and summarize inside bounded autonomy grants.
The system gates, logs, stops, and exposes the work through the Operator Console.
```

This preserves Operator authority while reducing per-step micromanagement.

## 13. Design Consequence

The Autonomy Gate layer should drive:

- autonomy grant schema
- autonomy status reporting
- technical readiness gate integration
- grant expiration and revocation logic
- autonomy evidence requirements
- stop-condition handling
- Operator Console autonomy view
- `/axiom:*` autonomy commands

Any autonomy rule that conflicts with Doctrine, Workflow, Transport, Delegation, Execution, Evaluation, or Operator Console rules must fail closed until Jeremy resolves the conflict.
