# Phase 7A Acceptance Inventory

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
