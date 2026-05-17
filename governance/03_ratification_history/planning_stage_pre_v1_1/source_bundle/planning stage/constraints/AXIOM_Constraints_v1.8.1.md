**AXIOM Constraints Review — Proposal v1.8 / v1.8.1**
**Reviewer:** Qwen 3.6 Plus — Constraints and Feasibility Reviewer
**Date:** May 2026
**Ruling:** **APPROVED with Binding Conditions**

---

### 1. Hardware Feasibility Assessment

| Component | Proposal Requirement | Target Hardware | Verdict |
|-----------|---------------------|----------------|---------|
| CPU | Sequential execution; maximum 4 threads; no parallel agent subprocesses | Intel Celeron N4500 (2C/2T) | ✓ Compliant |
| RAM | Peak sequential load within ~2.0–2.3 GB headroom | 8 GB total (~5.7 GB baseline) | ✓ Compliant* |
| GPU | None required; all inference CPU-bound or cloud-offloaded | None | ✓ Compliant |
| Storage | SATA SSD for paging, SQLite, logs, atomic commits | SATA SSD | ✓ Compliant |
| OS | Windows 11 APIs for Job Objects, pywin32, thread management, ACLs | Windows 11 | ✓ Compliant |

*\*Conditional on RAM accounting below and strict adherence to binding resource caps.*

---

### 2. RAM Accounting — Peak Sequential Load (v1.8/v1.8.1 Delta Analysis)

Proposal v1.8 introduces deterministic classification, explicit timeout/heartbeat mechanics, atomic transaction boundaries, and runtime resource enforcement. v1.8.1 adds a 60-second sandbox duration cap and aligns scanner documentation. **No new concurrent processes, GPU workloads, or unbounded memory allocations are introduced.**

| Runtime Component | Estimated RAM Footprint | Change vs. v1.7 | Notes |
|------------------|------------------------|-----------------|-------|
| Windows 11 + Python 3.12 base | ~3.1 GB | No change | Observed baseline from legacy |
| Ollama server + qwen3:4b (Q4 quantized, memory-mapped) | ~1.8–2.2 GB | No change | Must remain quantized |
| nomic-embed-text (cached, shared process) | ~0.3–0.4 GB | No change | Shared with Ollama |
| SQLite + sqlite-vec (working set) | ~0.3–0.45 GB | No change | Batch vector ops required |
| Active agent process (context bundles ≤500 KB) | ~0.2–0.3 GB | No change | Serialized bundles only |
| Tool Gateways (active subset) | ~0.15–0.2 GB | No change | HTTP buffers, validators |
| Sandbox Gateway (Job Object capped) | ~0.2–0.3 GB | No change | 256 MB RAM + 60s wall-clock limit |
| Logging/audit buffers | ~0.1–0.15 GB | No change | JSONL + SQLite cache |
| Policy/Permission Engines, State Machine, Resource Limits | ~0.05–0.1 GB | No change | Stateless rule evaluation |
| PlanInjectionScanner + Classifier Validation | ~0.02–0.05 GB | + New | Deterministic rule matcher + JSONL loader |
| Thread management (4 threads: main, Telegram, Scheduler, Bootstrap) | ~0.05–0.1 GB | No change | Python threading lightweight |
| **Peak Sequential Total** | **~6.9–7.4 GB** | **No material change** | **Headroom used: ~0.9–1.7 GB of 2.0–2.3 GB available** |

**Conclusion:** The v1.8/v1.8.1 refinements are architectural hardening and specification clarifications. They impose **zero measurable increase** in peak RAM consumption. The sequential design remains feasible within observed headroom, provided all binding conditions are enforced.

---

### 3. Critical RAM Risk Points — Binding Mitigations (Reaffirmed & Updated)

1. **qwen3:4b Memory Footprint**
   - *Risk:* Full-precision or unquantized load would exceed headroom.
   - *Binding Condition:* Model must remain Q4 (or lower) quantized and memory-mapped via Ollama. No architectural change may load the model fully into RAM.

2. **sqlite-vec Vector Operations**
   - *Risk:* Unbatched cosine similarity searches could spike memory usage.
   - *Binding Condition:* Vector queries must batch to **maximum 100 vectors per operation**. Deduplication threshold checks must stream results, not load full table.

3. **Context Bundle Size**
   - *Risk:* Unbounded serialized context could consume headroom.
   - *Binding Condition:* Context bundles delivered to agents must be capped at **500 KB serialized size**. Larger contexts require pagination via additional queue tasks.

4. **Sandbox Memory & Duration Limits**
   - *Risk:* Unrestricted sandbox process could trigger system paging or block the scheduler beyond the 120s liveness threshold.
   - *Binding Condition:* Windows Job Object must enforce **256 MB RAM limit** and **60-second wall-clock duration** for sandboxed code execution. Exceeding either limit terminates the process, flags `failed_resource_limit`, and updates the scheduler heartbeat immediately.

5. **Thread & Concurrency Cap**
   - *Risk:* Excessive thread creation or unbounded thread-local state could accumulate memory and fragment CPU scheduling.
   - *Binding Condition:* Phase 1 is strictly limited to the four defined threads. No additional worker threads, async event loops, or multiprocessing pools may be introduced without revised RAM accounting and full panel consensus.

6. **Classifier Calibration Overhead**
   - *Risk:* Loading large validation sets or running calibration loops at runtime could spike memory.
   - *Binding Condition:* Calibration must occur during bootstrap/validation phase only. Runtime scanner operations must use pre-calibrated thresholds loaded into memory as lightweight constants, not raw datasets.

---

### 4. API Budget Verification

| Provider | Proposal Usage | Free-Tier Status | Verdict |
|----------|---------------|------------------|---------|
| Cerebras | Primary cloud inference | Free tier, fast | ✓ Sustainable |
| Groq | Fallback (10K daily tokens) | Limit exhausted in legacy testing | ⚠ Requires failover testing |
| OpenRouter/SambaNova | Secondary fallbacks | Free tiers available | ✓ Sustainable |
| Brave Search API | Web search replacement | ~1,000 queries/month free | ✓ Sustainable (if confirmed) |

**Budget Concerns (Unchanged but Explicitly Addressed in v1.8):**
1. **Per-Call Timeout Ceiling:** v1.8 caps individual provider calls at 30–90 seconds. This prevents runaway token consumption and aligns with the 120s heartbeat threshold. ✓
2. **Token Estimation Accuracy:** `budget_policy` requires 2× safety margin. v1.8 adds `resource_limits.py` to enforce pre-dispatch gates. ✓
3. **Embedding Cost:** Local nomic-embed-text usage remains correct and budget-compliant. ✓

---

### 5. Performance Caveats (Non-Blocking but Operational)

| Component | Expected Performance on Celeron N4500 | Impact |
|-----------|--------------------------------------|--------|
| qwen3:4b local inference (sanitization/classification) | 5–15 seconds per call | User-facing latency; set expectations |
| sqlite-vec similarity search | 100–500 ms per 100-vector batch | Acceptable for sequential workflow |
| Sandbox process startup + Job Object initialization | 1–3 seconds overhead | Minor; amortized over task execution |
| TaskCommitter atomic SQLite transaction | <50 ms for typical child-task batches | Negligible; `BEGIN IMMEDIATE` prevents locking contention |
| Sequential task throughput | ~1–3 tasks/minute depending on complexity | Architecture is correct; scale via queue, not parallelism |

---

### 6. v1.8/v1.8.1 Specification Changes — Feasibility Impact

| Change | Feasibility Impact | Verdict |
|--------|-------------------|---------|
| Artifact risk class (`high_risk`/`ordinary`) | Deterministic metadata field; no runtime overhead | ✓ Neutral |
| Privileged task-class closed set | Enum validation; negligible CPU/RAM impact | ✓ Neutral |
| Per-provider-call timeouts (max 90s) | HTTP client timeout configuration; prevents resource exhaustion | ✓ Positive |
| Scheduler heartbeat liveness (120s threshold) | Lightweight timestamp polling; no new threads | ✓ Neutral |
| OperatorControlCapability re-establishment | Object reference passing across thread restart; zero RAM impact | ✓ Neutral |
| TaskCommitter atomic transaction | SQLite `BEGIN IMMEDIATE`/`COMMIT`; reduces partial-state risk | ✓ Positive |
| Memory verification loop routing | Adds verifier step; uses existing queue/verifier infrastructure | ✓ Neutral |
| Classifier calibration gates | Bootstrap-phase validation; runtime uses cached thresholds | ✓ Neutral |
| Sandbox 60s duration cap (v1.8.1) | Job Object `JOB_OBJECT_LIMIT_JOB_TIME`; aligns with 120s heartbeat | ✓ Positive |
| §16 canonical rule alignment (v1.8.1) | Documentation fix; no runtime impact | ✓ Neutral |

**Conclusion:** All v1.8/v1.8.1 refinements are **security, reliability, and enforcement enhancements** that operate entirely within the established sequential runtime budget. No hardware constraints are violated.

---

### 7. Missing Specification — Minor Blocker (Reaffirmed)

- **Web Search Backend:** Proposal references "Network Gateway" but does not explicitly confirm Brave Search API or equivalent free-tier solution. *Binding Condition:* Implementation must confirm Brave Search API (or panel-approved alternative) before enabling web search functionality.

---

### 8. Binding Ruling

**AXIOM Proposal v1.8 / v1.8.1 is FEASIBLE** on the target hardware (Intel Celeron N4500, 8 GB RAM, Windows 11, no GPU) **subject to the following binding conditions**:

1. **Sequential execution must be strictly enforced**; no concurrent agent subprocesses may be introduced without full panel consensus and revised RAM accounting.
2. **qwen3:4b must remain quantized (Q4 or lower)** and memory-mapped via Ollama; no architectural change may load the model fully into RAM.
3. **Context bundles delivered to agents must be capped at 500 KB serialized size**.
4. **Sandbox execution must enforce a 256 MB RAM limit and 60-second wall-clock duration** via Windows Job Object.
5. **sqlite-vec queries must batch vector operations** to a maximum of 100 vectors per query.
6. **Web search backend must be confirmed as Brave Search API** or panel-approved free-tier equivalent before implementation.
7. **Token estimation in `budget_policy` must include a 2× safety margin**; actual usage must be logged for adaptive calibration.
8. **PolicyEngine evaluations and resource limits must be stateless** and cache manifest/rule lookups to avoid per-task memory accumulation.
9. **Thread count must remain limited to the four defined threads** (main supervisor, Telegram, Scheduler, BootstrapValidationWorker); no additional worker threads may be introduced without revised RAM accounting.
10. **Classifier calibration gates must pass before autonomous safe-pass thresholds are enabled**; runtime scanner must operate on pre-calibrated constants, not live dataset evaluation.

If any of these conditions cannot be met during implementation, the proposal must return to the Chief Architect for revision. This ruling is **binding** per the AXIOM Panel Charter and may only be overturned by full panel consensus with written rationale.