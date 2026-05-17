I've reviewed v1.10.1 as a targeted patch. The seven items address my v1.10 objections directly—fingerprint error handling, Telegram alerts, manifest registration enforcement, token estimator coordination, WAL mode, calibration dependency acknowledgment, and test list reconciliation are all resolved in the direction I recommended or with acceptable alternatives. The patch is disciplined and doesn't introduce scope creep.

However, the new specifications contain their own edge cases and unstated assumptions. My objections follow.

---

OBJECTION 1 — 5-Second Ollama Timeout Is Unvalidated Against Target Hardware Under Load

What v1.10.1 specifies (Item 2):
model_fingerprint_verification_timeout_seconds = 5. On timeout, treat as mismatch, disable safe-pass, send Telegram alert.

What is unstated:
The expected response time of Ollama's /api/show endpoint on the Celeron N4500 under the RAM conditions described in the Constraints Register. The Constraints Reviewer's v1.9 analysis estimates qwen3:4b local inference at 5–15 seconds per call. The /api/show endpoint is a metadata query, not an inference call—it should be much faster. But under SATA SSD paging (which the Constraints Register warns will "degrade performance severely"), even a simple localhost HTTP request can stall if the Ollama process's memory pages have been evicted to disk and need to be faulted back in.

The failure mode:
A transient paging spike causes the /api/show call to take 5.1 seconds. The guard treats this as a verification failure. Safe-pass is disabled. A Telegram security alert fires. The operator receives an urgent "SECURITY ALERT" message. They stop what they're doing, physically check the laptop, and find... a paging spike. The system has degraded its own security posture and alarmed the operator over a performance hiccup.

The specification provides no distinction between "Ollama is genuinely unreachable" and "Ollama responded but slowly due to system load." Both produce a timeout. Both produce the same critical alert. Over time, the operator will learn to ignore fingerprint verification alerts—the classic alert fatigue problem.

Recommended consideration: The guard could retry once with a shorter timeout before declaring failure, or the Telegram alert for timeout could be worded differently from a genuine digest mismatch ("Model fingerprint verification delayed—system under load" vs. "Model fingerprint changed—possible tampering"). The current specification treats all failures identically.

---

OBJECTION 2 — Fingerprint Verification Failure on Current Artifact Has Unspecified Artifact Disposition

What v1.10.1 specifies (Item 2):
"current classifier-dependent decision cannot return passed" and provides a table for scanner decision based on artifact risk class.

What is unstated:
What happens to the plan artifact that was being scanned when the fingerprint check failed. The artifact has already been through PlanInjectionScanner rule evaluation up to the point where a classifier-dependent safe-pass decision was pending. The scanner now cannot complete its normal decision path.

The scanner decision table says:

· high_risk → quarantined
· ordinary → needs_human_input

But these are scanner decisions, not artifact lifecycle states. Does the artifact receive injection_scan_failed status? Does the parent planning task go to blocked or needs_human_input? Can the artifact be re-scanned later when the fingerprint check succeeds, or is it permanently tainted by the failed check? The proposal specifies the scanner's output label but not the artifact and task state transitions that follow.

Why this matters:
If a transient Ollama timeout causes a legitimate plan artifact to be quarantined, the operator needs to know whether they can re-submit the same goal (which will generate a new plan artifact and re-trigger the scanner) or whether the system is now in a state where all subsequent artifacts will hit the same degraded path until safe-pass is re-enabled. The proposal implies the latter (safe-pass stays disabled) but doesn't say whether quarantined artifacts from the degraded window can be rehabilitated after recalibration.

---

OBJECTION 3 — Manifest Registration CLI Has No Stated Database Connection Rules

What v1.10.1 specifies (Item 4):
tools/register_manifests.py is a separate CLI that computes SHA256, connects to the AXIOM database, writes manifest_fingerprints rows, and exits. It is "not imported by main AXIOM runtime" and "requires local filesystem access."

What is unstated:
How the CLI locates and connects to the AXIOM database. The main runtime connects using a database path configured at startup. The CLI needs the same path. If the operator runs the CLI with the wrong path (e.g., a development database instead of the production one), fingerprints are registered in the wrong place. The production runtime finds no matching fingerprints at boot, treats them as mismatches, and fails closed.

Additionally unstated: Whether the CLI uses the same WAL-mode pragma, whether it respects the same busy timeout, and whether it can safely run while AXIOM is stopped (which is the specified flow). If the operator accidentally runs the CLI while AXIOM is still running, two processes contend for the same SQLite database—potentially corrupting it if WAL mode checkpointing or file locking isn't handled correctly.

The specification says "Operator stops AXIOM" before running the CLI, but provides no enforcement. A well-intentioned operator following the wrong sequence should not be able to corrupt the database.

---

OBJECTION 4 — Checkpoint Token Estimator Requires a Prompt Approximation That May Diverge from Final Dispatch Prompt

What v1.10.1 specifies (Item 5):
"Checkpoint harness calls local TokenEstimator on proposed prompt/context shape."

What is unstated:
What "proposed prompt/context shape" means in practice. At checkpoint time, the Context Builder has not yet assembled the final prompt for the child task. The child task hasn't been committed to the queue yet—that's the whole point of checkpoint verification before TaskCommitter. The checkpoint harness has the proposed child task schema from the plan artifact. It has the task's input payload, role, and tool assignments. It does not have the retrieved memory chunks, the fully rendered system prompt, or the specific context bundle that will be assembled at dispatch time.

The coordination gap from v1.10 is narrowed but not closed:
The local TokenEstimator is the source of truth. But the input to the TokenEstimator at checkpoint time is an approximation of the prompt, not the actual prompt. Between checkpoint and dispatch, memory retrieval may return different results (new memories were written, the database changed). The system prompt template may include dynamic elements (session time, task ID, chain depth) that differ between checkpoint and dispatch.

If the checkpoint estimates 900 tokens and passes, but dispatch-time final prompt is 1100 tokens and fails, the task hits blocked_resource_limit at dispatch despite having passed checkpoint. The operator sees a task that was "verified" fail to execute, which confuses the chain-of-trust that checkpoint verification is meant to establish.

This is likely a minor divergence in practice (the difference between approximation and final prompt is probably small for most tasks), but the proposal should acknowledge it rather than imply checkpoint and dispatch use identical inputs. Kimi will need to specify what "proposed prompt/context shape" means concretely.

---

OBJECTION 5 — SQLite WAL Mode on SATA SSD Under Memory Pressure Has Known Checkpointing Behavior

What v1.10.1 specifies (Item 6):
PRAGMA journal_mode=WAL; with PRAGMA synchronous=FULL; and PRAGMA busy_timeout=5000;. Boot failure if WAL cannot be enabled.

What is unstated:
WAL mode creates a separate write-ahead log file (-wal) and a checkpoint file (-shm). Under sustained write load (task events, provider usage rows, gateway responses, session events, heartbeat updates, all from the sequential Scheduler loop), the WAL file grows. SQLite automatically checkpoints (merges WAL back into the main database) when the WAL file reaches a threshold (default: 1000 pages).

On a SATA SSD under memory pressure, automatic checkpointing during a long autonomous session could contend with the Scheduler's normal operations. The checkpoint is an I/O operation that reads from WAL and writes to the main database. If the main database has grown large (the Constraints Register's v1.9 analysis estimates 0.3–0.45 GB working set), checkpointing can take seconds. During checkpoint, writers block until the checkpoint completes—SQLite's WAL mode allows concurrent reads but still serializes the checkpoint with writes.

The operational risk:
A long autonomous session accumulates enough WAL pages to trigger automatic checkpointing. The checkpoint coincides with a cloud call returning and the Scheduler attempting to write provider usage and task events. The Scheduler's write blocks on the checkpoint. The heartbeat isn't updated during this block (the Scheduler is in the middle of a write, not free to write a heartbeat). If the checkpoint takes long enough, combined with the preceding cloud call, the heartbeat freshness could approach the 120-second threshold.

This is a low-probability edge case—SQLite WAL checkpointing is efficient, and 1000 pages is ~4MB, which should checkpoint quickly even on SATA SSD. But the interplay between WAL checkpointing, SATA SSD I/O contention, and heartbeat freshness is not analyzed in the proposal.

Recommended: Add a note that if WAL checkpointing latency becomes operationally significant, the auto-checkpoint threshold can be adjusted or passive checkpointing (which doesn't block writers) can be enabled.

---

OBJECTION 6 — No Aggregation or Rate-Limiting for Fingerprint-Related Telegram Alerts

What v1.10.1 specifies (Item 3):
Any fingerprint mismatch or verification failure sends an immediate Telegram alert.

The edge case:
The fingerprint guard runs before every classifier-dependent safe-pass decision. If the Ollama model has genuinely been replaced mid-session, every subsequent plan artifact that reaches the safe-pass evaluation stage will trigger the guard, detect the mismatch, and send a Telegram alert. In a session with multiple planning cycles, this could produce dozens of identical alerts flooding the operator's Telegram chat.

The operator already knows after the first alert that safe-pass is disabled and the model fingerprint changed. The subsequent alerts provide no new information and make it harder to find other messages (status responses, task outputs) in the chat.

The specification says nothing about alert deduplication, rate-limiting, or suppression of repeat alerts for the same root cause within the same session. The Telegram Gateway is on its own thread and capable of sending many messages quickly.

---

Summary of Objections

# Category Core Issue
1 Edge Case 5-second fingerprint timeout unvalidated against paging-loaded Celeron N4500; transient slowness triggers critical alert and safe-pass disablement
2 Specification Gap Artifact disposition after fingerprint-related scanner failure is unspecified; unclear if artifacts are permanently quarantined or re-scannable
3 Operational Risk Manifest registration CLI has unspecified database connection rules; risk of wrong-path registration or accidental concurrent access
4 Coordination Gap Checkpoint token estimation uses prompt approximation, not final dispatch prompt; minor divergence likely between checkpoint and dispatch estimates
5 Edge Case WAL checkpointing on SATA SSD under sustained write load could contend with scheduler writes; not analyzed for heartbeat freshness impact
6 Usability Gap No rate-limiting or deduplication on fingerprint-related Telegram alerts; repeated alerts from same root cause could flood operator chat

None of these are blocking for architectural validity. They are edge cases and specification gaps that will become implementation details for Kimi or operational observations for the first autonomous session. None rise to the level of a security boundary violation or a Core Value contradiction.

The patch successfully resolves my v1.10 objections. The architecture as specified in v1.10.1 is the most complete and internally consistent version the panel has produced. I recommend the Evaluator confirm coherence on the delta, and the panel advance to Kimi for implementation planning.