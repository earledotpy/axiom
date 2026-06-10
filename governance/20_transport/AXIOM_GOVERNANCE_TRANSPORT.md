# AXIOM Governance Transport

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Define how redesigned AXIOM governance information moves between Operator, terminal agents, artifacts, and command surfaces.

## 1. Transport Purpose

The Transport layer defines how governance messages, artifacts, command intent, reviews, and evidence move through the redesigned scaffold.

Doctrine defines what must always be true. Workflow defines the allowed lifecycle states. Transport defines how lifecycle artifacts and command intent are carried without accidentally creating authority.

The root transport rule is:

```text
Transport carries governance information; it does not confer governance authority.
```

## 2. Transport Non-Authority Rule

No transport surface is authority by itself.

This includes:

- JSON handoffs
- Markdown handoffs
- CLI-native slash commands
- `/axiom:*` command text before parser validation
- terminal chat output
- generated summaries
- implementation evidence
- verification reports
- archived files
- IPC messages or history

Authority exists only when explicit Operator decision is recorded through the governed workflow.

## 3. Transport Lanes

The redesigned scaffold uses three active transport lanes:

```text
1. Agent Handoff Transport
2. Operator Command Transport
3. Archive Transport
```

The redesigned scaffold does not include an external advisory council transport lane.

## 4. Agent Handoff Transport

Agent Handoff Transport carries structured advisory work between Cursor, Codex, Claude Code, Antigravity, and Jeremy.

Primary format:

```text
JSON
```

Primary location:

```text
governance/80_records/handoffs/
```

Use cases:

- proposals
- architecture reviews
- governance audits
- implementation plans
- mandate candidates
- implementation evidence
- verification audits
- blocking objections
- non-blocking concerns
- recommended next actions

Agent handoffs default to:

```json
{
  "authority_status": "advisory_only"
}
```

Agent handoffs may recommend a transition, but they may not perform the transition.

## 5. Operator Command Transport

Operator Command Transport carries Jeremy's governance intent.

Primary format:

```text
/axiom:* command intent routed through parser, manifest, and ledger
```

Recommended command namespace:

```text
/axiom:approve
/axiom:reject
/axiom:defer
/axiom:narrow-scope
/axiom:request-review
/axiom:show-active-state
/axiom:show-blockers
/axiom:archive-cycle
```

Operator commands must be validated before they are recorded.

Validation requirements:

- known command
- known manifest
- allowed payload shape
- explicit scope when required
- valid target artifact when required
- permitted lifecycle transition
- no implicit runtime execution
- no implicit autonomy enablement
- no implicit binding update without accepted workflow state

Operator command transport may carry authority-bearing intent only after parser validation and governed recording. It should record intent first; implementation, binding update, or runtime action remains a separate governed workflow step.

The Operator Command parser must reject non-namespaced commands that attempt Axiom governance actions. Governance-relevant command intent must use the `/axiom:*` namespace; native or ambiguous command text must fail closed.

For this redesign, parser means the governed Axiom component that validates `/axiom:*` command intent against command manifests, payload schemas, lifecycle rules, and authority boundaries before any ledger record or workflow action is produced. Parser code, manifest code, and ledger code are implementation surfaces and require a separate accepted mandate before modification.

## 6. CLI-Native Command Boundary

Native CLI slash commands are local workflow controls for their own tool.

Examples:

- Codex `/approve`
- Codex `/review`
- Codex `/status`
- Cursor CLI slash commands
- Claude Code slash commands
- Antigravity CLI commands

Native CLI commands must not be treated as Axiom governance decisions.

If a native CLI command name overlaps with Axiom governance language, the Axiom meaning must use the `/axiom:*` namespace and the governed parser/ledger path.

## 7. Artifact Formats

Recommended format split:

| Use | Format | Reason |
| --- | --- | --- |
| Doctrine | Markdown | stable human-readable authority root |
| Workflow | Markdown | human-readable state model |
| Transport rules | Markdown | human-readable governance design |
| Agent handoffs | JSON under `governance/80_records/handoffs/` | schema validation and cross-CLI consistency |
| Task cards | JSON under `governance/80_records/tasks/` | lightweight scoped work records |
| Delegation packets | JSON under `governance/80_records/delegations/` | scoped assignment and boundary records |
| Evaluation reports | JSON under `governance/80_records/evaluations/` | machine-readable findings and recommendations |
| Evidence records | JSON under `governance/80_records/evidence/` | check, command, and changed-file evidence |
| Operator commands | manifest + ledger record | validation and auditability |
| Decision records | JSON under `governance/80_records/decisions/` with explicit OP acceptance | authority record |
| Console views | JSON under `governance/80_records/console/` when materialized | advisory generated views |
| Autonomy grants | JSON under `governance/80_records/autonomy/` | scoped autonomy grant records |
| Archive indexes | JSON under `governance/80_records/archive/` | pointers to historical evidence |
| Archives | original format preserved outside active records | historical evidence |

Markdown may summarize JSON artifacts, but summaries must not replace schema-bound records when machine validation is required.

Mandate 3 schema location:

```text
governance/80_records/schemas/
```

Schema validation checks record shape. It does not create transport authority, command authority, ledger writes, runtime action, or autonomy.

## 8. IPC Boundary

IPC is not part of the redesigned active governance transport layer.

Current IPC materials are classified as:

```text
historical / inert / not active governance transport
```

IPC must not be used to:

- execute commands
- authorize decisions
- promote artifacts
- create accepted mandates
- update bindings
- enable autonomy
- reactivate scheduler or executor paths
- bypass Operator command validation

If IPC is ever reintroduced, it requires a separate accepted mandate and must be limited to explicitly scoped message transport unless Jeremy accepts a stronger scope.

## 9. Archive Transport

Archive Transport moves inactive artifacts out of active working context while preserving evidence.

The redesigned scaffold does not use legacy `governance/06_archives/` as an active input path. Future archive indexes should be JSON records under:

```text
governance/80_records/archive/
```

Archive transport does not reactivate or ratify artifacts.

Archived artifacts remain:

```text
historical_evidence
```

They become active only if Jeremy explicitly re-ratifies them through a governed decision.

## 10. Failure Rules

Transport must fail closed when:

- command namespace is ambiguous
- command manifest is missing
- command payload is invalid
- artifact schema is invalid
- target artifact is missing
- lifecycle state is unclear
- authority status is missing or inconsistent
- native CLI command is mistaken for Axiom command
- IPC message attempts active governance or runtime action
- archive artifact is treated as active authority

Failure should produce a refusal or blocking finding, not an inferred transition.

## 11. Design Consequence

The Transport layer should drive:

- `/axiom:*` parser and manifest design
- agent handoff schema design
- handoff directory structure
- ledger recording rules
- active vs archived artifact separation
- IPC exclusion rules
- CLI adapter boundaries

Any transport rule that conflicts with Doctrine or Workflow must fail closed until Jeremy resolves the conflict.
