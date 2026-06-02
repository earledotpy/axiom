# Level2A_Phase0_IPC_Freeze_Mandate_Candidate_REV_B

**Status:** Candidate only. Not signed. Not authority-bearing. No doctrine change authorized.
**Candidate ID:** `MND-CANDIDATE-2026-0001-REV-B`
**Target Level:** Level 2A pre-implementation containment
**Authorized Terminal State:** `VERIFIED_EVIDENCE_RECORDED` or `AUDIT_FAILED`
**Unauthorized Terminal State:** `VERIFIED_COMMIT`

---

## 1. Purpose

This mandate candidate authorizes a narrowly bounded Phase 0 containment slice for AXIOM’s IPC layer.

The purpose is to establish a cryptographically recorded IPC baseline, structurally freeze all unsafe IPC execution paths, halt watcher/executor behavior at source level, prevent re-arm through startup or composed services, preserve evidence, and add regression tests proving that IPC cannot execute shell commands, invoke CLI agents, or create peer-to-peer execution authority.

This mandate candidate does not authorize Orchestrator construction, Ed25519 Mandate tooling, verifier-account implementation, live-spine doctrine transition, autonomy, model calls, gateway activation, or Level 2A acceptance.

---

## 2. Governing Intent

AXIOM remains:

```text
non-autonomous by design
```

This mandate candidate exists only to reduce unsafe development-infrastructure risk before Level 2A implementation proceeds.

IPC may remain as historical evidence or inert review material. IPC must not remain an active execution bus.

For Phase 0, the chosen containment posture is:

```text
STRUCTURAL UNREACHABILITY
```

not deletion, and not notification-only live mode.

Structural unreachability means unsafe execution branches may remain in source only if a dominant fail-closed guard makes them unreachable before any watcher, dispatcher, shell evaluator, Codex invocation, Antigravity/Gemini invocation, ConPTY path, tmux/terminal path, database dispatch, markdown-inbox reader, or auto-send branch can run.

A stopped process is not sufficient. A comment saying “disabled” is not sufficient. A runtime condition that only holds in the current shell session is not sufficient. The freeze must survive manual relaunch and reboot.

---

## 3. Scope

The implementer may work only on Phase 0 IPC containment.

Scope includes:

1. Inventory every file and local IPC-adjacent artifact under:

```text
$AXIOM_WORKSPACE/ipc/
```

2. Generate pre-modification SHA-256 hashes for every file under:

```text
$AXIOM_WORKSPACE/ipc/
```

3. Classify every IPC file as one of:

```text
executor
watcher
startup_launcher
transport
database_index
notification_helper
historical_inbox
probe_or_scratch
conpty_or_terminal_bridge
posture_or_status_daemon
documentation_or_evidence
unknown
```

4. Record a composition graph showing:

   * which scripts dot-source other scripts;
   * which scripts launch other scripts;
   * which scripts start background runspaces;
   * which scripts invoke agent binaries;
   * which scripts read markdown inboxes;
   * which scripts read or mutate IPC database state;
   * which scripts can create outbound agent-directed sends.

5. Identify every active or re-armable execution path involving:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
scriptblock invocation
body-driven call operator usage
Start-Process driven by IPC message content
codex exec
agy --print
Invoke-ConPtyCaptureHosted
ConPTY-mediated agent execution
tmux/send-keys or equivalent terminal injection
auto-send-to-from_agent relay
FileSystemWatcher-triggered dispatch
IPC database pending-message dispatch
startup script auto-launch
local named pipe listener
local loopback listener
shared-memory or terminal-handle ingress
```

6. Make unsafe IPC execution structurally unreachable in source.

7. Prevent startup scripts and composed services from re-arming IPC execution.

8. Preserve markdown inbox files only as inert evidence.

9. Prevent markdown inbox files from being read by active background scripts during the freeze.

10. Add tests proving unsafe execution paths remain structurally unreachable.

11. Produce a Phase 0 evidence artifact using tokenized paths.

---

## 4. Explicitly Unsafe Execution Mechanisms

The following mechanisms are unsafe for Phase 0 and must be halted by structural unreachability.

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

### 4.4 Terminal / Tmux / Console ingress

```text
tmux send-keys
terminal input injection
console-handle inheritance
ConPTY session creation from IPC content
hidden shell host relaunch from IPC content
```

### 4.5 Peer-to-peer relay execution

```text
send.ps1 -To $msg.from_agent
automatic reply routing from executor to sender
agent-to-agent loop through markdown inboxes
agent-to-agent loop through ipc_messages.db
FileSystemWatcher-triggered cross-agent processing
```

### 4.6 Non-file local IPC ingress

```text
named pipes
loopback listeners
local socket listeners
shared-memory handles
background runspace listeners
posture daemons
watcher services
```

---

## 5. Allowed Actions

The implementer may:

1. Inventory all files and IPC-adjacent artifacts under `$AXIOM_WORKSPACE/ipc/`.

2. Generate pre-modification SHA-256 hashes for all files under `$AXIOM_WORKSPACE/ipc/`.

3. Create a baseline inventory showing:

   * file name;
   * SHA-256 hash;
   * role classification;
   * whether it can execute;
   * whether it can invoke an agent;
   * whether it can read inbox files;
   * whether it can write outbound agent messages;
   * whether it can mutate `ipc_messages.db`;
   * whether it is startup-launched;
   * whether it is composed through dot-sourcing or runspaces;
   * whether it is legacy, probe, scratch, or unknown.

4. Modify IPC files only to create structural unreachability for:

   * watcher loops;
   * executor loops;
   * startup-launched IPC services;
   * composed runspace services;
   * shell execution from IPC;
   * Codex execution from IPC;
   * Antigravity/Gemini execution from IPC;
   * ConPTY/tmux/terminal execution from IPC;
   * automatic send-back relay paths;
   * markdown inbox active reads;
   * IPC database pending-message execution dispatch.

5. Add tests proving IPC execution is structurally unreachable.

6. Add static risk scans as secondary tripwires.

7. Update IPC documentation narrowly to state that active IPC execution is frozen pending future Orchestrator mediation.

8. Create one Phase 0 evidence artifact.

9. Preserve markdown inboxes, logs, and database artifacts as historical evidence only, provided they are summarized rather than dumped and no active background reader processes them during the freeze.

10. Add minimal fail-closed guards to existing IPC files where necessary.

11. Modify execution-capable IPC support/probe files only to make them inert, fail-closed, or unreachable.

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

20. Preserve active ConPTY, tmux, terminal, or console-handle execution from IPC content.

21. Preserve active peer-to-peer execution loops.

22. Add new watcher services.

23. Add new hidden background execution services.

24. Add new agent-to-agent execution channels.

25. Add new durable IPC architecture or routing framework.

26. Add temporary production constants solely to satisfy tests.

27. Add a new durable disposition helper unless a stop-and-return governance review explicitly approves it.

28. Modify AXIOM runtime policy, manifests, gateway logic, scheduler logic, task lifecycle logic, model logic, memory logic, or database schema outside IPC containment.

29. Store secrets, tokens, private keys, local credentials, unredacted environment values, or machine-specific user paths in evidence.

---

## 7. Files and Artifacts Allowed

### 7.1 Mandatory Full IPC Inventory

The implementer must inventory every file under:

```text
$AXIOM_WORKSPACE/ipc/
```

No IPC file may be skipped because it is believed to be legacy, scratch, probe-only, generated, test-only, or inactive.

If any file contains an execute pattern, agent-invoke pattern, watcher pattern, launcher pattern, terminal-injection pattern, ConPTY pattern, or local IPC listener pattern, it must be listed as execution-capable or re-armable unless tests prove structural unreachability.

### 7.2 IPC Files Allowed for Containment Edits

The implementer may make minimal containment edits to any file under:

```text
$AXIOM_WORKSPACE/ipc/
```

only if the edit is necessary to make an unsafe IPC path structurally unreachable.

This includes, but is not limited to:

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
ipc/watcher_service.ps1
ipc/posture_daemon.ps1
ipc/conpty_capture.ps1
ipc/tmux_bridge.ps1
ipc/_agy_hosted_test.ps1
ipc/_agy_probe.ps1
ipc/_conpty_probe_diag.ps1
ipc/_conpty_probe.ps1
ipc/_conpty_probe2.ps1
ipc/_probe_raw.ps1
```

Allowed edits must be limited to:

```text
fail-closed guard insertion
early return before unsafe dispatch
hard rejection before unsafe dispatch
startup launch prevention
watcher/read-loop prevention
agent invocation prevention
terminal/ConPTY/tmux invocation prevention
auto-send-to-from_agent prevention
unsafe message-type rejection
evidence-preserving inerting
```

### 7.3 IPC Files Allowed for Evidence-Only Preservation

The following may be preserved as inert evidence:

```text
ipc/to_claude.md
ipc/to_codex.md
ipc/to_antigravity.md
ipc/pending_for_claude.md
ipc/*.log
ipc/*.db
ipc/*.db-wal
ipc/*.db-shm
ipc/*.md
```

They must not be dumped wholesale into the evidence artifact. They must be summarized and tokenized.

### 7.4 Test Files Allowed

The implementer may create focused tests under an appropriate IPC test location, such as:

```text
tests/test_ipc_inventory_complete.py
tests/test_ipc_pre_modification_hash_baseline.py
tests/test_ipc_composition_graph.py
tests/test_ipc_structural_unreachability.py
tests/test_ipc_watchers_halted_at_source.py
tests/test_ipc_command_execution_frozen.py
tests/test_ipc_db_command_type_rejected.py
tests/test_ipc_codex_autoinvocation_frozen.py
tests/test_ipc_antigravity_autoinvocation_frozen.py
tests/test_ipc_conpty_tmux_terminal_frozen.py
tests/test_ipc_peer_to_peer_relay_frozen.py
tests/test_ipc_markdown_inboxes_inert.py
tests/test_ipc_side_channel_ingress_blocked.py
tests/test_ipc_process_tree_clear.py
tests/test_ipc_static_execution_tripwires.py
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
tools/console.py
```

---

## 8. Required Containment Behavior

After implementation:

1. Unsafe IPC execution branches must be structurally unreachable in source.

2. The freeze must survive reboot and manual relaunch.

3. No active IPC watcher may read markdown inbox files and trigger processing.

4. No active IPC watcher may read `ipc_messages.db` pending messages and trigger execution.

5. No IPC path may execute a message body as shell or PowerShell.

6. No IPC path may pass a message body to Codex.

7. No IPC path may pass a message body to Antigravity/Gemini.

8. No IPC path may invoke ConPTY capture from message content.

9. No IPC path may invoke tmux, terminal injection, or console-handle execution from message content.

10. No IPC path may auto-send a response to `$msg.from_agent` in a way that creates an agent-to-agent loop.

11. Markdown inboxes may remain only as inert evidence.

12. `ipc_db.py` must reject, fail closed, or no longer represent `command` as an executable message type.

13. Startup scripts must not launch active IPC watcher/executor services during the freeze.

14. `ipc_service.ps1` must be safe as a composed service, not merely safe when leaf scripts are inspected separately.

15. Any retained IPC code must fail closed, remain unreachable, or produce a deterministic non-executing result before unsafe logic is reached.

---

## 9. Required Tests and Evidence

The implementation must provide tests or testable evidence for each of the following.

### 9.1 Inventory completeness

Test or audit proves every file under `$AXIOM_WORKSPACE/ipc/` was inventoried and classified.

### 9.2 Pre-modification hash baseline

Evidence records SHA-256 hashes of every file under `$AXIOM_WORKSPACE/ipc/` before containment edits.

If any pre-modification hash cannot be captured, implementation must stop and report the gap.

### 9.3 Composition graph

Test or audit records:

* dot-sourced files;
* launched files;
* background runspaces;
* startup edges;
* watcher edges;
* database dispatch edges;
* markdown inbox reader edges;
* outbound send edges;
* agent invocation edges.

### 9.4 Structural unreachability

Test proves unsafe execution branches are unreachable in source even if scripts are manually launched.

This must apply to at least:

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
watcher_service.ps1
posture_daemon.ps1
```

If any listed file does not exist, the evidence artifact must state that clearly.

### 9.5 Composed service safety

Test proves `ipc_service.ps1`, with all dot-sourced or runspace-loaded components accounted for, exposes no path to:

* shell execution;
* Codex invocation;
* Antigravity/Gemini invocation;
* ConPTY/tmux/terminal invocation;
* markdown inbox active dispatch;
* database pending-message execution dispatch;
* outbound agent-directed auto-send.

### 9.6 Launcher fail-closed behavior

Test proves startup scripts fail closed and do not launch watcher/executor services unless a future signed Orchestrator/Mandate mechanism exists.

No such future mechanism is authorized by this mandate.

### 9.7 Shell execution freeze

Test proves IPC content cannot reach:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
scriptblock invocation
body-driven call operator execution
Start-Process from message body
```

### 9.8 IPC database command-type freeze

Test proves `command` is rejected, non-representable, or treated as non-executable at the `ipc_db.py` layer.

This must not require changes to AXIOM core database schema.

### 9.9 Codex auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
codex exec
codex exec --sandbox workspace-write
```

### 9.10 Antigravity/Gemini auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
agy --print
Invoke-ConPtyCaptureHosted
ConPTY-based execution
```

### 9.11 Terminal / tmux / console freeze

Test or audit proves IPC content cannot invoke:

* tmux send-keys;
* terminal input injection;
* console-handle inherited execution;
* hidden shell-host launch;
* equivalent local terminal ingress.

### 9.12 Peer-to-peer relay freeze

Test proves an inbound message produces zero outbound agent-directed sends.

Specifically, no active path may automatically call:

```text
send.ps1 -To $msg.from_agent
```

or equivalent agent-directed response routing.

This property must be evaluated for all known executor surfaces, not a single representative file.

### 9.13 Markdown inbox inertness

Test or audit proves markdown inbox files are not active control inputs after containment edits.

No source file in active IPC launch paths may read `to_*.md` and transition state during the freeze.

### 9.14 Side-channel ingress block

Test or audit proves modifying an inert markdown inbox file produces:

* zero process invocations;
* zero agent invocations;
* zero database mutations;
* zero outbound agent-directed sends.

A bounded observation window may be used if the method is documented.

### 9.15 Non-file IPC channel inventory

Evidence records whether any of the following are active or re-armable:

* named pipes;
* loopback listeners;
* local sockets;
* shared-memory handles;
* background runspace listeners;
* ConPTY/tmux/terminal ingress;
* posture daemon channels.

If any such channel is active, implementation must stop and return for governance review unless it can be structurally frozen within the allowed IPC scope.

### 9.16 Process-tree validation

Evidence records that no IPC watcher, executor, posture daemon, agent bridge, or IPC service remains active after containment.

The evidence must summarize process-tree status without exposing local usernames, secrets, tokens, private keys, or active environment values.

### 9.17 Static tripwire scan

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
tmux send-keys
send.ps1 -To $msg.from_agent
FileSystemWatcher
pending --agent
```

If a forbidden string remains in historical or inert code, the test or audit must prove the file is not active and cannot be launched by startup paths during the freeze.

### 9.18 Test method disclosure

For each required test, the implementation handoff must state whether the test is:

* behavioral;
* source-analysis;
* process-tree evidence;
* static tripwire;
* manual audit evidence.

Source-only tests are allowed only when behavioral tests are impractical for the PowerShell surface, and the limitation must be stated.

---

## 10. Evidence Required

The implementation handoff must include:

1. Candidate ID:

```text
MND-CANDIDATE-2026-0001-REV-B
```

2. Statement that this is candidate-derived implementation evidence only.

3. Statement that no doctrine change was performed.

4. Statement that no `VERIFIED_COMMIT` claim is made.

5. Full IPC file inventory.

6. SHA-256 pre-modification baseline for every IPC file.

7. Classification table for every IPC file.

8. Composition graph.

9. List of executor files found.

10. List of watcher files found.

11. List of startup-launcher files found.

12. List of transport/database files found.

13. List of ConPTY/tmux/terminal bridge files found.

14. List of posture/status daemon files found.

15. List of markdown inbox files preserved as inert evidence.

16. List of probe/scratch files found.

17. Non-file IPC channel inventory.

18. Before/after summary of unsafe execution mechanisms.

19. Files changed.

20. Files inspected but unchanged.

21. Blocked files confirmed untouched.

22. Tests added or updated.

23. Test method disclosure for each test.

24. Test result summary.

25. Process-tree validation summary.

26. Residual risks.

27. Go/no-go recommendation for the next mandate.

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

7. IPC execution is structurally frozen, not accepted as Level 2A-compliant.

8. Further work requires a separate mandate candidate.

9. Any retained unsafe code is unreachable by source-level guard and documented as residual risk.

10. Any re-armable support/probe file is either structurally frozen or explicitly reported as a blocker.

---

## 12. Go / No-Go Blockers

Implementation must stop and return for governance review if:

1. Any IPC file cannot be inventoried.

2. Any pre-modification SHA-256 hash cannot be captured.

3. Any IPC file contains active execution logic that cannot be structurally frozen within allowed IPC scope.

4. Any probe/scratch file can invoke Codex, Antigravity/Gemini, ConPTY, tmux, terminal input, shell, or PowerShell execution after containment.

5. Any active path must keep watchers running to pass tests.

6. Any active path must preserve `Invoke-Expression`.

7. Any active path must preserve inbound `codex exec`.

8. Any active path must preserve inbound `agy --print`.

9. Any active path must preserve ConPTY invocation from message body.

10. Any active path must preserve tmux/terminal injection from message body.

11. Any active path must preserve auto-send-to-`from_agent`.

12. Any markdown inbox must remain an active control input.

13. Any startup script can re-arm IPC execution.

14. `ipc_service.ps1` remains unsafe as a composed service.

15. `command` remains representable as an executable IPC message type.

16. Any non-file IPC channel remains active and execution-capable.

17. Any test requires modifying files outside the allowed IPC/test/evidence scope.

18. Any implementation requires runtime AXIOM schema changes outside IPC.

19. Any implementation requires Orchestrator construction.

20. Any implementation requires Mandate signing/sealing.

21. Any implementation requires verifier-account setup.

22. Any implementation attempts to claim `VERIFIED_COMMIT`.

23. Any implementation attempts to mark Level 2A accepted.

24. Any implementation attempts to alter doctrine.

25. Any secret, token, private key, credential, unredacted environment value, or local user path appears in evidence.

---
