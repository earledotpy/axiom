**Arbiter Rulings: AXIOM Proposal v1.8.1 & v1.8**
As the Research and Knowledge Arbiter, I have reviewed the technical realities, API availability, and library mechanisms proposed in the v1.8.1 Patch and v1.8 Revision.
Here are my binding rulings on the factual claims made in the documents.
### 1. Claim: SQLite Atomic Transactions via BEGIN IMMEDIATE
 * **The Claim:** All child tasks produced from a verified plan artifact commit atomically in one SQLite transaction using BEGIN IMMEDIATE, COMMIT, and ROLLBACK.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. SQLite guarantees atomicity, consistency, isolation, and durability (ACID) for transactions. In Write-Ahead Logging (WAL) mode, executing BEGIN IMMEDIATE instantly acquires a RESERVED lock. This prevents other concurrent writers (such as the Telegram thread) from causing database is locked conflicts during the critical batch insert. If a process crash occurs midway, SQLite natively rolls back the partial transaction, preserving queue integrity.
### 2. Claim: Windows Job Object Wall-Clock Timeout
 * **The Claim:** Sandbox execution is capped at 60 seconds wall-clock duration via the Windows Job Object timeout mechanism.
 * **Arbiter Ruling: PARTIALLY VERIFIED — REQUIRES IMPLEMENTATION CAVEAT**
 * **The Reality:** Windows Job Objects natively enforce hard RAM limits (e.g., 256 MB) via JobObjectExtendedLimitInformation. However, the time limit features exposed by Job Objects (PerProcessUserTimeLimit or PerJobUserTimeLimit) strictly measure *User-Mode CPU Execution Time*, not wall-clock time. If a malicious or buggy script in the sandbox simply uses time.sleep() or waits on a dead socket, it consumes near-zero CPU time and will bypass the Job Object timeout indefinitely. To reliably enforce the 60-second wall-clock cap, the Sandbox Gateway implementation *must* wrap the execution in Python's subprocess.run(timeout=60) or use a dedicated thread timer alongside the Job Object.
### 3. Claim: Local Model Memory-Mapping (mmap) via Ollama
 * **The Claim:** The local model operates as a Q4 quantized version and is memory-mapped through Ollama.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Ollama is powered by llama.cpp, which natively utilizes mmap (memory-mapping) for GGUF model files. This allows the OS to map the model weights directly from the SATA SSD into virtual memory, swapping layers in and out as required. On constrained hardware like the Celeron N4500 with a total of 8 GB RAM, memory-mapping is the only technically viable method to run a multi-billion parameter model without triggering an immediate out-of-memory system crash.
### 4. Claim: Brave Search API as a Free-Tier Alternative
 * **The Claim:** Brave Search API is confirmed as a free-tier alternative that must be established before web search is enabled.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Legacy autonomous agents frequently fail when relying on HTML scraping libraries (like duckduckgo_search) due to strict anti-bot rate limiting. The Brave Search API offers a stable, official free tier (historically allowing ~2,000 queries per month) that perfectly satisfies the project's zero-cost API budget constraint while providing the structured JSON results required for reliable parsing by the Network Gateway.
### 5. Claim: SQLite-Vec Batch Processing Limits
 * **The Claim:** sqlite-vec queries are limited to a maximum of 100 vectors per query/batch to maintain performance.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. The sqlite-vec extension predominantly relies on brute-force distance calculations (checking the query vector against every stored row vector). On a low-power CPU like the Celeron N4500, attempting to embed and insert, or query against, massive batches of vectors simultaneously will pin the CPU at 100% and block the single SQLite database writer. Enforcing a hard cap of 100 vectors per batch is a factually required architectural constraint to maintain acceptable system latency.
### Arbiter Conclusion
The technical claims regarding SQLite atomicity, Ollama memory-mapping, the Brave Search API, and sqlite-vec hardware limits are completely factually sound.
**My single binding addition:** The Sandbox Gateway cannot rely *solely* on the Windows Job Object for a wall-clock timeout; the implementation must include a standard Python subprocess timeout to prevent sleeping scripts from hanging the queue.
With this caveat enforced by Kimi, the proposal is factually cleared.
