**Arbiter Rulings: AXIOM Proposal v1.9**
As the Research and Knowledge Arbiter, I have reviewed the technical claims embedded in the Chief Architect’s v1.9 Revision. This proposal addresses the remaining implementation-level mechanics required for the Minimum Viable Product (MVP).
Here are my binding rulings on the factual realities of these mechanisms.
### 1. Claim: Sandbox Wall-Clock Enforcement via subprocess.run(timeout=60)
 * **The Claim:** Sandbox wall-clock duration can be strictly enforced using Python's subprocess.run(timeout=60) in conjunction with Windows Job Objects.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. The timeout parameter in Python's subprocess module enforces a strict wall-clock limit. If the child process does not terminate within the specified seconds, a TimeoutExpired exception is raised in the parent process, allowing the Sandbox Gateway to terminate the process tree. This correctly mitigates the loophole where a script uses time.sleep() or waits on a dead socket to consume zero CPU time while hanging the scheduler.
### 2. Claim: Model Profile Fingerprinting via Ollama
 * **The Claim:** A model profile fingerprint can be computed at boot using Ollama model metadata, including the digest, quantization, and model file timestamps/sizes.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. The local Ollama server exposes HTTP API endpoints (specifically /api/tags and /api/show) that return deterministic metadata. This natively includes the exact SHA256 digest of the model file, the quantization level (e.g., Q4_0), the parameter size, and the modified timestamp. If the underlying local model is updated or swapped by the operator, the digest or timestamp changes, making this a highly reliable mechanism to detect silent model drift and enforce recalibration.
### 3. Claim: Local Token Estimation and Fallback Math
 * **The Claim:** Token counting can be performed locally using an OpenAI-compatible tokenizer (like tiktoken) or, as a conservative fallback, estimating via ceil(character_count / 3).
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Libraries such as tiktoken or Hugging Face's transformers tokenizers operate entirely offline in Python and require no API calls. Furthermore, the conservative fallback math is factually sound. Standard English text and Python code typically average around 4 characters per token. Dividing by 3 intentionally overestimates the token count, ensuring the system safely respects the 2× safety margin before dispatching to a cloud provider.
### 4. Claim: OS-Level Hang Limitations
 * **The Claim:** A single-machine system cannot fully detect whole-system hangs; if Windows hibernates or enters a severe paging storm, the Python process freezes and cannot notify the operator.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. This is a fundamental limitation of user-space execution. If the Windows OS scheduler suspends the process for system hibernation, or if the hardware exhausts its 8 GB of RAM and aggressively thrashes the SATA SSD, the Python interpreter ceases execution entirely. It cannot execute a watchdog hook, update a heartbeat, or fire a network request to Telegram. Acknowledging this limitation and relying on an operator-side expectation of periodic Telegram keepalive messages is the only technically correct Phase 1 mitigation.
### Arbiter Conclusion
The technical mechanisms proposed for token estimation, Ollama metadata retrieval, process timeouts, and the realities of OS-level process freezing are entirely factually sound.
The architecture is factually cleared to advance to targeted panel confirmation.
