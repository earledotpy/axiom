# Phase 7B Acceptance Runner

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
