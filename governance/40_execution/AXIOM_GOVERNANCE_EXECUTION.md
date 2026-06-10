# AXIOM Governance Execution

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define how delegated and approved governance work becomes implementation without leaking authority.

## 1. Execution Purpose

The Execution layer defines when and how agents may perform implementation work inside the redesigned governance scaffold.

Doctrine defines what must always be true. Workflow defines lifecycle states. Transport defines how information moves. Delegation defines how work is assigned. Execution defines how approved work is carried out.

The root execution rule is:

```text
Execution performs approved work; it does not create approval.
```

## 2. Execution Non-Authority Rule

Execution may modify files, run checks, collect evidence, and produce implementation reports only inside allowed scope.

Execution may not by itself authorize:

- mandate acceptance
- binding updates
- doctrine changes
- runtime autonomy
- IPC reactivation
- scheduler or executor integration
- model promotion
- security gate weakening
- network/tool permission expansion
- protected file edits outside accepted scope

Successful implementation does not convert a change into accepted governance. Acceptance remains an Operator decision.

## 3. Execution Inputs

Execution should begin from at least one of these inputs:

| Input | What it allows |
| --- | --- |
| Operator-scoped current-session instruction | Narrow implementation explicitly requested by Jeremy in the active session. |
| Delegation packet | Advisory, planning, evidence, and scoped work allowed by delegation. |
| Accepted mandate | Implementation of approved protected, runtime, binding, or authority-sensitive work. |
| Remediation request | Fixes to address audit or verification findings within accepted scope. |

When the requested work affects protected surfaces, runtime behavior, command authority, binding records, autonomy, IPC, scheduler/executor behavior, model policy, security gates, or network/tool permissions, execution must cite an accepted mandate or return a blocking finding.

## 4. Execution Classes

Recommended execution classes:

| Class | Purpose | Mandate required? |
| --- | --- | --- |
| draft_artifact_execution | Create or revise draft governance artifacts. | no, if Operator-scoped |
| research_artifact_execution | Produce research summaries, matrices, or options. | no, if Operator-scoped |
| schema_execution | Draft schemas, examples, and validation proposals. | no for draft, yes for enforced parser/runtime use |
| implementation_execution | Change product, tooling, parser, manifest, or governance code. | yes when protected or authority-sensitive |
| remediation_execution | Fix findings within approved scope. | yes if original work required mandate |
| evidence_execution | Run checks and collect implementation evidence. | no for non-destructive checks, yes if checks alter protected state |
| binding_execution | Update binding records or accepted records. | yes, OP accepted |
| runtime_execution | Change runtime, scheduler, executor, IPC, model, network, autonomy, or security behavior. | yes, OP accepted and reviewed |

## 5. Protected Execution Surfaces

Protected surfaces require explicit scope before execution.

Default protected surfaces:

- Doctrine files
- binding records
- decision records
- accepted mandates
- operator command manifests
- parser or ledger code for `/axiom:*`
- autonomy gate code or policy
- scheduler and executor code
- IPC execution or bridge code
- model promotion policy
- security gates
- sandbox or permission configuration
- network/provider configuration
- persistent memory or state stores

Draft-layer files may be created or revised during brainstorming when Jeremy explicitly asks for them, but they remain advisory until accepted through Workflow.

## 6. Command and Tool Execution

Agents may run local commands only when the command is relevant to the task and does not violate scope.

Allowed by default inside scoped work:

- read files
- inspect status
- search repository content
- validate JSON
- run non-destructive tests or checks
- inspect command help
- collect evidence

Requires explicit scope or accepted mandate:

- commands that alter protected state
- commands that start runtime services
- commands that change scheduler, executor, IPC, or autonomy behavior
- commands that access network/provider paths
- commands that install dependencies
- commands that modify security, sandbox, or permission posture

Execution must report commands run and results when those commands support an evidence claim.

## 7. Implementation Evidence

Every implementation execution should produce evidence.

Implementation evidence records belong under:

```text
governance/80_records/evidence/
```

Minimum implementation evidence:

```json
{
  "changed_files": [],
  "commands_run": [],
  "verification_results": [],
  "skipped_checks": [],
  "assumptions": [],
  "known_risks": [],
  "recommended_next_action": ""
}
```

Evidence must separate:

- live verification results
- assumptions
- memory-derived context
- recommendations
- unresolved risks

## 8. Stop Conditions

Execution must stop and return a blocking finding when:

- scope is unclear
- accepted mandate is required but absent
- protected surface is affected outside accepted scope
- implementation would weaken Doctrine
- Workflow transition is not allowed
- Transport meaning is ambiguous
- Delegation boundaries conflict with requested action
- tests or checks required by scope cannot run
- command requires unavailable permission
- runtime, autonomy, IPC, scheduler, executor, model, network, or security posture would change without accepted mandate

Stop conditions should include the reason, evidence, and recommended next action.

## 9. Operator UX

Recommended future command mapping:

```text
/axiom:request-implementation-plan
/axiom:authorize-implementation
/axiom:show-execution-scope
/axiom:show-execution-evidence
/axiom:stop-execution
```

Target operator flow:

```text
Jeremy delegates goal.
Agents plan and review.
Jeremy accepts mandate or gives narrow implementation scope.
Execution performs scoped work.
Execution reports evidence.
Evaluation verifies the result.
Jeremy accepts, rejects, defers, narrows, or requests remediation.
```

`/axiom:request-remediation` is owned by the Evaluation layer because remediation is triggered by evaluation findings. Execution performs remediation only after the request is scoped and allowed.

## 10. Autonomy Alignment

Execution is where bounded agent autonomy becomes practical, but not self-authorizing.

The intended operating model is:

```text
Agents may build inside approved scope.
Agents may collect evidence.
Agents may recommend next action.
Agents may not approve their own work into binding or runtime state.
```

Autonomous execution remains disabled unless both required autonomy gates are satisfied for the specific scope.

## 11. Design Consequence

The Execution layer should drive:

- implementation mandate requirements
- protected-surface registry
- execution scope records
- command permission rules
- evidence artifact schema
- remediation workflow
- `/axiom:*` implementation commands
- handoff-to-evidence conversion

Any execution rule that conflicts with Doctrine, Workflow, Transport, or Delegation must fail closed until Jeremy resolves the conflict.
