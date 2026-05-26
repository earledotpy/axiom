# CODEX_HANDOFF.md — AXIOM Current Implementation Transfer

Generated for Codex transfer after ChatGPT-based Phase 3 work.

## Current repository

```text
Project root: C:\axiom
Default shell: AXIOM Terminal / PowerShell 7
Python: 3.11.9 previously observed
venv: C:\axiom\venv
pytest: 8.4.2 previously observed
Canonical baseline: AXIOM_Implementation_v1.13.md

Use live output as authoritative.

Current posture

AXIOM is intentionally:

local-first
fail-closed
non-autonomous
autonomous_allowed = False
safe_pass_enabled = False

Do not treat fail-closed autonomous blocking as a failure.

Source priority

Read in this order:

1. AGENTS.md
2. docs/codex/CODEX_HANDOFF.md
3. AXIOM_Implementation_v1.13.md
4. AXIOM_Phase2_Closeout_Handoff_2026-05-21.md
5. Latest generated handoff in logs\
6. Latest project-state snapshot in logs\
7. AXIOM_Implementation_Chat_Source_*.md
8. AXIOM_Terminal_Implementation_Chat_Source_UI.md

The chat-source files are historical implementation records. They do not supersede v1.13 unless Jeremy explicitly says so.

Latest operator-reported state

Jeremy reported:

tests/test_phase2_closeout_doc.py -> 4 passed
full regression passed after first Phase 3 policy/security audit slice
full regression passed after integrating policy_security_audit into verification/reporting

Do not assume an exact test count. Run pytest tests -v.

Phase 2 completed work

Phase 2 covered:

StateMachine
Scheduler
TaskCommitter
SupervisorMonitor
ContextBuilder
TokenEstimator
ResourceLimitEvaluator
lifecycle audits
execution audits
manual no-op execution harness
manual no-op staging
manual scheduler-dispatched no-op cycle
execution readiness reporting
operator command indexing
snapshot/handoff reporting
Phase 2 closeout documentation

Important files from Phase 2 include:

axiom/core/execution_readiness.py
tools/execution_readiness_check.py
tests/test_execution_readiness.py

axiom/core/noop_task_stager.py
tools/stage_noop_task.py
tests/test_noop_task_stager.py

axiom/core/noop_task_executor.py
tools/execute_noop_task.py
tests/test_noop_task_executor.py

axiom/core/manual_noop_cycle.py
tools/run_manual_noop_cycle.py
tests/test_manual_noop_cycle.py

axiom/core/task_execution_audit.py
tools/audit_task_execution.py
tests/test_task_execution_audit.py

docs/phase2_closeout.md
tests/test_phase2_closeout_doc.py

Manual no-op cycle remains manual/test-only.

Phase 3 completed work in this chat
Slice 1 — Read-only policy/security audit

Added:

axiom/core/policy_security_audit.py
tools/audit_policy_security.py
tests/test_policy_security_audit.py

Purpose:

Read-only security audit around:
- active tool_capability_map row
- tool_capability_map SHA matching file
- manifest schema presence
- tool map schema presence
- active manifest files exist
- active manifest SHA values match
- ManifestBinder initializes
- PolicyEngine initializes
- PlanInjectionScanner enum domains match DB CHECK domains
- security_events table coverage
Slice 2 — Verification/reporting integration

Integrated policy security audit into:

tools/verify_foundation.py
tools/snapshot_project_state.py
tools/generate_handoff.py
tools/operator_command_index.py
tests/test_verify_foundation.py
tests/test_snapshot_project_state.py
tests/test_generate_handoff.py
tests/test_operator_command_index.py

Expected output now includes:

policy_security_audit:
checked: True
passed: True
checked_count: <N>
violation_count: 0

Generated handoff should include:

## Policy Security Audit

- Checked: `True`
- Passed: `True`
- Checked count: `<N>`
- Violation count: `0`
First commands for Codex to run
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1

git status
python -m py_compile tools\verify_foundation.py tools\snapshot_project_state.py tools\generate_handoff.py tools\operator_command_index.py
python -m py_compile axiom\core\policy_security_audit.py tools\audit_policy_security.py

pytest tests\test_policy_security_audit.py -v
pytest tests\test_verify_foundation.py tests\test_snapshot_project_state.py tests\test_generate_handoff.py tests\test_operator_command_index.py -v
pytest tests -v

python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py

Then get latest session and run supervisor health:

@'
from axiom.persistence.db import get_connection

with get_connection() as conn:
    row = conn.execute(
        """
        SELECT session_id
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row["session_id"] if row else "")
'@ | python

Then:

python tools\supervisor_health_check.py <SESSION_ID>

Do not type angle brackets literally.

Expected healthy result
foundation_passed: True
operational_mode: fail_closed_non_autonomous
autonomous_allowed: False
safe_pass_enabled: False
fail_closed_coherent: True
task_lifecycle_audit passed
task_execution_audit passed
policy_security_audit passed
supervisor_health_ok

execution_readiness.ready: False is acceptable after the manual no-op cycle if the only reason is:

no_pending_manifest_bound_task
Known model profile state

Expected local profile:

model_name = qwen3:4b
ollama_host = http://localhost:11434
quantization = Q4_K_M
thinking_mode = unknown
thinking_mode_rule_version = gateway_required_v1
calibration_run_id = pending_calibration
is_current = 0
registration_status = candidate

This is correct for the current host. Do not promote it.

Next safe implementation options

Prefer one of these:

Option A — Harden policy security audit coverage

Add focused tests/checks for additional fail-closed security-event coverage, without writing events or repairing state.

Possible targets:

ManifestBinder verify_file_integrity failure path
PolicyEngine missing required policy object denial
PlanInjectionScanner persistence contract
tool-capability map required command/operator-control cross-field checks
Option B — Add generated handoff/source update for Phase 3

Create a source record documenting:

policy_security_audit implementation
verify_foundation/snapshot/handoff/operator-command-index integration
latest regression result
prohibited next steps

Possible files:

docs/phase3_security_audit_handoff.md
tests/test_phase3_security_audit_handoff.py
Option C — Add read-only manifest completeness audit expansion

Extend policy_security_audit to verify active role/operator manifests meet mandatory policy object completeness without registering/repairing anything.

Do not do next

Do not implement:

autonomous operation
safe-pass enablement
classifier calibration approval
model profile promotion
real model calls
network fetches
sandbox process execution
Telegram/operator control
agent layer
automatic scheduler-to-executor integration
persistent scheduler service
Implementation habits

Use small patches. Targeted tests first. Full regression after integration-sensitive changes.

Do not use remembered test counts.

Do not weaken invariants to pass tests.

Do not patch canonical schema casually.

Do not put PowerShell here-string markers inside Python files.

Do not use INSERT OR REPLACE against manifest_fingerprints.
