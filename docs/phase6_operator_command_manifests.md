# AXIOM Phase 6B Operator Command Manifest Set

## Status

Phase 6B adds the first operator-control manifest set.

The implemented set is intentionally read-only:

```text
operator.status.v1 -> status -> session_controller.status
```

## Included Manifest

```text
axiom\policy\operator_control_manifests\status.v1.json
```

The manifest permits:

```text
command_name: status
effect_class: read_only
allowed_tools: session_controller.status
allowed_commands: status
allowed_when_autonomous_disabled: true
allowed_when_safe_pass_disabled: true
```

## Preserved Denials

Phase 6B does not add manifests for:

```text
cancel_current_chain
pause_after_current
resume
shutdown_after_current
run_classifier_validation
enable_autonomous
reconcile_provider_usage
```

Those commands are state-changing, calibration/reconciliation-related, or
autonomy-related and require later explicit authorization.

## Runtime Boundary

The status manifest does not authorize:

```text
Telegram runtime
external command ingestion
autonomous operation
safe-pass enablement
scheduler control
agent execution
task creation
model calls
cloud cascade calls
network fetches
sandbox execution
memory reads or writes
filesystem reads or writes
```

## Verification

Use:

```text
python tools\register_manifests.py
python tools\audit_policy_security.py
pytest tests\test_phase6_operator_command_manifests.py -v
```
