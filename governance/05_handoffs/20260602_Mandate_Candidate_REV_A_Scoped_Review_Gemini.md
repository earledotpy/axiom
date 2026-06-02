# Architecture & Portability Review: Phase 0 IPC Freeze Mandate

## 1. Executive Verdict

**APPROVE AFTER CHANGES**

The revised mandate candidate (`MND-CANDIDATE-2026-0001-REV-A`) represents an exceptional leap in control-plane discipline. By abandoning the soft "notification-only" live loop in favor of an absolute infrastructure halt, it successfully neutralizes the split-brain drift risk without prematurely implementing Level 2A verification tooling. However, architectural approval requires narrowing the scope regarding functional code injections and adding explicit coverage for non-file IPC channels.

---

## 2. Watcher/Executor Halt Posture Evaluation

The decision to enforce a **FULL WATCHER / EXECUTOR HALT** instead of a notification-only live mode is completely correct from a systems architecture standpoint.

```text
[Improvised CLI Layer] ──(Active File Watchers)──> Uncontrolled Shell Access [DRIFT]
                                  │
                       (Phase 0 Mandate Issued)
                                  ▼
[Improvised CLI Layer] ──(Static Dead-Letter)───> [CONTAINED BASELINE]

```

* **Elimination of Race Conditions:** Notification-only live loops under a standard user account maintain an active filesystem polling infrastructure (`loop_watcher.ps1`, `watcher_service.ps1`). This design causes disk I/O contention and leaves open windows for filesystem modification races.


* **Decoupled Posture Separation:** Halting the loops completely freezes the state plane. This prevents agents from exercising implicit authority via side-channel file drops before the deterministic Orchestrator is deployed.



---

## 3. Missing IPC Surfaces

While the file-centric mapping under Section 7 is extensive, the mandate ignores non-file local communication mechanisms present in the underlying workstation architecture:

* **Windows Named Pipes & Loopback Sockets:** Active daemons such as `posture_daemon.ps1` or `ipc_service.ps1` utilize named pipes or local loopback ports for process communication. The inventory boundaries must be expanded to catalog active listening ports or pipe handles.


* **Shared Memory & ConPTY Ingress:** Section 4.3 notes ConPTY-based execution, but the mandate must explicitly include the raw terminal abstractions (`conpty_capture.ps1`, `tmux_bridge.ps1`) in the freeze path to ensure an agent cannot re-arm a local shell connection through an inherited window handle.



---

## 4. Scope Overreach

* **Durable Logic Injections:** Section 5.6 permits the implementer to add a "small pure disposition helper only if it is durable containment logic". This introduces programmatic modification into a Phase 0 baseline slice. Phase 0 must remain an *inventory, freeze, and report* operation. Injecting code adjustments into active production pathways creates unverified surface variations and belongs strictly in Phase 2 or later.



---

## 5. Transferability and Path-Tokenization Concerns

* **Native Engine Serialization Dependency:** Section 7 forces the collection and inspection of absolute native Windows engine wrappers (`.ps1` scripts). While tokenizing the workspace path via `$AXIOM_WORKSPACE` protects the log artifacts from environment leakage, tracking file extensions directly links AXIOM's control architecture to the Windows host.


* **Remediation:** The classification phase should isolate the functional architecture (e.g., "Transport", "Ingress Gate") from the Windows-specific scripts wrapping them, ensuring that the baseline report remains valid when moving to containerized Linux environments (Level 2B target).



---

## 6. Required Evidence Additions

* **Pre-Modification Cryptographic Baseline:** The inventory sequence under Section 5.2 must generate and record SHA-256 hashes of all scripts *prior* to any containment modifications. This guarantees that the baseline report captures the exact drift state before code alterations occur.


* **Process Tree Validation:** The final evidence artifact must explicitly append a captured local process map proving that background daemons associated with `ipc_service.ps1` or `loop_watcher.ps1` have been terminated and are not currently active in memory.



---

## 7. Required Test Additions

* **Launcher Fail-Closed Test:** Add a test verifying that `startup_claude.ps1`, `startup_codex.ps1`, and `startup_agy.ps1` immediately exit or fail closed if called without an explicit operator-signed mandate reference.


* **Side-Channel Ingress Block Test:** Include an explicit automated assertion proving that modifying an inert markdown inbox file (`to_claude.md`) generates zero process invocations or database mutations across a standard 60-second observation window.



---

## 8. Go/No-Go Recommendation for Codex Feasibility Review

**GO**

Once Section 5.6 is adjusted to restrict the addition of structural disposition code into production script files, this candidate is fully ready for an offline Codex feasibility assessment. The explicit file blocks, tokenized pathing mandates, and clear delineation of allowed actions provide the precise constraints needed to prevent code generation errors.