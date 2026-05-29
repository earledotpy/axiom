# AXIOM IPC Channel

Shared message directory for cross-agent communication between Claude Code, Codex, and Antigravity.

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
