# AXIOM Governance Record Schemas

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Mandate: Mandate 3
Purpose: Define machine-readable JSON Schemas for records under `governance/80_records/`.

## Scope

These schemas validate record shape. They do not create command authority, parser behavior, ledger writes, runtime actions, IPC transport, or autonomy enablement.

## Schema Map

| Record directory | Schema file | Schema id |
| --- | --- | --- |
| `tasks/` | `task_card.schema.json` | `axiom.task_card.v0.1` |
| `delegations/` | `delegation_packet.schema.json` | `axiom.delegation_packet.v0.1` |
| `handoffs/` | `handoff.schema.json` | `axiom.handoff.v0.1` |
| `evaluations/` | `evaluation_report.schema.json` | `axiom.evaluation_report.v0.1` |
| `evidence/` | `evidence.schema.json` | `axiom.evidence.v0.1` |
| `decisions/` | `operator_decision.schema.json` | `axiom.operator_decision.v0.1` |
| `bindings/` | `binding.schema.json` | `axiom.binding.v0.1` |
| `console/` | `operator_console_state.schema.json` | `axiom.operator_console_state.v0.1` |
| `autonomy/` | `autonomy_grant.schema.json` | `axiom.autonomy_grant.v0.1` |
| `command_manifests/` | `command_manifest.schema.json` | `axiom.command_manifest.v0.1` |
| `command_intents/` | `command_intent.schema.json` | `axiom.command_intent.v0.1` |
| `archive/` | `archive_index.schema.json` | `axiom.archive_index.v0.1` |

The governance validator loads these schemas and then applies additional authority-boundary checks that are intentionally stricter than generic JSON Schema.
