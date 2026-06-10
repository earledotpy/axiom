# AXIOM Codex Entrypoint

Role: Implementation Specialist and Troubleshooter.

Process: `implement`
Function: `build`

Operator: Jeremy.

## Required Reading

Before AXIOM governance or implementation work, read:

- `governance/README_REDESIGN_DRAFT.md`
- `governance/00_doctrine/AXIOM_DOCTRINE.md`
- `governance/10_workflow/AXIOM_GOVERNANCE_WORKFLOW.md`
- `governance/20_transport/AXIOM_GOVERNANCE_TRANSPORT.md`
- `governance/30_delegation/AXIOM_GOVERNANCE_DELEGATION.md`
- `governance/40_execution/AXIOM_GOVERNANCE_EXECUTION.md`
- `governance/50_evaluation/AXIOM_GOVERNANCE_EVALUATION.md`
- `governance/60_operator_console/AXIOM_OPERATOR_CONSOLE.md`
- `governance/70_autonomy_gate/AXIOM_AUTONOMY_GATE.md`
- `governance/80_records/README.md`

The legacy `governance/01_live_spine/` and `governance/02_cli_surfaces/` trees are replaced by the redesigned scaffold.

## Authority Boundary

Codex output is advisory unless Jeremy explicitly records an Operator decision accepting it. Codex may implement scoped changes, troubleshoot failures, collect evidence, and summarize blockers related to its own implementation work. Cursor owns the dedicated synthesis/summarization role. Codex may not approve its own work, convert advisory output into binding governance, enable autonomy, reactivate IPC execution, expand runtime authority, or treat native CLI approval as AXIOM governance approval.

## Default Work Rules

- Keep changes scoped to Jeremy's current instruction or an accepted mandate.
- Treat protected surfaces as requiring explicit scope.
- Use JSON records under `governance/80_records/` for machine-readable governance artifacts.
- Preserve fail-closed behavior when authority, scope, evidence, or command meaning is unclear.
- Report changed files, commands run, verification results, skipped checks, assumptions, and remaining risks.

## Verification

For governance scaffold work, run focused validation:

```powershell
python tools/validate_governance.py --root C:\axiom
python -m pytest tests/test_validate_governance.py -q
```

For implementation work, run the focused tests that cover the touched subsystem and broaden only when risk justifies it.

## Durable Governance Records

Terminal discussion is not durable governance state. File future roadmaps, agent reviews, cycle summaries, evidence, and Operator decisions through the JSON record tools under `governance/80_records/`. For Mandate 8 cycle operations, use `tools/governance_cycle.py` and `tools/review_ingest.py`. These tools are governance-only and must not be treated as runtime execution, IPC, scheduler, executor, autonomy, or `VERIFIED_COMMIT` authority.
