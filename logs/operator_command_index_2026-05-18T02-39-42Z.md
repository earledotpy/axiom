# AXIOM Operator Command Index

Tool version: `operator_command_index.v2`

| Command | Purpose | When to run | Expected exit code |
|---|---|---|---|
| `python tools\bootstrap_check.py` | Validate AXIOM passive bootstrap foundation checks. | After schema, manifest, boot verifier, or bootstrap-validation changes. | 0 when foundation checks pass; 1 when foundation checks fail. |
| `python tools\status_check.py` | Show operator-visible AXIOM operational state. | When you need to see current foundation/autonomous/safe-pass state. | 0 when database is initialized; 1 when database is not initialized. |
| `python tools\repair_session_state.py` | Align latest session with fail-closed state when no current trusted model profile exists. | After model profile registration, bootstrap work, or suspicious session-state drift. | 0 on successful repair/check. |
| `python tools\autonomous_readiness_check.py` | Check whether AXIOM may enter autonomous operation. | Before any autonomous/scheduler/agent execution path. | 0 when autonomous operation is allowed; 2 when blocked. |
| `python tools\verify_foundation.py` | Run the core operator checks together and report coherent foundation state. | Before starting new implementation work or after completing a task. | 0 when foundation is healthy; 1 when foundation fails. |
| `python tools\snapshot_project_state.py` | Write a timestamped JSON snapshot of AXIOM project/database state. | Before handoff, debugging, or larger implementation transitions. | 0 on successful snapshot write. |
| `python tools\generate_handoff.py` | Generate a human-readable Markdown handoff from the latest project snapshot. | Before moving to a new chat/session or briefing another model. | 0 on successful handoff write. |
| `python tools\operator_command_index.py` | Show available operator commands and their intended use. | When unsure which maintenance or verification command to run next. | 0 on successful display/export. |
| `pytest tests -v` | Run the full AXIOM regression suite. | After every implementation task. | 0 when all tests pass. |

## Notes

- `python tools\verify_foundation.py` is the preferred quick health check.
- `python tools\autonomous_readiness_check.py` returning exit code `2` is expected while AXIOM is fail-closed non-autonomous.
- `pytest tests -v` remains the canonical regression check after implementation changes.
