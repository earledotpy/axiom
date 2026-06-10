# AXIOM Governance Records

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define the JSON-first machine-readable record root for the redesigned AXIOM governance scaffold.

## Root Rule

Records preserve governance state and evidence. Records do not create authority unless they contain or cite an explicit Operator decision accepted by Jeremy.

## Directory Map

| Directory | Record type | Default authority |
| --- | --- | --- |
| `tasks/` | lightweight task cards | advisory_only |
| `delegations/` | delegation packets | advisory_only |
| `handoffs/` | agent handoffs and synthesis packets | advisory_only |
| `evaluations/` | audit, review, verification, and evaluation reports | advisory_only |
| `evidence/` | implementation and verification evidence | evidence_only or advisory_only |
| `decisions/` | Operator decision records and accepted mandates | operator_accepted only when recorded by OP |
| `bindings/` | current active binding state produced from accepted decisions | binding |
| `console/` | materialized read-only console views | advisory_only |
| `autonomy/` | autonomy grant drafts and accepted scoped grants | advisory_only until OP accepted |
| `command_manifests/` | JSON-first `/axiom:*` command contracts | advisory_only until OP accepted |
| `command_intents/` | validated `/axiom:*` command intent records | advisory_only |
| `archive/` | archive indexes and historical pointers | historical_evidence |

## Schema Map

Mandate 3 adds JSON Schemas under:

```text
governance/80_records/schemas/
```

The schema directory is not a record directory. It defines record contracts for the directories above.

| Record directory | Schema id |
| --- | --- |
| `tasks/` | `axiom.task_card.v0.1` |
| `delegations/` | `axiom.delegation_packet.v0.1` |
| `handoffs/` | `axiom.handoff.v0.1` |
| `evaluations/` | `axiom.evaluation_report.v0.1` |
| `evidence/` | `axiom.evidence.v0.1` |
| `decisions/` | `axiom.operator_decision.v0.1` |
| `bindings/` | `axiom.binding.v0.1` |
| `console/` | `axiom.operator_console_state.v0.1` |
| `autonomy/` | `axiom.autonomy_grant.v0.1` |
| `command_manifests/` | `axiom.command_manifest.v0.1` |
| `command_intents/` | `axiom.command_intent.v0.1` |
| `archive/` | `axiom.archive_index.v0.1` |

## JSON Rules

- JSON files must have a top-level object.
- JSON files must include `schema`, an id field, `created_utc`, and `authority_status`.
- JSON files must validate against the schema assigned to their record directory.
- Agent-authored records default to `advisory_only`.
- `operator_accepted` is reserved for Operator records under `decisions/` or explicitly accepted autonomy records under `autonomy/`.
- `binding` is reserved for active binding records under `bindings/` and must cite an accepted `approve` decision.
- Generated console state is a view and must remain `advisory_only`.
- Command intent records are audit records only and must not execute runtime actions or write legacy ledger rows.
- Archive indexes are historical evidence and must not be treated as active authority.

## No-Write Boundary

Mandate 1 establishes this record root. Mandate 3 establishes schema validation for records in this root. Neither mandate implements parser behavior, command manifests, ledger writes, runtime state changes, IPC reactivation, scheduler or executor integration, or autonomy enablement.
