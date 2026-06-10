# AXIOM Governance Delegation

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define how Operator intent becomes scoped agent work without transferring governance authority.

## 1. Delegation Purpose

The Delegation layer defines how Jeremy can express a goal once and allow agents to plan, divide, execute, review, and report work inside governed boundaries.

Doctrine defines what must always be true. Workflow defines lifecycle states. Transport defines how information moves. Delegation defines how scoped work is assigned.

The root delegation rule is:

```text
Delegation assigns work; it does not transfer authority.
```

## 2. Delegation Non-Authority Rule

A delegation may authorize agents to perform scoped work, but it does not authorize binding governance state.

Delegation may allow:

- research
- planning
- architecture review
- governance audit
- synthesis
- implementation feasibility review
- implementation inside an accepted mandate
- verification
- evidence collection
- draft artifact creation

Delegation may not by itself authorize:

- doctrine change
- binding update
- mandate acceptance
- runtime autonomy
- IPC reactivation
- model promotion
- security gate weakening
- network/tool permission expansion
- scheduler or executor integration
- protected file edits outside accepted scope

## 3. Delegation Packet

A Delegation Packet is the canonical object that records Operator intent and agent working boundaries.

Delegation packet records belong under:

```text
governance/80_records/delegations/
```

Minimum schema:

```json
{
  "schema": "axiom.delegation_packet.v0.1",
  "delegation_id": "",
  "created_utc": "",
  "operator_goal": "",
  "scope": "",
  "out_of_scope": [],
  "authority_status": "advisory_only",
  "delegation_context": "operator_directed",
  "allowed_roles": [],
  "required_reviews": [],
  "allowed_actions": [],
  "forbidden_actions": [],
  "success_criteria": [],
  "evidence_required": [],
  "decision_points": [],
  "stop_conditions": [],
  "recommended_first_agent": ""
}
```

Delegation packets should be structured enough for CLI agents to consume reliably and plain enough for Jeremy to inspect quickly.

The `delegation_context` field may record that the packet was created from Operator direction. It is not an authority status and must not be treated as acceptance, binding governance, mandate approval, or runtime authorization.

## 4. Delegation Types

Recommended delegation types:

| Type | Purpose | Typical first agent |
| --- | --- | --- |
| research_delegation | investigate options, docs, risks, or context | ARCH |
| planning_delegation | produce an implementation or governance plan | Cursor or ARCH |
| implementation_delegation | implement approved scoped work | IMPL |
| audit_delegation | review policy, ambiguity, authority, and safety | AUD |
| verification_delegation | verify evidence, tests, and closeout readiness | AUD |
| synthesis_delegation | consolidate reviews, blockers, and decision options | Cursor |
| multi_agent_cycle | run a governed planning/review/implementation/evaluation cycle | Cursor or ARCH |

The most important delegation type for bounded autonomy is `multi_agent_cycle`.

## 5. Delegation vs Mandate

Delegation and mandate are separate governance concepts.

Delegation:

```text
Agents may work on this problem within these boundaries.
```

Mandate:

```text
This specific implementation, binding change, or governed action is approved.
```

Delegation can authorize advisory work and bounded preparation. Mandate authorizes implementation, binding update, or other authority-sensitive action when accepted by Jeremy.

An implementation delegation must cite an accepted mandate if it changes protected files, runtime behavior, binding records, command authority, IPC posture, scheduler/executor behavior, model policy, security gates, or autonomy posture.

## 6. Role Routing

Default routing for a multi-agent cycle:

```text
1. OP defines goal and boundaries.
2. Cursor converts goal into a delegation packet.
3. ARCH evaluates architecture and research direction.
4. AUD evaluates governance risk, ambiguity, and authority boundaries.
5. Cursor consolidates findings and drafts next action.
6. IMPL evaluates feasibility or implements only if mandate allows.
7. AUD verifies evidence after implementation.
8. Cursor summarizes blockers, evidence, and decision options.
9. OP decides approve, reject, defer, narrow, or continue.
```

Role routing may be simplified for low-risk work, but authority-sensitive work should keep independent review.

Approved machine-oriented process/function mapping:

| Agent | Process | Function |
| --- | --- | --- |
| Antigravity | `architect` | `plan` |
| Codex | `implement` | `build` |
| Claude Code | `audit` | `verify` |
| Cursor | `synthesize` | `summarize` |

These labels are suitable for JSON records, console summaries, routing metadata, and future read-only status views. They do not create authority and must not be interpreted as Operator acceptance.

## 7. Allowed Actions

Delegation packets should explicitly state allowed actions.

Common allowed actions:

- read repository files
- inspect existing governance artifacts
- create draft governance artifacts
- create advisory JSON handoffs
- run non-destructive local checks
- propose implementation plans
- draft mandate candidates
- collect implementation evidence
- summarize active blockers

Implementation actions should be allowed only when the delegation cites an accepted mandate or when Jeremy explicitly scopes the implementation work in the current session.

## 8. Forbidden Actions

Delegation packets should explicitly state forbidden actions.

Default forbidden actions:

- convert advisory output into binding governance
- approve mandate candidates
- update binding records without accepted decision
- change Doctrine without accepted decision
- enable runtime autonomy
- reactivate IPC execution
- alter security gates without accepted mandate
- promote models
- expand network or tool permissions
- bypass parser or manifest validation for `/axiom:*`
- treat native CLI approval as Axiom approval

Forbidden actions fail closed unless Jeremy explicitly changes the scope through a governed decision.

## 9. Stop Conditions

Delegated work should stop and return to Jeremy when:

- scope is ambiguous
- authority boundary is unclear
- required evidence is unavailable
- required review is missing
- implementation would touch protected surfaces without mandate
- command or artifact schema is invalid
- Doctrine conflict is detected
- Workflow transition is not permitted
- Transport meaning is ambiguous
- autonomy, IPC, scheduler, executor, model, network, or security posture would change

Stop conditions should produce a blocking finding and recommended next action.

## 10. Operator UX

Implemented Mandate 4 terminal tooling:

```text
python tools/delegation.py create --goal "<goal>" --scope "<scope>" --json
python tools/delegation.py list --json
python tools/delegation.py show <delegation_id> --json
```

This tooling writes and reads advisory delegation packet records under `governance/80_records/delegations/`. It does not implement `/axiom:*` parser behavior, command manifests, ledger writes, runtime action, IPC transport, scheduler/executor integration, or autonomy.

Recommended future command mapping:

```text
/axiom:delegate
/axiom:delegate-cycle
/axiom:assign-review
/axiom:show-delegations
/axiom:show-blockers
/axiom:close-delegation
```

Target operator flow:

```text
Jeremy states goal.
System creates delegation packet.
Agents plan, evaluate, implement when authorized, verify, and summarize.
Jeremy monitors blockers and decides at control points.
```

Example:

```text
/axiom:delegate-cycle "Redesign command transport for governance scaffold"
```

Expected outputs:

- delegation packet
- architecture review
- governance audit
- implementation plan
- mandate candidate when needed
- implementation evidence when implementation is authorized
- verification audit
- closeout summary

## 11. Autonomy Alignment

Delegation is the first scaffold layer that directly supports bounded agent autonomy.

The intended operating model is:

```text
Jeremy governs by goal, boundary, and decision.
Agents perform planning, building, evaluation, and synthesis inside delegated scope.
System workflow and transport preserve evidence, state, and fail-closed boundaries.
```

Delegation should reduce Operator micromanagement without reducing Operator authority.

## 12. Design Consequence

The Delegation layer should drive:

- delegation packet schema
- `/axiom:delegate*` command design
- role-routing automation
- active cycle dashboards
- blocker summaries
- mandate candidate generation
- implementation handoff creation
- verification handoff creation

Any delegation rule that conflicts with Doctrine, Workflow, or Transport must fail closed until Jeremy resolves the conflict.
