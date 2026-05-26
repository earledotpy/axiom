# AXIOM Phase 6 Entry Gate And Scope Lock

## Status

Phase 6A is the authorized entry-gate slice for Phase 6.

This document does not authorize runtime implementation beyond local
documentation, verification, and read-only terminal visibility.

## Entry Checklist

Before any later Phase 6 implementation slice starts, all of the following must
be true:

```text
Jeremy explicitly authorizes the bounded slice.
Phase 5 closeout docs remain current.
Phase 5 agent boundary audit passes.
Foundation verification passes.
Task lifecycle audit passes.
Task execution audit passes.
Policy/security audit passes.
The proposed slice names exact files, tools, tests, and rollback.
The proposed slice does not enable autonomous operation.
The proposed slice does not connect external chat or Telegram runtime.
```

## Preserved Prohibitions

Phase 6A preserves these prohibitions:

```text
autonomous operation
safe-pass enablement
scheduler-to-agent automation
scheduler-to-executor automation
real model calls
cloud cascade calls
network fetches
sandbox execution
memory writes
Telegram bot runtime
external command ingestion
agent task creation
child task commits
operator command execution from external adapters
```

## Approved Phase 6 Command Taxonomy

The Phase 6 operator control plane may define command classes only within this
taxonomy unless Jeremy explicitly approves an amendment.

```text
read_only_status
read_only_audit
read_only_queue_inspection
read_only_task_inspection
local_intent_record
local_intent_reject
local_intent_authorization_marker
design_only_external_adapter
```

Denied command classes:

```text
autonomous_enablement
safe_pass_enablement
model_profile_promotion
gateway_runtime_call
network_runtime_call
sandbox_runtime_call
memory_write_runtime_call
scheduler_start
agent_execution
external_command_execution
```

## Rollback Plan

Phase 6A rollback is documentation-only:

```text
remove docs\phase6_entry_gate.md
remove Phase 6A references from docs\phase6_roadmap.md
remove phase6-entry-gate from ui\terminal\modules\52-docs.ps1
remove tests\test_phase6_entry_gate_doc.py
rerun focused docs tests
rerun axiom-preflight
```

Later Phase 6 slices must define their own rollback steps before implementation.

## 6B Authorization Boundary

The next implementation slice may add only the read-only operator status
manifest unless Jeremy explicitly approves a broader command set.

State-changing operator commands remain outside the 6B boundary.

## Verification Commands

Use this verification chain before and after each Phase 6 slice:

```text
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py
python tools\audit_agent_boundary.py
pytest tests\test_phase6_entry_gate_doc.py -v
```

Run full `pytest tests -v` before Phase 6 closeout.

## Exit Criteria For 6A

6A is complete when:

```text
the entry checklist is documented
the preserved prohibitions are documented
the command taxonomy is documented
the rollback plan is documented
the verification command list is documented
focused tests pass
axiom-preflight passes
```
