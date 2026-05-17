AXIOM Proposal v1.11.1 — Canonical Schema, Manifest Schema, and Model Fingerprint Registration

Status

Proposal type: Spec completion
Scope: Gap 1, Gap 2, and initial calibrated model fingerprint registration
Architecture spine changed: No
Gap 3 included: No — thinking-mode inference remains routed to Gemini as Arbiter

This proposal responds to the Evaluator’s return of Kimi’s v1.11 plan. The Evaluator correctly identified that implementation must not proceed against inferred schema or inferred manifest structure, and that the missing initial fingerprint registration path creates a circular failure where verify_current_profile() can never succeed on first boot. 


---

1. Gap 1 — Canonical Database Schema

1.1 Design Decisions

Decision A — Audit-critical tables use ON DELETE RESTRICT

Audit-critical rows must not disappear because a parent task/session is deleted. Therefore:

security_events

session_events

provider_usage

provider_usage_reconciliations

plan_artifacts

task_permissions

resource_usage

model_profile_fingerprints

manifest_fingerprints

classifier_calibration_runs


use RESTRICT or no deletion path.

Operational cleanup should be handled later by archival/export, not cascading deletion.

Decision B — tasks.status canonical enum

Canonical tasks.status values:

pending
running
completed
failed
quarantined
needs_human_input
blocked_resource_limit
cancelled

checkpoint_blocked is not a task status. It is an artifact status. v1.10.2 explicitly separates artifact lifecycle from parent task lifecycle: high-risk fingerprint failure maps artifact → quarantined, parent task → quarantined; ordinary fingerprint failure maps artifact → checkpoint_blocked, parent task → needs_human_input. 

Decision C — checkpoint_failed and checkpoint_blocked are distinct

They are not duplicates.

Artifact status	Meaning	Parent task state

checkpoint_failed	Checkpoint ran and returned a negative verdict: token budget, context size, schema, deterministic validation, or resource failure.	Usually blocked_resource_limit, needs_human_input, or failed, depending on failure class.
checkpoint_blocked	Checkpoint/scanner could not safely complete because a security prerequisite failed, such as fingerprint verification or safe-pass disabled.	needs_human_input for ordinary artifacts.
quarantined	Artifact is tainted or high-risk unsafe.	quarantined.


Decision D — Manifest fingerprint naming collision resolved

Kimi’s inferred table used:

manifest_fingerprints.manifest_id INTEGER PRIMARY KEY

while manifest JSON used:

"manifest_id": "goal_planner_v1"

Canonical resolution:

Row primary key becomes fingerprint_id INTEGER PRIMARY KEY

Logical manifest identifier remains manifest_id TEXT NOT NULL UNIQUE

All task/permission references use the logical manifest_id

fingerprint_id is internal storage identity only


Decision E — memory_items.embedding is represented by sqlite-vec virtual table

Canonical resolution:

memory_items stores memory metadata/content.

memory_item_embeddings is the sqlite-vec virtual table.

memory_item_embeddings.rowid == memory_items.memory_item_id.


sqlite-vec stores vector columns through a vec0 virtual table declaration such as CREATE VIRTUAL TABLE ... USING vec0(embedding float[768]); virtual tables are the correct SQLite mechanism for this kind of extension-backed table. 


---

1.2 Canonical schema.sql

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;

-- ============================================================
-- AXIOM CANONICAL DATABASE SCHEMA
-- Version: v1.11.1 proposal
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
        CHECK (manifest_type IN ('role', 'operator_control')),

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

    provider TEXT NOT NULL,
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

    provider TEXT NOT NULL,

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


---

1.3 Scanner Return Contract Correction

Kimi v1.11 conflated scanner decision, artifact state, and task state. That is incompatible with v1.10.2’s two-tier lifecycle table. 

Canonical scanner result object:

{
  "scanner_result": "safe_pass_disabled",
  "risk_class": "ordinary",
  "artifact_status": "checkpoint_blocked",
  "parent_task_status": "needs_human_input",
  "reason": "fingerprint_verification_failed",
  "details": {}
}

For high-risk:

{
  "scanner_result": "safe_pass_disabled",
  "risk_class": "high_risk",
  "artifact_status": "quarantined",
  "parent_task_status": "quarantined",
  "reason": "fingerprint_verification_failed",
  "details": {}
}

Kimi v1.12 must implement this explicit return contract.


---

2. Gap 2 — Canonical Manifest JSON Schema

2.1 Design Decisions

Decision A — Manifests are security artifacts

A manifest defines:

1. What role or operator command is being bound.


2. What capabilities are allowed.


3. Which tools are explicitly allowed.


4. Which tools are explicitly forbidden.


5. Which network, sandbox, memory, and budget limits apply.



A task receives authority only through a registered manifest fingerprint.

Decision B — forbidden_tools wins over allowed_tools

Tool authorization rule:

tool allowed only if:
    tool ∈ allowed_tools
AND required capability branch allows operation
AND tool ∉ forbidden_tools
AND manifest fingerprint matches registered SHA256

If fields conflict, deny.

Decision C — Missing capability means deny

No implicit privileges. If a capability branch is absent or set to false, the operation is denied.

Decision D — Network allowlist uses structured endpoint objects, not URL strings

Canonical allowlist entry:

{
  "scheme": "https",
  "host": "api.search.brave.com",
  "port": 443,
  "path_prefix": "/res/v1/web/search",
  "methods": ["GET"],
  "purpose": "web_search"
}

Rules:

allowlist entries must be explicit.

denylist may use "*" wildcards.

Raw URL strings are invalid.

Redirects are denied unless redirect_policy allows same_host_only.



---

2.2 Common Manifest Fields

Both role manifests and operator control manifests share these required top-level fields:

{
  "schema_version": "axiom.manifest.v1",
  "manifest_type": "role | operator_control",
  "manifest_id": "role.goal_planner.v1",
  "manifest_version": "1.0.0",
  "approved_by_panel_version": "v1.11.1",
  "description": "Human-readable purpose.",
  "budget_policy": {},
  "allowed_capabilities": {},
  "allowed_tools": [],
  "forbidden_tools": [],
  "network_policy": {},
  "sandbox_policy": {},
  "memory_policy": {},
  "audit_policy": {}
}


---

2.3 Role Manifest Field Set

Role manifests additionally require:

"role": {
  "role_name": "goal_planner",
  "role_tier": "goal_planner | task_planner | tool_executor | result_verifier | system",
  "allowed_task_classes": [
    "goal_planning"
  ],
  "may_create_child_tasks": true,
  "may_commit_task_tree": false
}

Role manifests must not include operator_command.


---

2.4 Operator Control Manifest Field Set

Operator control manifests additionally require:

"operator_command": {
  "command_name": "status",
  "telegram_aliases": ["/status"],
  "creates_task": true,
  "created_task_class": "operator_control",
  "allowed_when_autonomous_disabled": true,
  "allowed_when_safe_pass_disabled": true,
  "effect_class": "read_only | state_change | shutdown | calibration | reconciliation"
},
"authorization_policy": {
  "telegram_operator_whitelist_required": true,
  "capability_token_required": false,
  "requires_active_session": false
}

Operator control manifests must not include role.


---

2.5 Canonical JSON Schema

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.manifest.schema.v1",
  "title": "AXIOM Manifest Schema v1",
  "oneOf": [
    { "$ref": "#/$defs/role_manifest" },
    { "$ref": "#/$defs/operator_control_manifest" }
  ],
  "$defs": {
    "manifest_id": {
      "type": "string",
      "pattern": "^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$"
    },
    "tool_id": {
      "type": "string",
      "pattern": "^[a-z_]+\\.[a-z_]+$"
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
        "max_estimated_input_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "max_estimated_output_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "max_provider_calls": {
          "type": "integer",
          "minimum": 0
        },
        "max_wall_clock_seconds": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "allowed_capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "model",
        "task_queue",
        "memory",
        "network",
        "sandbox",
        "filesystem",
        "operator_control"
      ],
      "properties": {
        "model": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "allow_model_calls",
            "allowed_provider_groups",
            "allow_local_classifier"
          ],
          "properties": {
            "allow_model_calls": {
              "type": "boolean"
            },
            "allowed_provider_groups": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "cloud_cascade",
                  "local_classifier"
                ]
              },
              "uniqueItems": true
            },
            "allow_local_classifier": {
              "type": "boolean"
            }
          }
        },
        "task_queue": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "read_scope",
            "write_scope",
            "may_create_tasks",
            "may_update_own_result",
            "may_update_other_tasks"
          ],
          "properties": {
            "read_scope": {
              "type": "string",
              "enum": [
                "none",
                "assigned_task",
                "own_chain"
              ]
            },
            "write_scope": {
              "type": "string",
              "enum": [
                "none",
                "own_result",
                "create_child_tasks",
                "operator_control_insert"
              ]
            },
            "may_create_tasks": {
              "type": "boolean"
            },
            "may_update_own_result": {
              "type": "boolean"
            },
            "may_update_other_tasks": {
              "type": "boolean"
            }
          }
        },
        "memory": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "read",
            "write",
            "max_results",
            "dedupe_required_on_write"
          ],
          "properties": {
            "read": {
              "type": "boolean"
            },
            "write": {
              "type": "boolean"
            },
            "max_results": {
              "type": "integer",
              "minimum": 0
            },
            "dedupe_required_on_write": {
              "type": "boolean"
            }
          }
        },
        "network": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "fetch"
          ],
          "properties": {
            "fetch": {
              "type": "boolean"
            }
          }
        },
        "sandbox": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "execute_code"
          ],
          "properties": {
            "execute_code": {
              "type": "boolean"
            }
          }
        },
        "filesystem": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "read",
            "write",
            "allowed_roots"
          ],
          "properties": {
            "read": {
              "type": "boolean"
            },
            "write": {
              "type": "boolean"
            },
            "allowed_roots": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "uniqueItems": true
            }
          }
        },
        "operator_control": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "allowed_commands"
          ],
          "properties": {
            "allowed_commands": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "uniqueItems": true
            }
          }
        }
      }
    },
    "network_allow_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "scheme",
        "host",
        "port",
        "path_prefix",
        "methods",
        "purpose"
      ],
      "properties": {
        "scheme": {
          "type": "string",
          "enum": [
            "https"
          ]
        },
        "host": {
          "type": "string",
          "pattern": "^[a-z0-9.-]+$"
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535
        },
        "path_prefix": {
          "type": "string",
          "pattern": "^/"
        },
        "methods": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "GET",
              "POST"
            ]
          },
          "minItems": 1,
          "uniqueItems": true
        },
        "purpose": {
          "type": "string"
        }
      }
    },
    "network_deny_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "scheme",
        "host",
        "port",
        "path_prefix",
        "reason"
      ],
      "properties": {
        "scheme": {
          "type": "string"
        },
        "host": {
          "type": "string"
        },
        "port": {
          "type": [
            "integer",
            "string"
          ]
        },
        "path_prefix": {
          "type": "string"
        },
        "reason": {
          "type": "string"
        }
      }
    },
    "network_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "mode",
        "allowlist",
        "denylist",
        "redirect_policy",
        "timeout_seconds",
        "max_response_bytes"
      ],
      "properties": {
        "mode": {
          "type": "string",
          "enum": [
            "deny_all",
            "allowlist_only"
          ]
        },
        "allowlist": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/network_allow_entry"
          },
          "uniqueItems": true
        },
        "denylist": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/network_deny_entry"
          },
          "uniqueItems": true
        },
        "redirect_policy": {
          "type": "string",
          "enum": [
            "deny",
            "same_host_only"
          ]
        },
        "timeout_seconds": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60
        },
        "max_response_bytes": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "sandbox_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "allowed",
        "max_ram_mb",
        "max_wall_clock_seconds",
        "network_access"
      ],
      "properties": {
        "allowed": {
          "type": "boolean"
        },
        "max_ram_mb": {
          "type": "integer",
          "minimum": 0,
          "maximum": 256
        },
        "max_wall_clock_seconds": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60
        },
        "network_access": {
          "type": "string",
          "enum": [
            "denied"
          ]
        }
      }
    },
    "memory_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "read",
        "write",
        "max_query_results",
        "write_requires_dedupe"
      ],
      "properties": {
        "read": {
          "type": "boolean"
        },
        "write": {
          "type": "boolean"
        },
        "max_query_results": {
          "type": "integer",
          "minimum": 0
        },
        "write_requires_dedupe": {
          "type": "boolean"
        }
      }
    },
    "audit_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "log_task_id",
        "log_manifest_id",
        "log_tool_calls",
        "log_policy_denials"
      ],
      "properties": {
        "log_task_id": {
          "type": "boolean",
          "const": true
        },
        "log_manifest_id": {
          "type": "boolean",
          "const": true
        },
        "log_tool_calls": {
          "type": "boolean"
        },
        "log_policy_denials": {
          "type": "boolean",
          "const": true
        }
      }
    },
    "role_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version",
        "manifest_type",
        "manifest_id",
        "manifest_version",
        "approved_by_panel_version",
        "description",
        "role",
        "budget_policy",
        "allowed_capabilities",
        "allowed_tools",
        "forbidden_tools",
        "network_policy",
        "sandbox_policy",
        "memory_policy",
        "audit_policy"
      ],
      "properties": {
        "schema_version": {
          "type": "string",
          "const": "axiom.manifest.v1"
        },
        "manifest_type": {
          "type": "string",
          "const": "role"
        },
        "manifest_id": {
          "$ref": "#/$defs/manifest_id"
        },
        "manifest_version": {
          "type": "string"
        },
        "approved_by_panel_version": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "role": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "role_name",
            "role_tier",
            "allowed_task_classes",
            "may_create_child_tasks",
            "may_commit_task_tree"
          ],
          "properties": {
            "role_name": {
              "type": "string"
            },
            "role_tier": {
              "type": "string",
              "enum": [
                "goal_planner",
                "task_planner",
                "tool_executor",
                "result_verifier",
                "system"
              ]
            },
            "allowed_task_classes": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "goal_planning",
                  "task_planning",
                  "tool_execution",
                  "result_verification",
                  "memory_operation",
                  "system_maintenance"
                ]
              },
              "uniqueItems": true
            },
            "may_create_child_tasks": {
              "type": "boolean"
            },
            "may_commit_task_tree": {
              "type": "boolean"
            }
          }
        },
        "budget_policy": {
          "$ref": "#/$defs/budget_policy"
        },
        "allowed_capabilities": {
          "$ref": "#/$defs/allowed_capabilities"
        },
        "allowed_tools": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/tool_id"
          },
          "uniqueItems": true
        },
        "forbidden_tools": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/tool_id"
          },
          "uniqueItems": true
        },
        "network_policy": {
          "$ref": "#/$defs/network_policy"
        },
        "sandbox_policy": {
          "$ref": "#/$defs/sandbox_policy"
        },
        "memory_policy": {
          "$ref": "#/$defs/memory_policy"
        },
        "audit_policy": {
          "$ref": "#/$defs/audit_policy"
        }
      }
    },
    "operator_control_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version",
        "manifest_type",
        "manifest_id",
        "manifest_version",
        "approved_by_panel_version",
        "description",
        "operator_command",
        "authorization_policy",
        "budget_policy",
        "allowed_capabilities",
        "allowed_tools",
        "forbidden_tools",
        "network_policy",
        "sandbox_policy",
        "memory_policy",
        "audit_policy"
      ],
      "properties": {
        "schema_version": {
          "type": "string",
          "const": "axiom.manifest.v1"
        },
        "manifest_type": {
          "type": "string",
          "const": "operator_control"
        },
        "manifest_id": {
          "$ref": "#/$defs/manifest_id"
        },
        "manifest_version": {
          "type": "string"
        },
        "approved_by_panel_version": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "operator_command": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "command_name",
            "telegram_aliases",
            "creates_task",
            "created_task_class",
            "allowed_when_autonomous_disabled",
            "allowed_when_safe_pass_disabled",
            "effect_class"
          ],
          "properties": {
            "command_name": {
              "type": "string"
            },
            "telegram_aliases": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^/"
              },
              "uniqueItems": true
            },
            "creates_task": {
              "type": "boolean"
            },
            "created_task_class": {
              "type": "string",
              "const": "operator_control"
            },
            "allowed_when_autonomous_disabled": {
              "type": "boolean"
            },
            "allowed_when_safe_pass_disabled": {
              "type": "boolean"
            },
            "effect_class": {
              "type": "string",
              "enum": [
                "read_only",
                "state_change",
                "shutdown",
                "calibration",
                "reconciliation"
              ]
            }
          }
        },
        "authorization_policy": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "telegram_operator_whitelist_required",
            "capability_token_required",
            "requires_active_session"
          ],
          "properties": {
            "telegram_operator_whitelist_required": {
              "type": "boolean",
              "const": true
            },
            "capability_token_required": {
              "type": "boolean"
            },
            "requires_active_session": {
              "type": "boolean"
            }
          }
        },
        "budget_policy": {
          "$ref": "#/$defs/budget_policy"
        },
        "allowed_capabilities": {
          "$ref": "#/$defs/allowed_capabilities"
        },
        "allowed_tools": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/tool_id"
          },
          "uniqueItems": true
        },
        "forbidden_tools": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/tool_id"
          },
          "uniqueItems": true
        },
        "network_policy": {
          "$ref": "#/$defs/network_policy"
        },
        "sandbox_policy": {
          "$ref": "#/$defs/sandbox_policy"
        },
        "memory_policy": {
          "$ref": "#/$defs/memory_policy"
        },
        "audit_policy": {
          "$ref": "#/$defs/audit_policy"
        }
      }
    }
  }
}


---

2.6 Canonical Role Manifest Example

{
  "schema_version": "axiom.manifest.v1",
  "manifest_type": "role",
  "manifest_id": "role.goal_planner.v1",
  "manifest_version": "1.0.0",
  "approved_by_panel_version": "v1.11.1",
  "description": "Goal Planner may decompose operator goals into plan artifacts but may not execute tools.",
  "role": {
    "role_name": "goal_planner",
    "role_tier": "goal_planner",
    "allowed_task_classes": ["goal_planning"],
    "may_create_child_tasks": true,
    "may_commit_task_tree": false
  },
  "budget_policy": {
    "max_estimated_input_tokens": 8000,
    "max_estimated_output_tokens": 4000,
    "max_provider_calls": 1,
    "max_wall_clock_seconds": 120
  },
  "allowed_capabilities": {
    "model": {
      "allow_model_calls": true,
      "allowed_provider_groups": ["cloud_cascade"],
      "allow_local_classifier": false
    },
    "task_queue": {
      "read_scope": "assigned_task",
      "write_scope": "create_child_tasks",
      "may_create_tasks": true,
      "may_update_own_result": true,
      "may_update_other_tasks": false
    },
    "memory": {
      "read": true,
      "write": false,
      "max_results": 8,
      "dedupe_required_on_write": true
    },
    "network": {
      "fetch": false
    },
    "sandbox": {
      "execute_code": false
    },
    "filesystem": {
      "read": false,
      "write": false,
      "allowed_roots": []
    },
    "operator_control": {
      "allowed_commands": []
    }
  },
  "allowed_tools": [
    "model_gateway.call",
    "memory_gateway.query"
  ],
  "forbidden_tools": [
    "sandbox_gateway.execute",
    "network_gateway.fetch",
    "filesystem.write"
  ],
  "network_policy": {
    "mode": "deny_all",
    "allowlist": [],
    "denylist": [
      {
        "scheme": "*",
        "host": "*",
        "port": "*",
        "path_prefix": "*",
        "reason": "default deny"
      }
    ],
    "redirect_policy": "deny",
    "timeout_seconds": 0,
    "max_response_bytes": 0
  },
  "sandbox_policy": {
    "allowed": false,
    "max_ram_mb": 0,
    "max_wall_clock_seconds": 0,
    "network_access": "denied"
  },
  "memory_policy": {
    "read": true,
    "write": false,
    "max_query_results": 8,
    "write_requires_dedupe": true
  },
  "audit_policy": {
    "log_task_id": true,
    "log_manifest_id": true,
    "log_tool_calls": true,
    "log_policy_denials": true
  }
}


---

2.7 Canonical Operator Control Manifest Example

{
  "schema_version": "axiom.manifest.v1",
  "manifest_type": "operator_control",
  "manifest_id": "operator.status.v1",
  "manifest_version": "1.0.0",
  "approved_by_panel_version": "v1.11.1",
  "description": "Operator may request current AXIOM runtime status.",
  "operator_command": {
    "command_name": "status",
    "telegram_aliases": ["/status"],
    "creates_task": true,
    "created_task_class": "operator_control",
    "allowed_when_autonomous_disabled": true,
    "allowed_when_safe_pass_disabled": true,
    "effect_class": "read_only"
  },
  "authorization_policy": {
    "telegram_operator_whitelist_required": true,
    "capability_token_required": false,
    "requires_active_session": false
  },
  "budget_policy": {
    "max_estimated_input_tokens": 0,
    "max_estimated_output_tokens": 0,
    "max_provider_calls": 0,
    "max_wall_clock_seconds": 15
  },
  "allowed_capabilities": {
    "model": {
      "allow_model_calls": false,
      "allowed_provider_groups": [],
      "allow_local_classifier": false
    },
    "task_queue": {
      "read_scope": "own_chain",
      "write_scope": "operator_control_insert",
      "may_create_tasks": true,
      "may_update_own_result": true,
      "may_update_other_tasks": false
    },
    "memory": {
      "read": false,
      "write": false,
      "max_results": 0,
      "dedupe_required_on_write": true
    },
    "network": {
      "fetch": false
    },
    "sandbox": {
      "execute_code": false
    },
    "filesystem": {
      "read": false,
      "write": false,
      "allowed_roots": []
    },
    "operator_control": {
      "allowed_commands": ["status"]
    }
  },
  "allowed_tools": [
    "session_controller.status"
  ],
  "forbidden_tools": [
    "model_gateway.call",
    "network_gateway.fetch",
    "sandbox_gateway.execute",
    "filesystem.write"
  ],
  "network_policy": {
    "mode": "deny_all",
    "allowlist": [],
    "denylist": [
      {
        "scheme": "*",
        "host": "*",
        "port": "*",
        "path_prefix": "*",
        "reason": "operator status command requires no network"
      }
    ],
    "redirect_policy": "deny",
    "timeout_seconds": 0,
    "max_response_bytes": 0
  },
  "sandbox_policy": {
    "allowed": false,
    "max_ram_mb": 0,
    "max_wall_clock_seconds": 0,
    "network_access": "denied"
  },
  "memory_policy": {
    "read": false,
    "write": false,
    "max_query_results": 0,
    "write_requires_dedupe": true
  },
  "audit_policy": {
    "log_task_id": true,
    "log_manifest_id": true,
    "log_tool_calls": true,
    "log_policy_denials": true
  }
}


---

3. Initial Calibrated Model Fingerprint Registration Mechanism

3.1 Problem

Kimi’s v1.11 plan implemented verify_current_profile() by reading:

profile_repo.get_current()

but did not define how the initial current profile is written. The Evaluator correctly identified this as a circular dependency: first boot finds no stored profile, safe-pass disables, and there is no approved mechanism to recover. 


---

3.2 Decision

Add a setup-only CLI:

tools/register_model_fingerprint.py

This tool is analogous to:

tools/register_manifests.py

It is not imported by the autonomous runtime.


---

3.3 Registration Sequence

Canonical first-run sequence:

1. Initialize schema.
2. Register manifests.
3. Run classifier calibration in manual setup mode.
4. Write classifier_calibration_runs row.
5. Run tools/register_model_fingerprint.py.
6. Boot AXIOM autonomous session.
7. ModelFingerprintGuard.verify_current_profile() compares runtime Ollama profile against registered current profile.

Autonomous operation must not be enabled before step 5 succeeds.


---

3.4 CLI Contract

Canonical command:

python tools\register_model_fingerprint.py `
  --profile-label default `
  --calibration-run-id injection_classifier_v1_2026_05_03 `
  --approved-by-panel-version v1.11.1

Required behavior:

1. Use the same database path as runtime.


2. Use the same SQLite PRAGMAs as runtime:

journal_mode=WAL

synchronous=FULL

busy_timeout=5000

foreign_keys=ON



3. Load calibration run by calibration_run_id.


4. Reject if calibration row does not exist.


5. Reject if classifier_calibration_runs.passed != 1.


6. Query Ollama /api/show for the configured model.


7. Extract quantization from the Ollama response, not from a hardcoded literal.


8. Determine thinking_mode using the Arbiter-approved inference rule only.


9. Reject if thinking_mode = unknown.


10. Compute selected-profile hashes.


11. In one transaction:

set previous current profile for same profile_label to is_current=0, registration_status='superseded'

insert new fingerprint with is_current=1, registration_status='current'

write security_events.event_type='model_fingerprint_registered'





---

3.5 Profile Hashing Rule

Do not hash the entire raw /api/show response blindly if it contains volatile fields.

Canonical selected profile object:

{
  "model_name": "qwen3:4b",
  "ollama_host": "http://localhost:11434",
  "ollama_model_tag": "<from configured model name>",
  "ollama_model_digest": "<from /api/show if present>",
  "quantization": "<from details.quantization_level or Arbiter-approved equivalent>",
  "parameter_size": "<from details.parameter_size if present>",
  "model_family": "<from details.family if present>",
  "model_format": "<from details.format if present>",
  "thinking_mode": "<enabled | disabled>",
  "template_sha256": "<sha256(template)>",
  "system_sha256": "<sha256(system)>",
  "parameters_sha256": "<sha256(parameters)>",
  "details_sha256": "<sha256(canonical details object)>"
}

Then compute:

selected_profile_sha256 = sha256(canonical_json(selected_profile_object))

Canonical JSON means:

json.dumps(obj, sort_keys=True, separators=(",", ":"))


---

3.6 Explicit Non-Decision: Thinking Mode

This proposal does not specify the qwen3:4b thinking-mode inference pattern.

Kimi v1.11 guessed at "/no_think" and the Evaluator correctly marked that as unsafe because it could either create false failures or allow a thinking-enabled model to pass as disabled. 

Canonical placeholder interface only:

def infer_thinking_mode_from_arbiter_rule(show_json: dict) -> str:
    """
    Returns one of:
        "enabled"
        "disabled"
        "unknown"

    Exact implementation awaits Gemini Arbiter ruling.
    """

register_model_fingerprint.py must fail closed if this returns "unknown".


---

3.7 Repository Contract

ModelProfileRepository must expose:

insert_current_profile(profile: dict) -> int
get_current(profile_label: str = "default") -> Optional[dict]
supersede_current(profile_label: str = "default") -> None

Transaction rule:

supersede_current + insert_current_profile must occur in the same transaction.

There must never be two current profiles for the same profile_label. The partial unique index enforces this.


---

3.8 Acceptance Tests for Kimi v1.12

Kimi must add:

test_register_model_fingerprint_requires_passed_calibration.py
test_register_model_fingerprint_sets_single_current_profile.py
test_register_model_fingerprint_rejects_unknown_thinking_mode.py
test_model_fingerprint_guard_happy_path.py
test_model_fingerprint_guard_no_stored_profile_fails_closed.py
test_model_fingerprint_quantization_not_hardcoded.py


---

4. Required Kimi v1.12 Adjustments

Kimi v1.12 must revise the implementation plan as follows:

1. Replace inferred schema with the canonical schema above.


2. Replace inferred manifest JSON with the canonical manifest schema above.


3. Do not run init_db() until the panel ratifies this schema.


4. Do not create/register manifests until the panel ratifies the manifest schema.


5. Add tools/register_model_fingerprint.py.


6. Add classifier_calibration_runs and model_profile_fingerprints repository methods.


7. Replace hardcoded quantization with extracted quantization.


8. Replace scanner return contract with explicit:

scanner_result

risk_class

artifact_status

parent_task_status

reason



9. Add positive-path fingerprint guard test.


10. Leave qwen3:4b thinking-mode inference unimplemented until Gemini provides a binding factual ruling.




---

5. Panel Ratification Questions

Evaluator

Check for:

Internal consistency of task/artifact states.

Whether checkpoint_failed and checkpoint_blocked are sufficiently distinct.

Whether manifest field names avoid ambiguity.


Critic

Stress-test:

Manifest privilege escalation paths.

Whether allowed_capabilities + allowed_tools creates any implicit allow.

Whether model fingerprint registration can be abused to bless a bad profile.


Arbiter

Verify later, separately:

sqlite-vec compatibility if needed beyond the vec0(embedding float[768]) pattern.

qwen3:4b thinking-mode inference from Ollama /api/show.


Constraints Reviewer

Check:

SQLite schema overhead against the 2.0–2.3 GB runtime headroom.

Whether added tables increase complexity beyond MVP.

Whether sqlite-vec virtual table usage remains acceptable on the target Windows 11 / Python 3.12 / SQLite environment, which is already part of the observed software baseline. 



---

6. Chief Architect Recommendation

Approve this proposal as v1.11.1 spec completion if the panel confirms:

1. The database schema is canonical.


2. Manifest schema is canonical.


3. register_model_fingerprint.py is the correct setup-time mechanism.


4. Gap 3 remains with Gemini and is not folded into this proposal.



After ratification and Gemini’s separate Gap 3 ruling, return to Kimi for AXIOM_Implementation_v1.12.