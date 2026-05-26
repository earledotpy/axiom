# AXIOM Terminal Implementation Source — Current Chat Addendum

Generated: 2026-05-20  
Project root: `C:\axiom`  
Terminal root: `C:\axiom\ui\terminal`  
Canonical baseline: `AXIOM_Implementation_v1.13.md`  
Scope: AXIOM Terminal overhaul, operator UI command surface, read-only visibility panels, terminal documentation discipline, editor repair, and manual log archival wrapper.

This source file records what was implemented or planned as implementation steps during the current AXIOM Terminal chat. It is not a replacement for `AXIOM_Implementation_v1.13.md`. It is a source/handoff addendum describing the terminal/operator-interface layer built on top of the existing AXIOM runtime.

The work in this chat did not supersede v1.13, did not authorize autonomous operation, did not enable safe-pass, did not promote a model profile, did not add real model/cloud calls, did not add real network fetches, did not add sandbox process execution, did not add Telegram/operator control, and did not connect the scheduler automatically to an executor.

---

## 1. Boundary Preserved

AXIOM Terminal was treated as an operator UI layer.

Allowed terminal responsibilities:

```text
- deterministic profile/module loading
- terminal-native editing
- read-only runtime visibility panels
- safe wrappers around approved tools
- terminal diagnostics
- terminal command registry discipline
- terminal documentation/changelog/reporting
- manual maintenance wrappers for approved tools
```

Explicitly prohibited terminal responsibilities:

```text
- enabling autonomous operation
- enabling safe-pass
- promoting model profiles
- registering manifests casually from terminal shortcuts
- bypassing manifest, policy, safe-pass, model-profile, scheduler, or operator-control gates
- starting/dispatching/completing/cancelling tasks as casual shortcuts
- running real model/cloud/network/sandbox/Telegram/agent operations
- mutating AXIOM runtime state outside approved tools
```

The one later exception added in this chat is `axiom-archive-logs`, which is a manual wrapper around an approved maintenance tool under `C:\axiom\tools`. It mutates log-file layout only, not AXIOM runtime database state.

---

## 2. AXIOM Terminal Root Structure

AXIOM Terminal was standardized around:

```text
C:\axiom\ui\terminal
```

Expected structure:

```text
C:\axiom\ui\terminal\
├── profile\
│   ├── profile-axiom.ps1
│   └── visual-mode.json
├── modules\
│   ├── 04-visual-mode.ps1
│   ├── 05-visual.ps1
│   ├── 06-oh-my-posh.ps1
│   ├── 40-dashboard.ps1
│   ├── 41-readiness.ps1
│   ├── 42-registry-discipline.ps1
│   ├── 45-model.ps1
│   ├── 46-manifests.ps1
│   ├── 47-budget.ps1
│   ├── 48-events.ps1
│   ├── 49-doctor.ps1
│   ├── 50-terminal-report.ps1
│   ├── 51-changelog.ps1
│   ├── 52-docs.ps1
│   ├── 53-system-map.ps1
│   ├── 54-terminal-test.ps1
│   ├── 55-terminal-snapshot.ps1
│   ├── 56-watch.ps1
│   ├── 57-task.ps1
│   ├── 58-compatibility-aliases.ps1
│   ├── 60-log-maintenance.ps1
│   └── 90-safety-help.ps1
├── registry\
│   └── axiom-terminal-command-registry.json
├── themes\
│   └── axiom-dashboard.omp.json
├── terminal\
│   └── windows-terminal-axiom-snippet.jsonc
├── assets\
│   ├── axiom-crt-background.png
│   └── axiom-terminal-icon.png
├── editor\
│   ├── settings.json
│   └── bindings.json
└── docs\
    ├── AXIOM_TERMINAL_CHANGELOG.md
    ├── AXIOM_TERMINAL_SPEC.md
    ├── AXIOM_EDITOR.md
    └── RECOMMENDED_APPLICATIONS.md
```

Some files above may be optional or planned depending on local installation status. The core convention is stable.

---

## 3. Profile Loader Hardened

Primary file:

```text
C:\axiom\ui\terminal\profile\profile-axiom.ps1
```

Final intended behavior:

```text
- set AXIOM root paths
- set AXIOM Terminal environment variables
- load modules from C:\axiom\ui\terminal\modules
- load modules deterministically by filename sort order
- fail-soft per module
- report the failing module name and exception
- keep startup profile logic minimal
```

Profile boundary:

```text
profile-axiom.ps1 must not contain runtime checks, dashboards, banners, command bodies, Oh My Posh logic, or database queries.
```

The profile is only a loader. Actual behavior belongs in modules.

Important module order rule:

```text
04-visual-mode.ps1 must load before 05-visual.ps1.
05-visual.ps1 must load before 06-oh-my-posh.ps1.
```

The obsolete name:

```text
43-visual-mode.ps1
```

was identified as unsafe because it loads too late. The corrected name is:

```text
04-visual-mode.ps1
```

---

## 4. Windows Terminal / AXIOM Terminal Profile Work

The Windows Terminal profile was configured around a custom `AXIOM Terminal` profile using:

```text
pwsh.exe -NoLogo
startingDirectory: C:\axiom
font: 0xProto Nerd Font Mono
backgroundImage: C:\axiom\ui\terminal\assets\axiom-crt-background.png
icon: C:\axiom\ui\terminal\assets\axiom-terminal-icon.png
colorScheme: AXIOM Fail-Closed CRT
tabTitle: AXIOM
```

A custom color scheme was used:

```json
{
  "name": "AXIOM Fail-Closed CRT",
  "background": "#020806",
  "foreground": "#C8FFD8",
  "green": "#5CFFA4",
  "cyan": "#7DFFD6",
  "selectionBackground": "#214D36",
  "cursorColor": "#5CFFA4"
}
```

Windows Terminal UI issues addressed:

```text
- missing profile drop-down caused by settings/keybinding/menu configuration
- profile launching via wt.exe -p "AXIOM Terminal" -d C:\axiom
- taskbar PowerShell icon behavior distinguished from Windows Terminal profile launching
- F11/fullscreen keyboard behavior on laptop Fn-key layout clarified
```

---

## 5. Visual Mode and Dashboard Direction

Implemented or planned modules:

```text
04-visual-mode.ps1
05-visual.ps1
06-oh-my-posh.ps1
```

Intended commands:

```text
axiom-visual-mode
axiom-visual-native
axiom-visual-dashboard
```

Final direction:

```text
- native prompt remains available
- Oh My Posh dashboard mode remains available
- visual mode is controlled from AXIOM Terminal config
- prompt/dashboard UI must be fast, local, and fail-soft visually
- prompt/dashboard display must not be treated as runtime truth unless backed by actual read-only AXIOM tools or SQLite mode=ro queries
```

A major correction made during the chat:

```text
Do not put JSON snippets directly into PowerShell command input.
```

The user encountered:

```text
Unexpected token ':' in expression or statement.
```

from pasting JSON profile fields into PowerShell. JSON must be edited inside Windows Terminal settings JSON, not executed.

---

## 6. Core Terminal Command Surface

AXIOM Terminal was structured around a registry discipline and a command surface divided roughly into:

```text
Core
Editing
Verification
State visibility
Reports
Terminal UI
Docs/navigation
Architecture maps
Maintenance
```

Primary commands covered in this chat:

```text
axiom-help
axiom-doctor
axiom-registry
axiom-guard
axiom-edit
ae
axiom-preflight
axiom-status
axiom-audit
axiom-health
axiom-regression
axiom-test
axiom-dashboard
axiom-readiness
axiom-queue
axiom-model
axiom-manifests
axiom-budget
axiom-events
axiom-task
axiom-task-latest
axiom-handoff
axiom-logs
axiom-terminal-report
axiom-terminal-changelog
axiom-terminal-note
axiom-docs
axiom-doc
axiom-doc-path
axiom-system-map
axiom-boundaries
axiom-runtime-map
axiom-terminal-map
axiom-terminal-test
axiom-terminal-snapshot
axiom-watch
axiom-watch-once
axiom-watch-help
axiom-archive-logs
```

Compatibility aliases discussed:

```text
axiom-open
np
axiom-snapshot
axiom-terminal-logs
axiom-root
axiom-files
```

The compatibility-alias policy:

```text
- aliases may exist for old habits
- aliases should not be primary help-surface commands
- preferred commands remain axiom-edit / ae and axiom-logs
```

---

## 7. Command Registry Discipline

Primary file:

```text
C:\axiom\ui\terminal\registry\axiom-terminal-command-registry.json
```

Registry object shape expected for commands:

```json
{
  "name": "axiom-command",
  "category": "state_visibility",
  "primary": true,
  "mutates_axiom_runtime": false,
  "risk": "low",
  "status": "implemented",
  "description": "..."
}
```

Property-add defect encountered:

```text
Exception setting "status": "The property 'status' cannot be found on this object."
```

Root cause:

```text
Some existing registry command objects did not already have a status property.
```

Correct pattern adopted:

```powershell
if (-not ($cmd.PSObject.Properties.Name -contains "status")) {
    $cmd | Add-Member -NotePropertyName status -NotePropertyValue "implemented"
}
else {
    $cmd.status = "implemented"
}
```

This same safe property-add pattern was reused for:

```text
category
primary
mutates_axiom_runtime
risk
status
description
backing_tools
```

---

## 8. T7 — Model Profile Panel

Module:

```text
C:\axiom\ui\terminal\modules\45-model.ps1
```

Commands:

```text
axiom-model
```

Purpose:

```text
Read-only model profile / trust-boundary visibility.
```

Reads:

```text
model_profile_fingerprints
classifier_calibration_runs
```

using SQLite:

```text
mode=ro
```

Shows:

```text
- profile labels
- latest model profile rows
- current trusted profile count
- thinking_mode
- thinking_mode_rule_version
- registration_status
- is_current
- calibration_run_id
- calibration row if present
- trust assessment
```

Trust logic surfaced:

```text
trusted only when:
- registration_status = current
- thinking_mode = disabled
- calibration exists and passed
- is_current = 1
```

Expected current state:

```text
current trusted profile absent
latest qwen3:4b profile candidate/non-current
thinking_mode = unknown
thinking_mode_rule_version = gateway_required_v1
calibration_run_id = pending_calibration
```

Boundary:

```text
axiom-model does not call Ollama, register models, promote models, alter calibration, or enable safe-pass.
```

---

## 9. T8 — Manifest / Tool-Capability Integrity Panel

Module:

```text
C:\axiom\ui\terminal\modules\46-manifests.ps1
```

Commands:

```text
axiom-manifests
```

Purpose:

```text
Read-only manifest/tool-capability integrity visibility.
```

Reads:

```text
manifest_fingerprints
tool_capability_map.json
manifest_schema.json
tool_capability_map_schema.json
```

Capabilities:

```text
- active manifest row listing
- inactive manifest count
- type counts
- registered SHA256 vs actual file SHA256
- missing file detection
- tool-capability map JSON parse check
- tool count
- active tool map row verification
```

Boundary:

```text
Does not run register_manifests.py.
Does not repair manifests.
Does not activate/deactivate manifests.
Does not rewrite manifest fingerprint rows.
```

---

## 10. T9 — Provider / Resource Budget Panel

Module:

```text
C:\axiom\ui\terminal\modules\47-budget.ps1
```

Commands:

```text
axiom-budget
```

Purpose:

```text
Read-only provider/resource budget visibility.
```

Reads:

```text
sessions
provider_usage
provider_budget_windows
provider_usage_reconciliations
resource_usage
tasks
```

Capabilities:

```text
- latest session status
- provider usage summary by provider/status
- estimated and actual token totals where present
- failed/rate-limited/quota-exhausted provider rows
- provider budget windows
- recent reconciliations
- resource usage summary
- exceeded resource rows
```

Boundary:

```text
Does not reconcile provider usage.
Does not create budget windows.
Does not update usage rows.
Does not call providers or models.
Does not change resource limits.
```

---

## 11. T10 — Events Panel

Module:

```text
C:\axiom\ui\terminal\modules\48-events.ps1
```

Commands:

```text
axiom-events
axiom-events -GlobalRisks
```

Purpose:

```text
Read-only recent session/security event visibility.
```

Reads:

```text
sessions
session_events
security_events
```

Capabilities:

```text
- latest session summary
- session event counts by event_type
- security event counts by severity/event_type
- recent session events
- recent security events
- recent critical/warning security risks
- optional global recent security risks
```

Boundary:

```text
Does not insert events.
Does not acknowledge events.
Does not delete events.
Does not repair sessions.
Does not alter scheduler state.
```

---

## 12. T11 — AXIOM Terminal Doctor

Module:

```text
C:\axiom\ui\terminal\modules\49-doctor.ps1
```

Commands:

```text
axiom-doctor
```

Purpose:

```text
Consolidated AXIOM Terminal diagnostics.
```

Checks:

```text
- terminal paths
- profile file
- module directory
- registry file
- visual config
- theme/assets
- venv activation path
- database presence
- required modules
- visual module order
- required terminal commands
- registry parse/schema/unique names
- implemented registry commands loaded
- runtime-mutating commands count
- visual config parseability
- external tools: python, pytest, micro, git, wt.exe, oh-my-posh
- approved AXIOM tool files
- unsafe shortcut absence
```

Boundary:

```text
Does not auto-fix.
Does not run repair_session_state.py.
Does not run register_manifests.py.
Does not start scheduler/executor/model/network/sandbox behavior.
```

---

## 13. T12 — Terminal Suite Report

Module:

```text
C:\axiom\ui\terminal\modules\50-terminal-report.ps1
```

Commands:

```text
axiom-terminal-report
axiom-terminal-report -Save
```

Purpose:

```text
Read-only AXIOM Terminal suite report.
```

Reports:

```text
- AXIOM root
- terminal root
- profile mode
- prompt engine
- startup banner
- terminal path presence
- modules
- visual config
- command registry summary
- primary command surface
- roadmap
- boundary statement
```

Optional output path:

```text
C:\axiom\logs\terminal_reports\axiom_terminal_report_YYYYMMDD_HHMMSS.md
```

Defect encountered:

```text
Variable reference is not valid. ':' was not followed by a valid variable name character.
```

Root cause:

```powershell
$lines.Add("$key: $state :: $path")
```

PowerShell interpreted `$key:` as a scoped variable. Fix:

```powershell
$lines.Add("${key}: $state :: $path")
```

Boundary:

```text
Does not call axiom-preflight.
Does not run runtime tools.
Does not mutate runtime state.
```

---

## 14. T13 — Terminal Changelog / Update Notes

Module:

```text
C:\axiom\ui\terminal\modules\51-changelog.ps1
```

Docs file:

```text
C:\axiom\ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md
```

Commands:

```text
axiom-terminal-changelog
axiom-terminal-note "note text"
axiom-terminal-changelog-path
```

Purpose:

```text
Terminal-suite changelog and update-note discipline.
```

Allowed write scope:

```text
C:\axiom\ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md
```

Boundary:

```text
This writes terminal documentation only.
It does not mutate AXIOM runtime state.
It is not a substitute for runtime handoff artifacts.
```

---

## 15. T14 — Docs / Navigation Panel

Module:

```text
C:\axiom\ui\terminal\modules\52-docs.ps1
```

Commands:

```text
axiom-docs
axiom-doc <name>
axiom-doc-path <name>
axiom-docs-terminal
axiom-docs-runtime
axiom-docs-policy
axiom-docs-tools
```

Purpose:

```text
Fast local documentation and project-navigation panel.
```

Indexed categories:

```text
terminal
runtime
policy
gateway
tool
```

Example doc keys:

```text
terminal-spec
terminal-editor
terminal-apps
terminal-changelog
terminal-registry
terminal-profile
visual-config
windows-terminal-snippet
dashboard-theme
schema
db
scheduler
scheduler-loop
supervisor
state-machine
task-committer
context-builder
token-estimator
manifest-schema
tool-map-schema
tool-map
manifest-binder
policy-engine
model-gateway
network-gateway
sandbox-gateway
memory-gateway
verify-foundation
audit-lifecycle
audit-execution
supervisor-health
snapshot
handoff
handoff-bundle
```

Boundary:

```text
Lists and opens local files only.
Opening a file is not runtime mutation.
Saving edits remains normal implementation work and must follow implementation discipline.
```

---

## 16. T15 — System Map / Boundary Map

Module:

```text
C:\axiom\ui\terminal\modules\53-system-map.ps1
```

Commands:

```text
axiom-system-map
axiom-boundaries
axiom-runtime-map
axiom-terminal-map
```

Purpose:

```text
Static/read-only boundary and architecture map.
```

Map layers:

```text
Layer 1 — AXIOM Terminal / Operator UI
Layer 2 — Approved AXIOM Tools
Layer 3 — AXIOM Runtime Core
Layer 4 — Persistence / Database
Layer 5 — Policy / Manifests / Tool Capability
Layer 6 — Model Trust Boundary
Layer 7 — Gateways / Future Execution
```

Boundary:

```text
Does not query the database.
Does not infer live runtime truth.
Does not call runtime tools.
```

Live state remains in:

```text
axiom-dashboard
axiom-readiness
axiom-queue
axiom-model
axiom-manifests
axiom-budget
axiom-events
axiom-preflight
```

---

## 17. T16 — Terminal Suite Regression Test

Module:

```text
C:\axiom\ui\terminal\modules\54-terminal-test.ps1
```

Commands:

```text
axiom-terminal-test
axiom-terminal-test -Quiet
```

Purpose:

```text
Terminal-suite regression check.
```

Checks:

```text
- profile file exists
- module directory exists
- every terminal module parses as PowerShell
- visual-mode load order is correct
- registry JSON parses
- registry schema is correct
- registry command names are unique
- required registry fields exist
- implemented registry commands are loaded
- visual config parses
- required commands exist
- unsafe shortcuts are absent
```

Defect encountered:

```text
Argument types do not match
Line: return @($results)
```

Fix:

```powershell
return $results.ToArray()
```

Boundary:

```text
Does not run axiom-preflight.
Does not query or write AXIOM runtime database.
Does not call scheduler/executor/model/network/sandbox tools.
```

---

## 18. T17 — Terminal Snapshot Artifact

Module:

```text
C:\axiom\ui\terminal\modules\55-terminal-snapshot.ps1
```

Commands:

```text
axiom-terminal-snapshot
```

Purpose:

```text
Saved AXIOM Terminal suite state artifact.
```

Output path:

```text
C:\axiom\logs\terminal_snapshots\
```

Generated files:

```text
axiom_terminal_snapshot_YYYYMMDD_HHMMSS.json
axiom_terminal_snapshot_YYYYMMDD_HHMMSS.md
```

Snapshot contents:

```text
- schema_version
- generated_at
- axiom_root
- terminal_root
- boundary
- environment
- paths
- visual_config
- registry summary
- module parse results
- command availability
- docs inventory
```

Defect encountered:

```text
Missing ')' in method call.
Unexpected token 'Boundary:' in expression or statement.
```

Root cause:

```powershell
$lines.Add("- Terminal root: `$($Snapshot.terminal_root)`")
```

The trailing backtick before the closing quote escaped the quote and broke parsing.

Fix:

```powershell
$lines.Add("- Terminal root: $($Snapshot.terminal_root)")
```

Final parse check confirmed:

```text
55-terminal-snapshot.ps1 parsed cleanly.
```

Boundary:

```text
Terminal snapshot only.
Does not include live runtime database contents.
Does not mutate AXIOM runtime state.
```

---

## 19. T18 — Watch Panel

Module:

```text
C:\axiom\ui\terminal\modules\56-watch.ps1
```

Commands:

```text
axiom-watch
axiom-watch-once
axiom-watch-help
```

Purpose:

```text
Foreground read-only refresh panel for AXIOM Terminal.
```

Modes:

```text
dashboard
readiness
queue
events
compact
ops
```

Default:

```powershell
axiom-watch -Mode compact -IntervalSeconds 10
```

Bounded test pattern:

```powershell
axiom-watch -Mode compact -IntervalSeconds 5 -MaxIterations 2
```

Risk classification:

```text
medium
```

Reason:

```text
It introduces a foreground loop.
```

Safety requirements:

```text
- foreground only
- interruptible with Ctrl+C
- no background service
- no runtime mutation
- no automatic axiom-preflight
- no scheduler dispatch
- no task execution
```

---

## 20. T19 — Task Detail Viewer

Module:

```text
C:\axiom\ui\terminal\modules\57-task.ps1
```

Commands:

```text
axiom-task <task_id>
axiom-task-latest
```

Purpose:

```text
Read-only task detail viewer by task_id.
```

Reads via SQLite:

```text
mode=ro
```

Reads:

```text
tasks
security_events
provider_usage
resource_usage
task_execution_records or task_executions if present
```

Displays:

```text
- task identity
- session_id
- parent_task_id
- chain_id
- task_class
- task_type
- status
- priority
- manifest_id
- timestamps
- goal/result/error previews
- child tasks
- sibling tasks
- security events
- provider usage
- resource usage
- execution records
```

Boundary:

```text
Does not start, dispatch, complete, fail, cancel, repair, or execute tasks.
```

Explicitly not added:

```text
axiom-task-start
axiom-task-dispatch
axiom-task-complete
axiom-task-fail
axiom-task-cancel
axiom-task-repair
```

---

## 21. Compatibility Alias Module

Module:

```text
C:\axiom\ui\terminal\modules\58-compatibility-aliases.ps1
```

Commands:

```text
axiom-open
np
axiom-terminal-logs
```

Purpose:

```text
Preserve old command names while steering daily use toward the current AXIOM Terminal command surface.
```

Alias behavior:

```text
axiom-open <path> -> axiom-edit <path>
np <path> -> prints legacy warning, then axiom-edit <path>
axiom-terminal-logs -> axiom-logs if available, else list recent logs
```

Reason for adding:

`axiom-registry` showed warnings:

```text
alias loaded: axiom-open not loaded
alias loaded: np not loaded
alias loaded: axiom-terminal-logs not loaded
```

These were not runtime concerns because:

```text
Registry discipline: PASS
```

But adding compatibility aliases quiets warnings and improves operator continuity.

---

## 22. Editor Integration Repair

Existing editor module shown by user:

```text
AXIOM Terminal editor integration
```

Problems identified:

```text
- fallback to Windows Notepad was still present
- micro config was not forced to C:\axiom\ui\terminal\editor
- axiom-install-editor copied config into $HOME\.config\micro
- stale user-level micro bindings could still break axiom-edit
- broken binding action Replace caused micro launch failure
```

Observed error:

```text
Error in bindings: action Replace does not exist
```

Corrected posture:

```text
- AXIOM Terminal is terminal-first
- do not fallback to Windows Notepad by default
- prefer micro
- set MICRO_CONFIG_HOME to C:\axiom\ui\terminal\editor when launching micro
- keep bindings minimal
- avoid Replace binding
- prioritize reliability over shortcut customization
```

Clean AXIOM-local editor config:

```text
C:\axiom\ui\terminal\editor\settings.json
C:\axiom\ui\terminal\editor\bindings.json
```

Safe minimal `bindings.json`:

```json
{
    "Ctrl-s": "Save",
    "Ctrl-q": "Quit",
    "Ctrl-f": "Find",
    "Ctrl-g": "FindNext",
    "Ctrl-z": "Undo",
    "Ctrl-y": "Redo"
}
```

If this binding file causes issues, delete or disable it and rely on micro defaults.

Commands still retained:

```text
axiom-edit
ae
axiom-edit-profile
axiom-edit-user-profile
axiom-edit-config
axiom-edit-schema
axiom-edit-db
axiom-edit-scheduler
axiom-edit-terminal-module
axiom-install-editor
axiom-editor-info
```

The proposed `axiom-editor-doctor` was not implemented by the user because it was considered too limited in scope and likely to be replaced during a later professional cleanup/reorganization pass.

---

## 23. Log Archival Tool Added to AXIOM UI

Runtime tool provided by user:

```text
C:\axiom\tools\archive_logs.py
```

Purpose:

```text
Archive older files directly under C:\axiom\logs into C:\axiom\logs\archive.
```

Behavior:

```text
- creates logs\archive if missing
- lists files directly inside logs
- detects newest handoff bundle manifest
- keeps newest generated bundle set
- always keeps newest 25 files as safety buffer
- zips older files into logs_archive_YYYYMMDD_HHMMSS.zip
- deletes archived originals after writing zip
- prints kept files table
```

Important classification:

```text
This is state-changing file maintenance.
It does not mutate AXIOM runtime database state.
It does not alter scheduler, task lifecycle, manifests, model profiles, or safe-pass.
```

Terminal wrapper module:

```text
C:\axiom\ui\terminal\modules\60-log-maintenance.ps1
```

Commands:

```text
axiom-archive-logs
axiom-archive-logs-path
```

Wrapper behavior:

```text
- verifies tools\archive_logs.py exists
- warns that older log files will be archived and deleted after zipping
- runs python tools\archive_logs.py
```

Registry classification:

```json
{
  "name": "axiom-archive-logs",
  "category": "reports",
  "primary": true,
  "mutates_axiom_runtime": false,
  "risk": "medium",
  "status": "implemented",
  "backing_tools": ["tools/archive_logs.py"],
  "description": "Archive older AXIOM log files into logs/archive using the approved archive_logs.py tool."
}
```

Manual only. Do not call from:

```text
profile startup
axiom-dashboard
axiom-watch
axiom-doctor
axiom-terminal-test
axiom-preflight
axiom-handoff
```

---

## 24. Help Surface Updates

Primary help module:

```text
C:\axiom\ui\terminal\modules\90-safety-help.ps1
```

Help surface was expanded across sections.

State visibility additions:

```text
axiom-model
axiom-manifests
axiom-budget
axiom-events
axiom-watch
axiom-watch-once
axiom-task <task_id>
axiom-task-latest
```

Reports additions:

```text
axiom-terminal-report
axiom-terminal-changelog
axiom-terminal-note
axiom-terminal-snapshot
axiom-archive-logs
```

Docs/navigation additions:

```text
axiom-docs
axiom-doc <name>
axiom-doc-path <name>
```

Architecture maps additions:

```text
axiom-system-map
axiom-boundaries
axiom-runtime-map
axiom-terminal-map
```

Terminal UI additions:

```text
axiom-terminal-test
axiom-watch-help
```

Editing retained:

```text
axiom-edit
ae
axiom-edit-profile
axiom-edit-user-profile
axiom-edit-config
axiom-edit-schema
axiom-edit-db
axiom-edit-scheduler
axiom-edit-terminal-module
axiom-install-editor
axiom-editor-info
```

`axiom-editor-doctor` was intentionally not finalized.

---

## 25. Verification Commands for AXIOM Terminal

Terminal-suite verification:

```powershell
Set-Location C:\axiom
. $PROFILE

axiom-terminal-test
axiom-doctor
axiom-registry
axiom-terminal-report
axiom-terminal-snapshot
```

Runtime verification remains separate:

```powershell
axiom-preflight
```

Expanded runtime verification:

```powershell
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1

pytest tests -v
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
```

Supervisor health:

```powershell
axiom-health
```

or fallback:

```powershell
python tools\supervisor_health_check.py <SESSION_ID>
```

Expected healthy fail-closed runtime shape remains:

```text
foundation_passed: True
operational_mode: fail_closed_non_autonomous
autonomous_allowed: False
fail_closed_coherent: True
supervisor_health_ok
task_lifecycle_audit passed
task_execution_audit passed
```

`autonomous_allowed: False` remains expected, not a defect.

---

## 26. Files Added or Modified in This Chat

### Profile / config

```text
ui\terminal\profile\profile-axiom.ps1
ui\terminal\profile\visual-mode.json
```

### Terminal modules

```text
ui\terminal\modules\04-visual-mode.ps1
ui\terminal\modules\05-visual.ps1
ui\terminal\modules\06-oh-my-posh.ps1
ui\terminal\modules\40-dashboard.ps1
ui\terminal\modules\41-readiness.ps1
ui\terminal\modules\42-registry-discipline.ps1
ui\terminal\modules\45-model.ps1
ui\terminal\modules\46-manifests.ps1
ui\terminal\modules\47-budget.ps1
ui\terminal\modules\48-events.ps1
ui\terminal\modules\49-doctor.ps1
ui\terminal\modules\50-terminal-report.ps1
ui\terminal\modules\51-changelog.ps1
ui\terminal\modules\52-docs.ps1
ui\terminal\modules\53-system-map.ps1
ui\terminal\modules\54-terminal-test.ps1
ui\terminal\modules\55-terminal-snapshot.ps1
ui\terminal\modules\56-watch.ps1
ui\terminal\modules\57-task.ps1
ui\terminal\modules\58-compatibility-aliases.ps1
ui\terminal\modules\60-log-maintenance.ps1
ui\terminal\modules\90-safety-help.ps1
```

### Registry

```text
ui\terminal\registry\axiom-terminal-command-registry.json
```

### Editor

```text
ui\terminal\editor\settings.json
ui\terminal\editor\bindings.json
```

### Terminal docs

```text
ui\terminal\docs\AXIOM_TERMINAL_CHANGELOG.md
ui\terminal\docs\AXIOM_TERMINAL_SPEC.md
ui\terminal\docs\AXIOM_EDITOR.md
ui\terminal\docs\RECOMMENDED_APPLICATIONS.md
```

### Terminal reports/snapshots output paths

```text
logs\terminal_reports\
logs\terminal_snapshots\
```

### Approved tool added

```text
tools\archive_logs.py
```

### Windows Terminal material

```text
ui\terminal\terminal\windows-terminal-axiom-snippet.jsonc
ui\terminal\themes\axiom-dashboard.omp.json
ui\terminal\assets\axiom-crt-background.png
ui\terminal\assets\axiom-terminal-icon.png
```

---

## 27. Known Issues / Cleanup Items

### 27.1 Editor cleanup deferred

The user chose not to implement `axiom-editor-doctor`.

Future cleanup should rationalize:

```text
ui\terminal\editor\
editor module command names
micro config handling
user-level config isolation
help and registry entries
```

### 27.2 Registry object shape normalization

Some registry entries may have been created before `status` became consistently required. Future cleanup should normalize all command entries to a uniform schema.

### 27.3 Module organization cleanup

The user intends to clean up and organize files more professionally after implementation stabilizes. Likely future cleanup targets:

```text
module numbering
module categories
compatibility aliases
editor config
docs/index files
registry schema
terminal report/snapshot formats
```

### 27.4 Terminal tasks should pause after T19 plus log archival

After T19 and the log archival wrapper, the terminal has enough near-term value. Further AXIOM Terminal expansion should pause unless a concrete runtime feature requires new operator visibility.

---

## 28. Explicitly Deferred / Not Implemented

Still not authorized or implemented:

```text
autonomous operation
safe-pass enablement
model profile promotion
classifier calibration approval
real model/cloud calls
real network fetches
sandbox process execution
Telegram/operator control plane
agent layer
automatic scheduler-to-executor integration
persistent scheduler service
terminal safe-pass controls
terminal model-promotion controls
terminal task mutation controls
terminal operator-control shortcuts
```

Do not add these as PowerShell convenience commands.

---

## 29. Recommended Next Step After This Chat

The terminal phase should stop expanding and return to AXIOM runtime implementation unless a specific terminal bug needs repair.

Recommended next implementation boundary:

```text
Return to AXIOM runtime Phase 2 / next approved runtime slice.
```

Before runtime work:

```powershell
axiom-terminal-test
axiom-doctor
axiom-registry
axiom-terminal-snapshot
axiom-preflight
```

If log clutter is high:

```powershell
axiom-archive-logs
```

Then proceed only after verifying:

```text
foundation_passed=True
operational_mode=fail_closed_non_autonomous
autonomous_allowed=False
fail_closed_coherent=True
supervisor_health_ok
task_lifecycle_audit passed
task_execution_audit passed
```

---

End of AXIOM Terminal implementation source addendum.
