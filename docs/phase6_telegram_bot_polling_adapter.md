# Phase 6J Telegram Bot Polling Adapter

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
