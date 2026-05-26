# Phase 6E Terminal Operator Control Visibility

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
