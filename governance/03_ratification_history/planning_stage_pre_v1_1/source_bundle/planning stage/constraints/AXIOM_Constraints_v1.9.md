**AXIOM Constraints Review — Proposal v1.9**
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
| Storage | SATA SSD for paging, SQLite, atomic commits, audit logs | SATA SSD | ✓ Compliant |
| OS | Windows 11 APIs for Job Objects, pywin32, subprocess timeouts, thread management | Windows 11 | ✓ Compliant |

*\*Conditional on RAM accounting below and strict adherence to binding resource caps.*

---

### 2. RAM Accounting — Peak Sequential Load (v1.9 Delta Analysis)

Proposal v1.9 introduces deterministic enforcement mechanisms, dispatch-time budgeting, model-profile verification, and MVP scope partitioning. **No new concurrent processes, GPU workloads, or unbounded memory allocations are introduced.** Module consolidation (`watchdog.py`, `cancellation.py` removed) yields a minor memory reduction.

| Runtime Component | Estimated RAM Footprint | Change vs. v1.8.1 | Notes |
|------------------|------------------------|-------------------|-------|
| Windows 11 + Python 3.12 base | ~3.1 GB | No change | Observed baseline |
| Ollama server + qwen3:4b (Q4 quantized, memory-mapped) | ~1.8–2.2 GB | No change | Must remain quantized |
| nomic-embed-text (cached, shared process) | ~0.3–0.4 GB | No change | Shared with Ollama |
| SQLite + sqlite-vec (working set) | ~0.3–0.45 GB | No change | Batch vector ops required |
| Active agent process (context bundles ≤500 KB) | ~0.2–0.3 GB | No change | Serialized bundles only |
| Tool Gateways (active subset) | ~0.15–0.2 GB | No change | HTTP buffers, validators |
| Sandbox Gateway (Job Object + `timeout=60`) | ~0.2–0.3 GB | No change | 256 MB RAM + 60s wall-clock cap |
| Logging/audit buffers | ~0.1–0.15 GB | No change | JSONL + SQLite cache |
| Policy/Permission Engines, State Machine | ~0.05–0.1 GB | No change | Stateless rule evaluation |
| `TokenEstimator` (`resource_limits.py`) | ~0.01–0.03 GB | + New | Character-based fallback or lightweight tokenizer |
| Calibration test set (bootstrap only) | ~0.01–0.02 GB | + New | Unloaded after threshold computation |
| Thread management (4 threads) | ~0.05–0.1 GB | No change | Python threading lightweight |
| **Peak Sequential Total** | **~6.85–7.35 GB** | **Slight reduction** | **Headroom used: ~1.0–1.7 GB of 2.0–2.3 GB available** |

**Conclusion:** v1.9's additions are deterministic logic layers and schema refinements. Module consolidation slightly reduces baseline overhead. Peak RAM remains safely within observed headroom, provided all binding conditions are enforced.

---

### 3. Critical RAM Risk Points — Binding Mitigations (Updated)

1. **qwen3:4b Memory Footprint**
   - *Risk:* Full-precision or unquantized load exceeds headroom.
   - *Binding Condition:* Model must remain Q4 (or lower) quantized and memory-mapped via Ollama. No architectural change may load the model fully into RAM.

2. **sqlite-vec Vector Operations**
   - *Risk:* Unbatched searches spike memory.
   - *Binding Condition:* Vector queries must batch to **maximum 100 vectors per operation**. Deduplication checks must stream results.

3. **Context Bundle Size**
   - *Risk:* Unbounded serialized context consumes headroom.
   - *Binding Condition:* Context bundles delivered to agents must be capped at **500 KB serialized size**. Larger contexts require pagination.

4. **Sandbox Memory & Duration Limits**
   - *Risk:* Runaway sandbox triggers paging or blocks scheduler.
   - *Binding Condition:* Windows Job Object must enforce **256 MB RAM limit**. `subprocess.run(timeout=60)` (or equivalent wrapper) must enforce **60-second wall-clock cap**. 10-second termination overhead budget is acknowledged.

5. **Thread & Concurrency Cap**
   - *Risk:* Excessive thread creation fragments CPU scheduling.
   - *Binding Condition:* Phase 1 is strictly limited to **four threads** (main supervisor, Telegram, Scheduler, BootstrapValidationWorker). No additional workers or async loops.

6. **Calibration Test-Set Lifecycle**
   - *Risk:* Retaining the 120-sample JSONL in memory during autonomous operation.
   - *Binding Condition:* The calibration test set must be loaded **only during bootstrap validation**, used to compute confidence thresholds, and **unloaded from RAM** before autonomous execution begins. Only threshold constants persist.

7. **Token Estimator Implementation**
   - *Risk:* Heavy tokenizer library (e.g., full `tiktoken` BPE tables) consumes baseline RAM.
   - *Binding Condition:* If `tiktoken` or equivalent is used, it must operate in lightweight mode. The fallback `ceil(character_count / 3)` must be available and RAM-neutral. No model-weight loading for estimation.

---

### 4. API Budget Verification

| Provider | Proposal Usage | Free-Tier Status | Verdict |
|----------|---------------|------------------|---------|
| Cerebras | Primary cloud inference | Free tier, fast | ✓ Sustainable |
| Groq | Fallback (10K daily tokens) | Limit exhausted in legacy | ⚠ Requires failover testing |
| OpenRouter/SambaNova | Secondary fallbacks | Free tiers available | ✓ Sustainable |
| Brave Search API | Web search replacement | ~1,000 queries/month free | ✓ Sustainable (if confirmed) |

**Budget Enhancements in v1.9:**
1. **Dispatch-Time Token Gate:** `TokenEstimator` validates final prompt against manifest budget with **2× safety margin** before HTTP dispatch. Prevents context-bundle drift from bypassing budget. ✓
2. **Manual Reconciliation (`/reconcile_provider_usage`):** Acknowledges free-tier API opacity. Conservative charging on orphaned `started` rows prevents budget drift. Monthly ledger reset maintains auditability. ✓
3. **Per-Call Timeouts:** Hard ceilings (30s–90s) prevent runaway token consumption during network instability. ✓

**Remaining Concern:** Groq limit exhaustion remains a structural risk. v1.9 correctly implements conservative dispatch gating, but the panel should monitor fallback chain behavior during extended autonomous sessions.

---

### 5. Performance Caveats (Non-Blocking but Operational)

| Component | Expected Performance on Celeron N4500 | Impact |
|-----------|--------------------------------------|--------|
| qwen3:4b local inference (sanitization/classification) | 5–15 seconds per call | User-facing latency; set expectations |
| sqlite-vec similarity search | 100–500 ms per 100-vector batch | Acceptable for sequential workflow |
| Sandbox `subprocess.run(timeout=60)` + termination | 1–3s startup + 60s max exec + ≤10s cleanup | Predictable; aligns with 120s heartbeat threshold |
| `TokenEstimator` dispatch check | <5 ms per prompt | Negligible |
| Sequential task throughput | ~1–3 tasks/minute depending on complexity | Architecture is correct; scale via queue, not parallelism |

---

### 6. v1.9 Specification Changes — Feasibility Impact

| Change | Feasibility Impact | Verdict |
|--------|-------------------|---------|
| `last_freshness_at` heartbeat semantics | Schema addition; deterministic update logic | ✓ Neutral |
| `subprocess.run(timeout=60)` + 10s overhead | Aligns sandbox wall-clock with scheduler stale threshold | ✓ Positive |
| Calibration test-set panel authorship | Security artifact ownership; no runtime impact | ✓ Neutral |
| TaskCommitter deterministic scope only | Removes semantic reasoning from commit path | ✓ Positive (RAM/CPU reduction) |
| Per-command operator-control manifests | JSON config loading; negligible overhead | ✓ Neutral |
| Dispatch-time token counting | Lightweight estimation; prevents budget overrun | ✓ Positive |
| Model-profile fingerprint verification | Ollama metadata/file hash check; negligible RAM | ✓ Neutral |
| Orphan provider reconciliation (manual) | Operator-driven; no background process | ✓ Neutral |
| Supervisor liveness limitation acknowledgment | Documentation/operator-keepalive policy | ✓ Neutral |
| MVP module subset consolidation | Removes `watchdog.py`, `cancellation.py`; reduces footprint | ✓ Positive |

**Conclusion:** All v1.9 refinements are enforcement, auditing, and scope optimizations. Hardware demands remain identical or slightly reduced.

---

### 7. Missing Specification — Minor Blocker (Reaffirmed)

- **Web Search Backend:** Proposal references "Network Gateway" but does not explicitly confirm Brave Search API or equivalent free-tier solution. *Binding Condition:* Implementation must confirm Brave Search API (or panel-approved alternative) before enabling web search functionality.

---

### 8. Binding Ruling

**AXIOM Proposal v1.9 is FEASIBLE** on the target hardware (Intel Celeron N4500, 8 GB RAM, Windows 11, no GPU) **subject to the following binding conditions**:

1. **Sequential execution must be strictly enforced**; no concurrent agent subprocesses may be introduced without full panel consensus and revised RAM accounting.
2. **qwen3:4b must remain quantized (Q4 or lower)** and memory-mapped via Ollama; no architectural change may load the model fully into RAM.
3. **Context bundles delivered to agents must be capped at 500 KB serialized size**.
4. **Sandbox execution must enforce a 256 MB RAM limit and 60-second wall-clock cap** via Windows Job Object + `subprocess.run(timeout=60)`.
5. **sqlite-vec queries must batch vector operations** to a maximum of 100 vectors per query.
6. **Web search backend must be confirmed as Brave Search API** or panel-approved free-tier equivalent before implementation.
7. **Token estimation must enforce a 2× safety margin at dispatch**; fallback `ceil(char/3)` must remain RAM-neutral.
8. **PolicyEngine evaluations and resource limits must be stateless** and cache manifest/rule lookups.
9. **Thread count must remain limited to the four defined threads**; no additional workers may be introduced.
10. **Calibration test set must be loaded only during bootstrap** and unloaded from RAM before autonomous execution begins; only threshold constants persist.
11. **Classifier safe-pass must remain disabled** until calibration passes against panel-authored test sets with verified confidence thresholds.
12. **Model-profile fingerprint mismatch must immediately disable classifier safe-pass** and require recalibration.

If any of these conditions cannot be met during implementation, the proposal must return to the Chief Architect for revision. This ruling is **binding** per the AXIOM Panel Charter and may only be overturned by full panel consensus with written rationale.