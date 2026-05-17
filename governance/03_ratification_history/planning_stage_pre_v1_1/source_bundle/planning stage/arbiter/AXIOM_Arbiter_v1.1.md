**Arbiter Rulings: AXIOM Proposal v1.1 & Addendum**
As the Research and Knowledge Arbiter, I have reviewed the factual and technical claims in the Chief Architect’s Proposal v1.1 and Addendum.
Here are my binding rulings on the technical realities, library capabilities, and OS-level mechanisms proposed.
### 1. Claim: Sandbox Isolation via Windows Job Objects + Restricted Token
 * **The Claim:** The proposal commits to "Windows Job Objects + restricted token via pywin32" as the mechanism to isolate code execution, enforce CPU/Memory limits, and block direct network permission.
 * **Arbiter Ruling: PARTIALLY VERIFIED — REQUIRES IMPLEMENTATION CAVEAT**
 * **The Reality:** * **Resource Limits:** Windows Job Objects, accessible via pywin32 (win32job), are indeed the correct factual mechanism for enforcing hard CPU and RAM limits on child processes in Windows.
   * **OS/File Permissions:** A restricted token (CreateRestrictedToken via win32security) correctly strips administrative rights and restricts file system access to prevent the sandbox from reading system secrets or writing outside its designated temporary directory.
   * **Network Isolation (The Gap):** A standard restricted token *does not* natively block outbound network sockets (Winsock) on Windows. Dropping privileges prevents the process from altering network adapter settings, but standard user tokens can still initiate outbound HTTP/TCP requests. To achieve the absolute network isolation required by Core Value 6, the implementation must either:
     1. Create an AppContainer environment (which natively drops the internetClient capability), though doing this pure Python via pywin32 is highly undocumented and complex.
     2. Run the sandbox under a dedicated, unprivileged local user account (axiom_sandbox_user) that has a strict Windows Defender Firewall rule blocking all outbound traffic for that specific user ID.
 * **Action:** The architectural commitment stands, but Kimi (Implementation Specialist) must explicitly utilize Windows Firewall rules mapped to the restricted token's SID, or the "no-network test" will fail.
### 2. Claim: subprocess.Popen Inherits Parent Network Permissions
 * **The Claim:** The legacy reference and proposal assert that subprocess.Popen does not provide network isolation because it inherits the parent process's network permissions on Windows.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. On Windows, a child process spawned via subprocess.Popen inherits the primary access token of the parent Python process by default. If the parent Telegram/Scheduler process can reach the internet, the spawned code can too. This validates the absolute necessity of the Job Object + Token architecture discussed above.
### 3. Claim: RAM Exhaustion via Concurrency
 * **The Claim:** The architecture must remain sequential because the hardware limits provide only 2.0–2.3 GB of runtime headroom, and concurrent agent subprocesses will exhaust RAM and force SATA SSD paging.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Python's multiprocessing or heavily threaded agent instances duplicate considerable memory overhead for the interpreter and loaded libraries. Given the Intel Celeron N4500 and 8GB system RAM constraint, running multiple distinct agent chains alongside Ollama and the SQLite Vector extension will rapidly consume the remaining ~2 GB. Paging to a SATA SSD will cause catastrophic latency for LLM inference and agent loops. The sequential state-machine architecture is the only factually viable path for this hardware.
### 4. Claim: SQLite Task Queue Viability
 * **The Claim:** Using SQLite for queue coordination and persistence is reliable for a sequential, single-physical-runtime architecture.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. SQLite handles single-writer, sequential operations with exceptional stability. Because the Scheduler operates strictly sequentially and inter-agent coordination occurs exclusively through this shared queue, you will not encounter SQLite's traditional concurrent-write locking issues (database is locked).
### 5. Claim: Write-Time Sanitization for Prompt Injection
 * **The Claim:** Prompt injection defense requires sanitization at the write boundary (before insertion into the task queue) rather than the read boundary.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate and aligns with current cybersecurity best practices for LLM architectures. If a malicious payload or embedded instruction (e.g., from a fetched webpage) is allowed to rest in the database, it creates a persistent threat surface. Any agent or query that later reads that data becomes compromised. Sanitizing and separating data from instructions *before* the commit is the only reliable way to maintain the zero-trust boundaries mandated by the Core Values.
### Arbiter Conclusion
The factual foundations of Proposal v1.1 and its Addendum are solid. The technologies identified (SQLite, Job Objects, Python sequential processing) match the capabilities of the constrained hardware.
**My single binding addition:** The restricted token mechanism for the sandbox must be paired with user-specific firewall rules or AppContainer logic to successfully block network sockets.
The proposal is factually cleared to advance to DeepSeek V4 for Adversarial Review.
