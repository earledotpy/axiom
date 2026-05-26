# AXIOM Phase 6C Local Operator Command Parser

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
