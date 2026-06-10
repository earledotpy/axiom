# AXIOM Operator Console Commands

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Mandate: MND-ACCEPTED-2026-0017-READONLY-OPERATOR-CONSOLE
Purpose: Define implemented read-only Operator Console command contracts.

## 1. Command Design Purpose

This document defines the minimum implemented read-only `/axiom:*` Operator Console command contracts.

These are implemented as file-backed terminal views through `tools/operator_console.py`. They are not parser behavior, command manifests, ledger behavior, runtime actions, or authority-bearing state transitions.

Root rule:

```text
Read-only console commands present state; they do not change state.
```

## 2. Shared Command Invariants

Every command in this design must obey:

- read-only only
- `authority_status: advisory_only` in output
- no lifecycle transition
- no Operator decision recording
- no ledger write
- no task creation
- no binding record update
- no scaffold source update
- no parser or manifest mutation
- no IPC read/write dependency
- no runtime action
- no autonomy enablement
- no native CLI slash-command interpretation as Axiom authority

Unknown, missing, or conflicting state must fail closed by returning a failure object or blocker.

## 3. Shared Output Envelope

All proposed commands should return:

```json
{
  "schema": "axiom.operator_console_command_output.v0.1",
  "command": "",
  "generated_utc": "",
  "authority_status": "advisory_only",
  "view": "",
  "source_refs": [],
  "data": {},
  "failure_state": {
    "failed_closed": false,
    "reasons": []
  },
  "recommended_next_actions": []
}
```

The output envelope is a view. It is not a source of governance authority.

## 4. Minimum Command Set

Initial command set:

```text
/axiom:show-active-state
/axiom:show-blockers
/axiom:show-decisions
/axiom:show-evidence
/axiom:show-autonomy-status
```

Implementation entrypoint:

```text
python tools/operator_console.py /axiom:show-active-state --json
python tools/operator_console.py /axiom:show-blockers --json
python tools/operator_console.py /axiom:show-decisions --json
python tools/operator_console.py /axiom:show-evidence --json
python tools/operator_console.py /axiom:show-autonomy-status --json
```

Commands intentionally deferred:

```text
/axiom:approve
/axiom:reject
/axiom:defer
/axiom:narrow-scope
/axiom:request-review
/axiom:request-remediation
/axiom:archive-cycle
/axiom:delegate
/axiom:grant-autonomy
/axiom:stop-autonomy
/axiom:revoke-autonomy
```

Deferred commands require separate mandates because they may record intent, request workflow changes, or affect authority-sensitive state.

Mandate 8 adds governance-only terminal helpers for guided cycle operations:

```text
python tools\governance_cycle.py show --json
python tools\governance_cycle.py summary
python tools\governance_cycle.py next-actions --json
python tools\governance_cycle.py decision-preview --decision approve --target-id "..." --scope "..."
python tools\governance_cycle.py decision-record --preview-id "..." --confirm "I_ACCEPT_AXIOM_DECISION:..."
python tools\review_ingest.py create --target-artifact "..." --scope "..." --review-file "..."
```

These helpers operate over `governance/80_records/`. Review ingestion and roadmap filing create advisory records. Guided decision recording creates `operator_accepted` records only through the existing exact confirmation-token decision flow.

The helpers are not an authority-bearing execution Orchestrator. They must not route agents, execute commands, apply patches, reactivate IPC, start scheduler or executor loops, enable autonomy, or emit `VERIFIED_COMMIT`.

## 5. `/axiom:show-active-state`

Purpose:

```text
Show active governance cycles, lifecycle state, current role, next expected role, blockers count, and recommended next action.
```

Inputs read:

- accepted mandates in `governance/80_records/decisions/`
- mandate candidates in `governance/80_records/handoffs/`
- review and synthesis JSON handoffs
- accepted decision records and scaffold source files for source context
- redesign scaffold docs for layer definitions

Output object:

```json
{
  "view": "active_state",
  "data": {
    "active_state": [],
    "summary": {
      "active_count": 0,
      "pending_operator_decision_count": 0,
      "blocked_count": 0
    }
  }
}
```

Failure behavior:

- Missing lifecycle state creates a blocker.
- Conflicting authority status creates a blocker.
- Archive artifacts used as active state are ignored and reported.

Explicit no-write rule:

```text
This command must not create, update, accept, reject, archive, or transition any artifact.
```

## 6. `/axiom:show-blockers`

Purpose:

```text
Show blocking objections that prevent acceptance, implementation, binding update, autonomy, or closeout.
```

Inputs read:

- `blocking_objections` fields in handoff JSON
- evaluation reports
- architecture reviews
- synthesis reports
- generated failure state from source inconsistencies

Output object:

```json
{
  "view": "blockers",
  "data": {
    "blockers": [],
    "summary": {
      "blocking_count": 0,
      "affected_layers": []
    }
  }
}
```

Failure behavior:

- Invalid blocker source JSON creates a generated blocker.
- A blocker without source trace is reported as incomplete.
- Non-blocking concerns must not be mixed into the blocker list.

Explicit no-write rule:

```text
This command must not resolve, dismiss, downgrade, or remediate blockers.
```

## 7. `/axiom:show-decisions`

Purpose:

```text
Show items ready for, or blocked from, Operator decision.
```

Inputs read:

- mandate candidates
- accepted mandate records
- OP decision handoffs
- evaluation reports
- synthesis reports
- blocking objections

Output object:

```json
{
  "view": "decision_queue",
  "data": {
    "decision_queue": [],
    "summary": {
      "ready_for_operator_decision_count": 0,
      "blocked_pending_review_count": 0,
      "blocked_pending_evidence_count": 0
    }
  }
}
```

Failure behavior:

- Candidate without traceable review status is `blocked_pending_review`.
- Candidate with unresolved blockers is not ready.
- Accepted decision must cite an Operator source record.

Explicit no-write rule:

```text
This command must not approve, reject, defer, narrow, request review, or archive.
```

## 8. `/axiom:show-evidence`

Purpose:

```text
Show latest evidence, verification status, skipped checks, assumptions, and known risks.
```

Inputs read:

- implementation evidence handoffs
- audit reports
- architecture reviews
- validation summaries
- synthesis handoffs

Output object:

```json
{
  "view": "evidence",
  "data": {
    "evidence": [],
    "summary": {
      "strong_count": 0,
      "partial_count": 0,
      "weak_count": 0,
      "missing_count": 0
    }
  }
}
```

Failure behavior:

- Claimed tests without command evidence are weak or missing evidence.
- Missing changed-file list is weak evidence for implementation work.
- Evidence target missing creates a blocker if authority-sensitive.

Explicit no-write rule:

```text
This command must not run tests, modify evidence, or mark evidence accepted.
```

## 9. `/axiom:show-autonomy-status`

Purpose:

```text
Show conservative autonomy posture, technical gate status, active grant presence, missing requirements, and stop conditions.
```

Inputs read:

- Autonomy Gate design docs
- future autonomy gate reports when separately implemented
- future accepted autonomy grants when separately implemented
- accepted decision records and scaffold source files for current posture

Output object:

```json
{
  "view": "autonomy_status",
  "data": {
    "autonomy_status": {
      "runtime_autonomy": "disabled",
      "authority_status": "advisory_only",
      "technical_gate_status": "not_evaluated",
      "active_grant_present": false,
      "missing_requirements": []
    }
  }
}
```

Failure behavior:

- If autonomy status cannot be determined, return `runtime_autonomy: unknown_failed_closed`.
- If an active grant cannot be traced to Operator acceptance, treat autonomy as disabled.
- If technical gate status conflicts with mandate status, fail closed.

Explicit no-write rule:

```text
This command must not grant, stop, revoke, or enable autonomy.
```

## 10. Future Implementation Mapping

Future implementation should treat these commands as read-only visibility commands, aligned with the existing terminal registry pattern where status panels have:

```text
mutates_axiom_runtime: false
risk: low
category: state_visibility
```

The existing operator parser and ledger model already separates parsing from execution and ledger writing. Future `/axiom:*` console implementation should preserve or strengthen that separation.

No future implementation should reuse native CLI slash command semantics as Axiom authority.

## 11. Review Questions

Reviewers should answer:

- Is the minimum command set sufficient?
- Does any command name imply authority it does not have?
- Are no-write rules explicit enough?
- Should `/axiom:show-decisions` be renamed `/axiom:show-decision-queue` before implementation?
- Should `/axiom:show-evidence` require a scope argument in the first implementation?
- Is autonomy status conservative enough?
- Are source inputs practical for a file-based first implementation?
