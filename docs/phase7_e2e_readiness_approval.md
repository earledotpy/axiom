# Phase 7 E2E Readiness Approval

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
