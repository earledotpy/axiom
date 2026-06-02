# Codex Feasibility Review - MND-CANDIDATE-2026-0001-REV-B

Role: Implementation Specialist and Troubleshooter

Status: Feasibility review only. Not implementation authority. No implementation performed.

## 1. Editable IPC Scope Sufficiency

Yes.

REV-B fixes the REV-A gap by allowing minimal containment edits to any file under `ipc/`, including support and probe surfaces such as:

- `ipc/conpty_capture.ps1`
- `ipc/watcher_service.ps1`
- `ipc/posture_daemon.ps1`
- IPC probe scripts

The scope is sufficient as long as all edits remain limited to structural unreachability, fail-closed behavior, and evidence-preserving inerting.

## 2. Full IPC Inventory and SHA-256 Baseline Feasibility

Yes.

A full IPC inventory and pre-modification SHA-256 baseline are feasible before edits.

The implementation evidence should explicitly state that the baseline captures the current working tree at implementation time, not necessarily a clean committed state, because IPC files and runtime artifacts already appear to have local changes.

## 3. Structural Unreachability Without Deletion

Yes.

Structural unreachability is feasible without deleting execution logic by using dominant fail-closed guards and early returns before:

- dot-sourcing;
- watcher creation;
- database dispatch;
- markdown inbox reads;
- runspace starts;
- CLI-agent invocations;
- ConPTY, tmux, or terminal calls;
- auto-send branches.

Unsafe code can remain as inert evidence if tests prove the guard dominates all entry paths.

## 4. `ipc_service.ps1` Composed-Service Safety

Yes, this can be tested.

The strongest approach is a composition graph plus source-level assertions that composed, dot-sourced, or runspace-loaded components cannot reach unsafe calls.

Behavioral execution tests should be limited and controlled, because launching PowerShell service code can itself create risk if containment is incomplete.

## 5. `ipc_db.py` Command-Type Neutralization

Yes.

`ipc_db.py` can reject, normalize, or neutralize executable `command` message type handling without AXIOM core schema changes.

Existing historical database rows should be preserved as evidence but treated as inert, not executable control input.

## 6. Non-File IPC Channel Inventory

Yes.

This is feasible as mixed source audit plus sanitized process-tree evidence.

The inventory should cover:

- named pipes;
- loopback listeners;
- local sockets;
- shared-memory handles;
- background runspace listeners;
- ConPTY, tmux, and terminal ingress;
- posture daemon channels.

If any active execution-capable non-file IPC channel cannot be structurally frozen within `ipc/`, the implementation should stop and return for governance review.

## 7. Tests Likely Required

Likely required tests include:

- IPC inventory completeness;
- pre-modification SHA-256 baseline evidence;
- composition graph coverage;
- structural unreachability;
- watcher and startup halt;
- composed `ipc_service.ps1` safety;
- `ipc_db.py` `command` rejection or neutralization;
- shell and PowerShell execution freeze;
- Codex auto-invocation freeze;
- Antigravity/Gemini auto-invocation freeze;
- ConPTY, tmux, terminal, and console ingress freeze;
- peer-to-peer relay freeze;
- markdown inbox inertness;
- side-channel ingress audit;
- process-tree validation;
- static tripwires with inert-evidence exclusions.

## 8. Remaining Blocked-File Need

None apparent.

REV-B keeps required implementation inside:

- `ipc/`;
- focused tests;
- one evidence artifact.

No AXIOM core, schema, policy, gateway, app, or live-spine changes appear necessary.

## 9. Existing-Test Breakage Risk

Moderate-low.

Core AXIOM tests should be unaffected if implementation stays tightly scoped.

Main risks:

- brittle static scans over historical markdown, database, or log content;
- SHA-256 baseline tests failing if runtime artifacts change between baseline and verification;
- any consumer or test expecting `command` IPC messages to remain executable;
- process-tree or side-channel tests becoming flaky if background IPC processes are already running before containment.

## 10. Go / No-Go Recommendation

Go after Jeremy approval.

REV-B is implementable and materially clearer than REV-A. The main implementation discipline is to capture hashes before edits, avoid dumping sensitive or machine-specific artifact content, and treat any active non-file IPC channel that cannot be frozen inside `ipc/` as a stop-and-return blocker.
