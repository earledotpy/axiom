# Level2A_Phase0_IPC_Freeze_Mandate_Candidate_REV_C

**Status:** Candidate only. Not signed. Not authority-bearing. No doctrine change authorized.
**Candidate ID:** `MND-CANDIDATE-2026-0001-REV-C`
**Target Level:** Level 2A pre-implementation containment
**Authorized Terminal State:** `VERIFIED_EVIDENCE_RECORDED` or `AUDIT_FAILED`
**Unauthorized Terminal State:** `VERIFIED_COMMIT`

---

## 1. Purpose

This mandate candidate authorizes a narrowly bounded Phase 0 containment slice for AXIOM’s IPC layer.

The purpose is to establish a mechanically anchored IPC baseline, structurally freeze unsafe IPC execution paths, prevent re-arm through startup scripts or composed services, preserve evidence, and add regression tests proving that IPC cannot execute shell commands, invoke CLI agents, or create peer-to-peer execution authority.

This mandate candidate does not authorize Orchestrator construction, Ed25519 Mandate tooling, verifier-account implementation, live-spine doctrine transition, autonomy, model calls, gateway activation, or Level 2A acceptance.

---

## 2. Governing Intent

AXIOM remains:

```text
non-autonomous by design
```

This candidate exists only to reduce unsafe development-infrastructure risk before Level 2A implementation proceeds.

IPC may remain as historical evidence or inert review material. IPC must not remain an active execution bus.

For Phase 0, the chosen containment posture is:

```text
STRUCTURAL UNREACHABILITY
```

not deletion, and not notification-only live mode.

Structural unreachability means unsafe execution branches may remain in source only if a dominant fail-closed guard makes them unreachable before any watcher, dispatcher, shell evaluator, Codex invocation, Antigravity/Gemini invocation, ConPTY path, tmux/terminal path, database dispatch, markdown-inbox reader, or auto-send branch can run.

A stopped process is not sufficient. A comment saying “disabled” is not sufficient. A runtime condition that only holds in the current shell session is not sufficient. The freeze must survive manual relaunch and reboot.

---

## 3. Phase 0 Rule of Construction

This mandate candidate authorizes containment, not redesign.

The implementer may add fail-closed guards, inerting edits, source-level launch prevention, and focused tests. The implementer must not introduce a new IPC architecture, new durable routing framework, new Orchestrator substitute, new signing/sealing mechanism, or new execution pathway.

Where a choice exists between preserving old execution logic behind a dominant guard and deleting old execution logic, the authorized choice is structural unreachability. Deletion is not required unless structural unreachability cannot be proven.

---

## 4. Required Mechanical Inventory Anchor

The IPC inventory must be mechanically anchored, not self-graded.

Before any containment edit, the implementer must create a recursive directory-walk manifest for:

```text
$AXIOM_WORKSPACE/ipc/
```

The manifest must include, for every path returned by the directory walk:

```text
relative_path
path_type
sha256
size_bytes
classification
contains_execution_sink
contains_launcher_edge
contains_reader_edge
contains_writer_edge
contains_agent_invocation
contains_terminal_or_conpty_edge
contains_non_file_ipc_edge
containment_status
```

The classification table must reconcile exactly with the directory-walk manifest.

Required invariant:

```text
classification_row_count == directory_walk_path_count
```

Every walked file path must have:

```text
one SHA-256 hash
one classification
one containment status
```

If any file cannot be hashed, classified, or reconciled, implementation must stop and return `AUDIT_FAILED`.

Completeness must mean:

```text
every path on disk has a row
```

not:

```text
every path the implementer remembered to list has a row
```

---

## 5. Generalized Execution Sink Definition

Unsafe sink detection must not rely only on literal string matching.

The implementation must define and test against a generalized sink model.

A generalized unsafe sink is any inbound-message-reachable path that can:

1. spawn an external process;
2. evaluate a scriptblock;
3. execute shell or PowerShell content;
4. invoke Codex;
5. invoke Antigravity/Gemini;
6. invoke ConPTY;
7. inject terminal or tmux input;
8. launch a hidden shell host;
9. read markdown inbox content and transition state;
10. read IPC database pending messages and transition state;
11. mutate IPC database state based on inbound message content;
12. produce outbound agent-directed sends;
13. open or use a named pipe, loopback listener, local socket, shared-memory handle, background runspace listener, or equivalent local IPC channel in an execution-capable way.

Static forbidden-string scans remain required as secondary tripwires, but they are not sufficient proof.

The primary proof must show that no inbound-message path reaches a generalized unsafe sink without crossing a dominant fail-closed guard.

---

## 6. Uniform Fail-Closed Guard Requirement

All neutralized PowerShell IPC files must use a uniform fail-closed guard pattern.

The guard must appear before:

```text
dot-sourcing
watcher creation
runspace creation
database pending-message reads
markdown inbox reads
message dispatch
shell execution
agent invocation
ConPTY/tmux/terminal invocation
auto-send routing
```

Required guard semantics:

```text
IPC_PHASE0_FREEZE_ACTIVE is true by default.
When the guard is active, the script must terminate or return before any unsafe sink can be reached.
No override is authorized by this mandate.
No environment-variable bypass is authorized by this mandate.
No command-line bypass is authorized by this mandate.
```

The exact code form may vary only where required by file type, but the implementation must use a single standardized guard block for PowerShell files and a single standardized guard block for Python files.

Guard placement must be verified by dominance analysis.

A guard is valid only if every path from file entry point to generalized unsafe sink crosses the guard first.

A guard is invalid if:

1. it appears after a reachable unsafe sink;
2. it can be bypassed by a parameter;
3. it can be bypassed by an environment variable;
4. it can be bypassed by message content;
5. it can be bypassed by dot-sourcing order;
6. it depends only on a process currently being stopped;
7. it depends only on operator memory.

---

## 7. Scope

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

3. Reconcile the classification table against the mechanical directory-walk manifest.

4. Classify every IPC file as one of:

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
runtime_artifact
unknown
```

5. Record a composition graph showing:

   * which scripts dot-source other scripts;
   * which scripts launch other scripts;
   * which scripts start background runspaces;
   * which scripts invoke agent binaries;
   * which scripts read markdown inboxes;
   * which scripts read or mutate IPC database state;
   * which scripts can create outbound agent-directed sends;
   * which scripts use local IPC channels.

6. Identify every active or re-armable execution path involving:

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
local socket listener
shared-memory or terminal-handle ingress
background runspace listener
```

7. Make unsafe IPC execution structurally unreachable in source.

8. Prevent startup scripts and composed services from re-arming IPC execution.

9. Preserve markdown inbox files only as inert evidence.

10. Prevent markdown inbox files from being read by active background scripts during the freeze.

11. Add tests proving unsafe execution paths remain structurally unreachable.

12. Produce a Phase 0 evidence artifact using tokenized paths.

---

## 8. Explicitly Unsafe Execution Mechanisms

The following mechanisms are unsafe for Phase 0 and must be halted by structural unreachability.

### 8.1 Shell / PowerShell execution

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
scriptblock invocation
body-driven call operator execution
Start-Process driven by IPC message content
external process spawn reachable from inbound message content
```

### 8.2 Codex execution

```text
codex exec
codex exec --sandbox workspace-write
any invocation where IPC message body becomes a Codex prompt
```

### 8.3 Antigravity / Gemini execution

```text
agy --print
Invoke-ConPtyCaptureHosted
ConPTY capture driven by IPC message body
any invocation where IPC message body becomes an Antigravity/Gemini prompt
```

### 8.4 Terminal / Tmux / Console ingress

```text
tmux send-keys
terminal input injection
console-handle inheritance
ConPTY session creation from IPC content
hidden shell host relaunch from IPC content
```

### 8.5 Peer-to-peer relay execution

```text
send.ps1 -To $msg.from_agent
automatic reply routing from executor to sender
agent-to-agent loop through markdown inboxes
agent-to-agent loop through ipc_messages.db
FileSystemWatcher-triggered cross-agent processing
```

### 8.6 Non-file local IPC ingress

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

## 9. Allowed Actions

The implementer may:

1. Inventory all files and IPC-adjacent artifacts under `$AXIOM_WORKSPACE/ipc/`.

2. Generate pre-modification SHA-256 hashes for all files under `$AXIOM_WORKSPACE/ipc/`.

3. Create a mechanically reconciled baseline inventory showing:

   * file name;
   * SHA-256 hash;
   * file size;
   * role classification;
   * whether it can execute;
   * whether it can invoke an agent;
   * whether it can read inbox files;
   * whether it can write outbound agent messages;
   * whether it can mutate `ipc_messages.db`;
   * whether it is startup-launched;
   * whether it is composed through dot-sourcing or runspaces;
   * whether it is legacy, probe, scratch, runtime artifact, or unknown.

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

9. Preserve markdown inboxes, logs, database files, and runtime artifacts as historical evidence only, provided they are summarized rather than dumped and no active background reader processes them during the freeze.

10. Add minimal fail-closed guards to existing IPC files where necessary.

11. Modify execution-capable IPC support/probe files only to make them inert, fail-closed, or unreachable.

12. Make a narrow `ipc_db.py` change only to reject, normalize, or neutralize executable `command` message type at IPC ingress/write handling.

---

## 10. Narrow `ipc_db.py` Authority

`ipc_db.py` remains inside Phase 0 scope only because it is IPC-local and can currently represent message types used by IPC dispatch.

Authorized `ipc_db.py` changes are limited to:

```text
reject type=command at write ingress
normalize type=command to a non-executable inert type
mark type=command as dead-letter/non-executable
prevent future command frames from being accepted as executable control input
```

Blocked `ipc_db.py` changes:

```text
schema redesign
data migration
new durable routing framework
new Orchestrator substitute
new signature model
new authority model
changes to AXIOM core persistence
changes outside ipc/
```

Historical rows, database files, and logs may be preserved as evidence. They must not be treated as active control input.

If `command` neutralization cannot be done narrowly inside `ipc_db.py`, implementation must stop and return for governance review.

---

## 11. Blocked Actions

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

29. Store secrets, tokens, private keys, local credentials, unredacted environment values, raw workstation usernames, or machine-specific user paths in evidence.

---

## 12. Files and Artifacts Allowed

### 12.1 Mandatory Full IPC Inventory

The implementer must inventory every path under:

```text
$AXIOM_WORKSPACE/ipc/
```

No IPC path may be skipped because it is believed to be legacy, scratch, probe-only, generated, test-only, runtime-only, binary, database, log, or inactive.

If a path is not text-readable, it still requires hash, size, classification, and containment status.

### 12.2 IPC Files Allowed for Containment Edits

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

### 12.3 IPC Artifacts Allowed for Evidence-Only Preservation

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

### 12.4 Test Files Allowed

The implementer may create focused tests under an appropriate IPC test location, such as:

```text
tests/test_ipc_inventory_reconciliation.py
tests/test_ipc_pre_modification_hash_baseline.py
tests/test_ipc_composition_graph.py
tests/test_ipc_dominant_guard_placement.py
tests/test_ipc_generalized_sink_unreachability.py
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

### 12.5 Evidence Artifact Allowed

The implementer may create one evidence artifact:

```text
governance/05_handoffs/Phase0_IPC_Freeze_Evidence.md
```

If governance handoff edits are unavailable or inappropriate in the active implementation environment, use:

```text
docs/phase0_ipc_freeze_evidence.md
```

The evidence artifact must use `$AXIOM_WORKSPACE` instead of raw local paths where possible.

### 12.6 Files Blocked from Modification

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

## 13. Required Containment Behavior

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

12. `ipc_db.py` must reject, fail closed, normalize, or no longer represent `command` as an executable message type.

13. Startup scripts must not launch active IPC watcher/executor services during the freeze.

14. `ipc_service.ps1` must be safe as a composed service, not merely safe when leaf scripts are inspected separately.

15. Any retained IPC code must fail closed, remain unreachable, or produce a deterministic non-executing result before unsafe logic is reached.

16. Every classified path must reconcile against the mechanical directory-walk manifest.

17. Every generalized unsafe sink must be dominated by a fail-closed guard or structurally absent.

---

## 14. Required Tests and Evidence

The implementation must provide tests or testable evidence for each of the following.

### 14.1 Inventory reconciliation

Test or audit proves every path under `$AXIOM_WORKSPACE/ipc/` was inventoried and classified.

Required proof:

```text
classification_row_count == directory_walk_path_count
```

Every walked path must have:

```text
sha256
size_bytes
classification
containment_status
```

### 14.2 Pre-modification hash baseline

Evidence records SHA-256 hashes of every path under `$AXIOM_WORKSPACE/ipc/` before containment edits.

If any pre-modification hash cannot be captured, implementation must stop and report the gap.

### 14.3 Composition graph

Test or audit records:

* dot-sourced files;
* launched files;
* background runspaces;
* startup edges;
* watcher edges;
* database dispatch edges;
* markdown inbox reader edges;
* outbound send edges;
* agent invocation edges;
* local IPC channel edges.

### 14.4 Dominant guard placement

Test or source-analysis proves that each neutralized file has a fail-closed guard that dominates every path from file entry point to generalized unsafe sink.

A guard is insufficient if it appears after a reachable sink or can be bypassed.

### 14.5 Generalized sink unreachability

Test or source-analysis proves no inbound-message-reachable path can reach a generalized unsafe sink.

This proof must not depend solely on the static forbidden-string list.

### 14.6 Structural unreachability

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
conpty_capture.ps1
tmux_bridge.ps1
```

If any listed file does not exist, the evidence artifact must state that clearly.

### 14.7 Composed service safety

Test proves `ipc_service.ps1`, with all dot-sourced or runspace-loaded components accounted for, exposes no path to:

* shell execution;
* Codex invocation;
* Antigravity/Gemini invocation;
* ConPTY/tmux/terminal invocation;
* markdown inbox active dispatch;
* database pending-message execution dispatch;
* outbound agent-directed auto-send.

### 14.8 Launcher fail-closed behavior

Test proves startup scripts fail closed and do not launch watcher/executor services.

The future Orchestrator/Mandate mechanism does not exist and is not authorized here. The current test must assert unconditional fail-closed behavior.

### 14.9 Shell execution freeze

Test proves IPC content cannot reach:

```text
Invoke-Expression
iex
Invoke-Command
[scriptblock]::Create
scriptblock invocation
body-driven call operator execution
Start-Process from message body
external process spawn from inbound IPC message
```

### 14.10 IPC database command-type freeze

Test proves `command` is rejected, normalized, non-representable, or treated as non-executable at the `ipc_db.py` write/ingress layer.

This must not require changes to AXIOM core database schema.

### 14.11 Codex auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
codex exec
codex exec --sandbox workspace-write
```

### 14.12 Antigravity/Gemini auto-invocation freeze

Test proves inbound IPC content cannot invoke:

```text
agy --print
Invoke-ConPtyCaptureHosted
ConPTY-based execution
```

### 14.13 Terminal / tmux / console freeze

Test or audit proves IPC content cannot invoke:

* tmux send-keys;
* terminal input injection;
* console-handle inherited execution;
* hidden shell-host launch;
* equivalent local terminal ingress.

### 14.14 Peer-to-peer relay freeze

Test proves an inbound message produces zero outbound agent-directed sends.

Specifically, no active path may automatically call:

```text
send.ps1 -To $msg.from_agent
```

or equivalent agent-directed response routing.

This property must be evaluated for all known executor surfaces, not a single representative file.

### 14.15 Markdown inbox inertness

Test or audit proves markdown inbox files are not active control inputs after containment edits.

No source file in active IPC launch paths may read `to_*.md` and transition state during the freeze.

### 14.16 Side-channel ingress block

Test or audit proves modifying an inert markdown inbox file produces:

* zero process invocations;
* zero agent invocations;
* zero database mutations;
* zero outbound agent-directed sends.

A bounded observation window may be used if the method is documented.

### 14.17 Non-file IPC channel inventory

Evidence records whether any of the following are active or re-armable:

* named pipes;
* loopback listeners;
* local sockets;
* shared-memory handles;
* background runspace listeners;
* ConPTY/tmux/terminal ingress;
* posture daemon channels.

If any such channel is active, implementation must stop and return for governance review unless it can be structurally frozen within the allowed IPC scope.

### 14.18 Process-tree validation

Evidence records that no IPC watcher, executor, posture daemon, agent bridge, or IPC service remains active after containment.

Process-tree evidence is supporting evidence only. It is not the primary proof of freeze. The primary proof is source-level structural unreachability.

The evidence must summarize process-tree status without exposing local usernames, secrets, tokens, private keys, or active environment values.

### 14.19 Static tripwire scan

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

### 14.20 Test method disclosure

For each required test, the implementation handoff must state whether the test is:

* behavioral;
* source-analysis;
* process-tree evidence;
* static tripwire;
* manual audit evidence.

Source-only tests are allowed only when behavioral tests are impractical for the PowerShell surface, and the limitation must be stated.

---

## 15. Evidence Required

The implementation handoff must include:

1. Candidate ID:

```text
MND-CANDIDATE-2026-0001-REV-C
```

2. Statement that this is candidate-derived implementation evidence only.

3. Statement that no doctrine change was performed.

4. Statement that no `VERIFIED_COMMIT` claim is made.

5. Mechanical directory-walk manifest.

6. Full IPC file inventory.

7. SHA-256 pre-modification baseline for every IPC path.

8. Inventory reconciliation result.

9. Classification table for every IPC path.

10. Composition graph.

11. Generalized unsafe sink model used.

12. Dominant guard pattern used.

13. Dominant guard placement summary.

14. List of executor files found.

15. List of watcher files found.

16. List of startup-launcher files found.

17. List of transport/database files found.

18. List of ConPTY/tmux/terminal bridge files found.

19. List of posture/status daemon files found.

20. List of markdown inbox files preserved as inert evidence.

21. List of probe/scratch files found.

22. List of runtime artifacts found.

23. Non-file IPC channel inventory.

24. Before/after summary of unsafe execution mechanisms.

25. Files changed.

26. Files inspected but unchanged.

27. Blocked files confirmed untouched.

28. Tests added or updated.

29. Test method disclosure for each test.

30. Test result summary.

31. Process-tree validation summary.

32. Residual risks.

33. Go/no-go recommendation for the next mandate.

Evidence must use tokenized paths such as:

```text
$AXIOM_WORKSPACE/ipc/_inbox_claude.ps1
```

not raw workstation-specific paths unless unavoidable.

If raw local paths appear in tool output, the evidence artifact must summarize them using tokenized paths and must not expose local usernames, secrets, tokens, private keys, active environment values, or machine-specific credentials.

---

## 16. Audit Requirements

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

11. Inventory completeness was mechanically reconciled against directory-walk output.

12. Generalized sink detection was used rather than string-list-only verification.

---

## 17. Go / No-Go Blockers

Implementation must stop and return for governance review if:

1. Any IPC path cannot be inventoried.

2. Any pre-modification SHA-256 hash cannot be captured.

3. Directory-walk path count does not equal classification row count.

4. Any IPC path lacks a classification.

5. Any IPC file contains active execution logic that cannot be structurally frozen within allowed IPC scope.

6. Any neutralized file lacks a dominant guard before unsafe sinks.

7. Any unsafe sink is reachable from inbound message content.

8. Any probe/scratch file can invoke Codex, Antigravity/Gemini, ConPTY, tmux, terminal input, shell, or PowerShell execution after containment.

9. Any active path must keep watchers running to pass tests.

10. Any active path must preserve `Invoke-Expression`.

11. Any active path must preserve inbound `codex exec`.

12. Any active path must preserve inbound `agy --print`.

13. Any active path must preserve ConPTY invocation from message body.

14. Any active path must preserve tmux/terminal injection from message body.

15. Any active path must preserve auto-send-to-`from_agent`.

16. Any markdown inbox must remain an active control input.

17. Any startup script can re-arm IPC execution.

18. `ipc_service.ps1` remains unsafe as a composed service.

19. `command` remains representable as an executable IPC message type.

20. Any non-file IPC channel remains active and execution-capable.

21. Any test requires modifying files outside the allowed IPC/test/evidence scope.

22. Any implementation requires runtime AXIOM schema changes outside IPC.

23. Any implementation requires Orchestrator construction.

24. Any implementation requires Mandate signing/sealing.

25. Any implementation requires verifier-account setup.

26. Any implementation attempts to claim `VERIFIED_COMMIT`.

27. Any implementation attempts to mark Level 2A accepted.

28. Any implementation attempts to alter doctrine.

29. Any secret, token, private key, credential, unredacted environment value, raw workstation username, or local user path appears in evidence.

---