# AXIOM Phase 7

Canonical consolidated Phase 7 documentation. This file supersedes the former Phase 7 slice documents while preserving acceptance inventory, runner, E2E gate, readiness approval, terminal visibility, and closeout material.

## Consolidated Sections
- Phase 7A Acceptance Inventory
- Phase 7B Acceptance Runner
- Phase 7C Full-Goal E2E Gate Audit
- Phase 7 E2E Readiness Approval
- Phase 7D Terminal Visibility
- Phase 7E Closeout And Hardening Audit

## Source Section: Phase 7A Acceptance Inventory

## Phase 7A Acceptance Inventory

## Scope

Phase 7A inventories the v1.13 acceptance surface. The inventory itself does
not enable autonomous operation, safe-pass, live Telegram,
scheduler-to-agent automation, scheduler-to-executor automation, or the
full-goal E2E path.

The v1.13 source requirement is:

```text
Run the canonical MVP acceptance suite listed below.
Run tests/e2e/test_full_goal_flow_minimum.py only after classifier calibration
and model fingerprint registration are complete.
```

## Canonical Acceptance Count

`AXIOM_Implementation_v1.13.md` contains **108 canonical MVP acceptance rows**.
The stable row span is:

```text
1..108
```

The rows are grouped below for implementation tracking.

## Inventory Map

| Rows | Bucket | Current evidence | Status |
| --- | --- | --- | --- |
| 1-28 | Schema and manifest foundation | `tests/test_sqlite_wal_mode.py`, `tests/test_schema_v1114_amendments.py`, `tests/test_manifest_binder.py`, `tests/test_register_manifests.py`, `tests/test_policy_security_audit.py` | Covered |
| 29-48 | Model fingerprint and ModelGateway | `tests/test_register_model_fingerprint.py`, `tests/test_model_fingerprint_guard.py`, `tests/test_model_gateway.py`, `tests/test_model_gateway_wrapper.py` | Covered for local contract; live current-profile path is satisfied by the approved Phase 7 readiness material |
| 49-56 | PlanInjectionScanner contract and enum domains | `tests/test_plan_injection_scanner.py`, `tests/test_plan_artifact_scanner_service.py`, `tests/test_policy_security_audit.py` | Covered |
| 57-67 | PolicyEngine and ManifestBinder behavior | `tests/test_policy_engine.py`, `tests/test_manifest_binder.py`, `tests/test_boot_verifier.py` | Covered |
| 68-83 | Database foreign keys, indexes, and enum domains | `tests/test_schema_v1114_amendments.py`, `tests/test_repositories.py`, `tests/test_task_permissions.py`, `tests/test_plan_artifacts.py`, `tests/test_bootstrap_validation.py`, `tests/test_policy_security_audit.py` | Covered |
| 84-92 | CLI behavior and registration hardening | `tests/test_register_manifests.py`, `tests/test_register_model_fingerprint.py` | Partial: Rows 84 and 85 require explicit under-30-second CLI timing evidence. |
| 93-100 | Boot logging and network policy edge validation | `tests/test_boot_verifier.py`, `tests/test_manifest_binder.py`, `tests/test_register_manifests.py` | Covered |
| 101-108 | Operator manifest and tool-map final integration rows | `tests/test_phase6_operator_command_manifests.py`, `tests/test_manifest_binder.py`, `tests/test_policy_security_audit.py`, `tests/test_register_manifests.py` | Covered |

## State-Aware E2E Status

Pre-readiness state:

```text
Rows 84 and 85 require explicit under-30-second CLI timing evidence.
tests/e2e/test_full_goal_flow_minimum.py is present as a bounded local gate-selection artifact.
full-goal E2E is blocked until classifier calibration approval material exists.
full-goal E2E is blocked until model fingerprint registration is complete.
```

Post-readiness accepted state:

```text
acceptance_inventory_passed = true
e2e_ready = true
e2e_blockers = []
e2e_test_present = true
executed = true
passed = true
final mapped acceptance run: 130 passed in 23.08s
```

The accepted post-readiness proof satisfies the previously named blockers:

```text
approved live classifier calibration run present
current model fingerprint tied to approved calibration present
safe-pass readiness enabled in latest session
explicit operator approval material supplied
```

## Authority Boundary

The accepted Phase 7 proof does not expand runtime authority:

```text
autonomous_operation_enabled remains false / 0
no autonomous operation is authorized
no scheduler-to-agent automation is authorized
no scheduler-to-executor automation is authorized
no live Telegram service is authorized by Phase 7
```

## Audit

Run:

```text
python tools\audit_phase7_acceptance_inventory.py
python tools\audit_phase7_acceptance_inventory.py --json
```

The audit verifies:

```text
canonical acceptance row count
contiguous row IDs
bucket ranges
mapped test files
named CLI timing gap
named full-goal E2E blockers and their accepted post-readiness state
```


## Source Section: Phase 7B Acceptance Runner

## Phase 7B Acceptance Runner

## Scope

Phase 7B adds a bounded acceptance runner and prerequisite report. By default,
it does not enable safe-pass, autonomous execution, live Telegram, live model
calls, classifier calibration writes, model fingerprint registration, or
full-goal E2E execution.

The runner is:

```text
tools\run_phase7_acceptance.py
```

Terminal command:

```text
axiom-phase7-acceptance
```

## Default Behavior

Default mode is read-only reporting:

```text
python tools\run_phase7_acceptance.py
python tools\run_phase7_acceptance.py --json
```

It reports:

```text
Phase 7A inventory status
canonical mapped pytest modules
classifier calibration prerequisite status
current model fingerprint prerequisite status
safe-pass readiness status
full-goal E2E blockers
```

## Running The Mapped Acceptance Suite

Run the mapped non-E2E acceptance suite:

```text
python tools\run_phase7_acceptance.py --run
```

This runs the canonical test modules mapped from the 108 v1.13 acceptance rows.
It does not include `tests/e2e/test_full_goal_flow_minimum.py`.

## Full-Goal E2E Gate

The full-goal E2E path is state-aware. In the pre-readiness state, it remains
blocked unless all of the following are true:

```text
classifier calibration approval material exists
approved live passing calibration run is stored in classifier_calibration_runs
current model fingerprint registration exists against that live calibration run
safe-pass readiness decision is positive
tests/e2e/test_full_goal_flow_minimum.py exists
explicit operator approval flag is supplied
```

The explicit approval can be supplied for a one-shot run with
`--operator-approved-e2e`, or recorded as operational readiness material with
`tools\approve_phase7_e2e_readiness.py` after the calibration and model
fingerprint prerequisites pass.

Even when requested with `--include-e2e`, the runner refuses the E2E test when
any blocker remains.

In the accepted post-readiness state, those blockers are satisfied:

```text
approved live classifier calibration run present
current model fingerprint tied to approved calibration present
safe-pass readiness enabled in latest session
explicit operator approval material supplied
```

The current accepted proof is:

```text
acceptance_inventory_passed = true
e2e_ready = true
e2e_blockers = []
e2e_test_present = true
executed = true
passed = true
final mapped acceptance run: 130 passed in 23.08s
```

## Calibration Approval Material

Dry-run calibration material:

```text
python tools\run_calibration.py --calibration-set-path axiom\policy\security_artifacts\calibration_set.json --target-model qwen3:4b --target-host http://localhost:11434 --calibration-run-id injection_classifier_v1_YYYY_MM_DD
```

Dry-run and simulation mode do not write Phase 7 readiness material and cannot
satisfy the full-goal E2E gate.

Approved calibration DB write requires the existing explicit token:

```text
python tools\run_calibration.py --live --write-db --calibration-set-path axiom\policy\security_artifacts\calibration_set.json --target-model qwen3:4b --target-host http://localhost:11434 --calibration-run-id injection_classifier_v1_YYYY_MM_DD --approved-by-panel-version phase4_calibration_manual_approval
```

The approval token is intentionally not supplied by the runner. Stored
calibration rows must carry live provenance in `details_json`; approved
simulation rows are reported as blockers.

## Model Fingerprint Registration Material

After a passing calibration run exists, candidate registration material is:

```text
python tools\register_model_fingerprint.py --host http://localhost:11434 --model qwen3:4b --profile-label default --calibration-run-id injection_classifier_v1_YYYY_MM_DD --registration-status candidate
```

Current registration material is:

```text
python tools\register_model_fingerprint.py --host http://localhost:11434 --model qwen3:4b --profile-label default --calibration-run-id injection_classifier_v1_YYYY_MM_DD --registration-status current
```

The registration tool still enforces calibration presence, model/host match,
Ollama reachability, quantization details, and thinking-mode constraints.

## Readiness Approval Material

After the approved passing calibration and current model fingerprint are both
present, record the bounded readiness decision:

```text
python tools\approve_phase7_e2e_readiness.py --approval-token phase7_e2e_operator_approval --enable-safe-pass --approve-e2e
```

This enables safe-pass on the latest session and records the operator approval
event for final full-goal E2E selection. It does not enable autonomous
operation and does not run the E2E test.

## Authority Boundary

The accepted Phase 7 run is acceptance evidence only:

```text
autonomous_operation_enabled remains false / 0
no autonomous operation is authorized
no scheduler-to-agent automation is authorized
no scheduler-to-executor automation is authorized
no live Telegram service is authorized by Phase 7
```


## Source Section: Phase 7C Full-Goal E2E Gate Audit

## Phase 7C Full-Goal E2E Gate Audit

## Scope

Phase 7C verifies that the final full-goal E2E path remains gated before
readiness material exists and becomes ready only after all readiness material is
present. The audit does not run the full-goal E2E test, enable safe-pass,
perform classifier calibration, register model fingerprints, or create runtime
shortcuts.

Audit command:

```text
python tools\audit_phase7_e2e_gate.py
python tools\audit_phase7_e2e_gate.py --json
```

Terminal command:

```text
axiom-phase7-e2e-gate
```

## Gate Rules

The audit verifies:

```text
default Phase 7 acceptance report does not execute tests
default Phase 7 acceptance report does not select the E2E test
--include-e2e without explicit operator approval is blocked
blocked E2E requests do not execute pytest
blocked E2E requests do not add tests/e2e/test_full_goal_flow_minimum.py
blocked E2E requests report named blockers
explicit operator approval remains mandatory
```

## State-Aware Expected State

Pre-readiness state:

```text
gate_status: blocked
e2e_ready: false
```

Expected pre-readiness blockers include:

```text
no approved live passing calibration run present
no current model fingerprint with matching approved passing calibration present
safe-pass is not enabled in latest session
explicit operator approval for full-goal E2E not supplied
```

If a calibration row was produced by simulation or lacks live provenance in
`details_json`, the gate treats it as blocked even when the approval token is
present.

Accepted post-readiness state:

```text
acceptance_inventory_passed = true
e2e_ready = true
e2e_blockers = []
e2e_test_present = true
executed = true
passed = true
final mapped acceptance run: 130 passed in 23.08s
```

The accepted state is backed by:

```text
approved live classifier calibration run present
current model fingerprint tied to approved calibration present
safe-pass readiness enabled in latest session
explicit operator approval material supplied
```

## Boundary

This audit proves the gate behavior. It is not the approval action. Calibration
approval material and model fingerprint registration material remain documented
in `docs\phase7.md`.

The accepted Phase 7 proof does not authorize autonomous operation,
scheduler-to-agent automation, scheduler-to-executor automation, or a live
Telegram service. `autonomous_operation_enabled` remains false / 0.


## Source Section: Phase 7 E2E Readiness Approval

## Phase 7 E2E Readiness Approval

## Scope

`tools\approve_phase7_e2e_readiness.py` records the remaining operator material
needed before the final full-goal E2E path can be selected.

It performs three bounded state changes only after prerequisite material is
already present:

```text
enable safe-pass on the latest session
record phase7_safe_pass_readiness_enabled in session_events
record phase7_full_goal_e2e_approved in session_events
```

It also records an informational security event. It does not enable autonomous
operation, run Telegram, call external providers, register model fingerprints,
write calibration results, or execute the final E2E test.

## Required Prerequisites

The tool refuses approval unless:

```text
classifier_calibration_runs has a passing row approved by phase4_calibration_manual_approval
model_profile_fingerprints has a current row tied to that calibration
the latest session exists and autonomous_operation_enabled remains 0
tests\e2e\test_full_goal_flow_minimum.py exists
```

## Command

```text
python tools\approve_phase7_e2e_readiness.py --approval-token phase7_e2e_operator_approval --enable-safe-pass --approve-e2e
python tools\approve_phase7_e2e_readiness.py --approval-token phase7_e2e_operator_approval --enable-safe-pass --approve-e2e --json
```

After this succeeds, `tools\run_phase7_acceptance.py --json` should report
`e2e_ready: true` while still reporting `executed: false` unless `--run` is
explicitly supplied. The final full-goal E2E run remains a separate action.


## Source Section: Phase 7D Terminal Visibility

## Phase 7D Terminal Visibility

## Scope

Phase 7D adds compact terminal visibility for Phase 7 acceptance and full-goal
E2E readiness. It does not execute pytest, enable safe-pass, approve classifier
calibration, register model fingerprints, run live model calls, or run the
full-goal E2E path. It also does not authorize autonomous operation,
scheduler-to-agent automation, scheduler-to-executor automation, or a live
Telegram service.

Terminal command:

```text
axiom-phase7
```

Backing module:

```text
ui\terminal\modules\60-phase7.ps1
```

## Operator Surface

The panel reports:

```text
Phase 7A inventory status
canonical mapped test count
whether the acceptance runner executed
Phase 7C E2E gate status
full-goal E2E blockers
calibration, fingerprint, and safe-pass prerequisite status
next required material
```

## Boundary

The panel calls only:

```text
python tools\run_phase7_acceptance.py --json
python tools\audit_phase7_e2e_gate.py --json
```

Those are report-mode calls. The panel intentionally does not pass `--run`,
`--include-e2e`, or `--operator-approved-e2e`.

## Report-Only Mode

The terminal panel remains report-only. It shows the runner report and isolated
gate audit output without passing execution or approval flags.

In pre-readiness state, expected output includes:

```text
gate_status: blocked
e2e_ready: false
runner executed: false
```

The pre-readiness operator-visible blockers are:

```text
approved classifier calibration run
current model fingerprint tied to approved calibration
safe-pass readiness decision
tests\e2e\test_full_goal_flow_minimum.py
explicit operator approval for full-goal E2E
```

## Accepted Phase 7 Proof

The accepted post-readiness Phase 7 proof is:

```text
acceptance_inventory_passed = true
e2e_ready = true
e2e_blockers = []
e2e_test_present = true
executed = true
passed = true
final mapped acceptance run: 130 passed in 23.08s
```

The satisfied prerequisites are:

```text
approved live classifier calibration run present
current model fingerprint tied to approved calibration present
safe-pass readiness enabled in latest session
explicit operator approval material supplied
```

The accepted proof does not change the panel boundary:

```text
autonomous_operation_enabled remains false / 0
no autonomous operation is authorized
no scheduler-to-agent automation is authorized
no scheduler-to-executor automation is authorized
no live Telegram service is authorized by Phase 7
```


## Source Section: Phase 7E Closeout And Hardening Audit

## Phase 7E Closeout And Hardening Audit

Phase 7 is implemented through 7E as an acceptance, prerequisite, and
full-goal E2E gate surface for `AXIOM_Implementation_v1.13.md`.

## Implemented Surface

- 7A: `tools\audit_phase7_acceptance_inventory.py` maps the 108 canonical MVP acceptance rows from `1..108`.
- 7B: `tools\run_phase7_acceptance.py` builds the mapped acceptance suite and prerequisite report.
- 7C: `tools\audit_phase7_e2e_gate.py` verifies the final full-goal E2E path stays blocked until all material is present and becomes ready after the material is accepted.
- 7D: `axiom-phase7` reports Phase 7 acceptance and E2E gate state in the terminal UI.
- 7E: `tools\audit_phase7_closeout.py` aggregates the Phase 7 hardening checks.

## State-Aware Gate State

The default Phase 7 acceptance runner remains a report unless explicitly invoked
with `--run`.

Pre-readiness state:

- runner executed: false
- gate_status: blocked
- E2E test path: `tests\e2e\test_full_goal_flow_minimum.py`

Current blockers reported by the gate:

- no approved passing calibration run present
- no current model fingerprint with matching approved passing calibration present
- safe-pass is not enabled in latest session
- explicit operator approval for full-goal E2E not supplied

Accepted post-readiness state:

```text
acceptance_inventory_passed = true
e2e_ready = true
e2e_blockers = []
e2e_test_present = true
executed = true
passed = true
final mapped acceptance run: 130 passed in 23.08s
```

The accepted state satisfies the prerequisites:

```text
approved live classifier calibration run present
current model fingerprint tied to approved calibration present
safe-pass readiness enabled in latest session
explicit operator approval material supplied
```

## Boundary

No state-changing enablement was performed by the Phase 7E closeout audit.

The closeout audit does not approve classifier calibration, register model
fingerprints, enable safe-pass, promote a model profile, run live model calls,
run Telegram runtime, or execute the full-goal E2E path.

The later approved readiness and final mapped acceptance run are acceptance
evidence only:

```text
autonomous_operation_enabled remains false / 0
no autonomous operation is authorized
no scheduler-to-agent automation is authorized
no scheduler-to-executor automation is authorized
no live Telegram service is authorized by Phase 7
```

## Operator Material

The material that was required before readiness was:

- classifier calibration approval material using `phase4_calibration_manual_approval`
- current model fingerprint tied to the approved passing calibration
- safe-pass readiness decision
- explicit operator approval for full-goal E2E

That material is now present for the accepted Phase 7 proof.

The bounded E2E artifact now exists at
`tests\e2e\test_full_goal_flow_minimum.py`. It uses local temporary database
state as a bounded local gate-selection artifact and does not mutate the
operational database.

## Subsequent Readiness Approval Slice

The bounded readiness path is implemented in
`tools\approve_phase7_e2e_readiness.py`. It can enable safe-pass on the latest
session and record `phase7_full_goal_e2e_approved` only after approved
calibration and a current matching model fingerprint exist. It still does not
enable autonomous operation or execute the final full-goal E2E test.

## Verification

Run:

```powershell
python tools\audit_phase7_closeout.py
python tools\audit_phase7_closeout.py --json
axiom-phase7-closeout
```

The audit should report `passed: True`, `runner executed: false`, and
`gate_status: blocked` in isolated pre-readiness gate mode. The accepted
post-readiness full-goal E2E proof reports `e2e_ready = true`, no E2E blockers,
and `130 passed in 23.08s`.



