# Phase 8B Repository Cleanup Plan

## Scope

Phase 8B is audit/planning only. It records the current repository hygiene state,
professional file naming risks, required reference-map work, and a risk-ranked
cleanup plan for later approved slices.

This audit does not rename files, delete files, move files, format files, patch
runtime code, update manifests, register manifests, touch database files, clean
logs, clean virtual environments, alter caches, change runtime behavior, enable
autonomy, add Telegram default runtime, add scheduler-to-agent automation, add
scheduler-to-executor automation, or expand gateway authority.

Phase 8B explicitly does not:

- enable autonomy
- add Telegram default runtime
- add scheduler-to-agent automation
- add scheduler-to-executor automation
- expand gateway authority

## Evidence Gathered

Successful read-only commands:

```powershell
git status --short
git status --ignored --short
Get-ChildItem -Force -Name
Get-ChildItem tests -Recurse -File -Name
Get-ChildItem docs -Recurse -File -Name
Get-ChildItem ui\terminal -Recurse -File -Name
Get-ChildItem axiom\agents -Force -Name
Get-ChildItem axiom\policy -Recurse -File -Name
Get-Content .gitignore
Get-Content tests\test_phase8a_release_freeze_documentation_reconciliation_doc.py
Get-Content tests\test_phase7_closeout.py
```

Read-only inventory commands rerun before the operator-approved implementation
slice:

```powershell
git ls-files
git ls-files --modified
git ls-files --deleted
git ls-files --others --exclude-standard
git ls-files --ignored --others --exclude-standard
rg --files
```

Implementation-slice inventory results:

| Command | Result |
| --- | --- |
| `git ls-files` | 411 tracked index paths before staging the final source/doc additions. |
| `git ls-files --modified` | 30 modified tracked paths. |
| `git ls-files --deleted` | 1 deleted worktree path: `GEMINI.md`. |
| `git ls-files --others --exclude-standard` | 210 untracked source/doc/test/tool/UI paths. |
| `git ls-files --ignored --others --exclude-standard` | 5333 ignored runtime/cache/local-environment paths. |
| `rg --files` | 619 visible repository files. |

The shell sandbox did not complete several inventory commands until they were
rerun with explicit approval because process spawn setup failed. The rerun
results above are the implementation-slice evidence.

## Worktree Inventory Summary

The worktree is heavily dirty. `git status --ignored --short` shows tracked
modifications, tracked deletions, untracked implementation material, untracked
docs/tests/tools/UI files, ignored runtime artifacts, ignored caches, and an
ignored local virtual environment.

Observed root-level entries include source and docs roots plus local/runtime
artifacts:

| Area | Observed paths or patterns | Current state | Cleanup meaning |
| --- | --- | --- | --- |
| Root instructions | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | tracked modified | Review as operator/tool instruction docs before any normalization. |
| Root phase doc | `AXIOM_Implementation_v1.13.md` | untracked | Likely source/reference doc; do not delete as artifact without provenance check. |
| Runtime DB | `axiom.db`, `axiom.db-shm`, `axiom.db-wal` | tracked deleted for `axiom.db`; ignored present for `axiom.db*` | Blocked cleanup candidate; requires explicit runtime/database approval. |
| Runtime logs | `logs\`, `axiom\logs\` | tracked deleted and ignored present | Blocked cleanup candidate; generated handoffs/snapshots must be separated from source references. |
| Python caches | `__pycache__`, `*.pyc` under `axiom`, `tests`, `tools` | tracked deleted and ignored present | Repo hygiene finding; future slice should untrack/ignore only after tracked-list proof. |
| Local env | `venv\` | tracked deleted and ignored present | Repo hygiene finding; requires separate dependency/venv cleanup approval. |
| Root inspection scripts | `inspect_axiom_state.py`, `inspect_heartbeat_schema.py`, `inspect_latest_axiom_session.py`, `inspect_latest_heartbeats.py`, `inspect_session_4573.py` | present at root, not listed as untracked by status because ignored/excluded state is mixed | Suspicious one-off tooling; map references and decide keep/move/archive/delete later. |
| Root snapshot | `project_state_snapshot_2026-05-24T20-45-36Z.json` | untracked; also editor buffer and logs references exist | Generated artifact candidate; do not delete until source vs generated references are mapped. |
| Node lock | `package-lock.json` | untracked | Suspicious dependency artifact unless a Node project contract exists. |
| Malformed color spill | `orColor...#A8FF60...,` | ignored present by `orColor*` rule | Low-value malformed filename; still require explicit cleanup approval because this phase is read-only. |
| Terminal UI | `ui\terminal\...` | untracked tree | Product surface; do not clean as artifact. It includes docs, modules, registry, scripts, templates, themes, and editor buffers. |
| Policy manifests | `axiom\policy\operator_control_manifests\`, `axiom\policy\role_manifests\`, `axiom\policy\security_artifacts\calibration_set.json` | untracked | Security/config material; separate approval and manifest registration required before cleanup. |

## Cleanup Classification Table

| Candidate | Git state | Bucket | Proposed later action | Risk | Required reference map before action | Required verification after action |
| --- | --- | --- | --- | --- | --- | --- |
| `axiom\core\manifest_binder.py`, `axiom\core\policy_engine.py`, gateway modules, `axiom\persistence\schema.sql`, `axiom\security\plan_injection_scanner.py` | modified | Source code | Keep for current worktree review; no cleanup in Phase 8B | high | Python imports, tests, docs, config, policy/schema references | focused tests for touched modules; `pytest tests -v` |
| `axiom\agents\*.py` | untracked, with `axiom\agents\_init_.py` deleted and `axiom\agents\__init__.py` untracked | Source code | Blocked package-init reconciliation; later likely rename/replace only after mapping | high | imports for `axiom.agents`, package discovery, tests, tools, docs, terminal command docs | `python -m py_compile axiom\agents\*.py`; agent tests; full pytest |
| `axiom\core\agent_boundary_audit.py`, `execution_readiness.py`, `noop_task_stager.py`, `operator_command_ledger.py`, `operator_command_parser.py`, `policy_security_audit.py` | untracked | Source code | Keep or add intentionally in feature slice; not cleanup | high | imports, tools, tests, docs, terminal registry | focused matching tests; preflight audits |
| `axiom\gateways\telegram_bot_adapter.py`, `telegram_gateway.py` | untracked | Source code / gateway | Keep only if Phase 6 gateway scope is approved; otherwise leave untouched | high | gateway imports, tests, docs, terminal commands, config/env references | gateway tests, boundary audits, Telegram audit |
| `axiom\tools\` | untracked | Source code / tools | Inspect; likely namespace candidate or artifact depending contents | medium | Python imports, CLI docs, tests, terminal registry | compile and focused tool tests |
| `tests\*.py`, `tests\e2e\` | modified/untracked | Tests | Keep; do not cleanup as artifact | medium | test imports, fixtures, command docs, CI expectations | focused pytest selection and full pytest |
| `docs\*.md`, `docs\codex\CODEX_HANDOFF.md` | untracked docs tree | Docs | Keep as phase documentation unless superseded by approved archival slice | medium | docs links, terminal docs index, closeout references, implementation plan references | phase doc tests; docs-focused pytest |
| `texts\` | existing docs/support | Docs | Keep; no action without doc taxonomy review | low | docs references and governance references | docs tests |
| `governance\` | present | Governance | Do not touch without separate explicit approval | blocked | governance spine, CLI surfaces, archives/deprecated links | governance-specific review only |
| `ui\terminal\` | untracked tree | Terminal UI | Keep for terminal surface review; no cleanup in Phase 8B | high | PowerShell function names, registry entries, docs/help, tests, command aliases | terminal visibility tests, registry tests, `axiom-preflight` |
| `config\axiom.yaml` | modified | Config/policy/manifests | Keep for current config review; no cleanup | high | config keys, boot validation, tests, docs | config/bootstrap tests and foundation audit |
| `axiom\policy\operator_control_manifests\`, `role_manifests\`, `security_artifacts\calibration_set.json` | untracked | Config/policy/manifests | Blocked; separate policy/security approval | blocked | manifest IDs, binder references, schemas, registration outputs, tests | `python tools\register_manifests.py`; policy/security audits; pytest |
| `axiom.db`, `axiom.db-shm`, `axiom.db-wal` | tracked deleted/ignored present | Runtime artifacts | Blocked; never clean in this slice | blocked | runtime DB usage, test DB isolation, config/env overrides, migration expectations | explicit DB backup/restore proof; persistence tests |
| `logs\archive\*.zip`, `logs\axiom_handoff_*.md`, `logs\handoff_bundle_manifest_*.json`, `logs\operator_command_index_*.json`, `logs\operator_command_index_*.md`, `logs\project_state_snapshot_*.json` | tracked deleted and ignored present | Runtime artifacts | Blocked; future untrack/archive/delete only after generated/source split | blocked | source refs vs generated handoff refs, docs links, operator ledger references, terminal log maintenance | handoff tests, operator command ledger audit, snapshot tests |
| root `project_state_snapshot_2026-05-24T20-45-36Z.json` | untracked | Runtime artifact | Later delete or move to logs only after reference map | medium | docs, editor buffers, tools/snapshot references, tests | snapshot tests and clean status proof |
| `venv\` | tracked deleted and ignored present | Dependency/cache artifacts | Blocked; separate dependency cleanup approval | blocked | tracked-list proof, scripts that assume `.\\venv\\Scripts\\python.exe`, docs commands | dependency reinstall proof; approved test command path update |
| `.pytest_cache\`, `__pycache__`, `*.pyc` | tracked deleted and ignored present | Dependency/cache artifacts | Later untrack/ignore generated cache paths | medium | tracked-list proof and ignore rules | clean status proof; tests regenerate caches as ignored |
| `.gitignore` | untracked | Config | Keep and review; current rules already ignore caches, DB, logs, venv, Antigravity, `orColor*` | medium | docs and tooling expectations for generated files | status ignored proof |
| `package-lock.json` | untracked | Dependency artifact | Delete or keep only after Node contract check | medium | `package.json`, npm scripts, terminal UI build docs, CI references | `npm` proof only if Node project exists; otherwise status proof after deletion |
| `Set-Location` | tracked deleted | Suspicious/malformed filename | Later remove from tracking if proven accidental | medium | references in docs/scripts/tests, shell examples, terminal buffers | clean status proof; shell docs tests |
| root `inspect_*.py` scripts | present root scripts | Suspicious/malformed filenames / one-off tools | Rename/move/archive/delete only after reference map | medium | tool imports, docs, terminal buffers, command history, tests | compile kept tools or clean status proof after removal |
| `orColor...#A8FF60...,` | ignored present | Suspicious/malformed filename | Later delete with explicit cleanup approval | low | root filename references, editor buffers, docs, shell history if available | status ignored proof and root listing |
| `ui\terminal\*.bak`, registry/profile backups | untracked within UI tree | Dependency/cache artifacts / terminal UI | Later archive/delete only after terminal owner approval | medium | terminal modules, docs, registry references | terminal tests and root status proof |
| `.antigravity.md`, `.antigravitycli\`, `.claude\` | ignored present | Local tool/editor artifacts | Leave ignored; delete only with local-tool approval | low | editor/tool config references | status ignored proof |

## File Naming Audit

| Path or pattern | Issue | Risk | Required decision |
| --- | --- | --- | --- |
| `axiom\agents\_init_.py` and `axiom\agents\__init__.py` | Incorrect package-init spelling appears deleted while correct init is untracked | high | Decide whether the correct `__init__.py` replaces the typo and map all imports before staging. |
| `inspect_*.py` at repo root | One-off investigative script naming; root clutter; unclear ownership | medium | Decide keep as tools, archive in docs/logs, or delete after reference map. |
| `Set-Location` | Shell command accidentally tracked as filename | medium | Confirm no intentional source purpose; remove from tracking only in later cleanup slice. |
| `orColor...#A8FF60...,` | Malformed color/control spill filename; already ignored by `orColor*` | low | Delete only in an explicit cleanup slice. |
| `package-lock.json` without visible `package.json` in root listing | Lockfile without observed Node project contract | medium | Keep only if terminal UI or tooling has a Node dependency contract. |
| `project_state_snapshot_2026-05-24T20-45-36Z.json` at root | Generated snapshot outside `logs\` | medium | Move/delete only after generated snapshot references are separated from source docs/tests. |
| `ui\terminal\modules\*.bak`, `profile\*.bak`, `registry\*.bak` | Backup suffixes in product UI tree | medium | Archive/delete only after terminal registry and docs references are mapped. |
| Tracked `__pycache__` and `*.pyc` paths | Generated cache files appear in tracking history | medium | Untrack/ignore in a dedicated hygiene slice with tracked-list proof. |
| Tracked `venv\` paths | Local virtual environment appears in tracking history | blocked | Requires separate dependency cleanup approval and command-path review. |
| Tracked `logs\` handoff/snapshot paths | Generated runtime files appear in tracking history | blocked | Requires runtime/log archival approval and source/generated reference split. |
| Governance archive/deprecated paths | Historical material must be preserved | blocked | Do not rename, move, or delete without Jeremy's explicit governance approval. |

## Reference Map Requirements

Before any future rename, delete, move, untrack, ignore, or archive action, run
and record a reference map for the exact path and likely symbolic names.

Minimum reference checks:

```powershell
git status --short
git status --ignored --short
git ls-files
git ls-files --modified
git ls-files --deleted
git ls-files --others --exclude-standard
git ls-files --ignored --others --exclude-standard
rg --files
rg "<candidate-name-or-symbol>"
rg "<candidate-path-with-forward-slashes>"
rg "<candidate-path-with-backslashes>"
```

Structured checks by candidate type:

| Candidate type | Reference map required |
| --- | --- |
| Python source rename/delete | Python imports, `from ... import ...` references, dynamic imports, CLI entry points, tests, fixtures, docs command examples, terminal command wrappers. |
| Tool/script rename/delete | Direct CLI use in docs/tests/terminal modules, PowerShell wrappers, operator help, command registry, generated handoff examples. |
| Terminal command or registry rename | `ui\terminal\modules\*.ps1`, `ui\terminal\registry\axiom-terminal-command-registry.json`, terminal docs, safety help, doctor/preflight wiring, tests. |
| Docs move/delete | Markdown links, phase closeouts, terminal docs index, governance references, tests that assert doc text, handoff references. |
| Policy/manifest move/delete | Manifest binder references, schema references, registered fingerprints, config paths, tests, security audit tools. |
| Config move/delete | Boot validation, environment overrides, tests, docs, terminal preflight. |
| Governance move/delete | `governance\02_cli_surfaces\codex\AGENTS.governance.md`, active live spine, archives, deprecated legacy references; separate approval required. |
| Runtime artifact cleanup | Source references separated from generated handoff/snapshot references; DB/log backup and restore plan. |
| Dependency/cache cleanup | Tracked-list proof, ignore rules, reinstall/regeneration proof, command path references. |
| Malformed filename cleanup | Root listing, exact path capture, ignore rule proof, no references in docs/scripts/editor buffers. |

Generated handoff/snapshot references must be classified separately from source
references. A generated artifact mentioning another generated artifact is not
enough to justify preserving it as source, but it is enough to require explicit
runtime/log cleanup approval.

## Risk-Ranked Cleanup Plan

### Safe Later Slice

Allowed only after rerunning the blocked inventory commands:

1. Add or confirm ignore rules for generated caches, DB files, logs, local tool
   directories, and malformed `orColor*` spill artifacts.
2. Add status-only proof that ignored artifacts remain ignored.
3. Do not delete or untrack anything in this slice unless separately approved.

### Medium-Risk Later Slice

Requires reference maps and focused tests:

1. Decide root `inspect_*.py` fate: keep under `tools\`, archive as evidence, or
   delete if unused.
2. Decide root snapshot fate: move to `logs\` or delete as generated output.
3. Decide `package-lock.json` fate after checking for `package.json`, npm
   scripts, terminal UI build docs, and CI references.
4. Decide `Set-Location` tracked deletion after proving it is accidental.
5. Decide terminal `.bak` backup fate after terminal registry/docs checks.

### High-Risk Later Slice

Requires source-level reference maps and full verification:

1. Reconcile `axiom\agents\_init_.py` with `axiom\agents\__init__.py`.
2. Stage or reject untracked `axiom\agents\`, `axiom\core\*`, gateway, tool,
   docs, tests, and terminal UI changes as intentional work.
3. Preserve Phase 8A boundaries: no autonomy enablement, no default Telegram
   runtime, no scheduler-to-agent automation, no scheduler-to-executor
   automation, and no gateway authority expansion.

### Blocked Slice

Requires separate explicit approval before action:

1. Governance archives, deprecated legacy material, and active live spine.
2. Policy/manifests/security artifacts and manifest registration outputs.
3. Runtime database files and WAL/SHM files.
4. `logs\` generated handoff/snapshot/operator ledger cleanup.
5. `venv\` or dependency-lock cleanup.
6. Any source rename affecting imports.
7. Any terminal registry command rename.
8. Any tool rename used in docs/tests/terminal help.

## Future Verification Commands

Before any later cleanup implementation:

```powershell
git status --short
python -m pytest tests -k "phase8 or docs or terminal" -v
```

After any future cleanup implementation:

```powershell
python -m py_compile tools\run_phase7_acceptance.py tools\audit_phase7_e2e_gate.py tools\audit_phase7_closeout.py tools\audit_phase6_closeout.py tools\audit_agent_boundary.py tools\audit_telegram_gateway.py
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py
python tools\audit_agent_boundary.py
python tools\audit_operator_command_ledger.py
python tools\audit_telegram_gateway.py
python tools\audit_phase6_closeout.py
python tools\run_phase7_acceptance.py --json
axiom-preflight
axiom-phase7
pytest tests -v
```

If the cleanup touches policy/manifests, also run:

```powershell
python tools\register_manifests.py
```

If the cleanup touches terminal command wiring, also run the focused terminal
visibility and registry tests before full pytest.

## Operator-Approved Implementation Slice

After this audit was accepted, Jeremy explicitly approved repository-cleanup
edits for this task. The implementation slice applied the low- and medium-risk
cleanup decisions that do not alter runtime behavior:

| Candidate | Decision applied |
| --- | --- |
| Generated Python caches, `.pytest_cache`, runtime DB files, logs, and local virtual environment files | Keep local files ignored; remove tracked generated artifacts from the repository index. |
| `.gitignore` | Keep as source and add `.claude/` to the local tool/editor artifact ignore rules. |
| Root `inspect_*.py` scripts | Keep as diagnostic tooling under `tools\`; no source references outside this cleanup document were found. |
| `Set-Location` tracked file | Remove from the repository index; reference-map hits were command examples or PowerShell function use, not source-file references to a root file. |
| Root `package-lock.json`, root `project_state_snapshot_2026-05-24T20-45-36Z.json`, and `orColor...#A8FF60...,` | No file was present on disk during implementation; no deletion was needed. |
| `axiom\agents\_init_.py` and package init files | Replace typo `_init_.py` with conventional `__init__.py` package markers. |

This implementation slice does not enable autonomy, add Telegram default
runtime, add scheduler-to-agent automation, add scheduler-to-executor
automation, expand gateway authority, change governance archives, or change the
active governance live spine.

## Items Not To Touch Without Separate Approval

- Governance files, especially `governance\06_archives\` and
  `governance\07_deprecated_legacy\`.
- Active governance live spine material.
- Policy/manifests and security artifacts.
- `axiom.db`, `axiom.db-shm`, `axiom.db-wal`, or any runtime DB file.
- `logs\`, generated handoffs, generated snapshots, and operator ledger output.
- `venv\`, dependency locks, package-manager artifacts, and dependency cache
  cleanup.
- Any source rename affecting imports.
- Any terminal registry command rename.
- Any tool rename used in docs, tests, terminal help, or command registry.
- Any cleanup that would change runtime behavior or Phase 8A boundaries.

## Phase 8B Acceptance

- The audit document exists and is complete.
- Every cleanup candidate class observed in the dirty worktree has a
  classification, risk, proposed later action, reference-map requirement, and
  verification requirement.
- No runtime/code cleanup is performed in Phase 8B.
- Phase 8A boundaries remain intact.
- Future implementation slices are separated into safe, medium-risk, high-risk,
  and blocked groups.
