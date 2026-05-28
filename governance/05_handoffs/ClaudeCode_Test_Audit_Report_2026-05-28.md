# AXIOM Test Suite Audit Report

**From**: Claude Code (Governance Auditor)
**Date**: 2026-05-28
**Suite state at time of audit**: 579 tests, all passing

---

## Purpose

Classify all current test modules by load-bearing value at the current AXIOM development stage (Phase 9 complete, fail_closed_non_autonomous, manual-noop execution integrated). Identify which tests are essential regression guards and which are low-value or testing features not yet authorized.

---

## Summary

| Category | Modules | Tests |
|---|---|---|
| Essential — boot chain and DB | 5 | ~15 |
| Essential — policy/manifest | 3 | ~37 |
| Essential — state machine/persistence | 4 | ~22 |
| Essential — task lifecycle | 9 | ~53 |
| Essential — scheduler/noop | 6 | ~42 |
| Essential — readiness gates | 4 | ~10 |
| Essential — gateway fail-closed | 9 | ~111 |
| Essential — plan scanner | 2 | ~13 |
| Essential — resource/model tracking | 6 | ~28 |
| Essential — agent layer (no-runtime paths) | 6 | ~24 |
| Essential — operator control plane | 10 | ~58 |
| Essential — monitoring/status | 5 | ~18 |
| Essential — foundation verification | 2 | ~10 |
| Essential — dev tools (tested) | 3 | ~16 |
| Low-value — doc content assertions | 3 | ~14 |
| Low-value — dev QoL tooling | 3 | ~16 |
| Low-value — meta/infra | 2 | ~5 |
| Stale — closed-phase doc checks | 2 | ~7 |
| **Total** | **84** | **579** |

Essential: ~541 tests (93%). Low-value/stale: ~42 tests (7%).

---

## Essential Tests — Must Keep

### Boot chain and DB integrity
| Module | What it protects |
|---|---|
| `test_sqlite_wal_mode.py` | WAL + synchronous=FULL + foreign_keys are set and enforced |
| `test_schema_v1114_amendments.py` | Schema version marker and structural invariants |
| `test_boot_verifier.py` | Boot manifest re-verification logic |
| `test_bootstrap_validation.py` | Full BootstrapValidator gate (pragma + schema + vec table + fingerprints) |
| `test_bootstrap_check_cli.py` | CLI exit codes and JSON shape |

### Policy and manifest
| Module | What it protects |
|---|---|
| `test_policy_engine.py` | All 7 authorization-chain steps; allowed and denied paths |
| `test_manifest_binder.py` | Schema validation, SHA256, semantic rules, tool-ID map |
| `test_policy_security_audit.py` | 15-check policy audit (standard tools, session_controller bindings, operator_control rules) |

### State machine and persistence
| Module | What it protects |
|---|---|
| `test_state_machine.py` | Allowed/denied transitions; terminal-state finality |
| `test_repositories.py` | CRUD contracts for sessions, tasks, manifests |
| `test_task_permissions.py` | Permissions table FK and uniqueness |
| `test_plan_artifacts.py` | Plan artifact storage and retrieval |

### Task lifecycle (7 + service + audit)
| Module | What it protects |
|---|---|
| `test_task_committer.py` | Manifest-ID guard, one-running invariant, heartbeat ordering |
| `test_task_starter.py` | Start path + audit integrity |
| `test_task_completer.py` | Completion path and terminal-state finality |
| `test_task_failer.py` | Failure path |
| `test_task_canceller.py` | Cancellation path |
| `test_task_lifecycle_guard.py` | Transition guard wiring |
| `test_task_lifecycle_service.py` | Facade delegation |
| `test_task_lifecycle_audit.py` | Audit logic |
| `test_audit_task_lifecycle_cli.py` | CLI |

### Scheduler and no-op execution
| Module | What it protects |
|---|---|
| `test_scheduler_foundation.py` | Count helpers, RunningTaskInvariant |
| `test_scheduler_dispatcher.py` | FIFO dispatch, one-running guard |
| `test_scheduler_tick.py` | Gated tick: readiness → repair → dispatch → audit |
| `test_scheduler_run_once.py` | Single-tick result shape |
| `test_scheduler_loop.py` | Bounded loop + automatic no-op completion (Phase 9) |
| `test_noop_task_stager.py` | Staged task preconditions |
| `test_noop_task_executor.py` | No-op run→complete, no gateway calls |
| `test_manual_noop_cycle.py` | Manual test-override cycle path |
| `test_task_execution_audit.py` | Execution audit pass/fail contract |

### Readiness gates
| Module | What it protects |
|---|---|
| `test_autonomous_gate.py` | autonomous_gate blocks without trusted profile |
| `test_execution_readiness.py` | Execution readiness check battery |
| `test_bootstrap_autonomous_readiness.py` | Boot-level autonomy check |
| `test_bootstrap_check_operational_mode.py` | Operational mode detection |

### Gateway fail-closed (all disabled features must stay denied)

These test the prohibition enforcement, not the features. They must remain even though the features are not authorized — they are the primary proof that gateways are fail-closed.

| Module | What it protects |
|---|---|
| `test_model_gateway.py` | `think=True` rejection; ModelGatewayDisabledError |
| `test_model_gateway_wrapper.py` | Cloud cascade policy checks; fake-HTTP dry-run |
| `test_memory_gateway.py` | Batch cap, sqlite-vec invariants, real-ops gate, deny paths |
| `test_network_gateway.py` | Allowlist enforcement, NetworkAccessDeniedError |
| `test_sandbox_gateway.py` | Job Object limits, SandboxExecutionDeniedError |
| `test_cloud_cascade_smoke_test.py` | CLI wrapper dry-run by default |
| `test_memory_gateway_smoke_test.py` | CLI wrapper dry-run by default |
| `test_network_gateway_smoke_test.py` | CLI wrapper dry-run by default |
| `test_sandbox_gateway_smoke_test.py` | CLI wrapper dry-run by default |

### Plan scanner
| Module | What it protects |
|---|---|
| `test_plan_injection_scanner.py` | Disposition matrix with `safe_pass_enabled=False`; stub scan always-pass contract |
| `test_plan_artifact_scanner_service.py` | Service wiring: scan → disposition → task transition |

### Resource and model tracking
| Module | What it protects |
|---|---|
| `test_resource_usage.py` | Usage row contract |
| `test_resource_limits.py` | Limit breach → task transition |
| `test_resource_accounting_integration.py` | Accounting integration |
| `test_provider_usage.py` | Provider usage row contract |
| `test_provider_usage_lifecycle.py` | Provider usage across task lifecycle |
| `test_model_fingerprint_guard.py` | Fingerprint guard blocks unregistered models |
| `test_register_model_fingerprint.py` | Fingerprint registration |
| `test_ollama_prereq.py` | Ollama prereq check gates model calls |
| `test_run_calibration.py` | Calibration pipeline structure (needed when scanner stubs are replaced) |

### Agent layer — no-runtime paths

Phase 5 agents are implemented as manual-only stubs. These tests prove no runtime calls occur — they are the fail-closed proof for the agent layer.

| Module | What it protects |
|---|---|
| `test_goal_planner.py` | Planner produces plan; zero model/tool/network calls |
| `test_task_planner.py` | Same |
| `test_tool_executor.py` | Same |
| `test_result_verifier.py` | Same |
| `test_agent_boundary_audit.py` | Read-only audit passes; detects runtime-call drift |
| `test_phase5_agent_cli.py` | CLI blocks without override; with override, zero runtime calls |

### Operator control plane

The Telegram gateway and operator command infrastructure are implemented as manual/explicit-only. These tests verify the fail-closed posture of the control plane.

`test_operator_command_index.py`, `test_phase6_operator_command_parser.py`, `test_phase6_operator_command_ledger.py`, `test_phase6_operator_command_manifests.py`, `test_phase6_external_adapter_design.py`, `test_phase6_telegram_bot_polling_adapter.py`, `test_phase6_telegram_gateway.py`, `test_phase6_telegram_gateway_terminal_visibility.py`, `test_phase6_terminal_operator_control_visibility.py`, `test_phase6_closeout_hardening_audit.py`

### Monitoring and status
`test_status_report.py`, `test_supervisor_monitor.py`, `test_supervisor_monitor_active_task.py`, `test_supervisor_health_check_cli.py`, `test_repair_session_state.py`

### Foundation verification
`test_verify_foundation.py`, `test_test_db_isolation.py`

### Developer tools with runtime coupling
These test tools that interact with the DB or lifecycle system — their tests catch regressions in the tool CLI contracts.

`test_register_manifests.py`, `test_context_builder.py`, `test_token_estimator.py`

---

## Phase 7 Tests — Keep With Note

The Phase 7 acceptance gate logic is still active as the authoritative E2E readiness check. These tests remain load-bearing:

| Module | Status |
|---|---|
| `test_phase7_acceptance_runner.py` | Keep — acceptance runner logic is still invoked |
| `test_phase7_acceptance_inventory.py` | Keep — inventory structure check |
| `test_phase7_e2e_gate_audit.py` | Keep — gate audit enforces preconditions |
| `test_phase7_e2e_readiness_approval.py` | Keep — operator approval token contract |

---

## Low-Value Tests — Flag for Future Removal

These tests pass but provide little regression value at the current stage. They should not be deleted without deliberation, but they are candidates for the next cleanup slice.

### Doc content assertions (fragile, test docs not runtime)

| Module | Tests | Issue |
|---|---|---|
| `test_historical_docs.py` | 7 | Checks specific phrases in consolidated doc files. Breaks on any doc update, even correct ones. Value: keeps docs honest, but brittle. |
| `test_scheduler_executor_boundary_doc.py` | 4 | Checks boundary content in `phase2.md`. Phase 9 has implemented the boundary — this is now historical. Passes only because phase2.md still contains the pre-Phase-9 boundary text. |
| `test_phase7_closeout.py` | 4 | Doc content check for phase7 closeout. Phase 7 is closed. |
| `test_phase7_terminal_visibility.py` | 3 | Terminal UI doc check for a closed phase. |

**Recommendation:** These 18 tests could be dropped in a future cleanup slice. They do not protect runtime behavior.

### Developer QoL tooling (not runtime-coupled)

| Module | Tests | Issue |
|---|---|---|
| `test_generate_handoff.py` | 7 | Tests handoff document generation tool. Useful for catching handoff-tool regressions but not runtime behavior. |
| `test_generate_handoff_bundle.py` | 3 | Same. |
| `test_snapshot_project_state.py` | 6 | Tests project state snapshot tool. Low coupling to runtime. |

**Recommendation:** Acceptable to keep if the tools are actively used. Not a priority to remove.

### Meta / infra tests

| Module | Tests | Issue |
|---|---|---|
| `test_test_inventory.py` | 3 | Tests a utility that counts collected test items. Meta-test with minimal regression value. |
| `e2e/test_full_goal_flow_minimum.py` | 2 | Full E2E goal-flow minimum — tests the E2E gate selection logic. This may be more valuable than it looks; keep pending further review. |

---

## Stale Coverage Gaps (not excess tests, but missing tests)

At this stage, two implemented modules have stub logic with no test coverage of the real behavior they will eventually perform:

1. **`_run_additional_check` in `policy_engine.py`** — always returns `True`. No tests for gateway-specific checks (filesystem root, network allowlist, sandbox limit enforcement) because they are not yet implemented.
2. **`PlanInjectionScanner.scan()`** — deterministic and classifier scans always pass. Tests cover the disposition matrix but not real scan logic.

These are coverage gaps to address when the stubs are replaced, not cleanup targets now.

---

## Recommended Actions

| Priority | Action |
|---|---|
| Now | None — suite is clean, all 579 pass |
| Next cleanup slice | Remove `test_historical_docs.py`, `test_scheduler_executor_boundary_doc.py`, `test_phase7_closeout.py`, `test_phase7_terminal_visibility.py` (18 tests, doc-only) |
| When stubs are replaced | Add real scan logic tests to `test_plan_injection_scanner.py`; add gateway-check tests to `test_policy_engine.py` |
| Optional | Review `test_generate_handoff.py`, `test_generate_handoff_bundle.py`, `test_snapshot_project_state.py` if those tools are retired |
