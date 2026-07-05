# AXIOM Governance Redesign Draft

Status: Operator-accepted Mandate 1 scaffold
Owner: Jeremy, Operator
Created: 2026-06-08
Updated: 2026-06-08
Purpose: Index the accepted redesigned governance scaffold for CLI-agent development.

## 1. Status

This document indexes the redesigned governance scaffold accepted for Mandate 1.

Jeremy has decided that the new numbered scaffold replaces the legacy `01_live_spine` governance structure for ongoing AXIOM governance work.

Current active governance scaffold:

```text
governance/00_doctrine/
governance/10_workflow/
governance/20_transport/
governance/30_delegation/
governance/40_execution/
governance/50_evaluation/
governance/60_operator_console/
governance/70_autonomy_gate/
governance/80_records/
```

Legacy `01_live_spine`, `02_cli_surfaces`, `03_advisory_council`, `04_decision_records`, `05_handoffs`, and `06_archives` paths are not active governance inputs in the redesigned scaffold unless Jeremy explicitly reintroduces a specific artifact.

## 2. Design Goal

The redesigned scaffold supports this operating model:

```text
Jeremy governs by goal, boundary, monitoring, and decision.
Agents perform planning, building, evaluation, remediation, and synthesis inside governed scope.
The system preserves evidence, exposes blockers, fails closed, and prevents accidental authority transfer.
```

The design aligns with bounded autonomy, not unbounded autonomy.

## 3. Layer Stack

| Layer | File | Purpose |
| --- | --- | --- |
| 00 Doctrine | `governance/00_doctrine/AXIOM_DOCTRINE.md` | Defines root doctrine, authority model, advisory-vs-binding rule, fail-closed rule, autonomy rule, and doctrine change rule. |
| 10 Workflow | `governance/10_workflow/AXIOM_GOVERNANCE_WORKFLOW.md` | Defines lifecycle states, transitions, role responsibilities, evidence requirements, and archive rules. |
| 20 Transport | `governance/20_transport/AXIOM_GOVERNANCE_TRANSPORT.md` | Defines how governance artifacts, command intent, and records move without conferring authority. |
| 30 Delegation | `governance/30_delegation/AXIOM_GOVERNANCE_DELEGATION.md` | Defines how Operator goals become scoped agent work without transferring authority. |
| 40 Execution | `governance/40_execution/AXIOM_GOVERNANCE_EXECUTION.md` | Defines how approved work is implemented, evidenced, and stopped when scope or authority is unclear. |
| 50 Evaluation | `governance/50_evaluation/AXIOM_GOVERNANCE_EVALUATION.md` | Defines how work is reviewed, audited, verified, scored, and prepared for Operator decision. |
| 60 Operator Console | `governance/60_operator_console/AXIOM_OPERATOR_CONSOLE.md` | Defines how Jeremy sees active state, blockers, decisions, evidence, and autonomy status. |
| 70 Autonomy Gate | `governance/70_autonomy_gate/AXIOM_AUTONOMY_GATE.md` | Defines scoped, revocable, evidence-bound autonomy grants and the two-key autonomy rule. |
| 80 Records | `governance/80_records/README.md` | Defines the JSON-first machine-readable record root for task cards, delegation packets, handoffs, evaluations, evidence, decisions, console views, autonomy grants, and archive indexes. |

## 4. Agent Process and Function Names

Approved single-word machine-oriented agent mapping:

| Agent | Human role | Process | Function |
| --- | --- | --- | --- |
| ARCH | Chief Architect and Researcher | `architect` | `plan` |
| IMPL | Implementation Specialist and Troubleshooter | `implement` | `build` |
| AUD | Governance Auditor and Specification Critic | `audit` | `verify` |
| SYNTH | Synthesis and summarization support | `synthesize` | `summarize` |

These names describe machine-readable governance process/function labels. They do not grant authority.

## 5. Root Rules

Each layer has a root rule:

| Layer | Root rule |
| --- | --- |
| Doctrine | AXIOM is operator-governed, fail-closed, autonomy-gated by design. |
| Workflow | No artifact advances into accepted, binding, executable, or autonomous state without explicit Operator decision. |
| Transport | Transport carries governance information; it does not confer governance authority. |
| Delegation | Delegation assigns work; it does not transfer authority. |
| Execution | Execution performs approved work; it does not create approval. |
| Evaluation | Evaluation informs acceptance; it does not perform acceptance. |
| Operator Console | The Operator Console presents governed state; it does not invent governed state. |
| Autonomy Gate | Autonomy is scoped, revocable, evidence-bound, and never self-authorizing. |

## 6. Scope Decisions From Brainstorming

The redesigned scaffold keeps these design decisions:

- Current role titles remain for now.
- Jeremy remains final governance authority.
- Codex retains Implementation Specialist and Troubleshooter duties.
- Cursor is the synthesis and summarization agent.
- Claude Code remains Governance Auditor and Specification Critic with bounded verification and small corrective-edit authority only when scoped by an accepted task card or mandate.
- Antigravity remains Chief Architect and Researcher with planning, research, scaffolding, and non-runtime governance-record drafting authority only.
- Native CLI slash commands remain tool-local workflow controls.
- Axiom governance command intent should use the `/axiom:*` namespace.
- Agent artifacts remain advisory unless Jeremy explicitly accepts a decision.
- IPC is excluded from active governance transport.
- Kimi, Qwen, DeepSeek, and any external advisory council are removed from the redesigned governance layer.
- Unbounded full autonomy is not defined.
- Machine-readable governance records use the new `governance/80_records/` JSON location.
- Root CLI entrypoint files `AGENTS.md`, `CLAUDE.md`, and `.antigravity.md` are recreated as pointers into the redesigned scaffold.
- Cursor project rules live under `.cursor/rules/` and define Cursor as the advisory `synthesize` / `summarize` agent.

## 7. Draft Command Surface

Recommended future `/axiom:*` command families:

```text
Decision:
/axiom:approve
/axiom:reject
/axiom:defer
/axiom:narrow-scope
/axiom:request-review
/axiom:request-remediation
/axiom:archive-cycle

Delegation:
/axiom:delegate
/axiom:delegate-cycle
/axiom:assign-review
/axiom:show-delegations
/axiom:close-delegation

Execution:
/axiom:request-implementation-plan
/axiom:authorize-implementation
/axiom:show-execution-scope
/axiom:show-execution-evidence
/axiom:stop-execution

Evaluation:
/axiom:request-evaluation
/axiom:request-audit
/axiom:request-architecture-review
/axiom:request-verification
/axiom:show-evaluation
/axiom:ready-for-decision

Console:
/axiom:show-active-state
/axiom:show-blockers
/axiom:show-decisions
/axiom:show-evidence
/axiom:show-autonomy-status

Autonomy:
/axiom:request-autonomy-review
/axiom:grant-autonomy
/axiom:stop-autonomy
/axiom:revoke-autonomy
/axiom:show-autonomy-evidence
```

These commands are design proposals only. They do not exist as accepted or implemented command authority unless later mandated.

## 8. Proposed Implementation Order

Recommended implementation sequence:

```text
1. Complete Mandate 1 scaffold reconciliation.
2. Implement read-only Operator Console/status commands.
3. Create additional schema definitions for delegation, handoff, evaluation, evidence, console state, and autonomy grants.
4. Implement delegation packet creation and listing.
5. Implement evaluation and blocker summary generation.
6. Implement Operator decision ledger commands.
7. Implement execution evidence capture.
8. Implement autonomy grant records and status reporting.
9. Consider bounded autonomy execution only after prior layers are working and audited.
```

The safest first functional implementation is read-only console/status support.

## 9. Review Needed Before Mandate

Before parser, ledger, runtime, or authority-bearing implementation, this scaffold should be reviewed for:

- internal consistency across all layers
- overlap or contradiction with accepted governance records
- authority expansion risk
- protected surface classification
- command namespace completeness
- schema validity and minimum required fields
- whether `/axiom:*` commands should record intent only or trigger additional workflow steps
- how draft JSON artifacts become accepted governance
- how any needed historical legacy artifacts should be reintroduced as archived evidence without reactivating legacy paths
- how legacy bindings AB-006, AB-007, and AB-010 should be retired or translated if needed and if historical binding continuity is required

## 10. Open Questions

Open design questions:

- Which exact JSON schemas should be enforced first under `governance/80_records/`?
- Should accepted mandates become JSON-only records, or JSON source records plus generated Markdown views?
- Should the Operator Console state be generated from files only, SQLite only, or a hybrid index?
- Which surfaces are protected by default in the first implementation mandate?
- Should `/axiom:approve` record intent only, or create a pending acceptance artifact for audit before becoming binding?
- What is the minimum viable read-only console command set?
- Should autonomy grants be stored as decision records, ledger entries, standalone JSON, or all three?
- Should the redesigned scaffold permanently remove the exception-path advisory council, and if so, which future active-binding changes retire AB-006, AB-007, and AB-010?

## 11. Recommended Next Mandate

First mandate:

```text
Mandate 1: Establish redesigned governance scaffold documents and index only.
```

Status:

```text
Accepted and implemented as the active scaffold direction.
```

Scope:

- review and revise draft layer documents
- treat the layer stack as accepted redesign direction
- do not implement parser changes
- do not implement runtime changes
- do not reactivate IPC
- do not enable autonomy
- do not add authority-bearing command behavior

Recommended second mandate:

```text
Mandate 2: Implement read-only Operator Console commands.
```

Status:

```text
Accepted by Jeremy on 2026-06-08 and implemented as file-backed read-only console views.
```

Scope:

- read current structured governance artifacts from `governance/80_records/`
- summarize active state
- show blockers
- show pending decisions
- show evidence
- show autonomy status as disabled unless valid gates exist
- no authority-bearing command execution

Implemented surfaces:

```text
axiom/core/operator_console.py
tools/operator_console.py
tests/test_operator_console.py
```

Recommended third mandate:

```text
Mandate 3: Implement governance record JSON Schemas.
```

Status:

```text
Accepted by Jeremy on 2026-06-08 and implemented as schema-backed validation for governance/80_records.
```

Scope:

- define JSON Schemas for task cards, delegation packets, handoffs, evaluations, evidence, decisions, console views, autonomy grants, and archive indexes
- validate governance records against schemas
- preserve explicit authority-boundary checks outside generic schema validation
- do not implement parser changes
- do not write ledger rows
- do not add runtime behavior
- do not reactivate IPC
- do not enable autonomy

Implemented surfaces:

```text
governance/80_records/schemas/
tools/validate_governance.py
tests/test_validate_governance.py
```

Recommended fourth mandate:

```text
Mandate 4: Implement delegation packet creation and listing.
```

Status:

```text
Accepted by Jeremy on 2026-06-08 and implemented as advisory JSON record tooling.
```

Scope:

- create delegation packet JSON records under `governance/80_records/delegations/`
- list and show delegation packet records
- expose delegation records through the read-only Operator Console active-state view
- keep records `authority_status: advisory_only`
- do not implement `/axiom:*` parser behavior
- do not write operator command ledger rows
- do not add runtime behavior
- do not reactivate IPC
- do not enable autonomy

Implemented surfaces:

```text
axiom/core/delegation.py
tools/delegation.py
tests/test_delegation.py
```

Recommended fifth mandate:

```text
Mandate 5: Implement evaluation and blocker summary generation.
```

Status:

```text
Accepted by Jeremy on 2026-06-08 and implemented as advisory evaluation JSON record tooling.
```

Scope:

- create evaluation report JSON records under `governance/80_records/evaluations/`
- list and show evaluation report records
- generate blocker summaries from evaluation report `blocking_objections`
- expose evaluation blockers and recommended decisions through the read-only Operator Console
- keep records `authority_status: advisory_only`
- do not implement `/axiom:*` parser behavior
- do not write operator command ledger rows
- do not add runtime behavior
- do not reactivate IPC
- do not enable autonomy
- do not accept work

Implemented surfaces:

```text
axiom/core/evaluation.py
tools/evaluation.py
tests/test_evaluation.py
```

Recommended sixth mandate:

```text
Mandate 6: Implement JSON-first governance operating records and authority-bearing decision flow.
```

Status:

```text
Accepted by Jeremy and implemented as governance-only JSON record tooling.
```

Scope:

- create task cards, handoffs, evidence, command manifests, and command intents as advisory or evidence records
- preview Operator decisions as advisory records
- record Operator decisions only with exact explicit confirmation
- create active binding records only from accepted `approve` decisions
- draft, accept, inspect, and revoke autonomy grant records without enabling runtime autonomy
- keep `governance/80_records/` as the canonical source of truth
- keep legacy SQLite/operator command components as compatibility surfaces only
- do not reactivate IPC
- do not start scheduler or executor loops
- do not enable runtime autonomy

Implemented surfaces:

```text
axiom/core/task_card.py
axiom/core/handoff.py
axiom/core/evidence.py
axiom/core/decision.py
axiom/core/binding.py
axiom/core/governance_command.py
axiom/core/autonomy_grant.py
tools/task_card.py
tools/handoff.py
tools/evidence.py
tools/decision.py
tools/binding.py
tools/governance_command.py
tools/autonomy_grant.py
```

Recommended seventh mandate:

```text
Mandate 7: Bind lower-level agent authorities and assign synthesis to Cursor.
```

Status:

```text
Accepted by Jeremy and implemented as governance scaffold and tooling defaults.
```

Scope:

- name Cursor as the synthesis and summarization agent
- keep Cursor output advisory unless accepted by Operator decision
- preserve the machine process/function labels `synthesize` and `summarize`
- use `CURSOR` as the active synthesis actor label while accepting legacy `SYN` records as compatibility input
- remove Codex ownership of the synthesis role from active role definitions
- grant Claude Code bounded review, verification, test-running, and small corrective-edit authority only when task scope is already accepted
- grant Antigravity bounded planning, scaffolding, and non-runtime governance-record drafting authority
- do not transfer decision, binding, autonomy, IPC, scheduler, executor, runtime, model-promotion, or protected-surface authority to any agent

Implemented surfaces:

```text
AGENTS.md
CLAUDE.md
.antigravity.md
.cursor/rules/axiom-governance.mdc
axiom/core/delegation.py
axiom/core/evaluation.py
axiom/core/handoff.py
tools/delegation.py
tools/evaluation.py
tools/handoff.py
governance/80_records/schemas/
```

Recommended eighth mandate:

```text
Mandate 8: Implement guided governance cycle operations.
```

Status:

```text
Accepted by Jeremy and implemented as governance-only cycle coordination tooling.
```

Scope:

- adopt v4.1a deterministic Orchestrator ideas as a non-executing record coordinator
- file future mandate roadmaps as advisory handoff records
- show active task, delegation, review, evidence, blocker, and decision state from `governance/80_records/`
- ingest terminal review reports into advisory evaluation records
- guide Operator decision preview and confirmation-token recording
- keep agents advisory and preserve Jeremy as the only source of `operator_accepted` decisions
- do not route agents
- do not execute commands or patches
- do not reactivate IPC
- do not start scheduler or executor loops
- do not enable autonomy
- do not emit `VERIFIED_COMMIT`

Implemented surfaces:

```text
axiom/core/governance_cycle.py
tools/governance_cycle.py
tools/review_ingest.py
```

## 12. Acceptance Boundary

This scaffold is active as Mandate 1 governance structure.

Agent outputs, draft JSON records, console summaries, evaluations, implementation evidence, and recommendations remain advisory unless Jeremy explicitly records an Operator decision accepting a specific artifact, transition, or mandate.
