**AXIOM Constraints Review — Proposal v1.7**
**Reviewer:** Qwen 3.6 Plus — Constraints and Feasibility Reviewer
**Date:** May 2026
**Ruling:** **APPROVED with Binding Conditions**

---

### 1. Hardware Feasibility Assessment

| Component | Proposal Requirement | Target Hardware | Verdict |
|-----------|---------------------|----------------|---------|
| CPU | Sequential execution; no parallel agent subprocesses | Intel Celeron N4500 (2C/2T) | ✓ Compliant |
| RAM | Peak sequential load within ~2.0–2.3 GB headroom | 8 GB total (~5.7 GB baseline) | ✓ Compliant* |
| GPU | None required; all inference CPU-bound or cloud-offloaded | None | ✓ Compliant |
| Storage | SATA SSD for paging, SQLite, logs | SATA SSD | ✓ Compliant |
| OS | Windows 11 APIs for Job Objects, pywin32, thread management | Windows 11 | ✓ Compliant |

*\*Conditional on RAM accounting below and adherence to prior binding conditions.*

---

### 2. RAM Accounting — Peak Sequential Load (v1.7 Delta Analysis)

Proposal v1.7 is a **targeted specification revision** resolving four implementation-facing ambiguities. It introduces **no new runtime components**, **no additional concurrent processes**, and **no increased memory footprint** beyond the v1.3.2 baseline.

| Runtime Component | Estimated RAM Footprint | Change vs. v1.3.2 | Notes |
|------------------|------------------------|-------------------|-------|
| Windows 11 + Python 3.12 base | ~3.1 GB | No change | Observed baseline from legacy |
| Ollama server + qwen3:4b (Q4 quantized, memory-mapped) | ~1.8–2.2 GB | No change | Must remain quantized |
| nomic-embed-text (cached, shared process) | ~0.3–0.4 GB | No change | Shared with Ollama |
| SQLite + sqlite-vec (working set) | ~0.3–0.45 GB | No change | Batch vector ops required |
| Active agent process (context bundles ≤500 KB) | ~0.2–0.3 GB | No change | Serialized bundles only |
| Tool Gateways (active subset) | ~0.15–0.2 GB | No change | HTTP buffers, validators |
| Sandbox Gateway (Job Object capped) | ~0.2–0.3 GB | No change | 256 MB hard limit enforced |
| Logging/audit buffers | ~0.1–0.15 GB | No change | JSONL + SQLite cache |
| Policy Engine + Permission Engine modules | ~0.05–0.1 GB | No change | Stateless rule evaluation |
| SessionController main thread overhead | ~0.05 GB | No change | Supervision logic only |
| Thread management (4 threads: main, Telegram, Scheduler, Bootstrap) | ~0.05–0.1 GB | No change | Python threading lightweight |
| PlanInjectionScanner (deterministic component) | ~0.02–0.04 GB | No change | Rule-based, no model load |
| **Peak Sequential Total** | **~6.9–7.4 GB** | **No material change** | **Headroom used: ~0.9–1.7 GB of 2.0–2.3 GB available** |

**Conclusion:** The v1.7 refinements are specification clarifications with **zero measurable RAM impact**. The sequential design remains feasible within observed headroom, provided all prior binding conditions are maintained.

---

### 3. Critical RAM Risk Points — Binding Mitigations (Reaffirmed)

1. **qwen3:4b Memory Footprint**
   - *Risk:* Full-precision or unquantized load would exceed headroom.
   - *Binding Condition:* Model must remain Q4 (or lower) quantized and memory-mapped via Ollama. No architectural change may load the model fully into RAM.

2. **sqlite-vec Vector Operations**
   - *Risk:* Unbatched cosine similarity searches could spike memory usage.
   - *Binding Condition:* Vector queries must batch to **maximum 100 vectors per operation**. Deduplication threshold checks must stream results, not load full table.

3. **Context Bundle Size**
   - *Risk:* Unbounded serialized context could consume headroom.
   - *Binding Condition:* Context bundles delivered to agents must be capped at **500 KB serialized size**. Larger contexts require pagination via additional queue tasks.

4. **Sandbox Memory Limits**
   - *Risk:* Unrestricted sandbox process could trigger system paging.
   - *Binding Condition:* Windows Job Object must enforce **256 MB RAM limit** for sandboxed code execution. Exceeding this limit terminates the process and flags a security event.

5. **Thread Management Overhead**
   - *Risk:* Excessive thread creation or unbounded thread-local state could accumulate memory.
   - *Binding Condition:* Phase 1 is limited to the four defined threads (main supervisor, Telegram, Scheduler, Bootstrap). No additional worker threads may be introduced without revised RAM accounting.

---

### 4. API Budget Verification

| Provider | Proposal Usage | Free-Tier Status | Verdict |
|----------|---------------|------------------|---------|
| Cerebras | Primary cloud inference | Free tier, fast | ✓ Sustainable |
| Groq | Fallback (10K daily tokens) | Limit exhausted in legacy testing | ⚠ Requires failover testing |
| OpenRouter/SambaNova | Secondary fallbacks | Free tiers available | ✓ Sustainable |
| Brave Search API | Web search replacement | ~1,000 queries/month free | ✓ Sustainable (if confirmed) |

**Budget Concerns (Unchanged):**
1. **Groq Limit Exhaustion:** Proposal retains Groq as fallback but does not specify behavior when both Cerebras and Groq are unavailable. *Recommendation:* Implement exponential backoff and queue-task deferral rather than hard failure.
2. **Token Estimation Accuracy:** `budget_policy` in permission manifest requires conservative estimation. *Binding Condition:* Token estimates must include 2× safety margin; actual usage must be logged and compared to estimate for adaptive calibration.
3. **Embedding Cost:** Local nomic-embed-text usage is correct and budget-compliant. ✓

---

### 5. Performance Caveats (Non-Blocking but Operational)

| Component | Expected Performance on Celeron N4500 | Impact |
|-----------|--------------------------------------|--------|
| qwen3:4b local inference (sanitization/classification) | 5–15 seconds per call | User-facing latency; set expectations |
| sqlite-vec similarity search | 100–500 ms per 100-vector batch | Acceptable for sequential workflow |
| PlanInjectionScanner rule evaluation | <10 ms per artifact | Negligible; deterministic rule matching |
| Thread context switching (4 threads) | <1 ms per switch | Negligible on Celeron N4500 |
| Sequential task throughput | ~1–3 tasks/minute depending on complexity | Architecture is correct; scale via queue, not parallelism |

---

### 6. v1.7 Specification Changes — Feasibility Impact

| Change | Feasibility Impact | Verdict |
|--------|-------------------|---------|
| PlanInjectionScanner ordered rules corrected | Logic fix; no runtime overhead | ✓ Neutral |
| SessionController on main supervisor thread | Thread assignment clarification; no new threads | ✓ Neutral |
| provider_usage single-row lifecycle | Schema clarification; same row count, different update pattern | ✓ Neutral |
| Thread object identity check (vs. name) | Object reference comparison; negligible RAM/CPU impact | ✓ Neutral |
| No new modules, processes, or concurrent execution | Architecture spine unchanged | ✓ Positive |

**Conclusion:** All v1.7 refinements are **implementation-facing specification clarifications** that improve correctness and testability without increasing hardware demands.

---

### 7. Missing Specification — Minor Blocker (Reaffirmed)

- **Web Search Backend:** Proposal references "Network Gateway" but does not explicitly confirm Brave Search API or equivalent free-tier solution. *Binding Condition:* Implementation must confirm Brave Search API (or panel-approved alternative) before enabling web search functionality.

---

### 8. Binding Ruling

**AXIOM Proposal v1.7 is FEASIBLE** on the target hardware (Intel Celeron N4500, 8 GB RAM, Windows 11, no GPU) **subject to the following binding conditions**:

1. **Sequential execution must be strictly enforced**; no concurrent agent subprocesses may be introduced without full panel consensus and revised RAM accounting.
2. **qwen3:4b must remain quantized (Q4 or lower)** and memory-mapped via Ollama; no architectural change may load the model fully into RAM.
3. **Context bundles delivered to agents must be capped at 500 KB serialized size**.
4. **Sandbox execution must enforce a 256 MB RAM limit** via Windows Job Object.
5. **sqlite-vec queries must batch vector operations** to a maximum of 100 vectors per query.
6. **Web search backend must be confirmed as Brave Search API** or panel-approved free-tier equivalent before implementation.
7. **Token estimation in `budget_policy` must include a 2× safety margin**; actual usage must be logged for adaptive calibration.
8. **PolicyEngine evaluations must be stateless** and cache manifest/rule lookups to avoid per-task memory accumulation.
9. **Thread count must remain limited to the four defined threads** (main supervisor, Telegram, Scheduler, Bootstrap); no additional worker threads may be introduced without revised RAM accounting.

If any of these conditions cannot be met during implementation, the proposal must return to the Chief Architect for revision. This ruling is **binding** per the AXIOM Panel Charter and may only be overturned by full panel consensus with written rationale.
