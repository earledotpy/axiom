**AXIOM Constraints Review — Proposal v1.11.2 / v1.11.3**
**Reviewer:** Qwen 3.6 Plus — Constraints and Feasibility Reviewer
**Date:** May 2026
**Ruling:** **APPROVED with Binding Conditions**

---

### 1. Hardware Feasibility Assessment

| Component | Proposal Requirement | Target Hardware | Verdict |
|-----------|---------------------|----------------|---------|
| CPU | Sequential execution; deterministic schema/policy validation | Intel Celeron N4500 (2C/2T) | ✓ Compliant |
| RAM | Peak sequential load within ~2.0–2.3 GB headroom | 8 GB total (~5.7 GB baseline) | ✓ Compliant* |
| GPU | None required; all inference CPU-bound or cloud-offloaded | None | ✓ Compliant |
| Storage | SATA SSD for paging, SQLite, indexes, audit logs | SATA SSD | ✓ Compliant |
| OS | Windows 11 APIs for Job Objects, pywin32, SQLite, subprocess | Windows 11 | ✓ Compliant |

*\*Conditional on RAM accounting below and strict adherence to binding resource caps.*

---

### 2. RAM Accounting — Peak Sequential Load (v1.11.2 / v1.11.3 Delta Analysis)

Proposals v1.11.2 and v1.11.3 are **security-boundary, schema-coherence, and policy-authorization refinements**. They introduce deterministic validation layers, static capability mappings, and database indexing strategies. **No new runtime threads, concurrent agents, background daemons, GPU workloads, or unbounded memory allocations are introduced.**

| Runtime Component | Estimated RAM Footprint | Change vs. v1.10 | Notes |
|------------------|------------------------|-----------------|-------|
| Windows 11 + Python 3.12 base | ~3.1 GB | No change | Observed baseline |
| Ollama server + qwen3:4b (Q4 quantized, memory-mapped) | ~1.8–2.2 GB | No change | Must remain quantized |
| nomic-embed-text (cached, shared process) | ~0.3–0.4 GB | No change | Shared with Ollama |
| SQLite + sqlite-vec (working set + new indexes) | ~0.3–0.45 GB | No change | Indexes increase page cache slightly; within existing buffer |
| Active agent process (context bundles ≤500 KB) | ~0.2–0.3 GB | No change | Serialized bundles only |
| Tool Gateways (active subset) | ~0.15–0.2 GB | No change | HTTP buffers, validators, redirect logic |
| Sandbox Gateway (Job Object + `timeout=60`) | ~0.2–0.3 GB | No change | 256 MB RAM + 60s wall-clock cap |
| Logging/audit buffers | ~0.1–0.15 GB | No change | JSONL + SQLite cache |
| Policy/Permission Engines, State Machine | ~0.05–0.1 GB | No change | Stateless rule evaluation |
| **New: `TOOL_CAPABILITY_MAP` (static dict)** | **~0.01–0.02 GB** | **+ New** | Loaded once at boot; negligible |
| **New: ManifestBinder + JSON Schema validators** | **~0.02–0.03 GB** | **+ New** | Boot-time schema compilation; stateless per-task |
| Thread management (4 threads) | ~0.05–0.1 GB | No change | Python threading lightweight |
| **Peak Sequential Total** | **~6.9–7.4 GB** | **Negligible increase** | **Headroom used: ~0.9–1.7 GB of 2.0–2.3 GB available** |

**Conclusion:** The v1.11.2/v1.11.3 refinements add deterministic security and policy layers with **zero measurable increase** in peak RAM consumption. The sequential design remains feasible within observed headroom.

---

### 3. Critical RAM & Performance Risk Points — Binding Mitigations

1. **qwen3:4b Memory Footprint**
   - *Risk:* Full-precision or unquantized load would exceed headroom.
   - *Binding Condition:* Model must remain Q4 (or lower) quantized and memory-mapped via Ollama. No architectural change may load the model fully into RAM.

2. **sqlite-vec Vector Operations**
   - *Risk:* Unbatched searches spike memory.
   - *Binding Condition:* Vector queries must batch to **maximum 100 vectors per operation**. Deduplication checks must stream results.

3. **Context Bundle Size**
   - *Risk:* Unbounded serialized context consumes headroom.
   - *Binding Condition:* Context bundles delivered to agents must be capped at **500 KB serialized size**. Larger contexts require pagination.

4. **Sandbox Memory & Duration Limits**
   - *Risk:* Runaway sandbox triggers paging or blocks scheduler.
   - *Binding Condition:* Windows Job Object must enforce **256 MB RAM limit** and **60-second wall-clock cap** via `subprocess.run(timeout=60)`.

5. **Thread & Concurrency Cap**
   - *Risk:* Excessive thread creation fragments CPU scheduling.
   - *Binding Condition:* Phase 1 is strictly limited to **four threads** (main supervisor, Telegram, Scheduler, BootstrapValidationWorker). No additional workers or async loops.

6. **Schema/Policy Validation Memory Lifecycle**
   - *Risk:* Recompiling JSON Schema validators or reloading `TOOL_CAPABILITY_MAP` per task causes fragmentation.
   - *Binding Condition:* Schema validators, capability maps, and manifest fingerprints must be **compiled and cached once at boot**. Runtime validation must operate on these pre-compiled constants, not reload artifacts per task.

7. **Database Index & Page Cache Pressure**
   - *Risk:* New indexes (`idx_scheduler_heartbeat_latest`, `idx_tasks_commit_batch`) could inflate SQLite's in-memory page cache.
   - *Binding Condition:* SQLite `cache_size` must remain explicitly bounded. Indexes must be used only for read-optimization; write-heavy operations (TaskCommitter atomic commits) must remain within the existing transaction buffer.

---

### 4. API Budget Verification

| Provider | Proposal Usage | Free-Tier Status | Verdict |
|----------|---------------|------------------|---------|
| Cerebras | Primary cloud inference | Free tier, fast | ✓ Sustainable |
| Groq | Fallback (10K daily tokens) | Limit exhausted in legacy | ⚠ Requires failover testing |
| OpenRouter/SambaNova | Secondary fallbacks | Free tiers available | ✓ Sustainable |
| Brave Search API | Web search replacement | ~1,000 queries/month free | ✓ Sustainable (if confirmed) |

**Budget Concerns (Unchanged but Explicitly Addressed):**
1. **Tiered Token-Margin Rule:** `2.0×` for calibrated tokenizers, `1.5×` for fallback `/3` estimator remains binding. ✓
2. **Network Gateway Timeouts:** `timeout_seconds = 0` valid only for `deny_all`; `allowlist_only` requires `≥1`. Prevents silent hang resource leaks. ✓
3. **Provider Enum Constraint:** `provider_usage.provider` restricted to known free-tier endpoints. Future additions require schema migration, preventing accidental paid-API routing. ✓

---

### 5. Performance Caveats (Non-Blocking but Operational)

| Component | Expected Performance on Celeron N4500 | Impact |
|-----------|--------------------------------------|--------|
| qwen3:4b local inference (sanitization/classification) | 5–15 seconds per call | User-facing latency; set expectations |
| sqlite-vec similarity search | 100–500 ms per 100-vector batch | Acceptable for sequential workflow |
| ManifestBinder JSON Schema validation | <50 ms per manifest | Negligible; compiled validators |
| Network redirect policy evaluation | <10 ms per URL | Deterministic string/pattern matching |
| Sequential task throughput | ~1–3 tasks/minute depending on complexity | Architecture is correct; scale via queue, not parallelism |

---

### 6. v1.11.2 / v1.11.3 Specification Changes — Feasibility Impact

| Change | Feasibility Impact | Verdict |
|--------|-------------------|---------|
| `allowed_capabilities` restructuring (network/sandbox/memory removed) | Schema simplification; eliminates double-source conflict | ✓ Positive |
| `TOOL_CAPABILITY_MAP` static routing | Boot-time dict load; zero runtime allocation | ✓ Neutral |
| Network wildcard/denylist semantics (`*` only) | Deterministic string matching; negligible CPU | ✓ Neutral |
| `scheduler_heartbeat` log model + latest-read index | Slightly larger disk writes; improves read performance | ✓ Positive |
| `tasks.manifest_id` lifecycle + state-machine enforcement | Prevents unbound task execution; RAM-neutral | ✓ Positive |
| Sparse `memory_item_embeddings` invariant | Reduces vec0 table bloat; improves SQLite cache efficiency | ✓ Positive |
| `commit_batch_id` immutable atomic identifier | String field in memory during commit; negligible | ✓ Neutral |
| Operator-control manifest cross-field equality check | Boot-time validation; prevents privilege escalation | ✓ Positive |
| Deferred: `scheduler_heartbeat` & `memory_items` retention policy | Acknowledged as disk-growth issue, not RAM issue for Phase 1 | ✓ Neutral |

**Conclusion:** All v1.11.2/v1.11.3 refinements are **security hardening, schema normalization, and authorization boundary clarifications**. They operate entirely within the established sequential runtime budget. No hardware constraints are violated.

---

### 7. Missing Specification — Minor Blocker (Reaffirmed)

- **Web Search Backend:** Proposal references "Network Gateway" but does not explicitly confirm Brave Search API or equivalent free-tier solution. *Binding Condition:* Implementation must confirm Brave Search API (or panel-approved alternative) before enabling web search functionality.

---

### 8. Binding Ruling

**AXIOM Proposal v1.11.2 / v1.11.3 is FEASIBLE** on the target hardware (Intel Celeron N4500, 8 GB RAM, Windows 11, no GPU) **subject to the following binding conditions**:

1. **Sequential execution must be strictly enforced**; no concurrent agent subprocesses may be introduced without full panel consensus and revised RAM accounting.
2. **qwen3:4b must remain quantized (Q4 or lower)** and memory-mapped via Ollama; no architectural change may load the model fully into RAM.
3. **Context bundles delivered to agents must be capped at 500 KB serialized size**.
4. **Sandbox execution must enforce a 256 MB RAM limit and 60-second wall-clock cap** via Windows Job Object + `subprocess.run(timeout=60)`.
5. **sqlite-vec queries must batch vector operations** to a maximum of 100 vectors per query.
6. **Web search backend must be confirmed as Brave Search API** or panel-approved free-tier equivalent before implementation.
7. **Token estimation must enforce tiered margins**: `2.0×` for calibrated tokenizers, `1.5×` for fallback estimators. Fallback must remain RAM-neutral.
8. **PolicyEngine evaluations, ManifestBinder validation, and `TOOL_CAPABILITY_MAP` lookups must be stateless** and cache compiled validators at boot to avoid per-task memory allocation.
9. **Thread count must remain limited to the four defined threads** (main supervisor, Telegram, Scheduler, BootstrapValidationWorker); no additional workers may be introduced.
10. **Classifier safe-pass must remain disabled** until calibration passes against panel-authored test sets with verified confidence thresholds.
11. **Model fingerprint mismatch, manifest SHA256 mismatch, or `allowed_commands` cross-field mismatch must immediately fail-closed** and require operator intervention.
12. **SQLite page cache must remain explicitly bounded**; new indexes must not trigger uncontrolled memory allocation during atomic TaskCommitter operations.

If any of these conditions cannot be met during implementation, the proposal must return to the Chief Architect for revision. This ruling is **binding** per the AXIOM Panel Charter and may only be overturned by full panel consensus with written rationale.

---

**Next Step:** Proposal v1.11.2 / v1.11.3 may advance to DeepSeek V4 — Adversarial Critic for targeted privilege-escalation and attack-surface review, pending attachment of this feasibility ruling.

*Constraints Review Complete.*