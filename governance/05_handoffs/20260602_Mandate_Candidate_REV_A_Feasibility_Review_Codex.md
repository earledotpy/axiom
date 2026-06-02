# Codex Feasibility Review - MND-CANDIDATE-2026-0001-REV-A

Role: Implementation Specialist and Troubleshooter

Status: Feasibility review only. Not implementation authority. No files were modified as part of the reviewed mandate.

## 1. Allowed File List Sufficiency

No, not fully.

The allowed edit list covers the main known active executors and watchers, but the current `ipc/` inventory includes additional execution-capable or watcher-adjacent surfaces outside the candidate's section 7.2 edit list:

- `ipc/watcher_service.ps1`
- `ipc/posture_daemon.ps1`
- `ipc/conpty_capture.ps1`
- `ipc/_agy_hosted_test.ps1`
- `ipc/_agy_probe.ps1`
- `ipc/_conpty_probe_diag.ps1`
- `ipc/_conpty_probe.ps1`
- `ipc/_conpty_probe2.ps1`
- `ipc/_probe_raw.ps1`
- possibly `ipc/tmux_bridge.ps1`

Under REV-A, these files can be inspected and classified, but not modified without stop-and-return governance review.

## 2. Full IPC Inventory Feasibility

Yes.

A complete inventory of `ipc/` is feasible. The observed IPC surface includes scripts, markdown inboxes, a SQLite database, logs, cache artifacts, probes, and documentation. The database and log artifacts should be summarized carefully as evidence; they should not be dumped into the evidence artifact.

## 3. Minimal Containment Approach

Freeze launch and dispatch first:

- disable startup scripts;
- disable watcher loops;
- disable IPC database dispatch;
- prevent markdown inbox reads as active control inputs;
- prevent message-body shell or PowerShell execution;
- prevent Codex invocation from IPC content;
- prevent Antigravity/Gemini or ConPTY invocation from IPC content;
- prevent automatic reply routing to `from_agent`.

Markdown inboxes, probes, logs, and DB artifacts should remain inert evidence. If execution-capable probe files must be made non-runnable, REV-A needs expanded edit authority.

## 4. Tests Likely Required

Focused pytest coverage is likely required for:

- complete IPC inventory and classification;
- halted startup/watchers;
- no `Invoke-Expression`, `iex`, `Invoke-Command`, `[scriptblock]::Create`, or message-body call-operator execution path;
- no `codex exec` path from inbound IPC content;
- no `agy --print`, `Invoke-ConPtyCaptureHosted`, or ConPTY invocation from inbound IPC content;
- no automatic send-back relay to `from_agent`;
- markdown inbox inertness;
- static forbidden-pattern tripwires with explicit inert-code exemptions.

## 5. Blocked File Need

No AXIOM core protected file appears required.

However, required containment may need IPC files that are not currently editable under section 7.2, especially:

- `ipc/watcher_service.ps1`
- `ipc/posture_daemon.ps1`
- `ipc/conpty_capture.ps1`
- IPC probe scripts

These are not globally blocked files, but they are outside the candidate's editable file list.

## 6. Missing Executor Surface

Yes.

Missing or under-specified executor surfaces include:

- `ipc/watcher_service.ps1`
- `ipc/posture_daemon.ps1`
- `ipc/conpty_capture.ps1`
- `ipc/_agy_hosted_test.ps1`
- `ipc/_agy_probe.ps1`
- `ipc/_conpty_probe_diag.ps1`
- `ipc/_conpty_probe.ps1`
- `ipc/_conpty_probe2.ps1`
- `ipc/_probe_raw.ps1`
- possibly `ipc/tmux_bridge.ps1`

The candidate mentions several as inspect-only, but current evidence suggests some are executable or re-armable.

## 7. Existing Test Breakage Risk

Likely low risk for core AXIOM tests if implementation stays inside `ipc/` plus new focused tests.

Possible breakage risks:

- existing tests may expect IPC artifacts, generated handoff files, or database paths to remain unchanged;
- broad static scans may accidentally fail on historical markdown, SQLite DB content, logs, or inert evidence containing forbidden strings;
- tests that scan all repository files may need precise exclusions for evidence-only IPC artifacts.

## 8. Specificity for Implementation

Mostly sufficient for the main freeze.

The underspecified area is what to do when executable probe, scratch, or support files outside section 7.2 are found. REV-A should clarify whether these files are:

- classify-only evidence;
- authorized for minimal fail-closed edits;
- quarantined by documentation only;
- renamed or moved;
- or mandatory stop-and-return blockers.

As written, the blocker language implies stop-and-return if these files are re-armable.

## 9. Go / No-Go Recommendation

Conditional no-go as written.

Implementation should proceed only after Jeremy either:

- expands the editable IPC file list to cover discovered executable and re-armable support/probe surfaces; or
- explicitly authorizes evidence-only classification for those surfaces and accepts that containment edits will stop at the current section 7.2 files.

The containment goal is feasible, but REV-A is likely to force a governance stop once the executable probe and support files are classified.
