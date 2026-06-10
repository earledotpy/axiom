# AXIOM Operator Console Schema

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Mandate: MND-ACCEPTED-2026-0017-READONLY-OPERATOR-CONSOLE
Purpose: Define the read-only Operator Console state schema for future review and implementation.

## 1. Schema Purpose

This document defines the proposed read-only schema for Operator Console status views.

Materialized console view records belong under:

```text
governance/80_records/console/
```

The schema is a view contract only. It does not create source authority, write ledger records, transition lifecycle state, update bindings, invoke parser behavior, reactivate IPC, alter runtime state, or enable autonomy.

Root rule:

```text
Console state is advisory view state, not source authority.
```

## 2. Console State Object

Minimum object:

```json
{
  "schema": "axiom.operator_console_state.v0.1",
  "generated_utc": "",
  "authority_status": "advisory_only",
  "source_state": [],
  "active_state": [],
  "blockers": [],
  "decision_queue": [],
  "evidence": [],
  "autonomy_status": {},
  "failure_state": {
    "failed_closed": false,
    "reasons": []
  },
  "recommended_next_actions": []
}
```

Required invariants:

- `authority_status` must be `advisory_only`.
- `generated_utc` records view generation time, not decision time.
- Empty arrays mean no valid source item was found for that view.
- Unknown, missing, or conflicting source state must populate `failure_state`.
- Console state must not contain `operator_accepted` unless quoting a source decision record in a nested source reference.

## 3. Source State Reference

Every summarized item should point back to source records.

```json
{
  "source_id": "",
  "source_path": "",
  "source_type": "",
  "authority_status": "",
  "lifecycle_state": "",
  "read_status": "read",
  "notes": []
}
```

Allowed `source_type` values:

```text
live_spine
draft_layer
handoff_json
mandate_candidate
accepted_mandate
operator_decision
evaluation_report
architecture_review
implementation_evidence
archive_index
runtime_gate_report
unknown
```

`read_status` values:

```text
read
missing
invalid
conflicting
ignored_archival
```

## 4. Active State Item

Active state answers what is currently happening.

```json
{
  "item_id": "",
  "title": "",
  "scope": "",
  "lifecycle_state": "",
  "authority_status": "advisory_only",
  "current_owner_role": "",
  "next_expected_role": "",
  "status": "",
  "source_refs": [],
  "recommended_next_action": ""
}
```

Recommended `status` values:

```text
active
pending_review
pending_operator_decision
blocked
deferred
closed
unknown
```

## 5. Blocker Item

Blockers are first-class console output.

```json
{
  "blocker_id": "",
  "severity": "blocking",
  "title": "",
  "scope": "",
  "affected_layer": "",
  "affected_boundary": "",
  "reported_by": "",
  "source_refs": [],
  "evidence": [],
  "recommended_resolution": "",
  "recommended_next_action": ""
}
```

Allowed `affected_layer` values:

```text
Doctrine
Workflow
Transport
Delegation
Execution
Evaluation
Operator Console
Autonomy Gate
Scaffold
Runtime
IPC
Unknown
```

Blockers must not be hidden inside summaries. If source state is inconsistent, the console should create a blocker rather than infer a clean state.

## 6. Decision Queue Item

Decision queue items identify what needs Jeremy's attention.

```json
{
  "decision_id": "",
  "scope": "",
  "title": "",
  "decision_status": "",
  "decision_options": [],
  "authority_status": "advisory_only",
  "source_refs": [],
  "blocking_objections": [],
  "non_blocking_concerns": [],
  "evidence_refs": [],
  "recommended_operator_decision": "",
  "recommended_next_action": ""
}
```

Allowed `decision_status` values:

```text
ready_for_operator_decision
blocked_pending_evidence
blocked_pending_review
needs_scope_clarification
needs_remediation
deferred
closed
unknown
```

Allowed `decision_options` values:

```text
approve
reject
defer
narrow_scope
request_review
request_remediation
archive
```

Decision queue entries may recommend a decision. They must not perform the decision.

## 7. Evidence Item

Evidence items summarize proof, checks, and known gaps.

```json
{
  "evidence_id": "",
  "scope": "",
  "evidence_type": "",
  "authority_status": "advisory_only",
  "source_refs": [],
  "files_changed": [],
  "commands_run": [],
  "verification_results": [],
  "skipped_checks": [],
  "assumptions": [],
  "known_risks": [],
  "evidence_quality": "",
  "recommended_next_action": ""
}
```

Allowed `evidence_type` values:

```text
implementation_evidence
verification_audit
governance_audit
architecture_review
schema_validation
operator_decision_record
unknown
```

Allowed `evidence_quality` values:

```text
strong
partial
weak
missing
conflicting
not_evaluated
```

## 8. Autonomy Status Object

Autonomy status must default conservative.

```json
{
  "runtime_autonomy": "disabled",
  "authority_status": "advisory_only",
  "technical_gate_status": "not_evaluated",
  "active_grant_present": false,
  "active_grant_id": null,
  "grant_state": null,
  "scope": null,
  "missing_requirements": [],
  "source_refs": [],
  "recommended_next_action": ""
}
```

Allowed `runtime_autonomy` values:

```text
disabled
enabled_for_scope
unknown_failed_closed
```

Allowed `technical_gate_status` values:

```text
not_evaluated
passed
failed
missing
conflicting
```

The console must report `runtime_autonomy: disabled` unless a future valid autonomy grant exists and the two-key rule is satisfied. This schema does not define autonomy grant execution.

## 9. Failure State Object

Failure state records fail-closed view generation.

```json
{
  "failed_closed": true,
  "reasons": [
    {
      "reason": "",
      "affected_view": "",
      "source_refs": [],
      "recommended_next_action": ""
    }
  ]
}
```

Common failure reasons:

```text
missing_source
invalid_json
missing_authority_status
missing_lifecycle_state
conflicting_authority_status
source_trace_missing
archive_used_as_active
operator_decision_untraceable
autonomy_status_unknown
native_cli_command_ambiguous
unknown_schema
```

## 10. Source Mapping

Initial source mapping:

| Console field | Source candidates | Notes |
| --- | --- | --- |
| active_state | accepted mandates, mandate candidates, review handoffs, synthesis handoffs | Drafts remain advisory unless accepted by OP. |
| blockers | `blocking_objections` fields in JSON handoffs and evaluation reports | Missing source state can create generated blockers. |
| decision_queue | mandate candidates, synthesis handoffs, evaluation reports | Queue entries are recommendations only. |
| evidence | implementation evidence, audits, reviews, validation summaries | Evidence quality must distinguish live checks from assumptions. |
| autonomy_status | Autonomy Gate docs and future gate reports | Default disabled unless valid accepted grant exists. |
| source_state | all read inputs | Preserve source traceability. |

## 11. No-Write Rule

Generating this schema object must not write:

- operator command ledger rows
- task rows
- binding records
- decision records
- scaffold source files
- parser manifests
- runtime state
- IPC messages
- autonomy grants

Any future implementation must be read-only unless separately mandated.

## 12. Review Questions

Reviewers should answer:

- Does the schema preserve advisory-only authority?
- Are source references sufficient for audit?
- Are blockers structurally distinct from concerns?
- Does failure state fail closed instead of inferring clean state?
- Does autonomy status avoid implying autonomy is enabled?
- Is the schema practical for a later file-based or hybrid index implementation?
