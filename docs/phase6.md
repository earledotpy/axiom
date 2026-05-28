# AXIOM Phase 6

Canonical consolidated Phase 6 documentation. This file supersedes the former Phase 6 slice documents while preserving their implementation evidence, safety boundaries, and closeout material.

## Consolidated Sections
- Phase 6 Roadmap Implementation Plan
- Phase 6A Entry Gate And Scope Lock
- Phase 6B Operator Command Manifest Set
- Phase 6C Local Operator Command Parser
- Phase 6D Operator Command Ledger
- Phase 6E Terminal Operator Control Visibility
- Phase 6F External Adapter Design Packet
- Phase 6G Telegram Gateway Runtime Foundation
- Phase 6H Telegram Gateway Terminal Visibility
- Phase 6I Closeout And Hardening Audit
- Phase 6J Telegram Bot Polling Adapter

## Source Section: Phase 6 Roadmap Implementation Plan

## AXIOM Phase 6 Roadmap Implementation Plan

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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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
docs\phase6.md
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


## Source Section: Phase 6A Entry Gate And Scope Lock

## AXIOM Phase 6 Entry Gate And Scope Lock

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
remove docs\phase6.md
remove Phase 6A references from docs\phase6.md
remove phase6 from ui\terminal\modules\52-docs.ps1
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


## Source Section: Phase 6B Operator Command Manifest Set

## AXIOM Phase 6B Operator Command Manifest Set

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


## Source Section: Phase 6C Local Operator Command Parser

## AXIOM Phase 6C Local Operator Command Parser

## Status

Phase 6C adds a local-only parser for operator command intent.

The parser does not execute commands and does not write the command ledger.

## Implemented Surface

```text
axiom\core\operator_command_parser.py
tools\parse_operator_command.py
tests\test_phase6_operator_command_parser.py
```

Accepted command forms:

```text
status
/status
{"command": "status", "payload": {}}
```

The parser loads local operator-control manifests and accepts only commands that
are manifest-bound, read-only, and non-task-creating.

## Rejection Reasons

The parser fails closed for:

```text
empty_command
unsupported_input_type
command_parse_error
command_field_missing_or_invalid
command_payload_must_be_object
command_payload_not_allowed
unknown_operator_command
operator_command_not_read_only
operator_command_creates_task
```

## Boundary

Phase 6C does not authorize:

```text
operator command execution
operator command ledger writes
Telegram runtime
external command ingestion
autonomous operation
safe-pass enablement
scheduler control
agent execution
task creation
model calls
network fetches
sandbox execution
memory writes
filesystem writes
```

## Verification

Use:

```text
python tools\parse_operator_command.py status --json
python tools\parse_operator_command.py resume --json
pytest tests\test_phase6_operator_command_parser.py -v
```


## Source Section: Phase 6D Operator Command Ledger

## Phase 6D Operator Command Ledger

## Scope

Phase 6D records local operator command intent before any runtime action exists.
It does not authorize, execute, schedule, dispatch, call models, call networks,
write memory, run sandbox code, or enable Telegram runtime.

## Implemented Boundary

```text
operator command parser -> accepted manifest-bound intent -> operator_control task
operator_control task -> operator_commands row
authorization_status = pending
command_status = pending
runtime_action_executed = false
```

Unknown or unsafe commands remain parser rejections and are not written to
`operator_commands` because they have no approved operator-control manifest.

## Artifacts

```text
axiom\core\operator_command_ledger.py
tools\record_operator_command_intent.py
tools\audit_operator_command_ledger.py
ui\terminal\modules\58-operator-commands.ps1
```

## Operator Intent Record

Accepted command intent creates:

```text
tasks.task_class = operator_control
tasks.task_type = operator_command_intent
tasks.status = pending
tasks.manifest_id = operator.status.v1
operator_commands.authorization_status = pending
operator_commands.command_status = pending
```

The ledger write requires:

```text
an accepted local parser result
an active operator_control manifest fingerprint
an active local AXIOM session
```

## Audit

The read-only audit checks:

```text
operator command rows link to operator_control intent tasks
task manifest_id matches operator_commands manifest_id
manifest row is active operator_control with matching command_name
Phase 6D rows remain pending/pending
command payload JSON is an object
pending command rows link to pending tasks
```

Run:

```text
python tools\audit_operator_command_ledger.py
python tools\audit_operator_command_ledger.py --json
```

## Terminal UI

`axiom-operator-commands` is read-only. It queries `axiom.db` with SQLite
`mode=ro` and shows counts plus the latest command intent rows. It does not
call `tools\record_operator_command_intent.py`.

## Preserved Prohibitions

Phase 6D still prohibits:

```text
autonomous operation
safe-pass enablement
scheduler-to-agent automation
real model calls
cloud cascade calls
network fetches
sandbox execution
memory writes
Telegram bot runtime
external command ingestion
agent task creation
child task commits
```


## Source Section: Phase 6E Terminal Operator Control Visibility

## Phase 6E Terminal Operator Control Visibility

## Scope

Phase 6E makes operator command intent visible in the AXIOM Terminal without
adding any shortcut that records, authorizes, or executes commands.

## Implemented Surface

```text
axiom-operator-commands
axiom-operator-command-audit
axiom-preflight step 6
axiom-terminal-report operator control visibility section
axiom-help / axiom-help-all visibility entries
axiom-doctor command/tool coverage
axiom-docs agent navigation entry
```

## Boundary

`axiom-operator-commands` is read-only and queries SQLite with `mode=ro`.

`axiom-operator-command-audit` runs:

```text
python tools\audit_operator_command_ledger.py
```

No terminal command calls:

```text
tools\record_operator_command_intent.py
axiom.core.operator_command_ledger.record_operator_command_intent
scheduler execution
agent execution
model gateways
network gateways
sandbox gateways
memory writes
Telegram runtime
```

## Operator Value

The operator can now answer these questions from the terminal:

```text
Are there operator command intents in the ledger?
How many are pending, authorized, or rejected?
Are ledger rows still Phase 6D-safe pending intent rows?
Is the terminal command registry aware of the operator control surface?
Does preflight include the operator command ledger audit?
```

## Acceptance

```text
operator can see pending/rejected/authorized command intents
preflight runs the read-only operator command ledger audit
terminal report includes operator control visibility
registry/help/doctor/docs expose only read-only inspection and audit
no direct shortcuts enable unsafe runtime behavior
```


## Source Section: Phase 6F External Adapter Design Packet

## Phase 6F External Adapter Design Packet

## Status

This is a design packet only. It does not authorize external adapter runtime,
network listeners, Telegram bot startup, webhook registration, polling loops,
external command ingestion, or command execution.

## Design Objective

Define the future external operator-control adapter boundary before any network
surface is implemented. The adapter may later receive chat or Telegram messages,
but it must reduce every external input to a local, manifest-bound operator
command intent and must fail closed before any runtime action.

## Preserved Phase 6 Prohibitions

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

## Future Entry Points

These names are reserved for a later authorized implementation slice. They do
not exist as runtime code in 6F.

```text
ExternalAdapter.receive_message(envelope)
ExternalAdapter.authenticate_sender(envelope)
ExternalAdapter.normalize_command(envelope)
ExternalAdapter.reject_message(envelope, reason)
ExternalAdapter.request_operator_confirmation(intent_id)
ExternalAdapter.record_confirmed_intent(intent_id)
```

Future CLI/tool names are also reserved only:

```text
tools\external_adapter_design_check.py
tools\telegram_adapter_smoke_test.py
tools\chat_adapter_smoke_test.py
```

No file above is implemented in 6F.

## Envelope Contract

Any future adapter must convert platform messages into this local envelope
before parsing:

```json
{
  "adapter": "telegram_or_chat",
  "platform_message_id": "platform-stable-id",
  "platform_sender_id": "platform-stable-sender-id",
  "platform_chat_id": "platform-stable-chat-id",
  "received_at": "RFC3339 timestamp",
  "command_text": "status",
  "raw_text_sha256": "sha256 of raw text",
  "raw_text_length": 6
}
```

Raw text may be accepted by the adapter process, but downstream logs and
operator-facing denials should prefer hashes, lengths, command names, and
reasons instead of storing full untrusted message bodies.

## Authentication And Whitelist Requirements

All future external messages must pass these checks before parsing:

```text
adapter_enabled_by_local_config = true
platform_sender_id is in local operator whitelist
platform_chat_id is in local allowed chat whitelist
message timestamp is inside allowed clock skew window
message id has not been processed before
message text length is within configured ceiling
transport secret or platform signature is valid when the platform provides one
```

Default behavior:

```text
missing whitelist -> deny: external_sender_not_whitelisted
missing chat allowlist -> deny: external_chat_not_allowed
missing adapter enable flag -> deny: external_adapter_disabled
missing signature on signed transport -> deny: external_signature_missing
invalid signature -> deny: external_signature_invalid
```

Jeremy remains the Operator and final authority. Concrete platform IDs are not
defined in this repository slice; a later implementation must require explicit
local configuration before accepting any external sender.

## Rate Limit And Replay Protection

Required future controls:

```text
per_sender_message_limit_per_minute
per_chat_message_limit_per_minute
global_adapter_message_limit_per_minute
dedupe table keyed by adapter + platform_message_id
short replay cache keyed by raw_text_sha256 + platform_sender_id + received_at bucket
max_command_text_length
max_rejection_events_per_window
```

Denial modes:

```text
rate_limit_sender_exceeded
rate_limit_chat_exceeded
rate_limit_global_exceeded
replay_message_id_seen
replay_payload_seen
command_text_too_long
```

Replay denials must not create operator command ledger rows unless a later
manifest explicitly authorizes rejected-intent recording.

## Operator Confirmation Model

Future external command handling must be two stage:

```text
stage 1: receive external message and parse local command intent
stage 2: require local operator confirmation before any ledger write or action
```

For Phase 6-compatible behavior:

```text
read-only status may be parsed but still requires local confirmation before ledger write
state-changing commands remain denied before parse because no manifests authorize them
external adapters may not authorize their own commands
confirmation must happen through a local approved surface
confirmation expiry must be short and explicit
```

Reserved confirmation statuses:

```text
confirmation_required
confirmation_expired
confirmation_rejected
confirmation_accepted
```

## Future Local Flow

The only acceptable future flow is:

```text
external envelope
-> authenticate sender
-> rate limit and replay check
-> normalize command text
-> local OperatorCommandParser.parse(...)
-> if accepted, create pending confirmation request
-> if locally confirmed, call record_operator_command_intent(...)
-> do not execute runtime action
```

The adapter must not call:

```text
scheduler dispatch
agent execution
model_gateway.call
network_gateway.fetch
sandbox_gateway.execute
memory_gateway.write
session_controller.enable_autonomous
session_controller.resume
session_controller.cancel_current_chain
```

## Denial Modes

Every future denial must include a stable reason code:

```text
external_adapter_disabled
external_sender_not_whitelisted
external_chat_not_allowed
external_signature_missing
external_signature_invalid
external_timestamp_out_of_window
external_payload_malformed
external_payload_too_large
external_command_empty
external_command_unknown
external_command_payload_not_allowed
external_command_not_manifest_bound
external_confirmation_required
external_confirmation_expired
external_confirmation_rejected
external_runtime_action_forbidden
external_replay_detected
external_rate_limited
```

Denials should be visible through future read-only audits, not through direct
runtime shortcuts.

## Implementation Gate For Any Later Adapter Code

Before adapter code is written, Jeremy must explicitly approve:

```text
selected platform: Telegram, local chat, or both
exact local config file path for whitelist and adapter enable flag
platform sender IDs and chat IDs
transport authentication mechanism
rate limits
confirmation surface
whether rejected external attempts are ledgered or audit-only
rollback steps
focused tests
```

Until that approval exists, the only valid Phase 6F deliverable is this design
packet plus tests that verify the packet is indexed and remains design-only.


## Source Section: Phase 6G Telegram Gateway Runtime Foundation

## Phase 6G Telegram Gateway Runtime Foundation

## Scope

Phase 6G adds a local Telegram gateway boundary for already-received
Telegram-shaped envelopes. It does not start a Telegram bot, poll Telegram,
register webhooks, send Telegram messages, execute operator commands, or enable
autonomous operation.

The gateway is disabled by default in `config\axiom.yaml`.

Later Phase 6J adds an explicit operator-invoked Telegram polling adapter, but
that adapter is separate from this local gateway foundation. No default
Telegram service/runtime is authorized by Phase 6 or Phase 7.

## Runtime Boundary

The gateway accepts a local `TelegramEnvelope` and applies these checks before
any operator-command ledger write is possible:

```text
gateway enabled
message shape and length
replay by adapter + platform_message_id
per-sender, per-chat, and global rate limits
operator whitelist
chat whitelist
capability_token_sha256 verification
operator command manifest parser
external confirmation request
```

Capability tokens are never stored. The config stores only SHA-256 hashes in
`telegram_gateway.capability_token_sha256`. Confirmation tokens are returned
once to the caller and persisted only as SHA-256 hashes.

## Persistence

Phase 6G adds two storage tables:

```text
external_adapter_messages
external_confirmation_requests
```

`external_adapter_messages` records Telegram adapter decisions, raw command
text hash, command length, short command text, platform sender/chat IDs, replay
identity, and denial reason.

`external_confirmation_requests` records pending, accepted, rejected, and
expired confirmation state. A command ledger row is created only after a pending
confirmation token is accepted.

## Confirmation Workflow

Accepted Telegram envelopes move to `confirmation_required`.

Only `TelegramGateway.confirm_intent(...)` can turn a pending confirmation into
a Phase 6 operator-command ledger record. That ledger record remains pending and
does not execute any runtime action:

```text
runtime_action_executed = false
ledger_written = true
authorization_status = pending
command_status = pending
```

Rejected and expired confirmations do not write the operator-command ledger.

## Audit

Run:

```text
python tools\audit_telegram_gateway.py
python tools\audit_telegram_gateway.py --json
```

The audit checks config shape, plaintext secret drift, enabled gateway
whitelist requirements, schema table presence, confirmation integrity, and
absence of implicit execution.

## Remaining Unauthorized Default Runtime Work

Phase 6G does not include default service/runtime enablement for:

```text
Telegram polling
Telegram webhooks
Telegram outbound replies
network client lifecycle
multi-command runtime expansion
terminal command shortcuts for external ingestion
automatic execution after confirmation
```

The explicit polling adapter remains manual-only. Confirmed command intents
remain pending and non-executing.


## Source Section: Phase 6H Telegram Gateway Terminal Visibility

## Phase 6H Telegram Gateway Terminal Visibility

## Scope

Phase 6H adds read-only AXIOM Terminal visibility for the Phase 6G Telegram
gateway foundation.

It does not add Telegram polling, webhooks, outbound replies, envelope
processing shortcuts, confirmation shortcuts, or operator-command execution.
It also does not start or supervise the explicit Telegram polling adapter.

## Terminal Surface

New command:

```text
axiom-telegram-gateway
```

The panel reports:

```text
gateway enabled/disabled posture
operator whitelist count
allowed chat count
capability hash count
rate-limit settings
confirmation expiry setting
plaintext token config drift
external adapter message totals
pending and expired confirmation counts
recent pending confirmations
recent external adapter decisions
```

The panel reads:

```text
config\axiom.yaml
axiom.db via SQLite mode=ro
```

## Operator Value

The operator can answer the useful questions without opening the database:

```text
Is the Telegram gateway enabled?
Is it configured with whitelist and token hashes?
Are there pending confirmations?
Are external messages being rejected, accepted, or waiting for confirmation?
Is there evidence of config secret drift?
```

## Preserved Boundary

The terminal panel must not call:

```text
TelegramGateway.process_envelope(...)
TelegramGateway.confirm_intent(...)
tools\record_operator_command_intent.py
Telegram network APIs
scheduler, agent, model, network, sandbox, or memory runtime tools
```

Runtime mutation remains confined to approved runtime/tool entrypoints and
their tests.

The Phase 6J polling adapter, when used, remains an explicit manual operator
command outside the terminal registry. Phase 7 safe-pass readiness does not
authorize autonomous operation, automatic execution, or a default live Telegram
service.


## Source Section: Phase 6I Closeout And Hardening Audit

## Phase 6I Closeout And Hardening Audit

## Status

Phase 6 is implemented through 6I as a bounded operator-control foundation.
The system remains:

```text
fail_closed_non_autonomous
safe-pass readiness may be enabled only for bounded Phase 7 E2E readiness
autonomous_operation_enabled = False
no automatic scheduler-to-agent integration
no automatic scheduler-to-executor integration
no default Telegram service/runtime enablement
```

## v1.13 Alignment

The Phase 6 source requirements in `AXIOM_Implementation_v1.13.md` are covered
as follows:

```text
Implement Telegram Gateway after operator whitelist mechanism is specified.
  Covered by Phase 6G local Telegram envelope gateway, disabled-by-default config,
  operator whitelist, chat whitelist, hashed capability tokens, replay storage,
  rate-limit storage, and external confirmation records.

Implement CommandParser and OperatorControlInserter.
  Covered by Phase 6C local OperatorCommandParser and Phase 6D operator command
  ledger insertion through record_operator_command_intent.

Enforce operator-control manifests and capability-token boundaries.
  Covered by operator_control manifest registration, parser binding, ledger
  manifest checks, Telegram capability_token_sha256 verification, and audits.
```

## Hardened Boundaries

Implemented hardening:

```text
operator command parsing is local-only
unknown commands fail closed
operator command ledger rows remain pending
runtime_action_executed = false
Telegram gateway is disabled by default
Telegram capability tokens are stored only as hashes
confirmation tokens are stored only as hashes
external adapter replay identity is persisted
rate limits are persisted and enforced before command confirmation
terminal Telegram panel reads SQLite mode=ro only
terminal surfaces do not expose confirmation or ingestion shortcuts
```

## Terminal Cognitive Load Audit

Useful operator information now surfaced:

```text
operator command ledger totals and latest command intents
Telegram gateway enabled/disabled posture
Telegram whitelist and capability hash counts
Telegram rate-limit settings
pending confirmation count
expired confirmation count
recent external adapter decisions
Phase 6 operator and Telegram audits in preflight
```

Redundancy accepted for now:

```text
axiom-preflight, axiom-terminal-report, axiom-help, and axiom-docs all reference
the same Phase 6 audit surfaces.
```

This is acceptable at closeout because those surfaces answer different operator
questions: run health, suite inventory, command recall, and file navigation.

Deferred refactor opportunity:

```text
centralize terminal command metadata rendering so help, doctor, report, docs,
and registry do not duplicate Phase 6 command names manually.
```

## Deferred Default Runtime Work

Not authorized as default service/runtime enablement:

```text
live Telegram polling
webhook registration
outbound Telegram replies
terminal envelope ingestion shortcut
terminal confirmation shortcut
automatic execution after confirmation
multi-command state-changing operator controls
autonomous operation
safe-pass enablement as Phase 6 runtime authority
```

Phase 6J added an explicit operator-invoked Telegram polling adapter, but it is
not a default service and it does not execute runtime actions. Safe-pass
readiness may be enabled by bounded Phase 7 E2E approval only; autonomous
operation and automatic execution remain disabled.

## Closeout Audit

Run:

```text
python tools\audit_phase6_closeout.py
python tools\audit_phase6_closeout.py --json
```

The audit checks:

```text
v1.13 Phase 6 source alignment
required Phase 6 artifacts
current roadmap status
Telegram disabled-by-default posture
absence of live Telegram runtime terms
read-only terminal gateway surface
non-mutating terminal registry entries
operator cognitive-load section bounds
explicit deferred runtime work
```

## Phase 6 Recommendation

Phase 6 can be treated as functionally complete for the local operator-control
foundation once the closeout audit and full regression suite pass.

Later Phase 7 E2E readiness/passing and the Phase 6J explicit polling adapter
do not change the closeout boundary: no autonomous operation, no automatic
execution, no scheduler-to-agent automation, no scheduler-to-executor
automation, and no default live Telegram service are authorized.


## Source Section: Phase 6J Telegram Bot Polling Adapter

## Phase 6J Telegram Bot Polling Adapter

## Scope

`tools\run_telegram_polling_adapter.py` is an explicit live Telegram Bot API
polling entrypoint. It is intentionally separate from
`axiom\gateways\telegram_gateway.py`, which remains the local fail-closed
gateway boundary.

The adapter can poll Telegram updates when the operator invokes it directly,
convert approved text messages into
`TelegramEnvelope` objects, call the existing gateway, and send bounded status
replies. It does not execute runtime actions, enable autonomous operation,
create scheduler work, or bypass the confirmation workflow.

It is not a default service, not a scheduler-launched runtime, and not authority
for scheduler-to-agent or scheduler-to-executor automation. Phase 7 safe-pass
readiness, when enabled for bounded E2E acceptance, does not change this
Telegram boundary.

## Required Environment

The bot token is read only from the environment:

```text
TELEGRAM_BOT_TOKEN
```

Do not store the bot token or plaintext capability token in `config\axiom.yaml`.
The config stores only `capability_token_sha256`.

## Message Formats

Submit a command:

```text
/axiom <capability-token> /status
```

Confirm a pending command intent:

```text
/axiom-confirm <capability-token> <confirmation-token>
```

Reject a pending command intent:

```text
/axiom-reject <capability-token> <confirmation-token>
```

The adapter checks the configured operator whitelist, chat whitelist, capability
token hash, replay storage, and rate limits before command intent can move
through the gateway.

## Commands

Poll once:

```text
python tools\run_telegram_polling_adapter.py --once --json
```

Run a development loop:

```text
python tools\run_telegram_polling_adapter.py --loop --json
```

This is not wired into the terminal command registry. Starting a live Bot API
poller remains an explicit operator action and is not authorized as a default
service/runtime by Phase 6 or Phase 7.




