# AXIOM Phase 6 Roadmap Implementation Plan

## Status

Phase 6 is in bounded implementation. Slices 6A through 6I are implemented
locally and preserve the fail-closed, non-autonomous posture.

Phase 6 must preserve the current AXIOM posture until Jeremy explicitly
authorizes each bounded implementation slice:

```text
fail_closed_non_autonomous
safe-pass readiness may be enabled only for bounded Phase 7 E2E readiness
autonomous_operation_enabled = False
no automatic scheduler-to-agent integration
no automatic scheduler-to-executor integration
no default Telegram service/runtime enablement
```

## Phase 6 Objective

Build the operator control plane foundation without enabling autonomous
operation. Phase 6 should make operator intent auditable, manifest-bound, and
terminal-visible before any external chat or Telegram surface is connected.
The local Telegram gateway foundation, the explicit Telegram polling adapter,
and default service/runtime enablement are separate boundaries.

## Implementation Map

### 6A. Entry Gate And Scope Lock

Deliverables:

```text
Phase 6 entry checklist
explicit preserved prohibitions
approved command taxonomy
rollback plan
verification command list
```

Artifact:

```text
docs\phase6_entry_gate.md
```

Acceptance:

```text
Phase 5 audits pass
Phase 6 docs name exact boundaries
no runtime mutation path is added
```

### 6B. Operator Command Manifest Set

Deliverables:

```text
read-only operator command manifest set
command identity and alias policy
manifest registration tests
policy-security audit coverage
```

Artifact:

```text
docs\phase6_operator_command_manifests.md
axiom\policy\operator_control_manifests\status.v1.json
```

Acceptance:

```text
registered manifests validate
operator commands bind one command each
no role manifest declares operator commands
only read-only status command is implemented in 6B
```

### 6C. Local Operator Command Parser

Deliverables:

```text
local parser for approved command names
structured command payload validation
rejection reasons for unknown or unsafe commands
tests for allowed and denied inputs
```

Artifact:

```text
docs\phase6_operator_command_parser.md
axiom\core\operator_command_parser.py
tools\parse_operator_command.py
```

Acceptance:

```text
parser is local-only
parser does not execute runtime actions
unknown commands fail closed
```

### 6D. Operator Command Ledger

Deliverables:

```text
append-only command intent records
authorization status lifecycle
terminal read-only inspection
audit coverage for malformed ledger rows
```

Artifacts:

```text
docs\phase6_operator_command_ledger.md
axiom\core\operator_command_ledger.py
tools\record_operator_command_intent.py
tools\audit_operator_command_ledger.py
ui\terminal\modules\58-operator-commands.ps1
```

Acceptance:

```text
operator intent is recorded before action
ledger writes require approved local tool
terminal UI remains read-only
```

### 6E. Terminal Operator Control Visibility

Deliverables:

```text
compact operator command status panel
doctor/report/registry coverage
docs navigation entries
preflight read-only audit hook
```

Artifacts:

```text
docs\phase6_terminal_operator_control_visibility.md
ui\terminal\modules\20-axiom-tools.ps1
ui\terminal\modules\50-terminal-report.ps1
ui\terminal\modules\52-docs.ps1
ui\terminal\modules\58-operator-commands.ps1
ui\terminal\modules\90-safety-help.ps1
ui\terminal\registry\axiom-terminal-command-registry.json
```

Acceptance:

```text
operator can see pending/rejected/authorized command intents
no direct shortcuts enable unsafe runtime behavior
```

### 6F. External Adapter Design Packet

Deliverables:

```text
Telegram/chat adapter design only
authentication and whitelist requirements
rate limit and replay protection plan
operator confirmation model
```

Artifact:

```text
docs\phase6_external_adapter_design.md
```

Acceptance:

```text
no network adapter code yet unless separately authorized
design names exact future entrypoints and denial modes
```

### 6G. Telegram Gateway Runtime Foundation

Deliverables:

```text
disabled-by-default Telegram gateway config
runtime operator and chat whitelist checks
hashed capability-token verification
external adapter replay and rate-limit storage
external confirmation request workflow
read-only Telegram gateway audit
```

Artifacts:

```text
docs\phase6_telegram_gateway_runtime_foundation.md
config\axiom.yaml
axiom\gateways\telegram_gateway.py
tools\audit_telegram_gateway.py
```

Acceptance:

```text
gateway processes only local envelopes
no default Telegram polling service, webhook, or outbound network service is added
operator-command ledger write requires confirmation token acceptance
confirmed ledger rows remain pending and non-executing
```

### 6H. Telegram Gateway Terminal Visibility

Deliverables:

```text
read-only Telegram gateway terminal panel
compact config posture summary
pending confirmation visibility
recent external adapter decision visibility
doctor/report/help/registry coverage
```

Artifacts:

```text
docs\phase6_telegram_gateway_terminal_visibility.md
ui\terminal\modules\59-telegram-gateway.ps1
ui\terminal\modules\49-doctor.ps1
ui\terminal\modules\50-terminal-report.ps1
ui\terminal\modules\52-docs.ps1
ui\terminal\modules\90-safety-help.ps1
ui\terminal\registry\axiom-terminal-command-registry.json
```

Acceptance:

```text
terminal panel reads config and SQLite mode=ro only
no terminal shortcut processes envelopes or confirms intents
operator can see config posture, pending confirmations, and recent decisions
```

### 6I. Closeout And Hardening Audit

Deliverables:

```text
Phase 6 v1.13 alignment audit
implemented/deferred runtime boundary record
operator cognitive-load audit
read-only closeout audit tool
Phase 6 closeout recommendation
```

Artifacts:

```text
docs\phase6_closeout_hardening_audit.md
tools\audit_phase6_closeout.py
```

Acceptance:

```text
audit verifies required Phase 6 artifacts and boundaries
default live Telegram runtime remains deferred
terminal surfaces remain non-mutating and read-only
Phase 6 can be closed after full verification passes
```

### 6J. Explicit Telegram Bot Polling Adapter

Deliverables:

```text
operator-invoked Telegram Bot API polling adapter
bounded status replies
no runtime action execution
no terminal registry startup shortcut
```

Artifact:

```text
docs\phase6_telegram_bot_polling_adapter.md
tools\run_telegram_polling_adapter.py
```

Acceptance:

```text
polling runs only by explicit operator command
default service/runtime enablement remains unauthorized
confirmed command intents remain pending and non-executing
```

## Explicit Non-Goals

Phase 6 does not authorize:

```text
autonomous operation
safe-pass enablement as Phase 6 runtime authority
scheduler-to-agent automation
scheduler-to-executor automation
real model calls
cloud cascade calls
network fetches
sandbox execution
memory writes
default Telegram bot service/runtime
automatic external command ingestion
agent task creation
child task commits
```

Phase 7 safe-pass readiness may be enabled for bounded E2E readiness only. It
does not authorize autonomous operation, automatic execution, or any default
Telegram runtime.

## Required Verification Cadence

Each bounded Phase 6 slice should run:

```text
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py
python tools\audit_agent_boundary.py
pytest <focused tests> -v
```

Run full `pytest tests -v` before Phase 6 closeout.
