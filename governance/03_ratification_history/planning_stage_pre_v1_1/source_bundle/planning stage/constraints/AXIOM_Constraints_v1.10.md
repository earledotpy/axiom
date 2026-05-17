**AXIOM Constraints Review — Proposal v1.10**
**Reviewer:** Qwen 3.6 Plus — Constraints and Feasibility Reviewer
**Date:** May 2026
**Ruling:** **APPROVED with Binding Conditions**

---

### 1. Hardware Feasibility Assessment

| Component | Proposal Requirement | Target Hardware | Verdict |
|-----------|---------------------|----------------|---------|
| CPU | Sequential execution; deterministic security gates | Intel Celeron N4500 (2C/2T) | ✓ Compliant |
| RAM | Peak sequential load within ~2.0–2.3 GB headroom | 8 GB total (~5.7 GB baseline) | ✓ Compliant* |
| GPU | None required; all inference CPU-bound or cloud-offloaded | None | ✓ Compliant |
| Storage | SATA SSD for paging, SQLite, atomic commits, audit logs | SATA SSD | ✓ Compliant |
| OS | Windows 11 APIs for Job Objects, file hashing, process metadata | Windows 11 | ✓ Compliant |

*\*Conditional on RAM accounting below and strict adherence to binding resource caps.*

---

### 2. RAM Accounting — Peak Sequential Load (v1.10 Delta Analysis)

Proposal v1.10 introduces deterministic security hardening, manifest integrity verification, mid-session model fingerprint checks, and tiered token-margin enforcement. **No new runtime threads, background daemons, GPU workloads, or unbounded memory allocations are introduced.** All additions are lightweight, stateless verification logic or file I/O operations.

| Runtime Component | Estimated RAM Footprint | Change vs. v1.9 | Notes |
|------------------|------------------------|-----------------|-------|
| Windows 11 + Python 3.12 base | ~3.1 GB | No change | Observed baseline |
| Ollama server + qwen3:4b (Q4 quantized, memory-mapped) | ~1.8–2.2 GB | No change | Must remain quantized |
| nomic-embed-text (cached, shared process) | ~0.3–0.4 GB | No change | Shared with Ollama |
| SQLite + sqlite-vec (working set) | ~0.3–0.45 GB | No change | Batch vector ops required |
| Active agent process (context bundles ≤500 KB) | ~0.2–0.3 GB | No change | Serialized bundles only |
| Tool Gateways (active subset) | ~0.15–0.2 GB | No change | HTTP buffers, validators |
| Sandbox Gateway (Job Object + `timeout=60`) | ~0.2–0.3 GB | No change | 256 MB RAM + 60s wall-clock cap |
| Logging/audit buffers | ~0.1–0.15 GB | No change | JSONL + SQLite cache |
| Policy/Permission Engines, State Machine | ~0.05–0.1 GB | No change | Stateless rule evaluation |
| **New: ManifestIntegrityVerifier (SHA256 at boot)** | **~0.01–0.02 GB** | **+ New** | Reads JSON files, computes hashes; negligible |
| **New: ModelFingerprintGuard (pre-decision)** | **~0.01–0.02 GB** | **+ New** | Ollama metadata query + string comparison |
| **Enhanced: TokenEstimator (tiered margin)** | **~0.01–0.02 GB** | **+ New** | Lightweight tokenizer math / fallback estimator |
| Thread management (4 threads) | ~0.05–0.1 GB | No change | Python threading lightweight |
| **Peak Sequential Total** | **~6.85–7.4 GB** | **Negligible increase** | **Headroom used: ~0.9–1.7 GB of 2.0–2.3 GB available** |

**Conclusion:** v1.10's additions are strictly deterministic security and governance layers. Memory overhead is effectively zero beyond existing buffers. Peak RAM remains safely within observed headroom.

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
   - *Binding Condition:* Windows Job Object must enforce **256 MB RAM limit**. `subprocess.run(timeout=60)` must enforce **60-second wall-clock cap**.

5. **Thread & Concurrency Cap**
   - *Risk:* Excessive thread creation fragments CPU scheduling.
   - *Binding Condition:* Phase 1 is strictly limited to **four threads** (main supervisor, Telegram, Scheduler, BootstrapValidationWorker). No additional workers or async loops.

6. **Calibration & Fingerprint State**
   - *Risk:* Loading large validation sets or model metadata dictionaries at runtime.
   - *Binding Condition:* The calibration test set and fingerprint tables must remain in SQLite or loaded only as lightweight constants during validation. No raw datasets persist in active RAM during autonomous operation.

7. **Token Estimator Implementation**
   - *Risk:* Heavy tokenizer library (e.g., full `tiktoken` BPE tables) consumes baseline RAM.
   - *Binding Condition:* If `tiktoken` is used, it must operate in lightweight mode. The fallback `ceil(character_count / 3)` must remain RAM-neutral. No model-weight loading for estimation.

---

### 4. API Budget Verification

| Provider | Proposal Usage | Free-Tier Status | Verdict |
|----------|---------------|------------------|---------|
| Cerebras | Primary cloud inference | Free tier, fast | ✓ Sustainable |
| Groq | Fallback (10K daily tokens) | Limit exhausted in legacy | ⚠ Requires failover testing |
| OpenRouter/SambaNova | Secondary fallbacks | Free tiers available | ✓ Sustainable |
| Brave Search API | Web search replacement | ~1,000 queries/month free | ✓ Sustainable (if confirmed) |

**Budget Enhancements in v1.10:**
1. **Tiered Token-Margin Rule:** Uses `2.0×` margin for calibrated tokenizers and `1.5×` for conservative `/3` estimators. Prevents excessive false-blocking while maintaining strict budget discipline. ✓
2. **Reconciliation Sanity Check:** `±50%` discrepancy threshold with operator confirmation prevents accidental budget ledger corruption. ✓
3. **Task Planner Manifest Sizing:** Task Planner must budget child tasks at ≤50% (calibrated) or ≤66% (fallback) of manifest input cap, ensuring dispatch-time gates are satisfied. ✓
4. **Per-Call Timeouts:** Hard ceilings (30s–90s) prevent runaway token consumption during network instability. ✓

---

### 5. Performance Caveats (Non-Blocking but Operational)

| Component | Expected Performance on Celeron N4500 | Impact |
|-----------|--------------------------------------|--------|
| qwen3:4b local inference (sanitization/classification) | 5–15 seconds per call | User-facing latency; set expectations |
| sqlite-vec similarity search | 100–500 ms per 100-vector batch | Acceptable for sequential workflow |
| Manifest SHA256 verification (boot) | <1 second for typical policy directory | Negligible; one-time cost |
| Model fingerprint query (pre-decision) | <50 ms via Ollama CLI/API | Negligible; prevents stale calibration |
| SupervisorMonitor stale check (120s) | Single timestamp comparison per tick | Negligible |

---

### 6. v1.10 Specification Changes — Feasibility Impact

| Change | Feasibility Impact | Verdict |
|--------|-------------------|---------|
| Calibration test-set authorship reassigned to Gemini | Governance change; no runtime impact | ✓ Neutral |
| Mid-session model fingerprint verification | Lightweight Ollama metadata check | ✓ Positive (Security) |
| Manifest integrity SHA256 verification | Boot-time file hashing; negligible RAM | ✓ Positive (Security) |
| End-to-end e2e test added | Test artifact only; no runtime impact | ✓ Neutral |
| Provider reconciliation ±50% sanity check | Math + Telegram prompt; no RAM impact | ✓ Neutral |
| Tiered token-margin rule (2.0× / 1.5×) | Estimator logic refinement; prevents false blocks | ✓ Positive |
| Keepalive reframed as retrospective | Documentation/UX adjustment | ✓ Neutral |
| Immediate goal acknowledgement | Telegram template addition | ✓ Neutral |
| Test list reconciliation | Documentation consolidation | ✓ Neutral |
| SupervisorMonitor located in SessionController | Refactoring; clarifies ownership | ✓ Neutral |
| Task-planner manifest-sizing rule | Planner logic constraint; reduces dispatch failures | ✓ Positive |
| Operator-control authorization ownership table | Documentation; clarifies implementation flow | ✓ Neutral |

**Conclusion:** All v1.10 refinements are security hardening, budget discipline, and governance clarifications. Hardware demands remain identical to v1.9. No constraints are violated.

---

### 7. Missing Specification — Minor Blocker (Reaffirmed)

- **Web Search Backend:** Proposal references "Network Gateway" but does not explicitly confirm Brave Search API or equivalent free-tier solution. *Binding Condition:* Implementation must confirm Brave Search API (or panel-approved alternative) before enabling web search functionality.

---

### 8. Binding Ruling

**AXIOM Proposal v1.10 is FEASIBLE** on the target hardware (Intel Celeron N4500, 8 GB RAM, Windows 11, no GPU) **subject to the following binding conditions**:

1. **Sequential execution must be strictly enforced**; no concurrent agent subprocesses may be introduced without full panel consensus and revised RAM accounting.
2. **qwen3:4b must remain quantized (Q4 or lower)** and memory-mapped via Ollama; no architectural change may load the model fully into RAM.
3. **Context bundles delivered to agents must be capped at 500 KB serialized size**.
4. **Sandbox execution must enforce a 256 MB RAM limit and 60-second wall-clock cap** via Windows Job Object + `subprocess.run(timeout=60)`.
5. **sqlite-vec queries must batch vector operations** to a maximum of 100 vectors per query.
6. **Web search backend must be confirmed as Brave Search API** or panel-approved free-tier equivalent before implementation.
7. **Token estimation must enforce tiered margins**: `2.0×` for calibrated tokenizers, `1.5×` for fallback estimators. Fallback must remain RAM-neutral.
8. **PolicyEngine evaluations and resource limits must be stateless** and cache manifest/rule lookups to avoid per-task memory accumulation.
9. **Thread count must remain limited to the four defined threads**; no additional workers may be introduced without revised RAM accounting.
10. **Calibration test set and fingerprint tables must not persist as raw datasets in RAM** during autonomous operation; only threshold constants and validation hashes may be loaded.
11. **Classifier safe-pass must remain disabled** until calibration passes against panel-authored test sets with verified confidence thresholds.
12. **Mid-session model fingerprint mismatch or manifest SHA256 mismatch must immediately disable autonomous safe-pass** and require operator intervention.

If any of these conditions cannot be met during implementation, the proposal must return to the Chief Architect for revision. This ruling is **binding** per the AXIOM Panel Charter and may only be overturned by full panel consensus with written rationale.

---

**Next Step:** Proposal v1.10 may advance to Claude Opus 4.7 — Quality and Coherence Evaluator for final structural validation, pending attachment of this feasibility ruling.

*Constraints Review Complete.*