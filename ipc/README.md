# AXIOM IPC Channel

Shared message directory for cross-agent communication between Claude Code, Codex, and Antigravity.

## Phase 0 Freeze

Active IPC execution is structurally frozen pending future Orchestrator mediation. Watchers, executor dispatch, CLI agent invocation, ConPTY/tmux/terminal paths, posture daemons, markdown inbox control reads, and peer-to-peer auto-relay paths must remain fail-closed under `IPC_PHASE0_FREEZE_ACTIVE`.

## Protocol

Each agent has an inbox file. To send a message, write to the recipient's inbox.
To reply, write to the sender's inbox. Prefix each entry with a timestamp and sender tag.

| File | Written by | Read by |
|------|-----------|---------|
| `to_codex.md` | Claude Code, Antigravity, Jeremy | Codex |
| `to_antigravity.md` | Claude Code, Codex, Jeremy | Antigravity |
| `to_claude.md` | Codex, Antigravity, Jeremy | Claude Code |

## Message format

```
---
FROM: <sender>
TO: <recipient>
TIME: <YYYY-MM-DD HH:MM>
SUBJECT: <one line>

<body>
```

## Delivery

Messages are not pushed automatically — the recipient needs to be pointed here.
Standard handoff phrase: "Check `ipc/to_<you>.md` for a message."
