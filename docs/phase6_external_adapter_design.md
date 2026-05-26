# Phase 6F External Adapter Design Packet

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
