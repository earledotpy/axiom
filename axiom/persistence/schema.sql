PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -32768;

-- ============================================================
-- AXIOM CANONICAL DATABASE SCHEMA
-- Version: v1.11.4 canonical
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

-- ------------------------------------------------------------
-- 18. External adapter messages
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS external_adapter_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,

    adapter TEXT NOT NULL
        CHECK (adapter IN ('telegram')),

    platform_message_id TEXT NOT NULL,
    platform_sender_id TEXT NOT NULL,
    platform_chat_id TEXT NOT NULL,

    raw_text_sha256 TEXT NOT NULL,
    raw_text_length INTEGER NOT NULL
        CHECK (raw_text_length >= 0),
    command_text TEXT,

    received_at TEXT NOT NULL,

    decision_status TEXT NOT NULL
        CHECK (decision_status IN (
            'accepted',
            'rejected',
            'confirmation_required'
        )),

    denial_reason TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (adapter, platform_message_id)
);

CREATE INDEX IF NOT EXISTS idx_external_adapter_messages_sender_created
    ON external_adapter_messages(adapter, platform_sender_id, created_at);

CREATE INDEX IF NOT EXISTS idx_external_adapter_messages_chat_created
    ON external_adapter_messages(adapter, platform_chat_id, created_at);

CREATE INDEX IF NOT EXISTS idx_external_adapter_messages_status
    ON external_adapter_messages(adapter, decision_status);

-- ------------------------------------------------------------
-- 19. External confirmation requests
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS external_confirmation_requests (
    confirmation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    message_id INTEGER NOT NULL,
    command_name TEXT NOT NULL,
    manifest_id TEXT NOT NULL,

    confirmation_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (confirmation_status IN (
            'pending',
            'accepted',
            'rejected',
            'expired'
        )),

    confirmation_token_sha256 TEXT NOT NULL UNIQUE,

    expires_at TEXT NOT NULL,
    command_id INTEGER,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,

    FOREIGN KEY (message_id)
        REFERENCES external_adapter_messages(message_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (command_id)
        REFERENCES operator_commands(command_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_external_confirmation_requests_status_expires
    ON external_confirmation_requests(confirmation_status, expires_at);

CREATE INDEX IF NOT EXISTS idx_external_confirmation_requests_message
    ON external_confirmation_requests(message_id);

INSERT OR IGNORE INTO schema_migrations (schema_version, notes)
VALUES (
    'v1.11.4',
    'Initial AXIOM MVP canonical schema with manifest schemas, tool-capability security artifact, network response ceiling, and Ollama think=false verification.'
);
