I've reviewed v1.11.2 and v1.11.3 together. They successfully close the capability/policy duplication and the operator-control privilege boundary—both are clean improvements. However, the new detail exposes several specific security and resilience gaps.

---

OBJECTION 1 — Tool Capability Map File Is Not Integrity-Verified, Undermining Manifest Authorization

What the proposals say:

· v1.11.2 introduces core/tool_capability_map.py as the static mapping that defines which tool requires which policy check, including that session_controller.* tools must have manifest_type = "operator_control" (v1.11.3).
· Manifest JSON files are SHA256-fingerprinted and verified at boot (manifest_fingerprints table).
· No equivalent integrity protection exists for Python source files.

The gap:
An attacker who modifies tool_capability_map.py can:

· Remove the session_controller.* → operator-control manifest requirement, allowing a role manifest to execute operator commands.
· Alter the sandbox or network tool mappings to bypass policy checks (e.g., allowing sandbox_gateway.execute without requiring sandbox_policy.allowed = true).
· Add entirely new tool IDs that map to no checks at all.

Because the map is loaded as a Python module and never checked against a stored hash, there is no boot-time detection of tampering. All the careful manifest schema work and OperatorControl capability guards are bypassed with a single file edit on the laptop's filesystem.

Remedy: The tool capability map must be treated as a security artifact and included in the manifest integrity system—either by storing its SHA256 in manifest_fingerprints alongside the JSON manifests, or by generating it from a verified JSON file that is already covered. Without this, the authorization framework has a silent bypass path.

---

OBJECTION 2 — Resource Policies (network_policy, sandbox_policy, memory_policy) Are Not Explicitly Required in the Manifest Schema

What the proposals imply:
The revised allowed_capabilities no longer contains network, sandbox, or memory. Tool authorization looks up those top-level policy objects. Examples show every manifest includes them, and the JSON Schema snippets define their structure.

What the proposals do not state:
That network_policy, sandbox_policy, and memory_policy are required top-level fields in the full manifest schema. The schema excerpts in v1.11.2 only show the $defs and the conditional allOf but not the required array at the root level.

The failure mode:
A manifest that omits network_policy entirely could pass schema validation if it's not a required field. When PolicyEngine later evaluates a network fetch tool, it references network_policy, which is missing. This could raise a Python KeyError or AttributeError. If that exception is not handled in a strict fail‑closed manner, it could lead to a default‑deny (safe) or a crash (DoS). If mishandled, it might even be interpreted as "no restrictions" depending on implementation. The architecture should guarantee that all task manifests that might be bound to a network-using tool have an explicit, present network_policy, and similarly for sandbox and memory.

Required fix: The manifest schema must declare network_policy, sandbox_policy, and memory_policy as required top-level fields for all manifest types that might use the corresponding gateways. ManifestBinder should reject any manifest missing them.

---

OBJECTION 3 — No Upper Bound on network_policy.max_response_bytes Permits Memory Exhaustion

What v1.11.2 specifies:
max_response_bytes is an integer ≥0. The allowlist_only example uses 1,048,576 (1 MB). There is no stated maximum.

The risk:
A Task Planner with network_gateway.fetch permission could create a child task whose manifest specifies max_response_bytes = 1,073,741,824 (1 GB). If the Network Gateway attempts to buffer the response, it will exhaust the process's memory, causing a SATA SSD paging storm or out-of-memory crash on a machine with only ~2 GB of runtime headroom. This violates the hard hardware constraints.

Possible mitigation: ManifestBinder or PolicyEngine must enforce a ceiling on max_response_bytes (e.g., 5 MB or 10 MB, well within the ~500 KB context bundle limit? Actually the response might not go into a context bundle; it could be stored as an artifact. But still, RAM consumption during fetch and processing must be bounded). A reasonable cap should be set and enforced at manifest registration or dispatch time.

---

OBJECTION 4 — No Retention Policy for scheduler_heartbeat or soft-deleted memory_items Leads to Unbounded Disk Growth

What the Evaluator flagged:
The v1.11.3 deferred list includes “scheduler_heartbeat retention” and “memory_items soft-deleted retention” for Constraints and Critic review.

The gap:

· scheduler_heartbeat is an append-only log table. A long-running autonomous session (hours or days) will accumulate thousands of rows. Without a retention policy (e.g., delete all but the last N rows per session, or rows older than X hours), the database will grow continuously, eventually competing for the limited SATA SSD space.
· memory_items with embedding_status = 'soft_deleted' are preserved “for audit.” Without a purge mechanism, they also grow indefinitely, and their associated vector entries are deleted but the row remains. Over months of use, this can bloat the database further.

Operational risk: Disk exhaustion causes hard failures, potentially corrupting the SQLite file. The Constraints Register’s hardware profile does not specify free disk space, but the SATA SSD capacity is finite. A purely append-log and never-delete design is a known long-term failure mode for embedded databases.

Recommended: Define a minimal retention policy now (e.g., keep heartbeats only for the current session and the previous session; purge soft-deleted memory items older than 90 days, or provide a manual /purge_old_memory operator command). This is not a Phase 1 blocking issue for the first autonomous run, but it is a design gap for sustained operation.

---

OBJECTION 5 — Allowed_tools Values Are Not Constrained to Canonical Tool Identifiers in the Manifest Schema

What the proposals define:

· TOOL_CAPABILITY_MAP has a closed set of canonical tool IDs.
· Tool authorization denies any tool not in the map.
· allowed_tools and forbidden_tools are arrays of strings.

The gap:
The manifest JSON Schema for allowed_tools items is not shown to be restricted to an enum of known tool IDs. Therefore, a manifest can contain a misspelled tool like "network_gatewat.fetch" or a future tool name that is not yet in the map. Because unmapped tools are denied, this is currently safe—the task would fail authorization. But it introduces a silent configuration error: a Goal Planner could generate a plan with a tool ID that passes plan verification (since it's syntactically valid) but then fails late at dispatch with a cryptic policy denial.

Why this matters for security:
If, in a future iteration, the “unmapped tool → deny” rule is relaxed accidentally, or if a tool ID is added to the map but the manifest schema isn’t updated, the system could fall into an inconsistent state. Tightening the schema now to accept only canonical tool IDs would prevent a whole class of configuration drift vulnerabilities. It also makes manifest validation fail early at registration time, which is preferable to runtime discovery.

---

OBJECTION 6 — Operator-Control Capability Token Is Not Verified When the Operator Is Using /status or /shutdown_after_current During Disabled Autonomous Mode

What v1.11.3 adds:
Tool authorization rule: “if tool_id starts with ‘session_controller.’, manifest_type must be ‘operator_control’.”

What the operator-control manifest example (in v1.11.2, Section 6) shows:
For /status, authorization_policy.capability_token_required = false and allowed_when_autonomous_disabled = true. This appears to be a deliberate design choice, allowing the operator to query status even if the system is not in full autonomous mode or the capability token is missing (e.g., after a restart where the token hasn't been re-initialized?).

The subtle risk:
If a non‑operator message could somehow reach the Telegram Gateway and be parsed as a /status command, it could trigger a status task without the capability token. The operator-control manifest’s allowed_when_autonomous_disabled and capability_token_required = false are permissive by design, to ensure the operator can always recover the session. However, this relies entirely on the Telegram Gateway’s operator_whitelist (user ID check) as the sole authentication. If a future code change or misconfiguration removes that whitelist, the /status command becomes accessible to anyone who can send a Telegram message to the bot. This is not a flaw in the current architecture, but it’s a concentrated risk: the only barrier is the Telegram user ID, not the multi-layer capability token system. The panel should document this as a conscious trade-off and ensure the whitelist is never deactivated without full panel consent.

---

Summary of Objections

# Category Core Issue
1 Security Weakness Tool capability map is not integrity-verified; modification can bypass manifest authorization entirely
2 Specification Gap Network/sandbox/memory policies not explicitly required in manifest schema; missing fields could cause unsafe behavior
3 Resource Exhaustion No upper bound on network max_response_bytes; large value can exhaust RAM
4 Operational Risk No retention policies for heartbeat log or soft-deleted memory items; unbounded disk growth
5 Defense-in-depth Gap allowed_tools values not constrained to canonical set; typo-tolerant but fragile
6 Risk Concentration /status and similar recovery commands rely solely on Telegram whitelist; capability token bypass is intentional but risky

None of these are bare assertions. Each cites specific sections of the proposals and identifies a concrete gap, unstated assumption, or potential failure mode. I await the Research Arbiter’s factual verification and the Constraints Reviewer’s feasibility assessment.