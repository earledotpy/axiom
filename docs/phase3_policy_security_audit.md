# AXIOM Phase 3 Policy Security Audit

## Status

Phase 3 is active and remains inside the policy/security layer.

AXIOM remains:

```text
fail_closed_non_autonomous
autonomous_allowed = False
safe_pass_enabled = False
```

This document records the implemented read-only policy/security audit boundary. It does not authorize autonomous operation, safe-pass enablement, model profile promotion, classifier calibration approval, real model calls, network fetches, sandbox execution, memory embedding writes/query, Telegram/operator control execution, agent-layer execution, persistent scheduler service, or automatic scheduler-to-executor integration.

## Implemented audit surface

The current policy/security audit is implemented in:

```text
axiom/core/policy_security_audit.py
tools/audit_policy_security.py
tests/test_policy_security_audit.py
```

The audit is read-only. It verifies policy files, registered manifest fingerprints, active artifact SHA values, `ManifestBinder` initialization, `PolicyEngine` initialization, tool-capability map semantics, scanner/schema enum coherence, scanner return-contract stability, expected schema domains, and `security_events` table coverage.

The current Phase 3 expansion also verifies active role/operator manifests and fail-closed security contracts:

```text
tool_capability_map_semantic_contracts
active_policy_manifests_validate_schema_and_policy
active_policy_manifest_rows_match_payload_identity
role_manifests_do_not_declare_operator_control_commands
operator_control_manifests_bind_single_command
plan_injection_scanner_return_contract_is_stable
security_events_table_supports_audit_coverage
```

These checks use existing validators and policy contracts. They also assert active manifest row-to-payload identity for manifest ID, manifest type, role name, operator-control command name, and expected policy subdirectory. They assert security-event severity/index/foreign-key coverage without writing events. They do not repair manifests, register manifests, write security events, or mutate runtime authority.

The tool-capability semantic contract now also verifies exact standard-tool bindings:

```text
standard tool source paths match expected policy objects
standard tool additional_checks match expected enforcement checks
standard tools do not declare operator-control command bindings
session_controller tools bind one schema-valid operator command each
```

## Current expected proof

The current healthy proof for this slice is:

```text
python -m py_compile axiom\core\policy_security_audit.py tests\test_policy_security_audit.py
pytest tests\test_policy_security_audit.py -v
pytest tests -v
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py
python tools\supervisor_health_check.py <SESSION_ID>
```

Expected result shape:

```text
policy_security_audit passed
checked_count: 15
violation_count: 0
foundation_passed: True
operational_mode: fail_closed_non_autonomous
autonomous_allowed: False
safe_pass_enabled: False
fail_closed_coherent: True
task_lifecycle_audit passed
task_execution_audit passed
supervisor_health_ok
```

Replace `<SESSION_ID>` with the latest live session ID. Do not type angle brackets literally.

## Preserved boundaries

The Phase 3 policy/security audit must remain read-only unless Jeremy explicitly approves a new bounded implementation step.

This slice does not authorize:

```text
autonomous operation
safe-pass enablement
model profile promotion
classifier calibration approval
real Ollama /api/chat or /api/generate calls
real cloud model/provider calls
real NetworkGateway fetches
real SandboxGateway process execution
real MemoryGateway embedding writes/query
Telegram/operator control execution
agent layer
persistent scheduler service
automatic scheduler-to-executor integration
terminal shortcuts that mutate runtime state directly
register_manifests.py automatic execution
```

## Next safe work

The next safe Phase 3 work should remain read-only or fail-closed. Candidate slices are:

```text
additional tool-capability map semantic checks
additional ManifestBinder negative coverage
additional PolicyEngine authorization-path coverage
generated handoff/reporting refresh after each verified slice
```

Do not weaken invariants to make tests pass. Patch code and tests to the canonical schema and contracts.
