# Phase 10: Variant B Console Layout, Native IPC Multiplexing, and UI/IPC Cleanup

**From**: Antigravity (Chief Architect)  
**To**: Codex (Implementation Specialist)  
**Date**: 2026-05-29  
**ADR-0006 Step**: 1 — Antigravity produces the written task plan  

---

## 1. Goal and Scope

This phase establishes the operator-facing interface upgrades, native multiplexing, and IPC hardening for **Phase 10**. The goals are:
1. **Variant B Dashboard Panels**: Build the active execution trace and approval gate panels to reflect autonomous-supervised operations.
2. **Dynamic Dashboard Switching**: Update `axiom-dashboard` to dynamically load Variant A or Variant B layouts based on the current session status.
3. **PSMUX Integration**: Wire up `psmux` as the native Windows standalone terminal multiplexer to enable split-pane key injection and capture fallback.
4. **Fix Infinite IPC Loop**: Resolve the logic defect where bridges and watchers continually execute and reply to responses.
5. **Professional UI Cleanup**: Rationalize the terminal modules into cleaner logical groupings.

---

## 2. Affected Files

The implementation slice involves the following file changes:

### New Files:
1. **[62-execution-trace.ps1](file:///C:/axiom/ui/terminal/modules/62-execution-trace.ps1)** — Implements `axiom-execution-trace` to render active pipeline traces (`plan` → `dispatch` → `run` → `verify`) and resource budget progress.
2. **[63-approval-gate.ps1](file:///C:/axiom/ui/terminal/modules/63-approval-gate.ps1)** — Implements `axiom-approval-gate` to display tasks in the DB queue currently blocked on operator countersign (status = `needs_human_input`).
3. **[64-autonomous-posture.ps1](file:///C:/axiom/ui/terminal/modules/64-autonomous-posture.ps1)** — Implements `axiom-autonomous-posture` to summarize the 7-step autonomous gate readiness checklist.

### Modified Files:
4. **[40-dashboard.ps1](file:///C:/axiom/ui/terminal/modules/40-dashboard.ps1)** — Modify `axiom-dashboard` to check `session.autonomous_operation_enabled` and route between Variant A and Variant B layouts.
5. **[tmux_bridge.ps1](file:///C:/axiom/ipc/tmux_bridge.ps1)** — Update the binary checking paths to prioritize `psmux.exe` (or local standalone `tmux.exe`) over Git Bash MSYS2 `tmux`.
6. **[loop_watcher.ps1](file:///C:/axiom/ipc/loop_watcher.ps1)** — Update the watcher to intercept and immediately mark `re:` (reply) messages as processed without running `Invoke-Expression`.
7. **[agent_bridge.ps1](file:///C:/axiom/ipc/agent_bridge.ps1)** — Update the bridge to intercept and immediately mark `re:` messages as processed without invoking the local CLI agent.
8. **[axiom-terminal-command-registry.json](file:///C:/axiom/ui/terminal/registry/axiom-terminal-command-registry.json)** — Register metadata for the three new commands and associate them with preflight/doctor verification targets.
9. **[49-doctor.ps1](file:///C:/axiom/ui/terminal/modules/49-doctor.ps1)** / **[52-docs.ps1](file:///C:/axiom/ui/terminal/modules/52-docs.ps1)** — Wire the new modules into the system doctor checklist and standard terminal documentation index.

---

## 3. Proposed Approach & Key Decisions

### A. Dynamic Layout Switching (Variant A vs Variant B)
* Update `axiom-dashboard` to query:
  ```sql
  SELECT autonomous_operation_enabled, current_chain_id FROM sessions ORDER BY session_id DESC LIMIT 1
  ```
* If `autonomous_operation_enabled` is `1` (True):
  * Replace the static **Manifest Integrity** panel with the dynamic output of `axiom-execution-trace`.
  * Replace the **Live Event Stream** panel with the output of `axiom-approval-gate`.
  * Render a **Resource Budget Limits** footer summarizing remaining tokens, active policy denials count, and memory margins.
* Provide an override flag (e.g. `axiom-dashboard --force-variant <A|B>`) to allow operators to review both layouts regardless of the DB session state.

### B. Execution Trace Pipeline (`axiom-execution-trace`)
* Query current active task chain stages from the database:
  ```sql
  SELECT task_id, task_type, status, execution_result FROM tasks WHERE chain_id = ?
  ```
* Match database task types (`goal_planning` / `task_planning` → `dispatched` → `running` → `result_verification`) to draw a progress bar:
  `[PLAN: OK] ── [DISPATCH: OK] ── [RUNNING: ACTIVE] ── [VERIFY: PEND]`

### C. Approval Gate Panel (`axiom-approval-gate`)
* Query tasks needing authorization:
  ```sql
  SELECT task_id, task_type, manifest_id, status FROM tasks WHERE status = 'needs_human_input'
  ```
* Format output with clear instructions on the exact command needed to countersign/resume the task.

### D. PSMUX/Tmux Bridging
* Update `Test-TmuxAvailable` in `ipc/tmux_bridge.ps1` to test for `psmux.exe` in common paths or `C:\Users\tanne\AppData\Local\Microsoft\WinGet\Packages\psmux.psmux_Active` before checking the MSYS2 path.
* Ensure command compatibility: `psmux` command format aligns with standard tmux capture/send keys syntax.

### E. Fixing the Infinite IPC Message Loop
* **The Defect**: Currently, when an agent sends a prompt, the recipient processes it and sends a reply message (e.g. `Subject: re: <OriginalSubject>`). The sender's watcher receives the reply, but treats it as a new prompt to execute/run, sending another reply and triggering an infinite loop of thinking/errors.
* **The Fix**: Both `loop_watcher.ps1` and `agent_bridge.ps1` must check incoming message subjects. If `subject` begins with `"re: "` (case-insensitive):
  * Mark the message as `processed = 1` immediately using `Mark-Done`.
  * Print a log trace to the local terminal: `[watcher] received reply: <Subject> (processed)`.
  * **Skip execution**: Do not run `Invoke-Expression` or `Invoke-Agent`.

### F. UI Directory Professionalization
* Group loose `.ps1` files inside `ui/terminal/modules/` into subfolders or load them under a module structure if appropriate, or keep current loading conventions but cleanly partition utilities from panel logic.

---

## 4. Risks & Constraints

* **Read-Only Console Rule**: The UI panels must remain strictly read-only display tools. They must not perform writes or trigger executions directly without the standard scheduler loop.
* **Fail-Closed Baseline**: The dashboard must default to Variant A if database records are unavailable or missing.
* **No Administrative Privileges**: Standalone psmux or user-space paths must be used for binary detection to avoid requiring admin rights for tool setup.

---

## 5. Verification Steps

To verify the implementation of Phase 10:
1. Run the system doctor to ensure load-order validation passes:
   ```powershell
   axiom-doctor
   ```
2. Test dashboard routing by manually forcing Variant layouts:
   ```powershell
   axiom-dashboard --force-variant A
   axiom-dashboard --force-variant B
   ```
3. Verify loop termination: Send an IPC message and verify the recipient replies, and the sender terminates execution immediately upon receiving the `re: ` reply.
4. Run the complete pytest suite to check that changes do not introduce syntax or import failures:
   ```powershell
   pytest tests -v
   ```

---

## 6. Rollback Plan

If the changes disrupt console operations:
1. Restore previous UI/IPC files:
   ```powershell
   git checkout HEAD -- ui/terminal/modules/39-now.ps1 ui/terminal/modules/40-dashboard.ps1 ipc/loop_watcher.ps1 ipc/agent_bridge.ps1 ui/terminal/registry/axiom-terminal-command-registry.json
   ```
2. Delete new modules:
   ```powershell
   Remove-Item ui/terminal/modules/62-*, ui/terminal/modules/63-*, ui/terminal/modules/64-* -ErrorAction SilentlyContinue
   ```

---

## 7. Future Architectural Considerations & Gaps (Notes)

### A. Python/Textual TUI Migration Note
* **Objective**: Evaluate migrating the PowerShell console print-rendering engine into an interactive Python TUI built using `textual` or `pyratatui`.
* **Rationale**: The current layout is built around simple text-stream outputs. An interactive application would enable mouse-scrollable panels, keyboard navigation, collapsible sections, and responsive layouts without console height limits.

### B. IPC Gaps for Testing and Production
* **Interactive Prompt Routing**: Plan a protocol to handle blocking stdin prompts inside IPC execution loops (e.g. routing user prompts dynamically back to the calling agent's stdout handle).
* **Cross-Agent Audit Logs**: Route IPC command records to AXIOM's database `security_events` table so that agent-to-agent operations are fully audited alongside standard user commands.
