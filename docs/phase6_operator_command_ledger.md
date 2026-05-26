# Phase 6D Operator Command Ledger

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
