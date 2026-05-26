# Phase 6G Telegram Gateway Runtime Foundation

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
