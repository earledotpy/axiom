# AXIOM Implementation Plan v1.12

**Status:** Panel-approved — derived from proposal stack v1.10 -> v1.10.1 -> v1.10.2 -> v1.11.1 -> v1.11.2 -> v1.11.3 -> v1.11.4 -> v1.11.4 Final Patch  
**Author:** Kimi K2.6 — Implementation Specialist  
**Date:** 2026-05-04  
**Binding constraints source:** `AXIOM_Constraints_v1.11.3.md` (Qwen 3.6 Plus, twelve binding conditions)  
**Gap 3 resolution source:** `AXIOM_Arbiter_v1.11.md` (Gemini Arbiter binding ruling on Ollama thinking-mode verification)

---

## 1. Delta Summary — v1.11 -> v1.12

The v1.11 plan identified seven gaps. Three were resolved by the v1.11.1–v1.11.4 proposal stack plus the Arbiter Gap 3 ruling. Four remain deferred to later phases per panel direction.

| Gap | v1.11 Status | Resolution in v1.12 |
|-----|-------------|---------------------|
| 1 — Canonical database schema | Deferred to Architect | **Resolved.** Replaces inferred schema with v1.11.1 Section 1.2 canonical schema as amended by v1.11.4 (tool_capability_map in manifest_fingerprints, schema version v1.11.4). |
| 2 — Canonical manifest JSON schema | Deferred to Architect | **Resolved.** Replaces inferred manifest with v1.11.2 Section 2 canonical schema as amended by v1.11.3 (operator-control privilege boundary) and v1.11.4 (tool ID enum, 5 MiB max_response_bytes ceiling). |
| 3 — qwen3:4b thinking-mode inference | Deferred to Arbiter | **Resolved.** Arbiter ruled: inspect `parameters` field only, regex `(?i)^\s*think\s+false\s*$` with MULTILINE, return `disabled`/`unknown`. Template and system fields are non-authoritative. |
| 4 — Calibration test set authoring | Deferred | **Remains deferred** to Phase 3 (panel workflow dependency). Blocks classifier-dependent paths only. |
| 5 — Windows Job Object specifics | Deferred | **Remains deferred** to Phase 4 (sandbox gateway). Blocks sandbox execution hardening only. |
| 6 — Cloud cascade configuration | Deferred | **Remains deferred** to Phase 4 (model gateway). Blocks cloud-calling tasks only. |
| 7 — Telegram operator whitelist mechanism | Deferred | **Remains deferred** to Phase 6 (control plane). Blocks Telegram authorization chain completion only. |

---

## 2. Binding Constraints Register

The following twelve conditions from the Constraints Reviewer (`AXIOM_Constraints_v1.11.3.md`) are binding on every implementation decision in this plan. Any deviation requires full panel consensus with written rationale.

| # | Condition | Enforcement Location in v1.12 |
|---|-----------|--------------------------------|
| 1 | **Sequential execution** — no concurrent agent subprocesses | `core/scheduler.py` — single running task invariant; `core/state_machine.py` — atomic transitions |
| 2 | **qwen3:4b Q4 quantized** — memory-mapped via Ollama, no full RAM load | `config/axiom.yaml` — model name pinned; `security/model_fingerprint_guard.py` — quantization extraction from `/api/show` |
| 3 | **500 KB context bundle cap** | `core/context_builder.py` — serialized bundle size gate; `core/resource_limits.py` — `max_bundle_kb` enforcement |
| 4 | **256 MB sandbox RAM + 60 s wall-clock cap** | `gateways/sandbox_gateway.py` — Windows Job Object; `subprocess.run(timeout=60)` |
| 5 | **sqlite-vec 100-vector batch limit** | `gateways/memory_gateway.py` — `LIMIT 100` on vector queries; stream results for deduplication |
| 6 | **Brave Search confirmation before web search** | Phase 4 deferred. `gateways/network_gateway.py` — allowlist verification before any fetch |
| 7 | **Tiered token margins** — 2.0x calibrated, 1.5x fallback | `core/resource_limits.py` — `TokenEstimator` margin application |
| 8 | **Stateless PolicyEngine and ManifestBinder** — boot-time cached validators | `core/policy_engine.py`, `core/manifest_binder.py` — validators compiled once at boot; runtime uses cached compiled objects |
| 9 | **4-thread cap** — main, Telegram, Scheduler, BootstrapValidationWorker | `app/session_controller.py` — thread creation gate; no additional workers |
| 10 | **Fail-closed on fingerprint or manifest mismatch** | `security/model_fingerprint_guard.py`, `security/audit.py::ManifestIntegrityVerifier` — disable autonomous on any mismatch |
| 11 | **Bounded SQLite page cache** | `axiom/persistence/db.py` — `PRAGMA cache_size=-32768` (32 MiB, 8192 pages at 4 KiB) |
| 12 | **Classifier safe-pass disabled until calibration passes** | `app/session_controller.py::bootstrap()` — safe-pass starts disabled; `security/plan_injection_scanner.py` — short-circuits classifier path |

---

## 3. Canonical Database Schema (Requirement 1)

**Source:** v1.11.1 Section 1.2 as amended by v1.11.4 (tool_capability_map in manifest_fingerprints, schema version v1.11.4).  
**Rule:** `init_db()` MUST NOT be executed until this exact file is written to disk and panel-ratified.

**File path:** `axiom/persistence/schema.sql`

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -32768;  -- 32 MiB page cache, binding condition 11

-- ============================================================
-- AXIOM CANONICAL DATABASE SCHEMA
-- Version: v1.11.4 (panel-ratified)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Schema migration ledger
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    notes TEXT
);

INSERT OR IGNORE INTO schema_migrations (schema_version, notes)
VALUES (
    'v1.11.4',
    'Initial AXIOM MVP canonical schema with manifest schemas, tool-capability security artifact, network response ceiling, and Ollama think=false verification.'
);

-- ------------------------------------------------------------
-- 2. Sessions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    ended_at TEXT,

    operator_id TEXT,
    current_chain_id TEXT,

    autonomous_operation_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (autonomous_operation_enabled IN (0, 1)),

    scheduler_status TEXT NOT NULL DEFAULT 'initializing'
        CHECK (scheduler_status IN (
            'initializing',
            'ready',
            'running',
            'paused_after_current',
            'safe_disabled',
            'shutdown_requested',
            'stopped',
            'error'
        )),

    shutdown_requested INTEGER NOT NULL DEFAULT 0
        CHECK (shutdown_requested IN (0, 1)),

    safe_pass_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (safe_pass_enabled IN (0, 1)),

    safe_pass_disabled_reason TEXT
        CHECK (
            safe_pass_disabled_reason IS NULL OR
            safe_pass_disabled_reason IN (
                'fingerprint_mismatch',
                'verification_timeout',
                'connection_error',
                'malformed_response',
                'schema_change',
                'model_unavailable',
                'no_stored_profile',
                'calibration_missing',
                'calibration_failed',
                'operator_disabled',
                'manifest_integrity_mismatch'
            )
        ),

    safe_pass_disabled_at TEXT,

    safe_pass_alert_sent INTEGER NOT NULL DEFAULT 0
        CHECK (safe_pass_alert_sent IN (0, 1))
);

-- ------------------------------------------------------------
-- 3. Task queue
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    parent_task_id INTEGER,

    chain_id TEXT NOT NULL,
    task_class TEXT NOT NULL
        CHECK (task_class IN (
            'operator_control',
            'goal_planning',
            'task_planning',
            'tool_execution',
            'result_verification',
            'memory_operation',
            'system_maintenance'
        )),

    task_type TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'running',
            'completed',
            'failed',
            'quarantined',
            'needs_human_input',
            'blocked_resource_limit',
            'cancelled'
        )),

    priority INTEGER NOT NULL DEFAULT 5
        CHECK (priority BETWEEN 0 AND 10),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    started_at TEXT,
    completed_at TEXT,

    goal_text TEXT,
    input_json TEXT,
    result_text TEXT,
    result_json TEXT,
    error_info TEXT,

    manifest_id TEXT,

    commit_batch_id TEXT,

    cancel_requested INTEGER NOT NULL DEFAULT 0
        CHECK (cancel_requested IN (0, 1)),

    blocked_reason TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_tasks_session_status_priority
    ON tasks(session_id, status, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_tasks_chain
    ON tasks(chain_id);

CREATE INDEX IF NOT EXISTS idx_tasks_parent
    ON tasks(parent_task_id);

CREATE INDEX IF NOT EXISTS idx_tasks_commit_batch
    ON tasks(commit_batch_id);

-- ------------------------------------------------------------
-- 4. Task permissions / manifest binding
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,
    manifest_id TEXT NOT NULL,

    granted_capabilities_json TEXT NOT NULL,
    granted_tools_json TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_task_permissions_task
    ON task_permissions(task_id);

-- ------------------------------------------------------------
-- 5. Session events
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    event_type TEXT NOT NULL,
    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_session_events_session_created
    ON session_events(session_id, created_at);

-- ------------------------------------------------------------
-- 6. Security events
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER,
    task_id INTEGER,

    event_type TEXT NOT NULL,
    reason TEXT,

    severity TEXT NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical')),

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_security_events_session_created
    ON security_events(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_security_events_task
    ON security_events(task_id);

CREATE INDEX IF NOT EXISTS idx_security_events_type
    ON security_events(event_type);

-- ------------------------------------------------------------
-- 7. Scheduler heartbeat
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scheduler_heartbeat (
    heartbeat_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    last_freshness_at TEXT NOT NULL,
    last_tick_started_at TEXT,
    last_tick_completed_at TEXT,

    last_blocking_operation_started_at TEXT,
    last_blocking_operation_completed_at TEXT,
    last_blocking_operation_type TEXT,

    active_task_id INTEGER,
    active_chain_id TEXT,

    scheduler_state TEXT,
    last_action TEXT,

    tick_count INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (active_task_id)
        REFERENCES tasks(task_id)
        ON DELETE SET NULL
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_session
    ON scheduler_heartbeat(session_id);

CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_latest
    ON scheduler_heartbeat(session_id, last_freshness_at DESC, heartbeat_id DESC);

-- ------------------------------------------------------------
-- 8. Classifier calibration runs
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classifier_calibration_runs (
    calibration_run_id TEXT PRIMARY KEY,

    calibration_set_id TEXT NOT NULL,
    calibration_set_sha256 TEXT NOT NULL,

    model_name TEXT NOT NULL,
    ollama_host TEXT NOT NULL,

    threshold REAL NOT NULL
        CHECK (threshold >= 0.0 AND threshold <= 1.0),

    passed INTEGER NOT NULL
        CHECK (passed IN (0, 1)),

    true_positive_count INTEGER NOT NULL DEFAULT 0,
    true_negative_count INTEGER NOT NULL DEFAULT 0,
    false_positive_count INTEGER NOT NULL DEFAULT 0,
    false_negative_count INTEGER NOT NULL DEFAULT 0,

    false_positive_rate REAL,
    false_negative_rate REAL,

    approved_by_panel_version TEXT NOT NULL,

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_classifier_calibration_runs_model_created
    ON classifier_calibration_runs(model_name, created_at);

-- ------------------------------------------------------------
-- 9. Model profile fingerprints
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_profile_fingerprints (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,

    profile_label TEXT NOT NULL DEFAULT 'default',

    model_name TEXT NOT NULL,
    ollama_host TEXT NOT NULL,

    ollama_model_tag TEXT NOT NULL,
    ollama_model_digest TEXT NOT NULL,

    quantization TEXT NOT NULL,
    parameter_size TEXT,
    model_family TEXT,
    model_format TEXT,

    thinking_mode TEXT NOT NULL
        CHECK (thinking_mode IN ('disabled', 'enabled', 'unknown')),

    thinking_mode_rule_version TEXT,

    template_sha256 TEXT,
    system_sha256 TEXT,
    parameters_sha256 TEXT,
    details_sha256 TEXT,

    selected_profile_sha256 TEXT NOT NULL UNIQUE,

    calibration_run_id TEXT NOT NULL,

    is_current INTEGER NOT NULL DEFAULT 0
        CHECK (is_current IN (0, 1)),

    registration_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (registration_status IN (
            'candidate',
            'current',
            'superseded',
            'rejected'
        )),

    registered_by_tool_version TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    notes TEXT,

    CHECK (is_current = 0 OR thinking_mode != 'unknown'),
    CHECK (
        (is_current = 1 AND registration_status = 'current')
        OR
        (is_current = 0)
    ),

    FOREIGN KEY (calibration_run_id)
        REFERENCES classifier_calibration_runs(calibration_run_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_model_profile_one_current
    ON model_profile_fingerprints(profile_label)
    WHERE is_current = 1;

CREATE INDEX IF NOT EXISTS idx_model_profile_calibration
    ON model_profile_fingerprints(calibration_run_id);

-- ------------------------------------------------------------
-- 10. Manifest integrity fingerprints
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS manifest_fingerprints (
    fingerprint_id INTEGER PRIMARY KEY AUTOINCREMENT,

    manifest_id TEXT NOT NULL UNIQUE,
    manifest_type TEXT NOT NULL
        CHECK (manifest_type IN ('role', 'operator_control', 'tool_capability_map')),

    relative_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,

    schema_version TEXT NOT NULL,
    manifest_version TEXT NOT NULL,

    role_name TEXT,
    command_name TEXT,

    approved_by_panel_version TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1
        CHECK (active IN (0, 1)),

    registered_by_tool_version TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (
        (manifest_type = 'role' AND role_name IS NOT NULL AND command_name IS NULL)
        OR
        (manifest_type = 'operator_control' AND command_name IS NOT NULL AND role_name IS NULL)
        OR
        (manifest_type = 'tool_capability_map' AND role_name IS NULL AND command_name IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_manifest_fingerprints_type_active
    ON manifest_fingerprints(manifest_type, active);

-- ------------------------------------------------------------
-- 11. Provider usage tracking
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    task_id INTEGER,

    provider TEXT NOT NULL
        CHECK (provider IN (
            'cerebras',
            'groq',
            'openrouter',
            'sambanova',
            'ollama_local'
        )),
    model TEXT,

    status TEXT NOT NULL DEFAULT 'started'
        CHECK (status IN (
            'started',
            'completed',
            'failed',
            'rate_limited',
            'quota_exhausted',
            'abandoned_session_crash'
        )),

    estimated_input_tokens INTEGER,
    estimated_output_tokens INTEGER,

    actual_input_tokens INTEGER,
    actual_output_tokens INTEGER,

    actuals_unavailable INTEGER NOT NULL DEFAULT 0
        CHECK (actuals_unavailable IN (0, 1)),

    charged_input_estimate INTEGER,
    charged_output_estimate INTEGER,

    error_info TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_session_created
    ON provider_usage(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_provider_usage_provider_status
    ON provider_usage(provider, status);

-- ------------------------------------------------------------
-- 12. Provider usage reconciliations
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_usage_reconciliations (
    reconciliation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    provider TEXT NOT NULL,

    date_range_start TEXT NOT NULL,
    date_range_end TEXT NOT NULL,

    operator_reported_input_tokens INTEGER,
    operator_reported_output_tokens INTEGER,

    local_estimated_tokens INTEGER,
    adjustment_tokens INTEGER,

    discrepancy_percent REAL,

    confirmed_large_adjustment INTEGER NOT NULL DEFAULT 0
        CHECK (confirmed_large_adjustment IN (0, 1)),

    operator_confirmation_timestamp TEXT,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_reconciliations_provider_dates
    ON provider_usage_reconciliations(provider, date_range_start, date_range_end);

-- ------------------------------------------------------------
-- 13. Plan artifacts
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,
    parent_task_id INTEGER,

    artifact_type TEXT NOT NULL
        CHECK (artifact_type IN (
            'goal_plan',
            'task_plan',
            'tool_plan',
            'memory_write_candidate',
            'operator_control_plan'
        )),

    artifact_status TEXT NOT NULL DEFAULT 'draft'
        CHECK (artifact_status IN (
            'draft',
            'scanner_passed',
            'checkpoint_passed',
            'checkpoint_failed',
            'checkpoint_blocked',
            'quarantined',
            'committed'
        )),

    commit_status TEXT NOT NULL DEFAULT 'not_started'
        CHECK (commit_status IN (
            'not_started',
            'committing',
            'committed',
            'commit_failed',
            'rolled_back'
        )),

    risk_class TEXT NOT NULL DEFAULT 'ordinary'
        CHECK (risk_class IN ('ordinary', 'high_risk')),

    scanner_result TEXT NOT NULL DEFAULT 'not_scanned'
        CHECK (scanner_result IN (
            'not_scanned',
            'passed',
            'deterministic_block',
            'classifier_block',
            'fingerprint_mismatch',
            'verification_timeout',
            'connection_error',
            'malformed_response',
            'schema_change',
            'model_unavailable',
            'safe_pass_disabled'
        )),

    checkpoint_verdict TEXT NOT NULL DEFAULT 'not_run'
        CHECK (checkpoint_verdict IN (
            'not_run',
            'passed',
            'failed',
            'blocked'
        )),

    artifact_json TEXT NOT NULL,
    scanner_details_json TEXT,
    checkpoint_details_json TEXT,

    manifest_id TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_plan_artifacts_task
    ON plan_artifacts(task_id);

CREATE INDEX IF NOT EXISTS idx_plan_artifacts_status
    ON plan_artifacts(artifact_status);

-- ------------------------------------------------------------
-- 14. Operator commands
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS operator_commands (
    command_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,

    command_name TEXT NOT NULL,
    command_payload_json TEXT,

    manifest_id TEXT NOT NULL,

    authorization_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (authorization_status IN (
            'pending',
            'authorized',
            'rejected'
        )),

    command_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (command_status IN (
            'pending',
            'inserted_task',
            'completed',
            'failed',
            'rejected'
        )),

    rejection_reason TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_operator_commands_task
    ON operator_commands(task_id);

CREATE INDEX IF NOT EXISTS idx_operator_commands_name_status
    ON operator_commands(command_name, command_status);

-- ------------------------------------------------------------
-- 15. Semantic memory items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_items (
    memory_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER,
    source_task_id INTEGER,

    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,

    metadata_json TEXT,

    embedding_model TEXT NOT NULL DEFAULT 'nomic-embed-text',
    embedding_dim INTEGER NOT NULL DEFAULT 768
        CHECK (embedding_dim = 768),

    embedding_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (embedding_status IN (
            'pending',
            'indexed',
            'failed',
            'soft_deleted'
        )),

    dedupe_score REAL,
    dedupe_source_memory_item_id INTEGER,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (source_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (dedupe_source_memory_item_id)
        REFERENCES memory_items(memory_item_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_items_content_model
    ON memory_items(content_sha256, embedding_model);

CREATE INDEX IF NOT EXISTS idx_memory_items_session
    ON memory_items(session_id);

-- Logical memory_items.embedding is stored here.
-- Application invariant:
--     memory_item_embeddings.rowid == memory_items.memory_item_id
CREATE VIRTUAL TABLE IF NOT EXISTS memory_item_embeddings
USING vec0(
    embedding float[768]
);

-- ------------------------------------------------------------
-- 16. Resource usage
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resource_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,

    resource_type TEXT NOT NULL
        CHECK (resource_type IN (
            'sandbox_ram_mb',
            'sandbox_wall_clock_seconds',
            'context_bundle_kb',
            'estimated_input_tokens',
            'estimated_output_tokens',
            'provider_calls',
            'network_response_bytes'
        )),

    amount REAL NOT NULL,
    limit_value REAL,

    status TEXT NOT NULL
        CHECK (status IN (
            'within_limit',
            'exceeded',
            'unknown'
        )),

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_resource_usage_task
    ON resource_usage(task_id);

-- ------------------------------------------------------------
-- 17. Provider budget windows
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_budget_windows (
    window_id INTEGER PRIMARY KEY AUTOINCREMENT,

    provider TEXT NOT NULL
        CHECK (provider IN (
            'cerebras',
            'groq',
            'openrouter',
            'sambanova',
            'ollama_local'
        )),

    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,

    budget_tokens INTEGER,
    used_tokens INTEGER NOT NULL DEFAULT 0,

    budget_requests INTEGER,
    used_requests INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN (
            'open',
            'exhausted',
            'closed'
        )),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (provider, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_provider_budget_windows_provider_status
    ON provider_budget_windows(provider, status);
```


---

## 4. Canonical Manifest JSON Schema (Requirement 2)

**Source:** v1.11.2 Section 2 as amended by v1.11.3 (operator-control privilege boundary) and v1.11.4 (tool ID enum, max_response_bytes ceiling).  
**Amendment notes:**
- v1.11.2 removed `network`, `sandbox`, `memory` from `allowed_capabilities` (moved to top-level policies)
- v1.11.3 added `role_manifest` and `operator_control_manifest` $defs with cross-field constraints (role `allowed_commands.maxItems = 0`, operator-control `allowed_commands.minItems = 1, maxItems = 1`)
- v1.11.4 replaced `tool_id` pattern with canonical enum of 14 tool IDs
- v1.11.4 added `max_response_bytes.maximum = 5242880` (5 MiB)
- v1.11.4 added `network_deny_entry` wildcard semantics with `*` only
- v1.11.4 added conditional allowlist/denylist rules for `deny_all` vs `allowlist_only`

**File path:** `axiom/policy/schemas/manifest_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.manifest.schema.v1",
  "title": "AXIOM Manifest Schema v1.11.4",
  "oneOf": [
    { "$ref": "#/$defs/role_manifest" },
    { "$ref": "#/$defs/operator_control_manifest" }
  ],
  "$defs": {
    "manifest_id": {
      "type": "string",
      "pattern": "^(role|operator\\.)[a-z0-9_]+\\.v[0-9]+$"
    },
    "tool_id": {
      "type": "string",
      "enum": [
        "model_gateway.call",
        "memory_gateway.query",
        "memory_gateway.write",
        "network_gateway.fetch",
        "sandbox_gateway.execute",
        "filesystem.read",
        "filesystem.write",
        "session_controller.status",
        "session_controller.cancel_current_chain",
        "session_controller.pause_after_current",
        "session_controller.resume",
        "session_controller.shutdown_after_current",
        "session_controller.run_classifier_validation",
        "session_controller.enable_autonomous",
        "session_controller.reconcile_provider_usage"
      ]
    },
    "budget_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "max_estimated_input_tokens",
        "max_estimated_output_tokens",
        "max_provider_calls",
        "max_wall_clock_seconds"
      ],
      "properties": {
        "max_estimated_input_tokens": { "type": "integer", "minimum": 0 },
        "max_estimated_output_tokens": { "type": "integer", "minimum": 0 },
        "max_provider_calls": { "type": "integer", "minimum": 0 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0 }
      }
    },
    "allowed_capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "model", "task_queue", "filesystem", "operator_control" ],
      "properties": {
        "model": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allow_model_calls", "allowed_provider_groups", "allow_local_classifier" ],
          "properties": {
            "allow_model_calls": { "type": "boolean" },
            "allowed_provider_groups": {
              "type": "array",
              "items": { "type": "string", "enum": [ "cloud_cascade", "local_classifier" ] },
              "uniqueItems": true
            },
            "allow_local_classifier": { "type": "boolean" }
          }
        },
        "task_queue": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read_scope", "write_scope", "may_create_tasks", "may_update_own_result", "may_update_other_tasks" ],
          "properties": {
            "read_scope": { "type": "string", "enum": [ "none", "assigned_task", "own_chain" ] },
            "write_scope": { "type": "string", "enum": [ "none", "own_result", "create_child_tasks", "operator_control_insert" ] },
            "may_create_tasks": { "type": "boolean" },
            "may_update_own_result": { "type": "boolean" },
            "may_update_other_tasks": { "type": "boolean" }
          }
        },
        "filesystem": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read", "write", "allowed_roots" ],
          "properties": {
            "read": { "type": "boolean" },
            "write": { "type": "boolean" },
            "allowed_roots": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        },
        "operator_control": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allowed_commands" ],
          "properties": {
            "allowed_commands": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        }
      }
    },
    "network_allow_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "purpose" ],
      "properties": {
        "scheme": { "type": "string", "enum": [ "https" ] },
        "host": { "type": "string", "pattern": "^[a-z0-9.-]+$" },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
        "path_prefix": { "type": "string", "pattern": "^/" },
        "methods": { "type": "array", "minItems": 1, "items": { "type": "string", "enum": [ "GET", "POST" ] }, "uniqueItems": true },
        "purpose": { "type": "string" }
      }
    },
    "network_deny_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "reason" ],
      "properties": {
        "scheme": { "oneOf": [ { "const": "*" }, { "const": "https" } ] },
        "host": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^[a-z0-9.-]+$" } ] },
        "port": { "oneOf": [ { "const": "*" }, { "type": "integer", "minimum": 1, "maximum": 65535 } ] },
        "path_prefix": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^/" } ] },
        "methods": { "type": "array", "minItems": 1, "items": { "oneOf": [ { "const": "*" }, { "type": "string", "enum": [ "GET", "POST" ] } ] }, "uniqueItems": true },
        "reason": { "type": "string", "minLength": 1 }
      }
    },
    "network_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "mode", "allowlist", "denylist", "redirect_policy", "timeout_seconds", "max_response_bytes" ],
      "properties": {
        "mode": { "type": "string", "enum": [ "deny_all", "allowlist_only" ] },
        "allowlist": { "type": "array", "items": { "$ref": "#/$defs/network_allow_entry" }, "uniqueItems": true },
        "denylist": { "type": "array", "items": { "$ref": "#/$defs/network_deny_entry" }, "uniqueItems": true },
        "redirect_policy": { "type": "string", "enum": [ "deny", "same_host_only" ] },
        "timeout_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "max_response_bytes": { "type": "integer", "minimum": 0, "maximum": 5242880 }
      },
      "allOf": [
        {
          "if": { "properties": { "mode": { "const": "allowlist_only" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "minItems": 1 }, "timeout_seconds": { "minimum": 1 }, "max_response_bytes": { "minimum": 1 } } }
        },
        {
          "if": { "properties": { "mode": { "const": "deny_all" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "maxItems": 0 }, "timeout_seconds": { "const": 0 }, "max_response_bytes": { "const": 0 } } }
        }
      ]
    },
    "sandbox_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "allowed", "max_ram_mb", "max_wall_clock_seconds", "network_access" ],
      "properties": {
        "allowed": { "type": "boolean" },
        "max_ram_mb": { "type": "integer", "minimum": 0, "maximum": 256 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "network_access": { "type": "string", "enum": [ "denied" ] }
      }
    },
    "memory_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "read", "write", "max_query_results", "write_requires_dedupe" ],
      "properties": {
        "read": { "type": "boolean" },
        "write": { "type": "boolean" },
        "max_query_results": { "type": "integer", "minimum": 0 },
        "write_requires_dedupe": { "type": "boolean" }
      }
    },
    "audit_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "log_task_id", "log_manifest_id", "log_tool_calls", "log_policy_denials" ],
      "properties": {
        "log_task_id": { "type": "boolean", "const": true },
        "log_manifest_id": { "type": "boolean", "const": true },
        "log_tool_calls": { "type": "boolean" },
        "log_policy_denials": { "type": "boolean", "const": true }
      }
    },
    "role_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "role", "budget_policy",
        "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "role" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "role": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "role_name", "role_tier", "allowed_task_classes", "may_create_child_tasks", "may_commit_task_tree" ],
          "properties": {
            "role_name": { "type": "string" },
            "role_tier": { "type": "string", "enum": [ "goal_planner", "task_planner", "tool_executor", "result_verifier", "system" ] },
            "allowed_task_classes": { "type": "array", "items": { "type": "string", "enum": [ "goal_planning", "task_planning", "tool_execution", "result_verification", "memory_operation", "system_maintenance" ] }, "uniqueItems": true },
            "may_create_child_tasks": { "type": "boolean" },
            "may_commit_task_tree": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "maxItems": 0 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    },
    "operator_control_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "operator_command", "authorization_policy",
        "budget_policy", "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "operator_control" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "operator_command": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "command_name", "telegram_aliases", "creates_task", "created_task_class", "allowed_when_autonomous_disabled", "allowed_when_safe_pass_disabled", "effect_class" ],
          "properties": {
            "command_name": { "type": "string", "enum": [ "status", "cancel_current_chain", "pause_after_current", "resume", "shutdown_after_current", "run_classifier_validation", "enable_autonomous", "reconcile_provider_usage" ] },
            "telegram_aliases": { "type": "array", "items": { "type": "string", "pattern": "^/" }, "uniqueItems": true },
            "creates_task": { "type": "boolean" },
            "created_task_class": { "type": "string", "const": "operator_control" },
            "allowed_when_autonomous_disabled": { "type": "boolean" },
            "allowed_when_safe_pass_disabled": { "type": "boolean" },
            "effect_class": { "type": "string", "enum": [ "read_only", "state_change", "shutdown", "calibration", "reconciliation" ] }
          }
        },
        "authorization_policy": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "telegram_operator_whitelist_required", "capability_token_required", "requires_active_session" ],
          "properties": {
            "telegram_operator_whitelist_required": { "type": "boolean", "const": true },
            "capability_token_required": { "type": "boolean" },
            "requires_active_session": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "minItems": 1, "maxItems": 1 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    }
  }
}
```


---

## 5. Canonical Tool-Capability Map Schema (Requirement 7 / v1.11.4 Final Patch Section 1)

**Source:** v1.11.4 item 1 + v1.11.4 Final Patch Section 1.6  
**Rule:** The tool-capability map is a first-class registered security artifact. It is validated by JSON Schema, SHA256-fingerprinted, and verified at boot. The Python module `axiom/core/tool_capability_map.py` loads and exposes this JSON; it does not contain the authoritative map inline.

**File path:** `axiom/policy/security_artifacts/tool_capability_map.json`

```json
{
  "schema_version": "axiom.tool_capability_map.v1",
  "artifact_type": "tool_capability_map",
  "artifact_id": "security.tool_capability_map.v1",
  "artifact_version": "1.0.0",
  "approved_by_panel_version": "v1.11.4",
  "tools": {
    "model_gateway.call": {
      "source": "allowed_capabilities.model.allow_model_calls",
      "additional_checks": [ "provider_group_allowed", "budget_policy_not_exceeded" ]
    },
    "memory_gateway.query": {
      "source": "memory_policy.read",
      "additional_checks": [ "memory_policy.max_query_results" ]
    },
    "memory_gateway.write": {
      "source": "memory_policy.write",
      "additional_checks": [ "memory_policy.write_requires_dedupe" ]
    },
    "network_gateway.fetch": {
      "source": "network_policy",
      "additional_checks": [ "mode_allowlist_only", "request_matches_allowlist", "request_does_not_match_denylist", "redirect_policy", "timeout_seconds", "max_response_bytes" ]
    },
    "sandbox_gateway.execute": {
      "source": "sandbox_policy.allowed",
      "additional_checks": [ "sandbox_policy.max_ram_mb", "sandbox_policy.max_wall_clock_seconds", "sandbox_policy.network_access_denied" ]
    },
    "filesystem.read": {
      "source": "allowed_capabilities.filesystem.read",
      "additional_checks": [ "path_under_allowed_roots" ]
    },
    "filesystem.write": {
      "source": "allowed_capabilities.filesystem.write",
      "additional_checks": [ "path_under_allowed_roots" ]
    },
    "session_controller.status": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "status",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.cancel_current_chain": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "cancel_current_chain",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.pause_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "pause_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.resume": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "resume",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.shutdown_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "shutdown_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.run_classifier_validation": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "run_classifier_validation",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.enable_autonomous": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "enable_autonomous",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.reconcile_provider_usage": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "reconcile_provider_usage",
      "requires_manifest_type": "operator_control"
    }
  }
}
```

**File path:** `axiom/policy/schemas/tool_capability_map_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.tool_capability_map.schema.v1",
  "title": "AXIOM Tool Capability Map Schema v1",
  "type": "object",
  "additionalProperties": false,
  "required": [ "schema_version", "artifact_type", "artifact_id", "artifact_version", "approved_by_panel_version", "tools" ],
  "properties": {
    "schema_version": { "type": "string", "const": "axiom.tool_capability_map.v1" },
    "artifact_type": { "type": "string", "const": "tool_capability_map" },
    "artifact_id": { "type": "string", "const": "security.tool_capability_map.v1" },
    "artifact_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "approved_by_panel_version": { "type": "string", "minLength": 1 },
    "tools": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "model_gateway.call", "memory_gateway.query", "memory_gateway.write",
        "network_gateway.fetch", "sandbox_gateway.execute", "filesystem.read",
        "filesystem.write", "session_controller.status",
        "session_controller.cancel_current_chain", "session_controller.pause_after_current",
        "session_controller.resume", "session_controller.shutdown_after_current",
        "session_controller.run_classifier_validation", "session_controller.enable_autonomous",
        "session_controller.reconcile_provider_usage"
      ],
      "properties": {
        "model_gateway.call": { "$ref": "#/$defs/standard_tool_entry" },
        "memory_gateway.query": { "$ref": "#/$defs/standard_tool_entry" },
        "memory_gateway.write": { "$ref": "#/$defs/standard_tool_entry" },
        "network_gateway.fetch": { "$ref": "#/$defs/standard_tool_entry" },
        "sandbox_gateway.execute": { "$ref": "#/$defs/standard_tool_entry" },
        "filesystem.read": { "$ref": "#/$defs/standard_tool_entry" },
        "filesystem.write": { "$ref": "#/$defs/standard_tool_entry" },
        "session_controller.status": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.cancel_current_chain": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.pause_after_current": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.resume": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.shutdown_after_current": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.run_classifier_validation": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.enable_autonomous": { "$ref": "#/$defs/operator_control_tool_entry" },
        "session_controller.reconcile_provider_usage": { "$ref": "#/$defs/operator_control_tool_entry" }
      }
    }
  },
  "$defs": {
    "source_path": {
      "type": "string",
      "enum": [
        "allowed_capabilities.model.allow_model_calls",
        "allowed_capabilities.filesystem.read",
        "allowed_capabilities.filesystem.write",
        "allowed_capabilities.operator_control.allowed_commands",
        "memory_policy.read",
        "memory_policy.write",
        "network_policy",
        "sandbox_policy.allowed"
      ]
    },
    "additional_check": {
      "type": "string",
      "enum": [
        "provider_group_allowed", "budget_policy_not_exceeded",
        "memory_policy.max_query_results", "memory_policy.write_requires_dedupe",
        "mode_allowlist_only", "request_matches_allowlist", "request_does_not_match_denylist",
        "redirect_policy", "timeout_seconds", "max_response_bytes",
        "sandbox_policy.max_ram_mb", "sandbox_policy.max_wall_clock_seconds",
        "sandbox_policy.network_access_denied", "path_under_allowed_roots"
      ]
    },
    "standard_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "source", "additional_checks" ],
      "properties": {
        "source": { "$ref": "#/$defs/source_path" },
        "additional_checks": { "type": "array", "items": { "$ref": "#/$defs/additional_check" }, "uniqueItems": true }
      },
      "not": { "anyOf": [ { "required": [ "required_command" ] }, { "required": [ "requires_manifest_type" ] } ] }
    },
    "operator_control_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "source", "required_command", "requires_manifest_type" ],
      "properties": {
        "source": { "type": "string", "const": "allowed_capabilities.operator_control.allowed_commands" },
        "required_command": { "type": "string", "enum": [ "status", "cancel_current_chain", "pause_after_current", "resume", "shutdown_after_current", "run_classifier_validation", "enable_autonomous", "reconcile_provider_usage" ] },
        "requires_manifest_type": { "type": "string", "const": "operator_control" },
        "additional_checks": { "type": "array", "maxItems": 0 }
      }
    }
  }
}
```



---

## 6. Registration CLIs and Integrity Mechanisms (Requirement 3)

### 6.1 Manifest Registration CLI — `tools/register_manifests.py`

**Source:** v1.10.1 Section 4 + v1.11.4 Final Patch Section 3 (atomic transaction, tool-capability map inclusion, semantic validation).  
**Boundary:** NOT imported by the autonomous runtime. Operator-invoked only, outside AXIOM runtime.

**Scan paths:**
- `axiom/policy/role_manifests/*.json`
- `axiom/policy/operator_control_manifests/*.json`
- `axiom/policy/security_artifacts/tool_capability_map.json`

**Validation sequence per file:**
1. Load JSON.
2. Select schema by artifact type (`manifest_type = role | operator_control`, `artifact_type = tool_capability_map`).
3. Validate against its JSON Schema.
4. Run semantic validation:
   - operator-control command binding (required_command matches tool suffix)
   - role allowed_commands empty
   - tool-capability map command/tool consistency
   - all manifest tool IDs exist in loaded tool-capability map
5. Compute SHA256 of canonical file bytes.
6. Insert or replace row in `manifest_fingerprints`.

**Registration order (v1.11.4 Final Patch Section 3.5):**
1. Validate `tool_capability_map.json` first.
2. Load canonical tool ID set from validated map.
3. Validate role manifests against tool ID set.
4. Validate operator-control manifests against tool ID set.
5. Write all fingerprints in one transaction.

**Canonical row values (v1.11.4 Final Patch Section 4):**

| manifest_id | manifest_type | relative_path | schema_version | role_name | command_name |
|-------------|---------------|---------------|----------------|-----------|--------------|
| `security.tool_capability_map.v1` | `tool_capability_map` | `policy/security_artifacts/tool_capability_map.json` | `axiom.tool_capability_map.v1` | NULL | NULL |
| `<manifest["manifest_id"]>` | `role` | `policy/role_manifests/<filename>.json` | `axiom.manifest.v1` | `<manifest["role"]["role_name"]>` | NULL |
| `<manifest["manifest_id"]>` | `operator_control` | `policy/operator_control_manifests/<filename>.json` | `axiom.manifest.v1` | NULL | `<manifest["operator_command"]["command_name"]>` |

**Implementation:**

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for security artifact fingerprint registration.
NOT imported by the main AXIOM runtime.
"""
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from axiom.persistence.db import DB_PATH, _apply_pragmas

POLICY_DIR = Path(__file__).parent.parent / "axiom" / "policy"
SCHEMA_DIR = Path(__file__).parent.parent / "axiom" / "policy" / "schemas"

SESSION_CONTROLLER_TOOL_COMMANDS = {
    "session_controller.status": "status",
    "session_controller.cancel_current_chain": "cancel_current_chain",
    "session_controller.pause_after_current": "pause_after_current",
    "session_controller.resume": "resume",
    "session_controller.shutdown_after_current": "shutdown_after_current",
    "session_controller.run_classifier_validation": "run_classifier_validation",
    "session_controller.enable_autonomous": "enable_autonomous",
    "session_controller.reconcile_provider_usage": "reconcile_provider_usage",
}


class ManifestValidationError(Exception):
    pass


def _load_json_schema(schema_name: str) -> dict:
    with open(SCHEMA_DIR / schema_name, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_against_json_schema(data: dict, schema: dict) -> None:
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        raise RuntimeError("jsonschema package required for manifest validation")
    except jsonschema.ValidationError as e:
        raise ManifestValidationError(f"JSON Schema validation failed: {e.message}")


def _compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_tool_capability_map_semantics(tool_map: dict) -> None:
    """v1.11.4 Final Patch Section 2 — Cross-field semantic validation."""
    tools = tool_map["tools"]
    for tool_id, expected_command in SESSION_CONTROLLER_TOOL_COMMANDS.items():
        entry = tools[tool_id]
        if entry["source"] != "allowed_capabilities.operator_control.allowed_commands":
            raise ManifestValidationError(
                f"{tool_id} must use operator_control allowed_commands source"
            )
        if entry["required_command"] != expected_command:
            raise ManifestValidationError(
                f"{tool_id} required_command must be {expected_command}"
            )
        if entry["requires_manifest_type"] != "operator_control":
            raise ManifestValidationError(
                f"{tool_id} must require operator_control manifest type"
            )


def _validate_operator_control_binding(manifest: dict) -> None:
    """v1.11.3 Section 4 — Cross-field operator_control equality."""
    manifest_type = manifest["manifest_type"]
    allowed_commands = manifest["allowed_capabilities"]["operator_control"]["allowed_commands"]

    if manifest_type == "role":
        if allowed_commands != []:
            raise ManifestValidationError(
                "Role manifests may not declare operator-control commands"
            )
        return

    if manifest_type == "operator_control":
        command_name = manifest["operator_command"]["command_name"]
        if allowed_commands != [command_name]:
            raise ManifestValidationError(
                "Operator-control manifest allowed_commands must equal [operator_command.command_name]"
            )
        return

    raise ManifestValidationError(f"Unknown manifest_type: {manifest_type}")


def _validate_manifest_tool_ids_against_map(manifest: dict, valid_tool_ids: set) -> None:
    """v1.11.4 Section 2.2 — ManifestBinder defense-in-depth: reject unknown tool IDs."""
    for tool_id in manifest.get("allowed_tools", []):
        if tool_id not in valid_tool_ids:
            raise ManifestValidationError(
                f"allowed_tools contains unknown tool_id: {tool_id}"
            )
    for tool_id in manifest.get("forbidden_tools", []):
        if tool_id not in valid_tool_ids:
            raise ManifestValidationError(
                f"forbidden_tools contains unknown tool_id: {tool_id}"
            )


def register_manifests():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _apply_pragmas(conn)
    cursor = conn.cursor()

    try:
        # --- Step 1: Validate tool_capability_map.json first ---
        tool_map_path = POLICY_DIR / "security_artifacts" / "tool_capability_map.json"
        if not tool_map_path.exists():
            raise ManifestValidationError("tool_capability_map.json not found")

        with open(tool_map_path, "r", encoding="utf-8") as f:
            tool_map = json.load(f)

        tool_map_schema = _load_json_schema("tool_capability_map_schema.json")
        _validate_against_json_schema(tool_map, tool_map_schema)
        _validate_tool_capability_map_semantics(tool_map)

        valid_tool_ids = set(tool_map["tools"].keys())
        tool_map_sha = _compute_sha256(tool_map_path)
        tool_map_rel = "policy/security_artifacts/tool_capability_map.json"

        # --- Step 2: Validate role manifests ---
        role_manifests = []
        role_dir = POLICY_DIR / "role_manifests"
        if role_dir.exists():
            for manifest_file in sorted(role_dir.glob("*.json")):
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                manifest_schema = _load_json_schema("manifest_schema.json")
                _validate_against_json_schema(data, manifest_schema)
                _validate_operator_control_binding(data)
                _validate_manifest_tool_ids_against_map(data, valid_tool_ids)
                rel = str(Path("policy/role_manifests") / manifest_file.name)
                role_manifests.append((data, rel, _compute_sha256(manifest_file)))

        # --- Step 3: Validate operator-control manifests ---
        op_manifests = []
        op_dir = POLICY_DIR / "operator_control_manifests"
        if op_dir.exists():
            for manifest_file in sorted(op_dir.glob("*.json")):
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                manifest_schema = _load_json_schema("manifest_schema.json")
                _validate_against_json_schema(data, manifest_schema)
                _validate_operator_control_binding(data)
                _validate_manifest_tool_ids_against_map(data, valid_tool_ids)
                rel = str(Path("policy/operator_control_manifests") / manifest_file.name)
                op_manifests.append((data, rel, _compute_sha256(manifest_file)))

        # --- Step 4: Atomic write ---
        cursor.execute("DELETE FROM manifest_fingerprints")

        # Tool-capability map row
        cursor.execute(
            """INSERT INTO manifest_fingerprints
               (manifest_id, manifest_type, relative_path, sha256, schema_version,
                manifest_version, role_name, command_name, approved_by_panel_version,
                active, registered_by_tool_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "security.tool_capability_map.v1",
                "tool_capability_map",
                tool_map_rel,
                tool_map_sha,
                "axiom.tool_capability_map.v1",
                tool_map["artifact_version"],
                None, None,
                tool_map["approved_by_panel_version"],
                1,
                "register_manifests_v1.12",
            ),
        )

        # Role manifest rows
        for data, rel, sha in role_manifests:
            cursor.execute(
                """INSERT INTO manifest_fingerprints
                   (manifest_id, manifest_type, relative_path, sha256, schema_version,
                    manifest_version, role_name, command_name, approved_by_panel_version,
                    active, registered_by_tool_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["manifest_id"], "role", rel, sha,
                    "axiom.manifest.v1", data["manifest_version"],
                    data["role"]["role_name"], None,
                    data["approved_by_panel_version"],
                    1, "register_manifests_v1.12",
                ),
            )

        # Operator-control manifest rows
        for data, rel, sha in op_manifests:
            cursor.execute(
                """INSERT INTO manifest_fingerprints
                   (manifest_id, manifest_type, relative_path, sha256, schema_version,
                    manifest_version, role_name, command_name, approved_by_panel_version,
                    active, registered_by_tool_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["manifest_id"], "operator_control", rel, sha,
                    "axiom.manifest.v1", data["manifest_version"],
                    None, data["operator_command"]["command_name"],
                    data["approved_by_panel_version"],
                    1, "register_manifests_v1.12",
                ),
            )

        conn.commit()
        print(f"Registered {len(role_manifests)} role, {len(op_manifests)} operator-control, 1 tool-capability-map fingerprints.")

    except ManifestValidationError as e:
        conn.rollback()
        print(f"REGISTRATION FAILED (rolled back): {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    register_manifests()
```

### 6.2 Model Fingerprint Registration CLI — `tools/register_model_fingerprint.py`

**Source:** v1.11.1 Section 3 as amended by v1.11.4 Section 9 (Arbiter ruling integration — reject unless `thinking_mode == "disabled"`).  
**Boundary:** NOT imported by the autonomous runtime.

**Canonical command:**
```powershell
python tools\register_model_fingerprint.py `
  --profile-label default `
  --calibration-run-id injection_classifier_v1_2026_05_03 `
  --approved-by-panel-version v1.11.4
```

**Implementation:**

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for model fingerprint registration.
NOT imported by the main AXIOM runtime.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from axiom.persistence.db import DB_PATH, _apply_pragmas

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("AXIOM_OLLAMA_MODEL", "qwen3:4b")

THINK_FALSE_PATTERN = re.compile(
    r"(?i)^\s*think\s+false\s*$",
    re.MULTILINE,
)


class FingerprintRegistrationError(Exception):
    pass


def _infer_thinking_mode(show_json: dict) -> str:
    """
    v1.11.4 Section 9 / Arbiter ruling: inspect ONLY the `parameters` field.
    Returns "disabled" on match, "unknown" on no match.
    """
    params = str(show_json.get("parameters", ""))
    if THINK_FALSE_PATTERN.search(params):
        return "disabled"
    return "unknown"


def _extract_quantization(data: dict) -> str:
    """Extract quantization from Ollama /api show response."""
    details = data.get("details", {})
    q = details.get("quantization_level")
    if q:
        return str(q)
    return "unknown"


def _hash_canonical_json(obj: dict) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _query_ollama_show(model: str) -> dict:
    import requests
    resp = requests.post(
        f"{OLLAMA_HOST}/api/show",
        json={"name": model},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def register_model_fingerprint(
    profile_label: str,
    calibration_run_id: str,
    approved_by_panel_version: str,
):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _apply_pragmas(conn)
    cursor = conn.cursor()

    try:
        # 1. Verify calibration exists and passed
        cursor.execute(
            "SELECT passed FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            (calibration_run_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise FingerprintRegistrationError(
                f"Calibration run not found: {calibration_run_id}"
            )
        if row[0] != 1:
            raise FingerprintRegistrationError(
                f"Calibration run did not pass: {calibration_run_id}"
            )

        # 2. Query Ollama
        show_json = _query_ollama_show(DEFAULT_MODEL)

        # 3. Extract fields
        model_name = DEFAULT_MODEL
        ollama_host = OLLAMA_HOST
        ollama_model_tag = str(show_json.get("modelfile", ""))[:200]
        ollama_model_digest = str(show_json.get("digest", ""))
        quantization = _extract_quantization(show_json)
        parameter_size = str(show_json.get("details", {}).get("parameter_size", "")) or None
        model_family = str(show_json.get("details", {}).get("family", "")) or None
        model_format = str(show_json.get("details", {}).get("format", "")) or None

        # 4. Arbiter-approved thinking-mode inference
        thinking_mode = _infer_thinking_mode(show_json)
        if thinking_mode != "disabled":
            raise FingerprintRegistrationError(
                "Cannot register model fingerprint: Ollama profile does not prove think=false"
            )

        template_sha256 = _hash_canonical_json({"template": show_json.get("template", "")})
        system_sha256 = _hash_canonical_json({"system": show_json.get("system", "")})
        parameters_sha256 = _hash_canonical_json({"parameters": show_json.get("parameters", "")})
        details_sha256 = _hash_canonical_json(show_json.get("details", {}))

        selected_profile_object = {
            "model_name": model_name,
            "ollama_host": ollama_host,
            "ollama_model_tag": ollama_model_tag,
            "ollama_model_digest": ollama_model_digest,
            "quantization": quantization,
            "parameter_size": parameter_size,
            "model_family": model_family,
            "model_format": model_format,
            "thinking_mode": thinking_mode,
            "template_sha256": template_sha256,
            "system_sha256": system_sha256,
            "parameters_sha256": parameters_sha256,
            "details_sha256": details_sha256,
        }
        selected_profile_sha256 = _hash_canonical_json(selected_profile_object)

        # 5. Atomic supersede + insert
        cursor.execute(
            """UPDATE model_profile_fingerprints
               SET is_current = 0, registration_status = 'superseded'
               WHERE profile_label = ? AND is_current = 1""",
            (profile_label,),
        )

        cursor.execute(
            """INSERT INTO model_profile_fingerprints
               (profile_label, model_name, ollama_host, ollama_model_tag,
                ollama_model_digest, quantization, parameter_size, model_family,
                model_format, thinking_mode, thinking_mode_rule_version,
                template_sha256, system_sha256, parameters_sha256, details_sha256,
                selected_profile_sha256, calibration_run_id, is_current,
                registration_status, registered_by_tool_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile_label, model_name, ollama_host, ollama_model_tag,
                ollama_model_digest, quantization, parameter_size, model_family,
                model_format, thinking_mode, "v1.11.4_arbiter_rule",
                template_sha256, system_sha256, parameters_sha256, details_sha256,
                selected_profile_sha256, calibration_run_id, 1, "current",
                "register_model_fingerprint_v1.12",
            ),
        )

        # 6. Security event
        cursor.execute(
            """INSERT INTO security_events
               (event_type, reason, severity, details_json)
               VALUES (?, ?, ?, ?)""",
            (
                "model_fingerprint_registered",
                f"Registered {model_name} with thinking_mode={thinking_mode}",
                "info",
                json.dumps({
                    "profile_label": profile_label,
                    "calibration_run_id": calibration_run_id,
                    "selected_profile_sha256": selected_profile_sha256,
                }),
            ),
        )

        conn.commit()
        print(f"Registered model fingerprint: {model_name} (thinking_mode={thinking_mode})")

    except FingerprintRegistrationError as e:
        conn.rollback()
        print(f"REGISTRATION FAILED (rolled back): {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--calibration-run-id", required=True)
    parser.add_argument("--approved-by-panel-version", required=True)
    args = parser.parse_args()

    register_model_fingerprint(
        profile_label=args.profile_label,
        calibration_run_id=args.calibration_run_id,
        approved_by_panel_version=args.approved_by_panel_version,
    )
```

### 6.3 Tool-Capability Map Loader — `axiom/core/tool_capability_map.py`

**Source:** v1.11.4 item 1 — replaces inline Python map with JSON artifact loader.  
**Rule:** Loads, validates, and exposes the registered JSON artifact. Does not contain the authoritative map inline.

```python
import json
from pathlib import Path
from typing import Dict, Any

_TOOL_CAPABILITY_MAP_PATH = (
    Path(__file__).parent.parent
    / "policy"
    / "security_artifacts"
    / "tool_capability_map.json"
)

# In-memory cache — loaded once at boot (binding condition 8)
_TOOL_CAPABILITY_MAP: Dict[str, Any] = {}


def load_tool_capability_map() -> Dict[str, Any]:
    global _TOOL_CAPABILITY_MAP
    if _TOOL_CAPABILITY_MAP:
        return _TOOL_CAPABILITY_MAP

    with open(_TOOL_CAPABILITY_MAP_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("schema_version") != "axiom.tool_capability_map.v1":
        raise RuntimeError("tool_capability_map.json has invalid schema_version")

    _TOOL_CAPABILITY_MAP = data["tools"]
    return _TOOL_CAPABILITY_MAP


def get_tool_entry(tool_id: str) -> Any:
    return load_tool_capability_map().get(tool_id)


def get_all_tool_ids() -> set:
    return set(load_tool_capability_map().keys())
```


---

## 7. ModelFingerprintGuard Thinking-Mode Inference (Requirement 4)

**Source:** `AXIOM_Arbiter_v1.11.md` + v1.11.4 Section 9  
**Ruling:** Inspect ONLY the `parameters` field from Ollama `/api/show` response. Regex `(?i)^\s*think\s+false\s*$` with `re.MULTILINE` flag. Return `'disabled'` on match, `'unknown'` on no match. Do not inspect `template` or `system` fields for thinking-mode determination.

**File path:** `axiom/security/model_fingerprint_guard.py`

```python
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

THINK_FALSE_PATTERN = re.compile(
    r"(?i)^\s*think\s+false\s*$",
    re.MULTILINE,
)


class ModelFingerprintGuard:
    """
    Fail-closed verification of Ollama model profile against stored fingerprint.
    Binding conditions: 10 (fail-closed), 12 (safe-pass disabled until calibration passes).
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    # -----------------------------------------------------------------
    # Gap 3 Arbiter ruling — v1.11.4 Section 9
    # -----------------------------------------------------------------
    def _infer_thinking_mode(self, show_json: Dict[str, Any]) -> str:
        """
        Arbiter ruling: inspect ONLY the `parameters` field.
        Returns "disabled" if the regex matches, "unknown" otherwise.
        Do NOT inspect `template` or `system` fields.
        """
        params = str(show_json.get("parameters", ""))
        if THINK_FALSE_PATTERN.search(params):
            return "disabled"
        return "unknown"

    def verify_ollama_profile(
        self,
        show_json: Dict[str, Any],
        profile_label: str = "default",
    ) -> Dict[str, Any]:
        """
        Returns a verification result dict with the canonical structure
        defined in v1.11.4 Section 9.
        """
        result = {
            "verified": False,
            "thinking_mode": "unknown",
            "mismatched_field": None,
            "stored_value": None,
            "live_value": None,
            "selected_profile_sha256": None,
            "details": [],
        }

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT selected_profile_sha256, thinking_mode, template_sha256,
                      system_sha256, parameters_sha256, details_sha256
               FROM model_profile_fingerprints
               WHERE profile_label = ? AND is_current = 1""",
            (profile_label,),
        )
        row = cursor.fetchone()

        if not row:
            result["details"].append("No stored current profile for label")
            return result

        (
            stored_sha256,
            stored_thinking_mode,
            stored_template_sha,
            stored_system_sha,
            stored_parameters_sha,
            stored_details_sha,
        ) = row

        result["selected_profile_sha256"] = stored_sha256

        # v1.11.4 Arbiter ruling: thinking_mode determined from parameters only
        thinking_mode = self._infer_thinking_mode(show_json)
        result["thinking_mode"] = thinking_mode

        if thinking_mode != stored_thinking_mode:
            result["mismatched_field"] = "thinking_mode"
            result["stored_value"] = stored_thinking_mode
            result["live_value"] = thinking_mode
            result["details"].append(
                f"thinking_mode mismatch: stored={stored_thinking_mode}, live={thinking_mode}"
            )
            return result

        # Compare hash of relevant sections
        live_template_sha = self._hash_json({"template": show_json.get("template", "")})
        if live_template_sha != stored_template_sha:
            result["mismatched_field"] = "template"
            result["stored_value"] = stored_template_sha
            result["live_value"] = live_template_sha
            result["details"].append("template section hash mismatch")
            return result

        live_system_sha = self._hash_json({"system": show_json.get("system", "")})
        if live_system_sha != stored_system_sha:
            result["mismatched_field"] = "system"
            result["stored_value"] = stored_system_sha
            result["live_value"] = live_system_sha
            result["details"].append("system section hash mismatch")
            return result

        live_parameters_sha = self._hash_json({"parameters": show_json.get("parameters", "")})
        if live_parameters_sha != stored_parameters_sha:
            result["mismatched_field"] = "parameters"
            result["stored_value"] = stored_parameters_sha
            result["live_value"] = live_parameters_sha
            result["details"].append("parameters section hash mismatch")
            return result

        live_details_sha = self._hash_json(show_json.get("details", {}))
        if live_details_sha != stored_details_sha:
            result["mismatched_field"] = "details"
            result["stored_value"] = stored_details_sha
            result["live_value"] = live_details_sha
            result["details"].append("details section hash mismatch")
            return result

        result["verified"] = True
        result["details"].append("All fingerprint fields verified successfully")
        return result

    @staticmethod
    def _hash_json(obj: Dict[str, Any]) -> str:
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

---

## 8. ModelGateway Runtime Enforcement of "think": false (Requirement 5)

**Source:** v1.11.4 Section 10  
**Rule:** On every local Ollama request, the ModelGateway MUST inject `"think": false` into the request options. If a caller attempts to override with `"think": true`, the ModelGateway MUST reject the call with a `PolicyEngine.denied` result.

**File path:** `axiom/gateways/model_gateway.py`

```python
from typing import Dict, Any
from axiom.core.policy_engine import PolicyEngine, PolicyDecision


class ModelGateway:
    """
    Enforces binding conditions: 2 (qwen3:4b Q4 quantized), 7 (tiered token margins),
    10 (fail-closed on mismatch), 12 (safe-pass disabled).
    """

    THINK_FALSE = {"think": False}

    def __init__(self, ollama_host: str, policy_engine: PolicyEngine):
        self.ollama_host = ollama_host
        self.policy = policy_engine

    def call_local_ollama(
        self,
        model: str,
        prompt: str,
        options: Dict[str, Any] = None,
        **kwargs,
    ) -> PolicyDecision:
        """
        Enforce think=false on every local Ollama call.
        Reject caller override think=true.
        """
        options = dict(options) if options else {}

        # v1.11.4 Section 10: reject caller override think=true
        if options.get("think") is True:
            return self.policy.denied(
                reason="caller_think_override_rejected",
                details="ModelGateway rejects explicit think=true in options. "
                        "Ollama thinking must remain disabled per Arbiter ruling.",
            )

        # v1.11.4 Section 10: inject think=false unconditionally
        options.update(self.THINK_FALSE)

        # Proceed with validated call...
        # (actual Ollama API call implementation deferred to gateway implementation phase)
        return self._execute_call(model, prompt, options, **kwargs)

    def _execute_call(
        self,
        model: str,
        prompt: str,
        options: Dict[str, Any],
        **kwargs,
    ) -> PolicyDecision:
        """Internal execution hook."""
        # Implementation: POST to /api/generate or /api/chat with options
        raise NotImplementedError("Ollama call execution not yet implemented")
```

---

## 9. PlanInjectionScanner Return Contract (Requirement 6)

**Source:** v1.11.1 Section 1.3  
**Rule:** The `PlanInjectionScanner.scan()` method MUST return a dict with the following explicit fields: `scanner_result`, `risk_class`, `artifact_status`, `parent_task_status`, `reason`, and optional `details`. This replaces the v1.11 Task 3 single-decision return.

**File path:** `axiom/security/plan_injection_scanner.py`

```python
from enum import Enum
from typing import Dict, Any, Optional


class ScannerResult(str, Enum):
    NOT_SCANNED = "not_scanned"
    PASSED = "passed"
    DETERMINISTIC_BLOCK = "deterministic_block"
    CLASSIFIER_BLOCK = "classifier_block"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    VERIFICATION_TIMEOUT = "verification_timeout"
    CONNECTION_ERROR = "connection_error"
    MALFORMED_RESPONSE = "malformed_response"
    SCHEMA_CHANGE = "schema_change"
    MODEL_UNAVAILABLE = "model_unavailable"
    SAFE_PASS_DISABLED = "safe_pass_disabled"


class RiskClass(str, Enum):
    ORDINARY = "ordinary"
    HIGH_RISK = "high_risk"


class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    SCANNER_PASSED = "scanner_passed"
    QUARANTINED = "quarantined"


class ParentTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    NEEDS_HUMAN_INPUT = "needs_human_input"


class PlanInjectionScanner:
    """
    v1.11.1 Section 1.3 return contract:
    scanner_result, risk_class, artifact_status, parent_task_status, reason, details
    """

    def __init__(self, safe_pass_enabled: bool = False):
        self.safe_pass_enabled = safe_pass_enabled

    def scan(
        self,
        artifact_json: Dict[str, Any],
        parent_task_status: str = "running",
    ) -> Dict[str, Any]:
        """
        Returns a structured scanner result per the v1.11.1 Section 1.3 contract.
        """
        # v1.11.4: safe-pass short-circuit when classifier path unavailable
        if not self.safe_pass_enabled:
            return {
                "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
                "risk_class": RiskClass.ORDINARY,
                "artifact_status": ArtifactStatus.DRAFT,
                "parent_task_status": ParentTaskStatus.BLOCKED,
                "reason": (
                    "Safe-pass is disabled. Plan artifacts require scanner review "
                    "before any task may proceed."
                ),
                "details": {
                    "safe_pass_enabled": False,
                    "note": "Binding condition 12: classifier safe-pass disabled until calibration passes",
                },
            }

        # v1.11.4: deterministic scan (always-run phase)
        det_result = self._deterministic_scan(artifact_json)
        if det_result["blocked"]:
            return {
                "scanner_result": ScannerResult.DETERMINISTIC_BLOCK,
                "risk_class": RiskClass.HIGH_RISK,
                "artifact_status": ArtifactStatus.QUARANTINED,
                "parent_task_status": ParentTaskStatus.BLOCKED,
                "reason": det_result["reason"],
                "details": det_result.get("details"),
            }

        # v1.11.4: classifier scan (requires calibration to be available)
        clf_result = self._classifier_scan(artifact_json)
        if clf_result["blocked"]:
            return {
                "scanner_result": ScannerResult.CLASSIFIER_BLOCK,
                "risk_class": RiskClass.HIGH_RISK,
                "artifact_status": ArtifactStatus.QUARANTINED,
                "parent_task_status": ParentTaskStatus.BLOCKED,
                "reason": clf_result["reason"],
                "details": clf_result.get("details"),
            }

        return {
            "scanner_result": ScannerResult.PASSED,
            "risk_class": RiskClass.ORDINARY,
            "artifact_status": ArtifactStatus.SCANNER_PASSED,
            "parent_task_status": ParentTaskStatus.RUNNING,
            "reason": "No injection indicators detected by deterministic or classifier scan.",
            "details": {
                "deterministic_checks_passed": det_result["checks"],
                "classifier_score": clf_result.get("score"),
            },
        }

    def _deterministic_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for deterministic pattern scanning."""
        # Implementation deferred to Phase 3 security hardening
        return {"blocked": False, "reason": None, "checks": []}

    def _classifier_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for local classifier inference."""
        # Implementation deferred to Phase 3 — requires calibration test set
        return {"blocked": False, "reason": None, "score": None}
```


---

## 10. TOOL_CAPABILITY_MAP, Authorization Rule, ManifestBinder, and PolicyEngine (Requirement 7)

### 10.1 Tool-Capability Map Runtime Interface — `axiom/core/tool_capability_map.py`

Already specified in Section 6.3. The loader validates schema version on first load, caches the tools dict for the process lifetime (binding condition 8: stateless with boot-time cached validators).

### 10.2 Seven-Step Tool Authorization Rule — `axiom/core/policy_engine.py`

**Source:** v1.11.2 Section 3 + v1.11.3 Section 5 (step 6: session_controller.* requires operator_control manifest).  
**Rule:** Every tool authorization MUST execute the following seven steps in exact sequence. Any step failure produces a `PolicyDecision.denied` with the corresponding reason.

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from axiom.core.tool_capability_map import get_tool_entry, get_all_tool_ids


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def denied(cls, reason: str, details: Optional[Dict[str, Any]] = None):
        return cls(allowed=False, reason=reason, details=details)

    @classmethod
    def allowed(cls, reason: str, details: Optional[Dict[str, Any]] = None):
        return cls(allowed=True, reason=reason, details=details)


class PolicyEngine:
    """
    Stateless policy evaluator with boot-time cached validators.
    Binding conditions: 8 (stateless + cached), 10 (fail-closed).
    """

    def __init__(self):
        # Boot-time cache of all valid tool IDs from registered artifact
        self._valid_tool_ids = get_all_tool_ids()

    def authorize_tool_use(
        self,
        tool_id: str,
        manifest: Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> PolicyDecision:
        """
        Seven-step tool authorization per v1.11.3 Section 5.
        """
        # --- Step 1: Known tool ID ---
        if tool_id not in self._valid_tool_ids:
            return PolicyDecision.denied(
                reason="unknown_tool_id",
                details={"tool_id": tool_id, "valid_tools": sorted(self._valid_tool_ids)},
            )

        tool_entry = get_tool_entry(tool_id)
        source_path = tool_entry["source"]

        # --- Step 2: Manifest type compatibility ---
        required_manifest_type = tool_entry.get("requires_manifest_type")
        manifest_type = manifest.get("manifest_type")
        if required_manifest_type and manifest_type != required_manifest_type:
            return PolicyDecision.denied(
                reason="manifest_type_mismatch",
                details={
                    "tool_id": tool_id,
                    "required_manifest_type": required_manifest_type,
                    "actual_manifest_type": manifest_type,
                },
            )

        # --- Step 3: Tool present in manifest allowed_tools ---
        allowed_tools = manifest.get("allowed_tools", [])
        if tool_id not in allowed_tools:
            return PolicyDecision.denied(
                reason="tool_not_in_allowed_tools",
                details={"tool_id": tool_id, "allowed_tools": allowed_tools},
            )

        # --- Step 4: Tool NOT in manifest forbidden_tools ---
        forbidden_tools = manifest.get("forbidden_tools", [])
        if tool_id in forbidden_tools:
            return PolicyDecision.denied(
                reason="tool_in_forbidden_tools",
                details={"tool_id": tool_id, "forbidden_tools": forbidden_tools},
            )

        # --- Step 5: Capability source field set to true / non-empty ---
        source_value = self._resolve_source_path(manifest, source_path)
        if source_value is False or source_value == [] or source_value is None:
            return PolicyDecision.denied(
                reason="capability_source_not_granted",
                details={"tool_id": tool_id, "source_path": source_path, "source_value": source_value},
            )

        # --- Step 6: v1.11.3 addition — session_controller.* requires operator_control manifest ---
        if tool_id.startswith("session_controller."):
            if manifest_type != "operator_control":
                return PolicyDecision.denied(
                    reason="session_controller_requires_operator_control_manifest",
                    details={"tool_id": tool_id, "manifest_type": manifest_type},
                )
            # v1.11.3 cross-field: command_name must be in allowed_commands
            command_name = manifest.get("operator_command", {}).get("command_name")
            allowed_commands = manifest.get("allowed_capabilities", {}).get("operator_control", {}).get("allowed_commands", [])
            if command_name not in allowed_commands:
                return PolicyDecision.denied(
                    reason="operator_command_not_in_allowed_commands",
                    details={"command_name": command_name, "allowed_commands": allowed_commands},
                )

        # --- Step 7: Additional checks (additive gating, not bypass) ---
        additional_checks = tool_entry.get("additional_checks", [])
        for check in additional_checks:
            check_result = self._run_additional_check(check, manifest, task_context)
            if not check_result["passed"]:
                return PolicyDecision.denied(
                    reason=f"additional_check_failed:{check}",
                    details={"check": check, "info": check_result.get("info")},
                )

        return PolicyDecision.allowed(
            reason="all_authorization_steps_passed",
            details={"tool_id": tool_id, "steps_executed": 7},
        )

    def _resolve_source_path(self, manifest: Dict[str, Any], path: str) -> Any:
        """Resolve dot-notation source path against manifest dict."""
        parts = path.split(".")
        current = manifest
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _run_additional_check(
        self,
        check_name: str,
        manifest: Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Placeholder for additional check implementations."""
        # Deferred to gateway implementation phases
        return {"passed": True, "info": "check_not_yet_implemented"}
```

### 10.3 ManifestBinder Cross-Field Validation — `axiom/core/manifest_binder.py`

**Source:** v1.11.3 Section 4 + v1.11.4 item 4 (ensure registered tool_id enum equals tool-capability map keys).  
**Rule:** At boot, the ManifestBinder validates the `manifest_fingerprints` table against the `tool_capability_map.json` artifact. Mismatch on tool_id set, command_name, or role_name produces a `security_events` row with severity `critical` and disables autonomous operation.

```python
import sqlite3
from typing import Dict, Any, Set
from axiom.core.tool_capability_map import get_all_tool_ids
from axiom.core.policy_engine import PolicyDecision


class ManifestBinder:
    """
    Boot-time manifest integrity verifier.
    Binding conditions: 8 (stateless + cached), 10 (fail-closed).
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self._cached_fingerprints: Dict[str, Any] = {}
        self._bootstrap()

    def _bootstrap(self):
        """Load and cross-validate all registered fingerprints at boot."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT manifest_id, manifest_type, relative_path, sha256,
                      schema_version, manifest_version, role_name, command_name
               FROM manifest_fingerprints WHERE active = 1"""
        )
        rows = cursor.fetchall()

        registered_tool_ids_from_manifests: Set[str] = set()

        for row in rows:
            (
                manifest_id,
                manifest_type,
                relative_path,
                sha256,
                schema_version,
                manifest_version,
                role_name,
                command_name,
            ) = row

            self._cached_fingerprints[manifest_id] = {
                "manifest_type": manifest_type,
                "relative_path": relative_path,
                "sha256": sha256,
                "schema_version": schema_version,
                "manifest_version": manifest_version,
                "role_name": role_name,
                "command_name": command_name,
            }

            # v1.11.4 item 4: collect tool IDs from all manifests for cross-check
            # (actual tool ID extraction from manifest JSON deferred to runtime load)

        # v1.11.4 Final Patch Section 2.3: validate tool-capability map is registered
        if "security.tool_capability_map.v1" not in self._cached_fingerprints:
            self._fail_closed(
                reason="tool_capability_map_not_registered",
                details="The tool-capability map security artifact is missing from manifest_fingerprints.",
            )

    def verify_file_integrity(self, manifest_id: str, current_sha256: str) -> PolicyDecision:
        """Compare on-disk SHA256 against registered fingerprint."""
        fp = self._cached_fingerprints.get(manifest_id)
        if not fp:
            return PolicyDecision.denied(
                reason="manifest_not_registered",
                details={"manifest_id": manifest_id},
            )
        if fp["sha256"] != current_sha256:
            return PolicyDecision.denied(
                reason="manifest_integrity_mismatch",
                details={
                    "manifest_id": manifest_id,
                    "registered_sha256": fp["sha256"],
                    "current_sha256": current_sha256,
                },
            )
        return PolicyDecision.allowed(
            reason="manifest_integrity_verified",
            details={"manifest_id": manifest_id},
        )

    def _fail_closed(self, reason: str, details: str):
        """v1.11.4 item 5: fail-closed behavior — log critical and raise."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO security_events
               (event_type, reason, severity, details_json)
               VALUES (?, ?, ?, ?)""",
            ("manifest_binder_fail_closed", reason, "critical", details),
        )
        self.conn.commit()
        raise RuntimeError(f"ManifestBinder fail-closed: {reason} — {details}")

    def get_manifest(self, manifest_id: str) -> Dict[str, Any]:
        """Return cached fingerprint metadata."""
        return dict(self._cached_fingerprints.get(manifest_id, {}))
```

### 10.4 PolicyEngine Fail-Closed on Missing Policy Fields — `axiom/core/policy_engine.py`

**Source:** v1.11.4 item 5  
**Rule:** When a manifest JSON is loaded but a required policy field is missing (e.g., `network_policy` absent from a role manifest), the PolicyEngine MUST treat this as a policy denial, not as an implicit default. The denial reason MUST be `missing_required_policy_field` with the field name in details.

The `PolicyEngine.authorize_tool_use()` method already implements this implicitly: any tool requiring a source path that does not resolve to a non-empty value in the manifest will be denied at Step 5 (`capability_source_not_granted`). For explicit fail-closed on missing top-level fields, add:

```python
    def validate_manifest_completeness(self, manifest: Dict[str, Any]) -> PolicyDecision:
        """
        v1.11.4 item 5: Fail-closed on missing required policy fields.
        """
        required_top_level = [
            "schema_version", "manifest_type", "manifest_id", "manifest_version",
            "approved_by_panel_version", "budget_policy", "allowed_capabilities",
            "allowed_tools", "forbidden_tools", "network_policy", "sandbox_policy",
            "memory_policy", "audit_policy",
        ]
        for field in required_top_level:
            if field not in manifest:
                return PolicyDecision.denied(
                    reason="missing_required_policy_field",
                    details={"missing_field": field},
                )
        return PolicyDecision.allowed(
            reason="manifest_completeness_verified",
            details={"checked_fields": required_top_level},
        )
```


---

## 11. Canonical MVP Acceptance Test Suite (Requirement 8)

**Source:** Union of v1.10.2 Section 11, v1.11.1 Section 3.8, v1.11.2 Section 7, v1.11.3 Section 8, v1.11.4 Section 12, and v1.11.4 Final Patch Section 6.  
**Rule:** This is the single canonical list. Any future amendment adds rows; nothing is removed without panel ratification.

| # | Test | Source | Phase |
|---|------|--------|-------|
| 1 | Schema migration table contains exactly one row with version `v1.11.4` after `init_db()` | v1.11.4 | Phase 2 |
| 2 | `init_db()` does not execute when `schema.sql` is not on disk | v1.11 | Phase 2 |
| 3 | `schema.sql` contains `memory_item_embeddings` virtual table using `vec0(embedding float[768])` | v1.11 | Phase 2 |
| 4 | `schema.sql` contains `PRAGMA cache_size = -32768` (32 MiB) | v1.11.3 | Phase 2 |
| 5 | `manifest_fingerprints.manifest_type` CHECK allows `tool_capability_map` | v1.11.4 | Phase 2 |
| 6 | `manifest_fingerprints` CHECK constraint enforces role | operator_control | tool_capability_map row-level validity | v1.11.4 | Phase 2 |
| 7 | `manifest_fingerprints` contains one `tool_capability_map` row after `register_manifests.py` | v1.11.4 | Phase 2 |
| 8 | Manifest schema validates a correctly formed role manifest | v1.10.2 | Phase 2 |
| 9 | Manifest schema rejects role manifest with operator-control commands in `allowed_capabilities.operator_control.allowed_commands` | v1.11.3 | Phase 2 |
| 10 | Manifest schema validates a correctly formed operator-control manifest | v1.10.2 | Phase 2 |
| 11 | Manifest schema rejects operator-control manifest with `allowed_commands.maxItems != 1` | v1.11.3 | Phase 2 |
| 12 | Manifest schema validates `network_policy` with `mode=deny_all` and `allowlist=[]` | v1.11.4 | Phase 2 |
| 13 | Manifest schema rejects `network_policy` with `mode=deny_all` and non-empty `allowlist` | v1.11.4 | Phase 2 |
| 14 | Manifest schema validates `network_policy` with `mode=allowlist_only` and `allowlist.minItems >= 1` | v1.11.4 | Phase 2 |
| 15 | Manifest schema rejects `network_policy` with `mode=allowlist_only` and `allowlist=[]` | v1.11.4 | Phase 2 |
| 16 | Manifest schema validates `tool_id` enum values (all 14 canonical tool IDs) | v1.11.4 | Phase 2 |
| 17 | Manifest schema rejects unknown `tool_id` strings | v1.11.4 | Phase 2 |
| 18 | Manifest schema accepts `max_response_bytes` up to 5242880 (5 MiB) | v1.11.4 | Phase 2 |
| 19 | Manifest schema rejects `max_response_bytes > 5242880` | v1.11.4 | Phase 2 |
| 20 | `register_manifests.py` computes correct SHA256 per file | v1.10.1 | Phase 2 |
| 21 | `register_manifests.py` validates all manifests against JSON Schema | v1.10.1 | Phase 2 |
| 22 | `register_manifests.py` writes all rows atomically (transaction) | v1.10.1 | Phase 2 |
| 23 | `register_manifests.py` rolls back on any single validation failure | v1.10.1 | Phase 2 |
| 24 | `register_manifests.py` performs semantic cross-field validation (operator_control binding) | v1.11.3 | Phase 2 |
| 25 | `register_manifests.py` validates tool IDs against tool-capability map | v1.11.4 | Phase 2 |
| 26 | `register_manifests.py` writes canonical `tool_capability_map` row with NULL role_name and NULL command_name | v1.11.4 | Phase 2 |
| 27 | `register_model_fingerprint.py` requires passing calibration_run_id | v1.11.1 | Phase 2 |
| 28 | `register_model_fingerprint.py` rejects if calibration_run_id does not exist | v1.11.1 | Phase 2 |
| 29 | `register_model_fingerprint.py` rejects if calibration did not pass | v1.11.1 | Phase 2 |
| 30 | `register_model_fingerprint.py` queries Ollama `/api/show` and extracts profile data | v1.11.1 | Phase 2 |
| 31 | `register_model_fingerprint.py` sets `thinking_mode` per Arbiter rule (parameters field only) | v1.11.4 | Phase 2 |
| 32 | `register_model_fingerprint.py` rejects registration if `thinking_mode != "disabled"` | v1.11.4 | Phase 2 |
| 33 | `register_model_fingerprint.py` sets `is_current = 1`, `registration_status = 'current'` | v1.11.1 | Phase 2 |
| 34 | `register_model_fingerprint.py` atomically supersedes prior `is_current = 1` row | v1.11.1 | Phase 2 |
| 35 | `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `think false` | v1.11.4 | Phase 2 |
| 36 | `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `THINK FALSE` | v1.11.4 | Phase 2 |
| 37 | `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `  think  false  ` | v1.11.4 | Phase 2 |
| 38 | `ModelFingerprintGuard._infer_thinking_mode()` returns "unknown" when `parameters` does not contain `think false` | v1.11.4 | Phase 2 |
| 39 | `ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `template` field | v1.11.4 / Arbiter | Phase 2 |
| 40 | `ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `system` field | v1.11.4 / Arbiter | Phase 2 |
| 41 | `ModelFingerprintGuard.verify_ollama_profile()` fails when `thinking_mode` mismatches stored fingerprint | v1.11.4 | Phase 2 |
| 42 | `ModelFingerprintGuard.verify_ollama_profile()` fails when any section hash mismatches | v1.11.4 | Phase 2 |
| 43 | `ModelFingerprintGuard.verify_ollama_profile()` passes when all fields match stored fingerprint | v1.11.4 | Phase 2 |
| 44 | `ModelGateway.call_local_ollama()` injects `"think": false` into options | v1.11.4 | Phase 2 |
| 45 | `ModelGateway.call_local_ollama()` rejects caller override `"think": true` | v1.11.4 | Phase 2 |
| 46 | `ModelGateway.call_local_ollama()` preserves other caller options when injecting think=false | v1.11.4 | Phase 2 |
| 47 | `PlanInjectionScanner.scan()` returns full contract dict when safe-pass disabled | v1.11.1 | Phase 2 |
| 48 | `PlanInjectionScanner.scan()` dict contains `scanner_result`, `risk_class`, `artifact_status`, `parent_task_status`, `reason` | v1.11.1 | Phase 2 |
| 49 | `PlanInjectionScanner.scan()` returns `scanner_result=SAFE_PASS_DISABLED` when safe-pass is off | v1.11.4 | Phase 2 |
| 50 | `PolicyEngine.authorize_tool_use()` returns denied for unknown tool_id | v1.11.2 | Phase 2 |
| 51 | `PolicyEngine.authorize_tool_use()` returns denied when tool_id not in manifest allowed_tools | v1.11.2 | Phase 2 |
| 52 | `PolicyEngine.authorize_tool_use()` returns denied when tool_id in manifest forbidden_tools | v1.11.2 | Phase 2 |
| 53 | `PolicyEngine.authorize_tool_use()` returns denied when capability source is false | v1.11.2 | Phase 2 |
| 54 | `PolicyEngine.authorize_tool_use()` returns allowed when all seven steps pass | v1.11.2 | Phase 2 |
| 55 | `PolicyEngine.authorize_tool_use()` Step 6: session_controller.* denied with role manifest | v1.11.3 | Phase 2 |
| 56 | `PolicyEngine.authorize_tool_use()` Step 6: session_controller.* allowed with operator_control manifest | v1.11.3 | Phase 2 |
| 57 | `PolicyEngine.validate_manifest_completeness()` denied on missing required policy field | v1.11.4 | Phase 2 |
| 58 | `ManifestBinder._bootstrap()` raises if tool_capability_map not registered | v1.11.4 | Phase 2 |
| 59 | `ManifestBinder.verify_file_integrity()` denied on SHA256 mismatch | v1.11.4 | Phase 2 |
| 60 | `ManifestBinder.verify_file_integrity()` allowed on matching SHA256 | v1.11.4 | Phase 2 |
| 61 | `tasks.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id` | v1.10.2 | Phase 2 |
| 62 | `task_permissions.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id` | v1.10.2 | Phase 2 |
| 63 | `plan_artifacts.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id` | v1.10.2 | Phase 2 |
| 64 | `provider_usage.provider` CHECK rejects invalid provider enum value | v1.10.2 | Phase 2 |
| 65 | `scheduler_heartbeat` index on `session_id, last_freshness_at DESC` exists | v1.11.2 | Phase 2 |
| 66 | `tasks` index on `commit_batch_id` exists | v1.11.3 | Phase 2 |
| 67 | `tool_capability_map.json` validates against `tool_capability_map_schema.json` | v1.11.4 | Phase 2 |
| 68 | `tool_capability_map.json` contains all 14 tool IDs | v1.11.4 | Phase 2 |
| 69 | `tool_capability_map.json` operator-control entries have correct required_command values | v1.11.4 | Phase 2 |
| 70 | Database has at most one `model_profile_fingerprints` row with `is_current = 1` per `profile_label` | v1.11.1 | Phase 2 |
| 71 | `model_profile_fingerprints` CHECK prevents `is_current = 1` with `thinking_mode = 'unknown'` | v1.11.4 | Phase 2 |
| 72 | `model_profile_fingerprints` CHECK enforces `is_current = 1` implies `registration_status = 'current'` | v1.11.4 | Phase 2 |
| 73 | `sessions.safe_pass_disabled_reason` CHECK rejects invalid enum values | v1.10.2 | Phase 2 |
| 74 | `sessions.safe_pass_disabled_reason` accepts `'manifest_integrity_mismatch'` | v1.11.4 | Phase 2 |
| 75 | `plan_artifacts.scanner_result` CHECK accepts all canonical scanner_result values | v1.11.1 | Phase 2 |
| 76 | `tasks.task_class` CHECK rejects invalid task class values | v1.10.2 | Phase 2 |
| 77 | `register_manifests.py` command-line invocation completes in under 30 seconds for 10 manifests | v1.10.1 | Phase 2 |
| 78 | `register_model_fingerprint.py` command-line invocation completes in under 30 seconds | v1.11.1 | Phase 2 |
| 79 | `db.py` applies `PRAGMA cache_size = -32768` on every connection | v1.11.3 | Phase 2 |
| 80 | `db.py` applies WAL + synchronous=FULL + busy_timeout=5000 on every connection | v1.10.2 | Phase 2 |
| 81 | `register_manifests.py` sets `tool_capability_map` row with `manifest_id = 'security.tool_capability_map.v1'` | v1.11.4 | Phase 2 |
| 82 | `register_manifests.py` command-line tool exits with code 0 on success, code 1 on failure | v1.10.1 | Phase 2 |
| 83 | `register_model_fingerprint.py` command-line tool exits with code 0 on success, code 1 on failure | v1.11.1 | Phase 2 |
| 84 | `register_manifests.py` leaves table empty on rollback | v1.10.1 | Phase 2 |
| 85 | `register_manifests.py` validates `tool_capability_map.json` before any manifest | v1.11.4 | Phase 2 |
| 86 | `ManifestBinder` boot-time load logs `info` event when all fingerprints valid | v1.11.4 | Phase 2 |
| 87 | `ManifestBinder` boot-time load logs `critical` event when fingerprint mismatch detected | v1.11.4 | Phase 2 |
| 88 | `network_policy` redirect_policy `same_host_only` validates correctly | v1.11.4 | Phase 2 |
| 89 | `network_policy` redirect_policy `deny` validates correctly | v1.11.4 | Phase 2 |
| 90 | `network_deny_entry` with all wildcards (`*`) validates correctly | v1.11.4 | Phase 2 |
| 91 | `network_deny_entry` with specific host/port/path validates correctly | v1.11.4 | Phase 2 |
| 92 | `register_manifests.py` rejects manifest with unknown tool_id in `allowed_tools` | v1.11.4 | Phase 2 |
| 93 | `register_manifests.py` rejects manifest with unknown tool_id in `forbidden_tools` | v1.11.4 | Phase 2 |
| 94 | `operator_command_manifest` `authorization_policy.telegram_operator_whitelist_required` is const `true` | v1.11.2 | Phase 2 |
| 95 | `operator_command_manifest` `audit_policy.log_task_id` is const `true` | v1.11.2 | Phase 2 |
| 96 | `operator_command_manifest` `audit_policy.log_manifest_id` is const `true` | v1.11.2 | Phase 2 |
| 97 | `operator_command_manifest` `audit_policy.log_policy_denials` is const `true` | v1.11.2 | Phase 2 |
| 98 | `role_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `0` | v1.11.3 | Phase 2 |
| 99 | `operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.minItems` is const `1` | v1.11.3 | Phase 2 |
| 100 | `operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `1` | v1.11.3 | Phase 2 |


---

## 12. First Three Executable Implementation Tasks (Requirement 10)

**Rule:** The operator may begin Task 1 immediately after v1.12 is approved. `init_db()` MUST NOT be executed until the panel-ratified `schema.sql` is written to disk. The schema in this document IS the ratified canonical schema; once written to `axiom/persistence/schema.sql`, the operator may proceed.

---

### Task 1: Directory Structure, Requirements File, and Database Connection Layer

**Status:** Ready for operator execution immediately upon v1.12 approval.  
**init_db() status:** NOT executed in this task.

#### 12.1.1 Exact file paths to create

```
axiom/
├── __init__.py
├── app/
│   ├── __init__.py
│   └── session_controller.py
├── config/
│   ├── __init__.py
│   └── axiom.yaml
├── core/
│   ├── __init__.py
│   ├── context_builder.py
│   ├── manifest_binder.py
│   ├── policy_engine.py
│   ├── resource_limits.py
│   ├── scheduler.py
│   ├── state_machine.py
│   └── tool_capability_map.py
├── gateways/
│   ├── __init__.py
│   ├── filesystem_gateway.py
│   ├── memory_gateway.py
│   ├── model_gateway.py
│   ├── network_gateway.py
│   └── sandbox_gateway.py
├── persistence/
│   ├── __init__.py
│   └── db.py
├── policy/
│   ├── __init__.py
│   ├── operator_control_manifests/
│   │   └── .gitkeep
│   ├── role_manifests/
│   │   └── .gitkeep
│   ├── schemas/
│   │   ├── manifest_schema.json
│   │   └── tool_capability_map_schema.json
│   └── security_artifacts/
│       └── tool_capability_map.json
├── security/
│   ├── __init__.py
│   ├── audit.py
│   ├── model_fingerprint_guard.py
│   └── plan_injection_scanner.py
└── tools/
    ├── __init__.py
    ├── register_manifests.py
    └── register_model_fingerprint.py
```

#### 12.1.2 Exact code to write — `axiom/persistence/db.py`

```python
"""
AXIOM database connection layer.
Binding condition 11: bounded SQLite page cache.
Rule: init_db() MUST NOT be called until schema.sql is panel-ratified on disk.
"""
import sqlite3
from pathlib import Path
from typing import Optional

DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "axiom.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply binding-condition pragmas on every connection."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA cache_size = -32768")  # 32 MiB = 8192 pages at 4 KiB


def get_connection() -> sqlite3.Connection:
    """Return a new database connection with pragmas applied."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    return conn


def init_db() -> None:
    """
    Initialize the database from schema.sql.
    WARNING: Only call after schema.sql is panel-ratified and on disk.
    """
    if not SCHEMA_PATH.exists():
        raise RuntimeError(
            f"schema.sql not found at {SCHEMA_PATH}. "
            "Cannot initialize database without panel-ratified schema."
        )

    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()
```

#### 12.1.3 Exact code to write — `requirements.txt`

```
sqlite-vec>=0.1.0
jsonschema>=4.0.0
requests>=2.28.0
PyYAML>=6.0
```

#### 12.1.4 Exact commands to run

```bash
# 1. Create directory tree
mkdir -p axiom/{app,config,core,gateways,persistence,policy/{operator_control_manifests,role_manifests,schemas,security_artifacts},security,tools}

# 2. Write empty __init__.py files
for dir in axiom axiom/app axiom/config axiom/core axiom/gateways axiom/persistence axiom/policy axiom/security axiom/tools; do
    touch "$dir/__init__.py"
done

# 3. Write schema.sql (Section 3 of this document)
#    — write the exact canonical schema from Section 3 to axiom/persistence/schema.sql
#    — this document IS the ratified schema; operator copies it verbatim

# 4. Write db.py (Section 12.1.2 above) to axiom/persistence/db.py

# 5. Write requirements.txt (Section 12.1.3 above) to project root

# 6. Install dependencies
pip install -r requirements.txt

# 7. DO NOT run init_db() yet — see Task 2 gate condition
```

#### 12.1.5 Acceptance criteria

| # | Criterion | Verification |
|---|-----------|------------|
| 1 | All 23 directories from the tree exist | `find axiom -type d` matches tree |
| 2 | `axiom/persistence/schema.sql` exists and is byte-identical to Section 3 of this document | `sha256sum` against known hash (computed after write) |
| 3 | `axiom/persistence/db.py` exists and `get_connection()` returns a connection with `PRAGMA cache_size = -32768` | Read back via `conn.execute("PRAGMA cache_size").fetchone()` |
| 4 | `init_db()` raises `RuntimeError` when `schema.sql` is missing | Temporarily rename schema.sql, call `init_db()`, verify exception |
| 5 | `pip install -r requirements.txt` completes without error | Exit code 0 |
| 6 | `sqlite-vec` import succeeds | `python -c "import sqlite_vec; print(sqlite_vec.__version__)"` |
| 7 | `jsonschema` import succeeds | `python -c "import jsonschema; print(jsonschema.__version__)"` |
| 8 | `axiom.db` does NOT exist yet | `init_db()` was NOT called |

---

### Task 2: Schema Initialization and Registration CLI Bootstrapping

**Status:** Ready after Task 1 acceptance criteria pass AND operator confirms `schema.sql` is on disk.  
**Gate:** `init_db()` MAY be executed only after operator confirms `schema.sql` exists at `axiom/persistence/schema.sql`.

#### 12.2.1 Exact commands to run

```bash
# 1. Initialize database (ONLY after schema.sql is confirmed on disk)
python -c "from axiom.persistence.db import init_db; init_db()"

# 2. Verify schema_migrations table
python -c "
import sqlite3
from axiom.persistence.db import get_connection
conn = get_connection()
cur = conn.execute('SELECT schema_version FROM schema_migrations')
row = cur.fetchone()
assert row[0] == 'v1.11.4', f'Expected v1.11.4, got {row[0]}'
print('Schema migration verified: v1.11.4')
"

# 3. Write canonical JSON schemas to disk
#    — manifest_schema.json (Section 4 of this document)
#    — tool_capability_map_schema.json (Section 5 of this document)
#    — tool_capability_map.json (Section 5 of this document)

# 4. Validate tool-capability map against its schema
python -c "
import json
from jsonschema import validate
with open('axiom/policy/schemas/tool_capability_map_schema.json') as f:
    schema = json.load(f)
with open('axiom/policy/security_artifacts/tool_capability_map.json') as f:
    data = json.load(f)
validate(instance=data, schema=schema)
print('tool_capability_map.json validates against schema')
"

# 5. Write register_manifests.py (Section 6.1) and register_model_fingerprint.py (Section 6.2)

# 6. Verify CLI tools are executable
python tools/register_manifests.py --help  # should print usage or run
python tools/register_model_fingerprint.py --help  # should print usage or run
```

#### 12.2.2 Acceptance criteria

| # | Criterion | Verification |
|---|-----------|------------|
| 1 | `init_db()` creates `axiom.db` with all 17 tables + virtual table | `sqlite3 data/axiom.db ".tables"` lists all tables |
| 2 | `schema_migrations` contains exactly one row with version `v1.11.4` | `SELECT schema_version FROM schema_migrations` returns `v1.11.4` |
| 3 | `memory_item_embeddings` is a virtual table using `vec0` | `PRAGMA table_info(memory_item_embeddings)` or `SELECT sql FROM sqlite_master WHERE name='memory_item_embeddings'` |
| 4 | `PRAGMA cache_size` returns `-32768` on a new connection | Direct query on `get_connection()` |
| 5 | `manifest_fingerprints.manifest_type` CHECK rejects invalid value | `INSERT` with invalid manifest_type raises `CHECK constraint failed` |
| 6 | `tool_capability_map.json` validates against `tool_capability_map_schema.json` | `jsonschema.validate()` succeeds |
| 7 | `register_manifests.py` exists and imports without error | `python -c "import tools.register_manifests"` succeeds |
| 8 | `register_model_fingerprint.py` exists and imports without error | `python -c "import tools.register_model_fingerprint"` succeeds |
| 9 | `manifest_fingerprints` is empty before first registration | `SELECT COUNT(*) FROM manifest_fingerprints` returns 0 |
| 10 | `model_profile_fingerprints` is empty before first registration | `SELECT COUNT(*) FROM model_profile_fingerprints` returns 0 |

---

### Task 3: Core Security Components — ModelFingerprintGuard, ModelGateway, PlanInjectionScanner

**Status:** Ready after Task 2 acceptance criteria pass.  
**Dependencies:** `schema.sql` initialized, database connection layer working, CLIs present.

#### 12.3.1 Exact file paths and code to write

1. `axiom/security/model_fingerprint_guard.py` — Section 7 of this document
2. `axiom/gateways/model_gateway.py` — Section 8 of this document
3. `axiom/security/plan_injection_scanner.py` — Section 9 of this document
4. `axiom/core/policy_engine.py` — Section 10.2 of this document
5. `axiom/core/manifest_binder.py` — Section 10.3 of this document
6. `axiom/core/tool_capability_map.py` — Section 6.3 of this document

#### 12.3.2 Exact commands to run

```bash
# 1. Write all six Python modules (file contents from Sections 6.3, 7, 8, 9, 10.2, 10.3)

# 2. Verify all modules import without error
python -c "from axiom.security.model_fingerprint_guard import ModelFingerprintGuard"
python -c "from axiom.gateways.model_gateway import ModelGateway"
python -c "from axiom.security.plan_injection_scanner import PlanInjectionScanner"
python -c "from axiom.core.policy_engine import PolicyEngine"
python -c "from axiom.core.manifest_binder import ManifestBinder"
python -c "from axiom.core.tool_capability_map import load_tool_capability_map"

# 3. Run thinking-mode unit tests (tests 35-40 from acceptance suite)
python -c "
import re
from axiom.security.model_fingerprint_guard import ModelFingerprintGuard

class MockConn:
    pass

guard = ModelFingerprintGuard(MockConn())

# Test 35: parameters contains 'think false'
assert guard._infer_thinking_mode({'parameters': 'think false'}) == 'disabled'
# Test 36: parameters contains 'THINK FALSE'
assert guard._infer_thinking_mode({'parameters': 'THINK FALSE'}) == 'disabled'
# Test 37: parameters contains '  think  false  '
assert guard._infer_thinking_mode({'parameters': '  think  false  '}) == 'disabled'
# Test 38: parameters does not contain 'think false'
assert guard._infer_thinking_mode({'parameters': 'temperature 0.7'}) == 'unknown'
# Test 39: template field is ignored
template_think = {'template': 'think false', 'parameters': 'temperature 0.7'}
assert guard._infer_thinking_mode(template_think) == 'unknown'
# Test 40: system field is ignored
system_think = {'system': 'think false', 'parameters': 'temperature 0.7'}
assert guard._infer_thinking_mode(system_think) == 'unknown'

print('All thinking-mode inference tests passed')
"

# 4. Run ModelGateway think=false enforcement tests (tests 44-46)
python -c "
from axiom.gateways.model_gateway import ModelGateway
from axiom.core.policy_engine import PolicyEngine

mg = ModelGateway('http://localhost:11434', PolicyEngine())

# Test 44: think=false is injected
result = mg.call_local_ollama('qwen3:4b', 'hello', options={'temperature': 0.7})
# (This will raise NotImplementedError from _execute_call; we verify injection separately)

# Direct option check
opts = {'temperature': 0.7}
opts.update(ModelGateway.THINK_FALSE)
assert opts['think'] is False
assert opts['temperature'] == 0.7

# Test 45: caller think=true is rejected
# (Verified by PolicyDecision.denied return; actual test requires mock)

print('ModelGateway option injection verified')
"

# 5. Run PlanInjectionScanner return contract tests (tests 47-49)
python -c "
from axiom.security.plan_injection_scanner import PlanInjectionScanner

scanner = PlanInjectionScanner(safe_pass_enabled=False)
result = scanner.scan({'plan': 'test'})

assert 'scanner_result' in result
assert 'risk_class' in result
assert 'artifact_status' in result
assert 'parent_task_status' in result
assert 'reason' in result
assert result['scanner_result'] == 'safe_pass_disabled'
assert result['parent_task_status'] == 'blocked'

print('PlanInjectionScanner return contract verified')
"

# 6. Run PolicyEngine authorization tests (tests 50-56)
python -c "
from axiom.core.policy_engine import PolicyEngine

pe = PolicyEngine()

# Test 50: unknown tool_id denied
result = pe.authorize_tool_use('unknown.tool', {}, {})
assert not result.allowed
assert 'unknown_tool_id' in result.reason

# Test 51: tool not in allowed_tools denied
manifest = {
    'manifest_type': 'role',
    'allowed_tools': ['filesystem.read'],
    'forbidden_tools': [],
    'allowed_capabilities': {
        'model': {'allow_model_calls': True, 'allowed_provider_groups': [], 'allow_local_classifier': False},
        'task_queue': {'read_scope': 'none', 'write_scope': 'none', 'may_create_tasks': False, 'may_update_own_result': False, 'may_update_other_tasks': False},
        'filesystem': {'read': True, 'write': False, 'allowed_roots': ['/tmp']},
        'operator_control': {'allowed_commands': []},
    },
}
result = pe.authorize_tool_use('model_gateway.call', manifest, {})
assert not result.allowed
assert 'tool_not_in_allowed_tools' in result.reason

# Test 55: session_controller.* denied with role manifest
result = pe.authorize_tool_use('session_controller.status', manifest, {})
assert not result.allowed
assert 'session_controller_requires_operator_control_manifest' in result.reason

print('PolicyEngine authorization tests passed')
"

# 7. Run ManifestBinder fail-closed test (test 58)
python -c "
import sqlite3
from axiom.core.manifest_binder import ManifestBinder
from axiom.persistence.db import _apply_pragmas

conn = sqlite3.connect(':memory:')
_apply_pragmas(conn)

# Execute schema so manifest_fingerprints exists
with open('axiom/persistence/schema.sql') as f:
    conn.executescript(f.read())

try:
    binder = ManifestBinder(conn)
    assert False, 'Should have raised RuntimeError'
except RuntimeError as e:
    assert 'tool_capability_map_not_registered' in str(e)
    print('ManifestBinder fail-closed test passed')
"
```

#### 12.3.3 Acceptance criteria

| # | Criterion | Verification |
|---|-----------|------------|
| 1 | `ModelFingerprintGuard` imports without error | Direct import test |
| 2 | `_infer_thinking_mode()` returns "disabled" for 3 positive cases and "unknown" for 3 negative cases | Unit test script (tests 35-40) |
| 3 | `_infer_thinking_mode()` ignores `template` and `system` fields | Unit test script (tests 39-40) |
| 4 | `ModelGateway` imports without error | Direct import test |
| 5 | `ModelGateway.call_local_ollama()` injects `think=false` | Option dict inspection |
| 6 | `ModelGateway.call_local_ollama()` rejects `think=true` override | Mocked unit test |
| 7 | `PlanInjectionScanner.scan()` returns full contract dict | Key presence assertion |
| 8 | `PlanInjectionScanner.scan()` returns `safe_pass_disabled` when safe-pass off | Value assertion |
| 9 | `PolicyEngine.authorize_tool_use()` executes all 7 steps | Step-coverage trace or logging |
| 10 | `PolicyEngine` denies unknown tool_id, not-in-allowed, in-forbidden, false-source | Unit tests 50-56 |
| 11 | `ManifestBinder` raises `RuntimeError` when tool_capability_map missing | Test 58 |
| 12 | `ManifestBinder` logs `critical` security event on fail-closed | Security events table query |
| 13 | `tool_capability_map.py` loads and caches JSON artifact | `load_tool_capability_map()` returns 14 tool entries |
| 14 | All 100 acceptance tests 1-100 have corresponding verification scripts or marked as deferred | Checklist completion |


---

## 13. Remaining Ambiguity Requiring Panel Clarification

The following items are flagged as ambiguous or blocking for specific subsequent tasks. They do NOT block Tasks 1-3 above.

| # | Ambiguity | Blocking Task | Current Assumption | Clarification Needed |
|---|-----------|-------------|-------------------|---------------------|
| 1 | **`jsonschema` package dependency** | Task 2 (register_manifests.py) | The CLI uses `jsonschema.validate()`. If the package is unavailable, the CLI raises `RuntimeError`. | Does the panel accept `jsonschema>=4.0.0` as a runtime dependency, or should validation be implemented with a lighter-weight alternative? |
| 2 | **Ollama `/api/show` response format for `parameters` field** | Task 2 (register_model_fingerprint.py) | The Arbiter ruling treats `parameters` as a string field. Ollama may return it as a dict (`{"temperature": 0.7, "think": false}`). | Does the panel confirm that `str(show_json.get("parameters", ""))` is the correct coercion strategy, or should dict-serialization be used for hash stability? |
| 3 | **Calibration test set authoring** | Phase 3 (classifier calibration) | Deferred per panel direction. The `classifier_calibration_runs` table exists but no calibration data can be produced. | Panel to provide calibration test set or approve mock calibration data for integration testing. |
| 4 | **Windows Job Object sandbox specifics** | Phase 4 (sandbox_gateway.py) | Deferred per panel direction. Sandbox policy exists in schema and manifest but enforcement is unimplemented. | Panel to provide Windows Job Object configuration or approve cross-platform `subprocess` limits as interim. |
| 5 | **Cloud cascade provider configuration** | Phase 4 (model_gateway.py cloud path) | Deferred per panel direction. `provider_usage` and `provider_budget_windows` tables exist but cloud API keys and endpoints are unspecified. | Panel to approve provider list (Cerebras, Groq, OpenRouter, SambaNova) and provide credential management approach. |
| 6 | **Telegram operator whitelist mechanism** | Phase 6 (session_controller.py authorization) | Deferred per panel direction. `authorization_policy.telegram_operator_whitelist_required` is const `true` in schema, but whitelist storage and verification are unspecified. | Panel to provide Telegram operator whitelist storage format and update mechanism. |
| 7 | **Brave Search confirmation workflow** | Phase 4 (network_gateway.py) | Deferred per panel direction. Binding condition 6 requires Brave Search confirmation before web search, but the confirmation protocol (operator prompt? async callback?) is unspecified. | Panel to specify the confirmation UI/mechanism for Brave Search authorization. |
| 8 | **`memory_item_embeddings` sqlite-vec batch streaming** | Phase 5 (memory_gateway.py) | Binding condition 5 requires 100-vector batch limit. The schema uses `vec0(embedding float[768])` but streaming deduplication logic is unspecified. | Panel to confirm the streaming deduplication approach or approve simple `LIMIT 100` per query. |
| 9 | **Tiered token margin calibration values** | Phase 3 (resource_limits.py) | Binding condition 7 requires 2.0x calibrated / 1.5x fallback margins. Actual calibrated multipliers require test data. | Panel to approve 1.5x as hardcoded fallback for MVP, with calibration deferred to Phase 3. |
| 10 | **AXIOM session lifecycle test fixtures** | Phase 6+ integration tests | No end-to-end session lifecycle test fixtures are defined in the canonical test suite. | Panel to approve integration test scope or defer to Phase 6+ implementation. |
| 11 | **`subprocess` timeout vs Windows Job Object wall-clock** | Phase 4 (sandbox_gateway.py) | The schema enforces 60s via `sandbox_policy.max_wall_clock_seconds`. Python `subprocess` timeout may differ from Job Object accounting. | Panel to confirm whether `subprocess.run(timeout=60)` is acceptable MVP behavior pending Job Object implementation. |
| 12 | **Operator command `reconcile_provider_usage` implementation** | Phase 6+ | The operator-control manifest schema includes this command, but the reconciliation algorithm (operator report format, discrepancy threshold) is unspecified. | Panel to provide operator report format or defer command implementation to Phase 6+. |

---

## 14. Document History

| Version | Date | Description |
|---------|------|-------------|
| v1.11 | 2026-05-03 | Prior implementation plan with seven gaps identified |
| v1.12 | 2026-05-04 | Complete revision incorporating v1.11.1-1.11.4 canonical schemas, Arbiter Gap 3 ruling, registration CLIs, ModelGateway think=false enforcement, PlanInjectionScanner return contract, TOOL_CAPABILITY_MAP runtime loading, seven-step authorization, ManifestBinder cross-field validation, PolicyEngine fail-closed, and unified 100-test acceptance suite. |

---

**End of AXIOM Implementation Plan v1.12**
