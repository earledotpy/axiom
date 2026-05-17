**Arbiter Rulings: AXIOM Proposals v1.11.2 & v1.11.3**
As the Research and Knowledge Arbiter, I have evaluated the factual claims regarding libraries, schemas, and API capabilities in the latest targeted revisions.
Here are my binding rulings on the technical realities.
### 1. Claim: JSON Schema 2020-12 Limitations on Cross-Field Equality
 * **The Claim:** Pure JSON Schema 2020-12 is not reliable for enforcing cross-field equality (e.g., verifying that allowed_commands[0] exactly matches operator_command.command_name) without implementation-specific extensions.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Standard JSON Schema validates the static structure and data types of a document. It does not possess native operators to compare the value of one arbitrary dynamic field to another within the same document. While custom extensions (like $data in Ajv) exist, they are non-standard. Shifting the equality enforcement layer into Python via the ManifestBinder is factually necessary.
### 2. Claim: JSON Schema Conditional Rejections (additionalProperties, allOf)
 * **The Claim:** Using additionalProperties: false will successfully reject unauthorized branches (such as network or sandbox within allowed_capabilities), and conditional allOf / if / then arrays can dynamically enforce minItems depending on the mode parameter.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. These are standard, well-supported validation mechanisms in JSON Schema Draft 2020-12. Standard Python validators like the jsonschema library will correctly fail validation if unlisted properties are introduced or if the conditional dependency logic is violated.
### 3. Claim: SQLite Descending Indexes for Log-Based Reading
 * **The Claim:** Applying CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_latest ON scheduler_heartbeat(session_id, last_freshness_at DESC, heartbeat_id DESC); will efficiently support querying the latest heartbeat in a log-model table.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. SQLite fully supports descending indexes (DESC). This index exactly aligns with the ORDER BY last_freshness_at DESC, heartbeat_id DESC LIMIT 1 query pattern. This guarantees an O(1) or O(log N) index lookup, avoiding full table scans on the SATA SSD as the heartbeat table grows.
### 4. Claim: SQLite-Vec Sparse Virtual Tables
 * **The Claim:** The sqlite-vec extension allows memory_item_embeddings to remain sparse by explicitly inserting vectors with an exact rowid mapping back to the primary table (INSERT INTO memory_item_embeddings(rowid, embedding)) only once the embedding is indexed.
 * **Arbiter Ruling: VERIFIED**
 * **The Reality:** Factually accurate. Virtual tables in sqlite-vec are inherently tied to SQLite's hidden rowid. Explicitly supplying the rowid during insertion to mirror the memory_items.memory_item_id is the architecturally correct way to link the semantic text to its vector without requiring placeholder embeddings for pending or failed items.
### 5. Claim: Intercepting and Validating HTTP Redirects
 * **The Claim:** The network gateway can enforce a redirect_policy of same_host_only by ensuring the redirected URL exactly matches the original request's scheme, host, port, and path prefix.
 * **Arbiter Ruling: VERIFIED WITH IMPLEMENTATION CAVEAT**
 * **The Reality:** Factually implementable, but requires specific configuration. Standard Python HTTP libraries (such as requests and aiohttp) default to following 3xx redirects automatically.
 * **The Caveat:** To enforce the strict validation specified in the proposal, Kimi must configure the HTTP client to disable automatic redirection (allow_redirects=False in requests). The NetworkGateway must manually catch 3xx responses, extract the Location header, parse it via urllib.parse, run the scheme/host/port/path comparisons, and then manually dispatch the secondary request.
### Arbiter Conclusion
The factual claims regarding JSON Schema boundaries, SQLite index optimization, vector sparsity, and HTTP redirect semantics are technically sound.
The proposals are factually cleared.
