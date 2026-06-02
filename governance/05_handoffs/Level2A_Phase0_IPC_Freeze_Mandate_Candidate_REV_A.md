# Level2A_Phase0_IPC_Freeze_Mandate_Candidate

**Status:** Candidate only. Not signed. Not authority-bearing. No doctrine change authorized.
**Candidate ID:** `MND-CANDIDATE-2026-0001-REV-A`
**Target Level:** Level 2A pre-implementation containment
**Terminal State Authorized:** `VERIFIED_EVIDENCE_RECORDED` or `AUDIT_FAILED`
**Terminal State Not Authorized:** `VERIFIED_COMMIT`

---

## 1. Purpose

This mandate candidate authorizes a narrowly bounded Phase 0 containment slice for AXIOM’s IPC layer.

The purpose is to establish a current baseline, halt active IPC watcher/executor services, freeze unsafe agent-to-agent execution paths, preserve evidence, and add regression tests proving that IPC cannot execute shell commands, invoke CLI agents, or create peer-to-peer execution authority.

This mandate candidate does not authorize Orchestrator construction, cryptographic Mandate tooling, verifier-account implementation, live-spine doctrine transition, autonomy, model calls, gateway activation, or any Level 2A acceptance claim.

---

## 2. Governing Intent

AXIOM remains **non-autonomous by design**.

This mandate candidate exists to reduce unsafe development-infrastructure risk before Level 2A implementation proceeds.

IPC may remain as historical evidence or inert review material. IPC must not remain as an active execution bus.

For Phase 0, the chosen containment posture is:

```text
FULL WATCHER / EXECUTOR HALT
```

not:

```text
NOTIFICATION-ONLY LIVE MODE
```

Notification-only mode may be reconsidered later only behind a deterministic Orchestrator and signed Mandate model. It is not authorized in this Phase 0 slice.

---

## 3. Scope

The implementer may work only on Phase 0 IPC containment.

Scope includes:

1. Inventory every file under:

```text
$AXIOM_WORKSPACE/ipc/
```

2. Classify every IPC file as one of:

```text
executor
watcher
startup_launcher
transport
database_index
notification_only
historical_inbox
probe_or_scratch
documentation_or_evidence
unknown
```

3. Identify every active or re-armable execution path involving:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
body-driven call operator usage
Start-Process from message body
codex exec
agy --print
Invoke-ConPtyCaptureHosted
ConPTY-mediated agent execution
auto-send-to-from_agent relay
FileSystemWatcher-triggered dispatch
IPC database pending-message dispatch
startup script auto-launch
```

4. Halt or disable active IPC watcher/executor behavior.

5. Preserve markdown inbox files only as evidence or inert review material.

6. Prevent markdown inbox files from being read by active background scripts during the freeze.

7. Add tests proving unsafe execution paths are halted.

8. Produce a Phase 0 evidence artifact using tokenized paths.

---

## 4. Explicitly Unsafe Execution Mechanisms

The following mechanisms are unsafe for Phase 0 and must be halted, removed from active paths, or made unreachable:

### 4.1 Shell / PowerShell execution

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
scriptblock invocation
body-driven call operator execution
Start-Process driven by IPC message content
```

### 4.2 Codex execution

```text
codex exec
codex exec --sandbox workspace-write
any invocation where IPC message body becomes a Codex prompt
```

### 4.3 Antigravity / Gemini execution

```text
agy --print
Invoke-ConPtyCaptureHosted
ConPTY capture driven by IPC message body
any invocation where IPC message body becomes an Antigravity/Gemini prompt
```

### 4.4 Peer-to-peer relay execution

```text
send.ps1 -To $msg.from_agent
automatic reply routing from executor to sender
agent-to-agent loop through markdown inboxes
agent-to-agent loop through ipc_messages.db
FileSystemWatcher-triggered cross-agent processing
```

---

## 5. Allowed Actions

The implementer may:

1. Inventory all files under `$AXIOM_WORKSPACE/ipc/`.

2. Create a baseline inventory showing:

   * file name;
   * role classification;
   * whether it can execute;
   * whether it can invoke an agent;
   * whether it can read inbox files;
   * whether it can write outbound agent messages;
   * whether it is active, startup-launched, legacy, scratch, or unknown.

3. Modify IPC files only to halt, disable, or make unreachable:

   * watcher loops;
   * executor loops;
   * startup-launched IPC services;
   * shell execution from IPC;
   * Codex execution from IPC;
   * Antigravity/Gemini execution from IPC;
   * automatic send-back relay paths.

4. Add tests proving IPC execution is halted.

5. Add static risk scans as secondary tripwires.

6. Add a small pure disposition helper only if it is durable containment logic, not temporary test scaffolding.

7. Update IPC documentation narrowly to state that active IPC execution is frozen pending future Orchestrator mediation.

8. Create one Phase 0 evidence artifact.

9. Preserve markdown inboxes as historical evidence, provided no active watcher/executor reads them during the freeze.

---

## 6. Blocked Actions

The implementer must not:

1. Build the deterministic Orchestrator.

2. Build Ed25519 signing, sealing, or Mandate-verification tools.

3. Build or activate a signing Console.

4. Implement verifier-account isolation.

5. Claim Level 2A acceptance.

6. Emit or claim `VERIFIED_COMMIT`.

7. Modify live doctrine.

8. Enable autonomous operation.

9. Enable `safe_pass_enabled`.

10. Promote any model profile.

11. Activate model calls.

12. Activate cloud calls.

13. Activate network gateway calls.

14. Activate sandbox execution.

15. Activate memory embedding writes or queries.

16. Activate Telegram/operator control execution.

17. Preserve active IPC command execution for convenience.

18. Preserve active inbound IPC invocation of Codex.

19. Preserve active inbound IPC invocation of Antigravity/Gemini.

20. Preserve active peer-to-peer execution loops.

21. Add new watcher services.

22. Add new hidden background execution services.

23. Add new agent-to-agent execution channels.

24. Modify AXIOM runtime policy, manifests, gateway logic, scheduler logic, task lifecycle logic, model logic, memory logic, or database schema outside IPC containment.

25. Store secrets, tokens, private keys, local credentials, or unredacted environment values in evidence.

---

## 7. Files and Artifacts Allowed

### 7.1 Mandatory Full IPC Inventory

The implementer must inventory every file under:

```text
$AXIOM_WORKSPACE/ipc/
```

No IPC file may be skipped because it is believed to be legacy, scratch, probe-only, or inactive.

If any executor or re-armable probe is found outside the known file list, implementation must stop and return for governance review unless the file is clearly inert and can be documented as evidence-only without modification.

### 7.2 IPC Files Allowed for Containment Edits

The implementer may make minimal containment edits to:

```text
ipc/_inbox_claude.ps1
ipc/_inbox_codex.ps1
ipc/_inbox_antigravity.ps1
ipc/loop_watcher.ps1
ipc/agent_bridge.ps1
ipc/ipc_service.ps1
ipc/send.ps1
ipc/ipc_db.py
ipc/startup_claude.ps1
ipc/startup_codex.ps1
ipc/startup_agy.ps1
```

Edits must be limited to halting execution, disabling watcher launch, disabling executor dispatch, preventing active reads from inboxes, preventing outbound agent-directed auto-send, or recording deterministic unsafe disposition.

### 7.3 IPC Files Allowed for Inspection and Classification

The implementer may inspect and classify all other files under:

```text
ipc/
```

including but not limited to:

```text
ipc/conpty_capture.ps1
ipc/watcher_service.ps1
ipc/notify.ps1
ipc/tmux_bridge.ps1
ipc/to_claude.md
ipc/to_codex.md
ipc/to_antigravity.md
ipc/pending_for_claude.md
ipc/*probe*
ipc/*test*
ipc/*hosted*
ipc/*.md
ipc/*.ps1
ipc/*.py
```

If any of these files contain execution logic, startup logic, or re-armable agent invocation logic, they must be identified in the evidence artifact. Modification requires either inclusion under §7.2 or stop-and-return governance review.

### 7.4 Test Files Allowed

The implementer may create focused tests under an appropriate IPC test location, such as:

```text
tests/test_ipc_inventory_complete.py
tests/test_ipc_watchers_halted.py
tests/test_ipc_command_execution_frozen.py
tests/test_ipc_codex_autoinvocation_frozen.py
tests/test_ipc_antigravity_autoinvocation_frozen.py
tests/test_ipc_peer_to_peer_relay_frozen.py
tests/test_ipc_static_execution_tripwires.py
tests/test_ipc_markdown_inboxes_inert.py
```

If the repository convention uses a subdirectory, these may instead be placed under:

```text
tests/ipc/
```

### 7.5 Evidence Artifact Allowed

The implementer may create one evidence artifact:

```text
governance/05_handoffs/Phase0_IPC_Freeze_Evidence.md
```

If governance handoff edits are unavailable or inappropriate in the active implementation environment, use:

```text
docs/phase0_ipc_freeze_evidence.md
```

The evidence artifact must use `$AXIOM_WORKSPACE` instead of raw local paths where possible.

### 7.6 Files Blocked from Modification

The implementer must not modify:

```text
governance/01_live_spine/
governance/06_archives/
axiom/core/
axiom/persistence/
axiom/security/
axiom/gateways/
axiom/app/
axiom/agents/
axiom/policy/
config/axiom.yaml
requirements.txt
```

The implementer also must not create the following unless separately authorized:

```text
tools/seal.py
tools/gatekeeper.py
tools/orchestrator.py
tools/verify_mandate.py
```

---

## 8. Required Containment Behavior

After implementation:

1. No active IPC watcher may read markdown inbox files and trigger processing.

2. No active IPC watcher may read `ipc_messages.db` pending messages and trigger execution.

3. No IPC path may execute a message body as shell or PowerShell.

4. No IPC path may pass a message body to Codex.

5. No IPC path may pass a message body to Antigravity/Gemini.

6. No IPC path may invoke ConPTY capture from message content.

7. No IPC path may auto-send a response to `$msg.from_agent` in a way that creates an agent-to-agent loop.

8. Markdown inboxes may remain only as inert evidence.

9. Any retained IPC code must fail closed, remain unreachable, or produce a deterministic non-executing disposition.

10. Startup scripts must not launch active IPC watcher/executor services during the freeze.

---

## 9. Required Tests

The implementation must provide tests or testable evidence for each of the following.

### 9.1 Inventory completeness

Test or audit proves every file under `$AXIOM_WORKSPACE/ipc/` was inventoried and classified.

### 9.2 Watcher halt

Test proves the following do not start active execution processing:

```text
ipc_service.ps1
loop_watcher.ps1
agent_bridge.ps1
_inbox_claude.ps1
_inbox_codex.ps1
_inbox_antigravity.ps1
startup_claude.ps1
startup_codex.ps1
startup_agy.ps1
```

### 9.3 Shell execution freeze

Test proves IPC content cannot reach:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
body-driven call operator execution
Start-Process from message body
```

### 9.4 Codex auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
codex exec
codex exec --sandbox workspace-write
```

### 9.5 Antigravity/Gemini auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
agy --print
Invoke-ConPtyCaptureHosted
ConPTY-based execution
```

### 9.6 Peer-to-peer relay freeze

Test proves an inbound message produces zero outbound agent-directed sends.

Specifically, no active path may automatically call:

```text
send.ps1 -To $msg.from_agent
```

or equivalent agent-directed response routing.

### 9.7 Markdown inbox inertness

Test or audit proves markdown inbox files are not active control inputs during the freeze.

### 9.8 Static tripwire scan

Add a static tripwire scan for forbidden execution patterns. This scan is secondary evidence only and must not be treated as sufficient by itself.

The forbidden-pattern scan must include at minimum:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
Start-Process
codex exec
agy --print
Invoke-ConPtyCaptureHosted
send.ps1 -To $msg.from_agent
```

If a forbidden string remains in historical or inert code, the test or audit must prove the file is not active and cannot be launched by startup paths during the freeze.

---

## 10. Evidence Required

The implementation handoff must include:

1. Candidate ID:

```text
MND-CANDIDATE-2026-0001-REV-A
```

2. Statement that this is candidate-derived implementation evidence only.

3. Statement that no doctrine change was performed.

4. Statement that no `VERIFIED_COMMIT` claim is made.

5. Full IPC file inventory.

6. Classification table for every IPC file.

7. List of executor files found.

8. List of watcher files found.

9. List of startup-launcher files found.

10. List of transport/database files found.

11. List of markdown inbox files preserved as inert evidence.

12. List of probe/scratch files found.

13. Before/after summary of unsafe execution mechanisms.

14. Files changed.

15. Files inspected but unchanged.

16. Blocked files confirmed untouched.

17. Tests added or updated.

18. Test result summary.

19. Residual risks.

20. Go/no-go recommendation for the next mandate.

Evidence must use tokenized paths such as:

```text
$AXIOM_WORKSPACE/ipc/_inbox_claude.ps1
```

not raw workstation-specific paths unless unavoidable.

If raw local paths appear in tool output, the evidence artifact must summarize them using tokenized paths and must not expose local usernames, secrets, tokens, private keys, active environment values, or machine-specific credentials.

---

## 11. Audit Requirements

The audit section must distinguish:

```text
VERIFIED_EVIDENCE_RECORDED
```

from:

```text
VERIFIED_COMMIT
```

Only `VERIFIED_EVIDENCE_RECORDED` is permitted for a successful Phase 0 outcome.

The audit must explicitly state:

1. AXIOM remains non-autonomous by design.

2. No live-spine doctrine update was made.

3. No Orchestrator was built.

4. No Mandate signing or sealing was built.

5. No verifier-account pathway was built.

6. No CLI agent is granted execution authority by this candidate.

7. IPC execution is frozen, not accepted as Level 2A-compliant.

8. Further work requires a separate mandate candidate.

---

## 12. Go / No-Go Blockers

Implementation must stop and return for governance review if:

1. Any IPC file outside the known executor list contains active execution logic.

2. Any probe/scratch file can invoke Codex, Antigravity/Gemini, ConPTY, shell, or PowerShell execution.

3. Any active path must keep watchers running to pass tests.

4. Any active path must preserve `Invoke-Expression`.

5. Any active path must preserve inbound `codex exec`.

6. Any active path must preserve inbound `agy --print`.

7. Any active path must preserve ConPTY invocation from message body.

8. Any active path must preserve auto-send-to-`from_agent`.

9. Any markdown inbox must remain an active control input.

10. Any test requires modifying files outside the allowed IPC/test/evidence scope.

11. Any implementation requires runtime AXIOM schema changes outside IPC.

12. Any implementation requires Orchestrator construction.

13. Any implementation requires Mandate signing/sealing.

14. Any implementation requires verifier-account setup.

15. Any implementation attempts to claim `VERIFIED_COMMIT`.

16. Any implementation attempts to mark Level 2A accepted.

17. Any implementation attempts to alter doctrine.

18. Any secret, token, private key, credential, or unredacted environment value appears in evidence.

---