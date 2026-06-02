# Codex Feasibility Review - MND-CANDIDATE-2026-0001-REV-C

Role: Implementation Specialist and Troubleshooter

Status: Feasibility review only. Not implementation authority. No mandate implementation performed.

Note: This review is based on the REV-C summary provided by Jeremy plus the prior REV-B surface assessment, not a fresh read of the REV-C file.

## 1. Editable IPC Scope Sufficiency

Yes, if REV-C preserves REV-B's authority to edit any file under `ipc/` for fail-closed structural containment, including support and probe files.

## 2. Mechanical Inventory Reconciliation

Yes.

Mechanical inventory reconciliation is feasible by comparing actual `ipc/` file enumeration against the evidence inventory and failing if any file is missing, duplicated, or unclassified.

## 3. Full IPC Inventory and SHA-256 Baseline

Yes.

A full IPC inventory and pre-modification SHA-256 baseline are feasible. The baseline should state that it represents the current working tree at implementation time.

## 4. Structural Unreachability Without Deletion

Yes.

Dominant guards and early returns can keep unsafe code as inert evidence while preventing manual relaunch or reboot re-arm.

## 5. Dominant Guard Verification

Yes, mostly through source analysis.

Tests can assert that fail-closed guards occur before:

- watcher setup;
- dot-sourcing;
- runspace creation;
- database dispatch;
- markdown inbox reads;
- CLI-agent invocation;
- ConPTY, tmux, or terminal calls;
- auto-send sinks.

## 6. Generalized Sink Detection

Yes.

Generalized sink detection is feasible and preferable to fixed string checks alone. It should include executable sinks, dynamic call operators, process launch, agent binaries, terminal injection, watcher setup, database pending dispatch, and outbound relay patterns.

## 7. `ipc_service.ps1` Composed-Service Safety

Yes.

This can be tested with composition graph checks plus source assertions that all dot-sourced or runspace-loaded paths are guarded before unsafe sinks.

## 8. `ipc_db.py` Command Neutralization

Yes, if limited to IPC-layer message-type validation, normalization, and retrieval behavior.

It should not touch AXIOM core schema or persistence.

## 9. Non-File IPC Channel Inventory

Yes.

This is feasible as source audit plus sanitized process-tree evidence after approval. Any active execution-capable channel outside `ipc/` containment should trigger stop-and-return review.

## 10. Tests Likely Required

Likely required tests include:

- inventory reconciliation;
- SHA-256 baseline evidence;
- composition graph coverage;
- dominant guard verification;
- generalized sink detection;
- watcher and startup halt;
- composed service safety;
- `ipc_db.py` command neutralization;
- markdown inbox inertness;
- peer relay freeze;
- ConPTY, tmux, and terminal freeze;
- non-file IPC inventory;
- process-tree validation;
- static tripwires.

## 11. Remaining Blocked-File Need

None apparent if REV-C keeps changes inside:

- `ipc/`;
- focused tests;
- one evidence artifact.

## 12. Existing-Test Breakage Risk

Moderate-low.

Main risks:

- brittle scans over historical evidence, logs, or databases;
- changing runtime artifacts affecting hashes;
- any existing expectation that IPC `command` messages remain executable.

## 13. Go / No-Go Recommendation

Go after Jeremy approval, with one condition:

Before implementation, confirm REV-C's actual text authorizes all claimed additions and does not narrow REV-B's expanded `ipc/` edit authority.
