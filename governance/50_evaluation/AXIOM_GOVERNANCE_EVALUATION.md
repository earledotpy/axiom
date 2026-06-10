# AXIOM Governance Evaluation

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define how delegated and executed work is reviewed, verified, audited, and prepared for Operator decision.

## 1. Evaluation Purpose

The Evaluation layer defines how AXIOM determines whether delegated or executed work is good enough for Operator decision.

Doctrine defines what must always be true. Workflow defines lifecycle states. Transport defines how information moves. Delegation defines how work is assigned. Execution defines how work is performed. Evaluation defines how work is judged.

The root evaluation rule is:

```text
Evaluation informs acceptance; it does not perform acceptance.
```

## 2. Evaluation Non-Authority Rule

Evaluation may verify evidence, identify findings, recommend remediation, and recommend Operator decisions.

Evaluation may not by itself authorize:

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

Evaluation language should avoid ambiguous authority terms such as `approved`, `accepted`, or `authorized` unless clearly prefixed as a recommendation for Operator decision.

Preferred language:

```text
recommended_for_operator_acceptance
blocked
needs_remediation
insufficient_evidence
out_of_scope
```

## 3. Evaluation Types

Recommended evaluation types:

| Type | Purpose | Typical owner |
| --- | --- | --- |
| implementation_verification | Verify changed files, commands, tests, and behavior. | IMPL or AUD |
| governance_audit | Review authority, policy, ambiguity, and Doctrine compliance. | AUD |
| architecture_review | Review design fit, system tradeoffs, and long-range risk. | ARCH |
| evidence_review | Review whether evidence supports claims. | AUD |
| scope_review | Review whether work stayed inside delegation or mandate scope. | AUD |
| regression_review | Review whether existing behavior remains intact. | IMPL or AUD |
| security_boundary_review | Review security, permission, sandbox, network, and runtime boundary risk. | AUD |
| autonomy_readiness_review | Review whether autonomy-related conditions are satisfied for a specific scope. | AUD with ARCH/IMPL input |
| closeout_review | Review whether the item is ready for Operator decision or archive. | Cursor with AUD input |

## 4. Evaluation Report Schema

Minimum schema:

Evaluation report records belong under:

```text
governance/80_records/evaluations/
```

```json
{
  "schema": "axiom.evaluation_report.v0.1",
  "evaluation_id": "",
  "created_utc": "",
  "evaluating_actor": "",
  "actor_role": "",
  "target_artifact": "",
  "target_lifecycle_state": "",
  "authority_status": "advisory_only",
  "evaluation_type": "",
  "inputs_reviewed": [],
  "checks_performed": [],
  "findings": [],
  "blocking_objections": [],
  "non_blocking_concerns": [],
  "evidence_quality": "",
  "scope_compliance": "",
  "doctrine_compliance": "",
  "workflow_compliance": "",
  "transport_compliance": "",
  "delegation_compliance": "",
  "execution_compliance": "",
  "recommended_operator_decision": ""
}
```

Evaluation reports should be machine-readable when they participate in workflow transitions, blocker summaries, dashboards, or command outputs.

Mandate 5 adds the first active advisory tooling for this layer:

```text
python tools\evaluation.py create --target-artifact "..." --scope "..." --json
python tools\evaluation.py list --json
python tools\evaluation.py show EVL-... --json
python tools\evaluation.py blockers --json
```

Generated records are written only to:

```text
governance/80_records/evaluations/
```

The tool may create advisory evaluation JSON and derive blocker summaries from those records. It may not write ledger rows, mutate parser manifests, execute runtime actions, reactivate IPC, enable autonomy, or accept work.

Mandate 8 adds terminal review ingestion:

```text
python tools\review_ingest.py create --target-artifact "..." --scope "..." --review-file "..."
```

This converts a Claude Code, Cursor, Codex, or Antigravity terminal report into an advisory evaluation record. The ingested terminal text is preserved as source material, but the record remains `authority_status: advisory_only`. Review ingestion does not accept work, write Operator decisions, update bindings, execute commands, or create runtime authority.

## 5. Verdicts

Recommended verdict values:

```text
pass
pass_with_concerns
blocked
needs_remediation
out_of_scope
insufficient_evidence
not_evaluated
```

Verdicts are advisory. A `pass` verdict does not accept the work. A `blocked` verdict does not permanently reject the work. Both inform Operator decision.

## 6. Role Responsibilities

| Actor role | Evaluation responsibilities |
| --- | --- |
| IMPL/Codex | implementation verification, command evidence, changed-file summary, remediation evidence |
| AUD/Claude Code | governance audit, authority boundary review, evidence sufficiency, scope drift, blocking findings |
| ARCH/Antigravity | architecture fit, design coherence, long-range risk, research-backed tradeoffs |
| Cursor | evaluation consolidation, blocker summary, decision options, closeout packaging |
| OP/Jeremy | final decision, acceptance, rejection, deferral, narrowing, or remediation direction |

No role should be the sole evaluator of authority-sensitive work it authored or implemented when independent review is required.

Machine-oriented role naming:

| Surface | Process | Function |
| --- | --- | --- |
| Claude Code | audit | verify |
| Antigravity | architect | plan |
| Codex implementation | implement | build |
| Cursor | synthesize | summarize |

## 7. Evidence Quality Rules

Evaluation must distinguish:

- live verification evidence
- claims
- assumptions
- memory-derived context
- recommendations
- unresolved risks

Evidence is strong when it cites:

- files inspected
- files changed
- commands run
- command outputs or summarized results
- tests performed
- schema validation results
- explicit skipped checks and reasons

Evidence is weak when it relies on:

- expected behavior without verification
- memory
- unstated assumptions
- generic confidence
- missing command output
- missing changed-file list
- ambiguous scope

Weak evidence should produce either a non-blocking concern or blocking objection depending on risk.

## 8. Evaluation Stop Conditions

Evaluation must stop or return a blocking finding when:

- target artifact is missing
- implementation evidence is missing
- claimed tests were not actually run
- mandate is required but absent
- protected surface changed outside scope
- scope cannot be determined
- authority expansion is detected
- Doctrine conflict is detected
- Workflow transition is not allowed
- Transport record is ambiguous
- Delegation boundaries are unclear
- Execution evidence is insufficient
- runtime, autonomy, IPC, scheduler, executor, model, network, or security posture changed without accepted mandate
- schema is invalid where schema validity is required

Stop conditions should include:

- reason
- evidence
- affected boundary
- recommended next action

## 9. Operator UX

Recommended future command mapping:

```text
/axiom:request-evaluation
/axiom:request-audit
/axiom:request-architecture-review
/axiom:request-verification
/axiom:show-evaluation
/axiom:show-blockers
/axiom:request-remediation
/axiom:ready-for-decision
```

Target operator view:

```text
What was evaluated?
What passed?
What is blocked?
What evidence supports the result?
What decision is recommended?
What needs remediation?
```

The Evaluation layer should reduce the number of artifacts Jeremy must manually inspect by producing concise blocker summaries and decision-ready closeout reports.

## 10. Autonomy Alignment

Evaluation is where agents do the quality, risk, architecture, governance, and evidence assessment needed for bounded autonomy.

The intended operating model is:

```text
Agents evaluate thoroughly.
Agents recommend clearly.
System preserves evidence and blockers.
Jeremy accepts, rejects, defers, narrows, or requests remediation.
```

Autonomy readiness evaluation may determine that a scoped autonomy proposal satisfies technical conditions, but it does not enable runtime autonomy. Runtime autonomy still requires both required autonomy gates for the specific scope.

## 11. Design Consequence

The Evaluation layer should drive:

- evaluation report schema
- audit report schema
- verification report schema
- blocker summary generation
- ready-for-decision summaries
- remediation routing
- closeout workflow
- `/axiom:*` evaluation commands

Any evaluation rule that conflicts with Doctrine, Workflow, Transport, Delegation, or Execution must fail closed until Jeremy resolves the conflict.
