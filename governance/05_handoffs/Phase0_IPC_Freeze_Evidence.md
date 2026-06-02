# Phase 0 IPC Freeze Evidence

Accepted Mandate ID: `MND-ACCEPTED-2026-0001-PHASE0-IPC-FREEZE`

Source Candidate ID: `MND-CANDIDATE-2026-0001-REV-C`

Status: Candidate-derived implementation evidence only. No doctrine change was performed. No `VERIFIED_COMMIT` claim is made.

AXIOM remains non-autonomous by design. IPC execution is structurally frozen for Phase 0 only; this is not Level 2A acceptance.

## Implementation Summary

The implementation captured a pre-modification IPC manifest, inserted uniform default-active fail-closed guards into execution-capable IPC PowerShell surfaces, neutralized executable `command` message type handling in `$AXIOM_WORKSPACE/ipc/ipc_db.py`, added focused source-analysis tests, updated IPC documentation narrowly, stopped one pre-existing active IPC service process, and verified that no IPC watcher/executor process remained active.

Terminal recommendation: `VERIFIED_EVIDENCE_RECORDED`.

## Generalized Unsafe Sink Model

A generalized unsafe sink is any inbound-message-reachable path that can spawn a process, evaluate shell or PowerShell content, invoke Codex, invoke Antigravity/Gemini, invoke ConPTY, inject tmux or terminal input, launch hidden shell hosts, read markdown inboxes and transition state, read IPC database pending rows and transition state, mutate IPC database state based on inbound content, produce outbound agent-directed sends, or open/use local non-file IPC channels in an execution-capable way.

Static forbidden-string scans were used only as secondary tripwires.

## Dominant Guard Pattern

PowerShell files use this uniform guard before unsafe sinks:

```powershell
$script:IPC_PHASE0_FREEZE_ACTIVE = $true
if ($script:IPC_PHASE0_FREEZE_ACTIVE) {
    Write-Output "[ipc-freeze] Phase 0 IPC freeze active; unsafe IPC execution path is structurally unreachable."
    return
}
```

For scripts with `param(...)`, the guard appears immediately after the parameter block because PowerShell requires `param` to be the first non-comment statement.

Python IPC command neutralization uses default-active `IPC_PHASE0_FREEZE_ACTIVE = True` and has no environment or command-line bypass.

## Mechanical Inventory Reconciliation

Directory-walk path count: `36`

Classification row count: `36`

Reconciliation result: `classification_row_count == directory_walk_path_count`

Every walked path has one SHA-256 hash, size, classification, and containment status.

## Pre-Modification SHA-256 Baseline

This baseline was captured before containment edits. It represents the current working tree at implementation time.

| Path | Size bytes | SHA-256 |
| --- | ---: | --- |
| ipc/_agy_hosted_test.ps1 | 283 | 3f722a78818b497152f979ddffe7ef0e726b98c05115caf3bf4808ce9a05d33c |
| ipc/_agy_hosted_test.txt | 15 | f2f2e0f2d7d779d57c033e67360ccbb6af40c1a714707badd9d7063b0e8d2fd1 |
| ipc/_agy_probe_stdout.txt | 857 | b6f9ea3275d8f0b858128c30464a4471b1eecf9b9e6ee735f41be99f7b28bdb5 |
| ipc/_agy_probe.ps1 | 272 | 20969c9183e11a0ccd3ab905e585f06e6b3bbd4456303fb429cf1e90cf6215f2 |
| ipc/_agy_probe.txt | 72 | 78e248c6666fcecb6961be9a03ac0f19004f0a8a2b94a866163a82ad0aed1381 |
| ipc/_conpty_probe_diag.ps1 | 179 | 1b41ccfefc185a7caae67a61f6cf9634e4fce970fbeda5f02acfd9d8a0ef8353 |
| ipc/_conpty_probe.ps1 | 267 | b758bb2961e7c2bd4be4ce3764cbb9318dc3f0557b894d85d807a678fbdd495e |
| ipc/_conpty_probe.txt | 23 | 17c9d9f02656121f3a54fc86c8cc20a83735ca0d1ddab40fbd330dc7ef72fb59 |
| ipc/_conpty_probe2.ps1 | 488 | 7878dede00646eede52cb13ff54e3a23d5a346c0f593d0a7f50298fb2ac08c06 |
| ipc/_inbox_antigravity.ps1 | 5781 | 7cdc873d30afc107e77f2781a7cb3936c4437d4a6eb1a902abca7546523d4b22 |
| ipc/_inbox_claude.ps1 | 3603 | ed2048427c0b4938c77f10e4fe632d29061640d74619a67e461a15d0cc140258 |
| ipc/_inbox_codex.ps1 | 5584 | da8dc76669af191318265f2bc4f368ba04222ea3307e8a604a579f8e93701c09 |
| ipc/_posture_runspace.ps1 | 2001 | 75fa9168cda97cdefede06b6efdc68bab7ab6f6679ed5606efbc8c812c2fd77e |
| ipc/_probe_diag.txt | 118 | 3f5b5d05b3055c23692b3840bf9a6ed34a1fbaea7a019eea76d2700414be2c3d |
| ipc/_probe_raw.ps1 | 724 | 3f3f846dbb7caacc7a090a27cee12dfe1edd74ee67c1e4761d3a366b5cc65d7a |
| ipc/_probe_raw.txt | 409 | 6df08f7dc3baf66fd4ce3bd1873b0e715052184b41da0df40b8c1be11e8bfedc |
| ipc/agent_bridge.ps1 | 3453 | 5d3ba889ee0953a49e996c4842ff318877fb14d472680aad9328785f62e84faa |
| ipc/conpty_capture.ps1 | 19088 | e72fadf289b2252edaf25b50c51c592a7805085d30d5fe6b968ba41c9174afbe |
| ipc/ipc_db.py | 12626 | a0b7cb5b6cf1bcf3cf09279ce5f5819de91ec153c5afb9e78a9c6a66333f4869 |
| ipc/ipc_messages.db | 65536 | 097f8a03e519f2d1faba0a968e868eb6760636beda50b881fe250868e07d525f |
| ipc/ipc_service.ps1 | 3032 | 6c733e8ab44df34412a441cacd08272bcf23d38fc400049afd1084f89257dce2 |
| ipc/loop_watcher.ps1 | 2098 | 9e48a498980fbb5a9c4e9d4050fc024340bf1c0922f2fd36e3e525b78c434d82 |
| ipc/notify.ps1 | 222 | 0c5ba36f12e48779a4efa3741ac4cfd187c7acb19b39b4cd07459d768fd4b60b |
| ipc/posture_cache.json | 1812 | 9104621e699200b588d699e96f1febb15874b794a28e2edbeb0c951a7c97245f |
| ipc/posture_daemon.log | 246895 | ea54452a7b5786aac2ba4f3e51d1ed613398a7d057d76228be56f0c99385fc23 |
| ipc/posture_daemon.ps1 | 3061 | c7bfd80f9259ac5f903060f9eb960d43c5acf21ffc8fb7282ba852633e9c57de |
| ipc/README.md | 869 | 7449302af34d4d73ac0335075277f558b9d6f36afdb64235e849f800ea796958 |
| ipc/send.ps1 | 1342 | aefd52ce888d22d4198187233b655d8c2379e87d503b4beaf35d6e834664f907 |
| ipc/startup_agy.ps1 | 384 | d982f626bab4befc97e7c276fc4ab4315a5fbef85feb774b7f8512a742290618 |
| ipc/startup_claude.ps1 | 486 | 1b597e06ca9d6d73fadb0f07af8ac9739ce64ee319e12a9351899af572e91dd7 |
| ipc/startup_codex.ps1 | 368 | 79004d2c3261ffc78ab218c39103af2afc64cd710427571ea779eca95b1324ef |
| ipc/tmux_bridge.ps1 | 3546 | e00f4fbdf629f0aa8cc34346e16509c5907a86f7f41da130499347dabc629845 |
| ipc/to_antigravity.md | 9181 | b33c1267e2430a75d280f31cc71fae6d859ee99120b230c76629eb8d71705052 |
| ipc/to_claude.md | 958 | 9a6ed9d3a607ab585adbf033c586eecefd3530dfdb5c0a73937e558482c54ab0 |
| ipc/to_codex.md | 23311 | eac87a1cb44dcb622b4cc19ee3338afea68cd34b73bae1cee6268e5383d01675 |
| ipc/watcher_service.ps1 | 1159 | e8caad4a57eacfa632fe7786b9ca5ccdea6ba4b4a0002a9e46ea05f3e5b0ccdd |

## Classification Table

| Path | Classification | Containment status |
| --- | --- | --- |
| ipc/_agy_hosted_test.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_agy_hosted_test.txt | documentation_or_evidence | inert_evidence |
| ipc/_agy_probe_stdout.txt | documentation_or_evidence | inert_evidence |
| ipc/_agy_probe.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_agy_probe.txt | documentation_or_evidence | inert_evidence |
| ipc/_conpty_probe_diag.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_conpty_probe.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_conpty_probe.txt | documentation_or_evidence | inert_evidence |
| ipc/_conpty_probe2.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_inbox_antigravity.ps1 | executor | guarded_fail_closed |
| ipc/_inbox_claude.ps1 | executor | guarded_fail_closed |
| ipc/_inbox_codex.ps1 | executor | guarded_fail_closed |
| ipc/_posture_runspace.ps1 | posture_or_status_daemon | guarded_fail_closed |
| ipc/_probe_diag.txt | documentation_or_evidence | inert_evidence |
| ipc/_probe_raw.ps1 | probe_or_scratch | guarded_fail_closed |
| ipc/_probe_raw.txt | documentation_or_evidence | inert_evidence |
| ipc/agent_bridge.ps1 | executor | guarded_fail_closed |
| ipc/conpty_capture.ps1 | conpty_or_terminal_bridge | guarded_fail_closed |
| ipc/ipc_db.py | database_index | command_type_neutralized |
| ipc/ipc_messages.db | runtime_artifact | inert_evidence |
| ipc/ipc_service.ps1 | watcher | guarded_fail_closed |
| ipc/loop_watcher.ps1 | watcher | guarded_fail_closed |
| ipc/notify.ps1 | notification_helper | guarded_fail_closed |
| ipc/posture_cache.json | runtime_artifact | inert_evidence |
| ipc/posture_daemon.log | runtime_artifact | inert_evidence |
| ipc/posture_daemon.ps1 | posture_or_status_daemon | guarded_fail_closed |
| ipc/README.md | documentation_or_evidence | freeze_documented |
| ipc/send.ps1 | transport | guarded_fail_closed |
| ipc/startup_agy.ps1 | startup_launcher | guarded_fail_closed |
| ipc/startup_claude.ps1 | startup_launcher | guarded_fail_closed |
| ipc/startup_codex.ps1 | startup_launcher | guarded_fail_closed |
| ipc/tmux_bridge.ps1 | conpty_or_terminal_bridge | guarded_fail_closed |
| ipc/to_antigravity.md | historical_inbox | inert_evidence |
| ipc/to_claude.md | historical_inbox | inert_evidence |
| ipc/to_codex.md | historical_inbox | inert_evidence |
| ipc/watcher_service.ps1 | watcher | guarded_fail_closed |

## Composition Graph Summary

Traversal was bounded to three nested layers. No unresolved edge exceeded the traversal bound.

| Edge type | Source | Target / sink | Containment |
| --- | --- | --- | --- |
| startup edge | ipc/startup_claude.ps1 | ipc/watcher_service.ps1, ipc/ipc_service.ps1, ipc/tmux_bridge.ps1, CLI `claude` | source guard before all edges |
| startup edge | ipc/startup_codex.ps1 | ipc/watcher_service.ps1, ipc/tmux_bridge.ps1, CLI `codex` | source guard before all edges |
| startup edge | ipc/startup_agy.ps1 | ipc/watcher_service.ps1, ipc/tmux_bridge.ps1, CLI `agy` | source guard before all edges |
| runspace edge | ipc/ipc_service.ps1 | ipc/_inbox_claude.ps1, ipc/_inbox_codex.ps1, ipc/_inbox_antigravity.ps1, ipc/_posture_runspace.ps1 | service guard before runspace pool creation |
| dot-source edge | ipc/_inbox_antigravity.ps1 | ipc/conpty_capture.ps1 | inbox guard before dot-source |
| dot-source edge | ipc/agent_bridge.ps1 | ipc/conpty_capture.ps1 | bridge guard before dot-source |
| dot-source edge | IPC probe scripts | ipc/conpty_capture.ps1 | probe guards before dot-source |
| watcher edge | ipc/_inbox_*.ps1, ipc/agent_bridge.ps1, ipc/loop_watcher.ps1, ipc/watcher_service.ps1 | `FileSystemWatcher` | guard before watcher creation |
| database dispatch edge | ipc/_inbox_*.ps1, ipc/agent_bridge.ps1, ipc/loop_watcher.ps1 | `ipc_db.py pending --agent` | guard before pending reads |
| outbound send edge | inbox/bridge/watcher scripts | ipc/send.ps1 to `$msg.from_agent` | guard before send branch; send.ps1 also guarded |
| terminal edge | ipc/tmux_bridge.ps1 | tmux/psmux `send-keys` and capture | bridge guard before function definitions |
| ConPTY edge | ipc/conpty_capture.ps1 and callers | ConPTY class/functions and hidden host launch | guard before Add-Type/function definitions |

## File Groups

Executor files found: `ipc/_inbox_antigravity.ps1`, `ipc/_inbox_claude.ps1`, `ipc/_inbox_codex.ps1`, `ipc/agent_bridge.ps1`.

Watcher files found: `ipc/ipc_service.ps1`, `ipc/loop_watcher.ps1`, `ipc/watcher_service.ps1`.

Startup-launcher files found: `ipc/startup_agy.ps1`, `ipc/startup_claude.ps1`, `ipc/startup_codex.ps1`.

Transport/database files found: `ipc/send.ps1`, `ipc/ipc_db.py`, `ipc/ipc_messages.db`.

ConPTY/tmux/terminal bridge files found: `ipc/conpty_capture.ps1`, `ipc/tmux_bridge.ps1`.

Posture/status daemon files found: `ipc/posture_daemon.ps1`, `ipc/_posture_runspace.ps1`, `ipc/posture_cache.json`, `ipc/posture_daemon.log`.

Markdown inbox files preserved as inert evidence: `ipc/to_antigravity.md`, `ipc/to_claude.md`, `ipc/to_codex.md`.

Probe/scratch files found: `ipc/_agy_hosted_test.ps1`, `ipc/_agy_probe.ps1`, `ipc/_conpty_probe_diag.ps1`, `ipc/_conpty_probe.ps1`, `ipc/_conpty_probe2.ps1`, `ipc/_probe_raw.ps1`.

Runtime artifacts found: `ipc/ipc_messages.db`, `ipc/posture_cache.json`, `ipc/posture_daemon.log`.

## Non-File IPC Channel Inventory

Named mutex: `ipc/send.ps1` contains a global named mutex writer edge; it is guarded before mutex creation.

Background runspaces: `ipc/ipc_service.ps1` creates runspace pool edges; it is guarded before runspace pool creation.

ConPTY/terminal handles: `ipc/conpty_capture.ps1` contains ConPTY session creation and hidden host launch logic; it is guarded before type loading and function definitions. Probe callers are also guarded before dot-sourcing.

Tmux/psmux terminal ingress: `ipc/tmux_bridge.ps1` contains tmux/psmux discovery, send-keys, new-session, and capture-pane logic; it is guarded before function definitions.

Loopback listeners, local socket listeners, shared-memory handles: no active source edge found in `$AXIOM_WORKSPACE/ipc/`.

Posture daemon channels: posture daemon and runspace cache refreshers are guarded before loops and Python calls.

## `ipc_db.py` Command Neutralization Summary

`$AXIOM_WORKSPACE/ipc/ipc_db.py` now defines `IPC_PHASE0_FREEZE_ACTIVE = True` and `IPC_PHASE0_NEUTRALIZED_COMMAND_TYPE = "phase0-frozen-command"`.

At write ingress, `type=command` is normalized to `phase0-frozen-command`.

Pending-message retrieval excludes both historical `command` rows and neutralized `phase0-frozen-command` rows. No AXIOM core schema or persistence file was modified.

## Before / After Unsafe Mechanisms

Before containment, IPC scripts contained reachable `FileSystemWatcher` loops, database pending dispatch, `Invoke-Expression`, `codex exec`, `Invoke-ConPtyCaptureHosted`, ConPTY session probes, tmux send-keys support, startup relaunches, posture daemons, markdown inbox reads, and auto-send-to-`from_agent` relay branches.

After containment, those branches remain as historical source but are structurally unreachable behind default-active guards. Startup scripts fail closed before watcher/service/terminal/CLI launch. `ipc_service.ps1` fails closed before runspace pool creation. `ipc_db.py` neutralizes executable `command` message types at write ingress and pending retrieval.

## Files Changed

- `ipc/_agy_hosted_test.ps1`
- `ipc/_agy_probe.ps1`
- `ipc/_conpty_probe_diag.ps1`
- `ipc/_conpty_probe.ps1`
- `ipc/_conpty_probe2.ps1`
- `ipc/_inbox_antigravity.ps1`
- `ipc/_inbox_claude.ps1`
- `ipc/_inbox_codex.ps1`
- `ipc/_posture_runspace.ps1`
- `ipc/_probe_raw.ps1`
- `ipc/agent_bridge.ps1`
- `ipc/conpty_capture.ps1`
- `ipc/ipc_db.py`
- `ipc/ipc_service.ps1`
- `ipc/loop_watcher.ps1`
- `ipc/notify.ps1`
- `ipc/posture_daemon.ps1`
- `ipc/README.md`
- `ipc/send.ps1`
- `ipc/startup_agy.ps1`
- `ipc/startup_claude.ps1`
- `ipc/startup_codex.ps1`
- `ipc/tmux_bridge.ps1`
- `ipc/watcher_service.ps1`
- `tests/test_ipc_phase0_freeze.py`
- `governance/05_handoffs/Phase0_IPC_Freeze_Evidence.md`

## Files Inspected But Unchanged

- `ipc/_agy_hosted_test.txt`
- `ipc/_agy_probe_stdout.txt`
- `ipc/_agy_probe.txt`
- `ipc/_conpty_probe.txt`
- `ipc/_probe_diag.txt`
- `ipc/_probe_raw.txt`
- `ipc/ipc_messages.db`
- `ipc/posture_cache.json`
- `ipc/posture_daemon.log`
- `ipc/to_antigravity.md`
- `ipc/to_claude.md`
- `ipc/to_codex.md`

## Blocked Files Confirmed Untouched

No implementation edits were made to `governance/01_live_spine/`, `governance/06_archives/`, `axiom/core/`, `axiom/persistence/`, `axiom/security/`, `axiom/gateways/`, `axiom/app/`, `axiom/agents/`, `axiom/policy/`, `config/axiom.yaml`, or `requirements.txt`.

Pre-existing modifications in some blocked/live-spine files were observed before implementation and were not touched by this implementation.

## Process-Tree Validation Summary

Initial process inspection found one pre-existing `pwsh.exe` process launched with `$AXIOM_WORKSPACE/ipc/ipc_service.ps1`.

That process was stopped as part of the Phase 0 IPC halt.

Follow-up process-tree validation returned zero matching IPC watcher, executor, posture daemon, agent bridge, inbox handler, or IPC service processes.

## Side-Channel Ingress Result

Method: source-analysis plus process-tree evidence.

No active IPC process remains to observe markdown inbox changes. Startup and watcher source paths are guarded before watcher creation, inbox reads, database dispatch, and outbound sends. Therefore markdown inbox files are inert evidence in the current contained state.

## Tests Added Or Updated

- `tests/test_ipc_phase0_freeze.py`

## Test Method Disclosure

- Inventory reconciliation: source-analysis.
- Pre-modification hash baseline presence: source-analysis against this evidence artifact.
- Dominant guard placement: source-analysis.
- Generalized sink unreachability: source-analysis plus static tripwire.
- `ipc_service.ps1` composed-service safety: source-analysis.
- Startup launcher fail-closed behavior: source-analysis.
- `ipc_db.py` command-type neutralization: source-analysis.
- Markdown inbox inertness: source-analysis.
- Static tripwire scan: static tripwire.
- Process-tree validation: process-tree evidence.
- Side-channel ingress: source-analysis plus process-tree evidence.

Behavioral launching of the PowerShell services was avoided because source-level structural unreachability is the primary proof and launching legacy services would be riskier than source inspection for this containment slice.

## Test Result Summary

Focused pytest module added: `tests/test_ipc_phase0_freeze.py`.

Attempted pytest verification:

- `.\venv\Scripts\python.exe -m pytest tests\test_ipc_phase0_freeze.py -q` failed because the venv launcher points to a missing local Python interpreter.
- `python -m pytest tests\test_ipc_phase0_freeze.py -q` failed because `python` is not available through PATH.
- `py --version` reported no installed Python.
- `.\venv\Scripts\pytest.exe tests\test_ipc_phase0_freeze.py -q` failed with the same missing venv interpreter.

PowerShell verification performed because Python execution was unavailable:

- Inventory reconciliation: `ActualCount=36`, `ExpectedCount=36`, no missing paths, no extra paths.
- Dominant guard placement source check: every IPC `.ps1` file had `IPC_PHASE0_FREEZE_ACTIVE = $true`; detected sink lines were after guard lines.
- PowerShell parser check: passed for all IPC `.ps1` files.
- `ipc_db.py` source check: confirmed default-active freeze constant, neutralized command type, `neutralize_message_type`, `command` normalization, and pending-query exclusion.
- Process-tree validation: final matching IPC watcher/executor process count was `0`.

Python-based pytest verification was not performed because no usable Python interpreter is available in the current environment.

## Residual Risks

Unsafe source code remains present by mandate design, but is guarded as structurally unreachable.

Historical markdown, database, and log artifacts still contain old IPC content and forbidden strings as inert evidence.

The pre-modification baseline includes runtime artifacts whose sizes and hashes can change if unrelated background processes write to them after the baseline capture.

No Orchestrator, Mandate signing, verifier account, model call, cloud call, network gateway call, sandbox execution, Telegram control, or memory embedding pathway was built or activated.

## Audit Distinction

Successful Phase 0 terminal state is `VERIFIED_EVIDENCE_RECORDED`.

`VERIFIED_COMMIT` is not claimed and is not authorized.
