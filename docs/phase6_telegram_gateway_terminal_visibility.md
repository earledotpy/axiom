# Phase 6H Telegram Gateway Terminal Visibility

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
