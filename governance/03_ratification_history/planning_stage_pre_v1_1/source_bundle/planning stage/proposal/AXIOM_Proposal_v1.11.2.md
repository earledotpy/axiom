AXIOM Proposal v1.11.2 — Targeted Revision to v1.11.1

Status

Proposal version: v1.11.2
Type: Targeted Architect revision
Scope: Manifest authorization coherence, network wildcard semantics, allowlist validation, and schema cleanup items
Architecture spine changed: No
Gap 3 included: No — qwen3:4b thinking-mode inference remains routed to Gemini

The Evaluator returned v1.11.1 because the manifest schema duplicated authorization surfaces across allowed_capabilities and top-level resource policies without defining precedence. The Evaluator also required explicit wildcard semantics, an allowlist_only non-empty rule, and several schema cleanup items.  


---

1. Architect Ruling — Capability / Policy Precedence

Decision

Adopt a stricter version of Option B:

> Resource permissions are authored only in their top-level policy objects. allowed_capabilities no longer contains network, sandbox, or memory branches. ManifestBinder derives effective capabilities from the authoritative policies and stores the derived result in task_permissions.granted_capabilities_json.



This removes the conflicting double-source problem rather than merely defining precedence after conflict.

Authoritative sources

Resource	Authoritative manifest field

Network	network_policy
Sandbox	sandbox_policy
Memory	memory_policy
Model calls	allowed_capabilities.model + budget_policy
Task queue coordination	allowed_capabilities.task_queue
Filesystem	allowed_capabilities.filesystem
Operator control	allowed_capabilities.operator_control + operator_command


ManifestBinder behavior

ManifestBinder must enforce this sequence:

1. Validate manifest against JSON Schema.
2. Reject manifest if allowed_capabilities contains network, sandbox, or memory.
3. Verify manifest SHA256 against manifest_fingerprints.
4. Compute effective_capabilities from:
   - allowed_capabilities
   - network_policy
   - sandbox_policy
   - memory_policy
   - allowed_tools
   - forbidden_tools
5. Store computed effective_capabilities in task_permissions.granted_capabilities_json.
6. Store allowed tool list in task_permissions.granted_tools_json.

There is no runtime “which wins?” case. If a manifest attempts to express resource permission in both places, it fails schema validation before registration.


---

2. Revised Manifest Schema Sections

Only the affected manifest schema sections are replaced here. All unchanged portions of v1.11.1 remain in force.

2.1 Revised allowed_capabilities

{
  "allowed_capabilities": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "model",
      "task_queue",
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
  }
}

Removed from allowed_capabilities

The following branches are no longer valid:

"network": {}
"sandbox": {}
"memory": {}

Any manifest containing those branches fails schema validation because additionalProperties: false.


---

2.2 Revised Network Wildcard Semantics

Decision

Use "*" as the only legal wildcard string.

No other wildcard spelling is valid. The following are invalid:

"all"
"any"
"wildcard"
".*"
"%"

Denylist matching rule

A denylist entry matches a candidate request when all fields match.

A field matches when:

deny field == "*"
OR
deny field == candidate field

For path_prefix:

deny path_prefix == "*"
OR
candidate path starts with deny path_prefix

For methods:

methods contains "*"
OR
methods contains candidate HTTP method

Evaluation order

1. If network_policy.mode == "deny_all":
      deny request.
2. If network_policy.mode == "allowlist_only":
      request must match at least one allowlist entry.
3. Request must not match any denylist entry.
4. Redirect policy is evaluated after initial allowlist match.
5. Any ambiguity denies the request.

Denylist overrides allowlist.


---

2.3 Revised network_deny_entry

{
  "network_deny_entry": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "scheme",
      "host",
      "port",
      "path_prefix",
      "methods",
      "reason"
    ],
    "properties": {
      "scheme": {
        "oneOf": [
          { "const": "*" },
          { "const": "https" }
        ]
      },
      "host": {
        "oneOf": [
          { "const": "*" },
          {
            "type": "string",
            "pattern": "^[a-z0-9.-]+$"
          }
        ]
      },
      "port": {
        "oneOf": [
          { "const": "*" },
          {
            "type": "integer",
            "minimum": 1,
            "maximum": 65535
          }
        ]
      },
      "path_prefix": {
        "oneOf": [
          { "const": "*" },
          {
            "type": "string",
            "pattern": "^/"
          }
        ]
      },
      "methods": {
        "type": "array",
        "minItems": 1,
        "items": {
          "oneOf": [
            { "const": "*" },
            {
              "type": "string",
              "enum": [
                "GET",
                "POST"
              ]
            }
          ]
        },
        "uniqueItems": true
      },
      "reason": {
        "type": "string",
        "minLength": 1
      }
    }
  }
}


---

2.4 Revised network_policy

{
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
    },
    "allOf": [
      {
        "if": {
          "properties": {
            "mode": {
              "const": "allowlist_only"
            }
          },
          "required": [
            "mode"
          ]
        },
        "then": {
          "properties": {
            "allowlist": {
              "minItems": 1
            },
            "timeout_seconds": {
              "minimum": 1
            },
            "max_response_bytes": {
              "minimum": 1
            }
          }
        }
      },
      {
        "if": {
          "properties": {
            "mode": {
              "const": "deny_all"
            }
          },
          "required": [
            "mode"
          ]
        },
        "then": {
          "properties": {
            "allowlist": {
              "maxItems": 0
            },
            "timeout_seconds": {
              "const": 0
            },
            "max_response_bytes": {
              "const": 0
            }
          }
        }
      }
    ]
  }
}

Timeout convention

network_policy.timeout_seconds = 0

means:

no network call permitted

It is valid only when:

network_policy.mode = "deny_all"

For allowlist_only, timeout must be 1–60.


---

2.5 Revised deny-all example

"network_policy": {
  "mode": "deny_all",
  "allowlist": [],
  "denylist": [
    {
      "scheme": "*",
      "host": "*",
      "port": "*",
      "path_prefix": "*",
      "methods": ["*"],
      "reason": "default deny"
    }
  ],
  "redirect_policy": "deny",
  "timeout_seconds": 0,
  "max_response_bytes": 0
}


---

2.6 Example allowlist_only network policy

"network_policy": {
  "mode": "allowlist_only",
  "allowlist": [
    {
      "scheme": "https",
      "host": "api.search.brave.com",
      "port": 443,
      "path_prefix": "/res/v1/web/search",
      "methods": ["GET"],
      "purpose": "web_search"
    }
  ],
  "denylist": [
    {
      "scheme": "*",
      "host": "169.254.169.254",
      "port": "*",
      "path_prefix": "*",
      "methods": ["*"],
      "reason": "block metadata service"
    },
    {
      "scheme": "*",
      "host": "localhost",
      "port": "*",
      "path_prefix": "*",
      "methods": ["*"],
      "reason": "block loopback access through network gateway"
    }
  ],
  "redirect_policy": "same_host_only",
  "timeout_seconds": 10,
  "max_response_bytes": 1048576
}

Brave Search remains a gateway-phase binding condition, not a manifest-schema dependency. The Constraints Register already identifies DuckDuckGo failure and Brave Search as the pre-rebuild replacement candidate. 


---

3. Tool-to-Capability Mapping

Decision

PolicyEngine maintains a static tool-to-capability mapping table.

Canonical location:

axiom/core/tool_capability_map.py

Adding a new tool requires:

1. Panel-approved tool ID.
2. Tool-to-capability map entry.
3. Manifest schema compatibility check.
4. PolicyEngine test proving authorization and denial paths.

Initial canonical mapping

TOOL_CAPABILITY_MAP = {
    "model_gateway.call": {
        "source": "allowed_capabilities.model.allow_model_calls",
        "additional_checks": [
            "provider_group_allowed",
            "budget_policy_not_exceeded"
        ]
    },

    "memory_gateway.query": {
        "source": "memory_policy.read",
        "additional_checks": [
            "memory_policy.max_query_results"
        ]
    },

    "memory_gateway.write": {
        "source": "memory_policy.write",
        "additional_checks": [
            "memory_policy.write_requires_dedupe"
        ]
    },

    "network_gateway.fetch": {
        "source": "network_policy",
        "additional_checks": [
            "mode_allowlist_only",
            "request_matches_allowlist",
            "request_does_not_match_denylist",
            "redirect_policy",
            "timeout_seconds",
            "max_response_bytes"
        ]
    },

    "sandbox_gateway.execute": {
        "source": "sandbox_policy.allowed",
        "additional_checks": [
            "sandbox_policy.max_ram_mb",
            "sandbox_policy.max_wall_clock_seconds",
            "sandbox_policy.network_access_denied"
        ]
    },

    "filesystem.read": {
        "source": "allowed_capabilities.filesystem.read",
        "additional_checks": [
            "path_under_allowed_roots"
        ]
    },

    "filesystem.write": {
        "source": "allowed_capabilities.filesystem.write",
        "additional_checks": [
            "path_under_allowed_roots"
        ]
    },

    "session_controller.status": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "status"
    },

    "session_controller.cancel_current_chain": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "cancel_current_chain"
    },

    "session_controller.pause_after_current": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "pause_after_current"
    },

    "session_controller.resume": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "resume"
    },

    "session_controller.shutdown_after_current": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "shutdown_after_current"
    },

    "session_controller.run_classifier_validation": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "run_classifier_validation"
    },

    "session_controller.enable_autonomous": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "enable_autonomous"
    },

    "session_controller.reconcile_provider_usage": {
        "source": "allowed_capabilities.operator_control.allowed_commands",
        "required_command": "reconcile_provider_usage"
    }
}

Tool authorization rule

Tool is allowed only if:

1. tool_id ∈ allowed_tools
2. tool_id ∉ forbidden_tools
3. TOOL_CAPABILITY_MAP contains tool_id
4. mapped capability/policy check passes
5. all additional checks pass

Otherwise deny and log policy denial.

forbidden_tools wins over every allow path.


---

4. Schema Cleanup Revisions

4.1 scheduler_heartbeat write model

Decision

scheduler_heartbeat is a log table, not a single-current-row table.

SupervisorMonitor reads the latest heartbeat using:

SELECT *
FROM scheduler_heartbeat
WHERE session_id = ?
ORDER BY last_freshness_at DESC, heartbeat_id DESC
LIMIT 1;

Add this index:

CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_latest
    ON scheduler_heartbeat(session_id, last_freshness_at DESC, heartbeat_id DESC);

Heartbeat ordering invariant

Scheduler must write a heartbeat row:

before starting any blocking operation

and must write another heartbeat row:

after completing sandbox execution and before starting any following blocking operation

This preserves the test_sandbox_heartbeat_ordering.py requirement carried forward from v1.10.2. 


---

4.2 tasks.manifest_id lifecycle

Decision

tasks.manifest_id remains nullable at the database layer but is controlled by state-machine rules.

Lifecycle

Task state	manifest_id allowed to be NULL?	Rule

pending	Yes	Newly inserted task may be unbound before ManifestBinder runs.
running	No	StateMachine must reject transition to running unless manifest is bound.
completed	No	Completed executable task must retain its bound manifest.
failed	Yes only if pre-binding validation failed	Failure before binding is allowed and must be accompanied by a security or session event.
quarantined	Yes only if quarantine occurred before binding	Must be accompanied by security event.
needs_human_input	Yes only if block occurred before binding	Must include blocked_reason.
blocked_resource_limit	No	Resource limit checks occur after binding.
cancelled	Yes	Operator may cancel pending unbound task.


StateMachine enforcement

Kimi must implement:

def assert_manifest_bound_before_running(task):
    if task["status"] == "running" and not task["manifest_id"]:
        raise StateTransitionError("Cannot run task without bound manifest")

Repository write paths must not directly mutate task state outside StateMachine.


---

4.3 Initial schema version

Initial schema version is pinned to:

v1.11.2

Add this to the initial schema application:

INSERT OR IGNORE INTO schema_migrations (schema_version, notes)
VALUES (
    'v1.11.2',
    'Initial AXIOM MVP canonical schema: database, manifests, fingerprint registration, and v1.11.2 manifest authorization cleanup.'
);


---

4.4 Provider enum constraint

Decision

provider_usage.provider is constrained. Future provider additions require a schema migration.

Revise provider_usage.provider:

provider TEXT NOT NULL
    CHECK (provider IN (
        'cerebras',
        'groq',
        'openrouter',
        'sambanova',
        'ollama_local'
    )),

Revise provider_budget_windows.provider similarly:

provider TEXT NOT NULL
    CHECK (provider IN (
        'cerebras',
        'groq',
        'openrouter',
        'sambanova',
        'ollama_local'
    )),

ollama_local is included for local classifier accounting and diagnostics. It does not consume API budget.


---

4.5 memory_items.embedding_status and memory_item_embeddings invariant

Decision

memory_item_embeddings is sparse.

No placeholder vector row is written for pending or failed memory items.

Canonical invariant

memory_items.embedding_status	memory_item_embeddings row

pending	Must not exist yet
indexed	Must exist with rowid = memory_items.memory_item_id
failed	Must not exist
soft_deleted	Must not participate in retrieval


Write sequence

1. Insert memory_items row with embedding_status = 'pending'.
2. Compute embedding.
3. In one transaction:
   a. INSERT INTO memory_item_embeddings(rowid, embedding) using memory_item_id.
   b. UPDATE memory_items SET embedding_status = 'indexed'.

Failure sequence

1. Leave memory_items row intact.
2. Set embedding_status = 'failed'.
3. Write security/session event if failure affects task outcome.
4. Do not insert vec0 row.

Soft delete sequence

1. Set memory_items.embedding_status = 'soft_deleted'.
2. Delete corresponding memory_item_embeddings row if present.
3. Preserve memory_items content and metadata row.

The virtual table is a derived retrieval index, not the audit record.


---

5. Revised Role Manifest Example

The role example from v1.11.1 is revised so allowed_capabilities no longer duplicates network, sandbox, or memory.

{
  "schema_version": "axiom.manifest.v1",
  "manifest_type": "role",
  "manifest_id": "role.goal_planner.v1",
  "manifest_version": "1.0.0",
  "approved_by_panel_version": "v1.11.2",
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
        "methods": ["*"],
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

6. Revised Operator Control Manifest Example

{
  "schema_version": "axiom.manifest.v1",
  "manifest_type": "operator_control",
  "manifest_id": "operator.status.v1",
  "manifest_version": "1.0.0",
  "approved_by_panel_version": "v1.11.2",
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
        "methods": ["*"],
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

7. Required Tests Added to v1.11.2

Kimi v1.12 must add these tests:

test_manifest_rejects_network_branch_in_allowed_capabilities.py
test_manifest_rejects_sandbox_branch_in_allowed_capabilities.py
test_manifest_rejects_memory_branch_in_allowed_capabilities.py
test_network_denylist_wildcard_exact_star_only.py
test_network_allowlist_only_requires_nonempty_allowlist.py
test_network_denylist_overrides_allowlist.py
test_network_timeout_zero_only_valid_for_deny_all.py
test_tool_capability_map_denies_unmapped_tool.py
test_task_cannot_transition_running_without_manifest.py
test_scheduler_heartbeat_latest_read_pattern.py
test_memory_embedding_sparse_until_indexed.py
test_provider_usage_rejects_unknown_provider.py

Carry forward these v1.11.1 tests unchanged:

test_register_model_fingerprint_requires_passed_calibration.py
test_register_model_fingerprint_sets_single_current_profile.py
test_register_model_fingerprint_rejects_unknown_thinking_mode.py
test_model_fingerprint_guard_happy_path.py
test_model_fingerprint_guard_no_stored_profile_fails_closed.py
test_model_fingerprint_quantization_not_hardcoded.py


---

8. Final v1.11.2 Position

v1.11.2 resolves the Evaluator’s required revisions:

Evaluator item	v1.11.2 resolution

Capability/policy precedence	Removed duplicated resource permissions from allowed_capabilities; resource policies are authoritative.
Wildcard semantics	"*" is the only legal wildcard; matching rules defined.
Empty allowlist with allowlist_only	JSON Schema conditional requires allowlist.minItems = 1.
Tool-to-capability mapping	Static TOOL_CAPABILITY_MAP added as canonical PolicyEngine dependency.
scheduler_heartbeat read pattern	Log model retained; latest-read query and index defined.
tasks.manifest_id lifecycle	Nullable only before binding or pre-binding failure/cancel/quarantine; running requires manifest.
Initial schema version	Pinned to v1.11.2.
provider_usage.provider	Constrained enum; future providers require migration.
Memory embedding invariant	Sparse vec0 table; indexed rows only.
network_policy.timeout_seconds = 0	Means no network permitted; valid only with deny_all.


Chief Architect recommendation

Attach v1.11.2 as a targeted revision to v1.11.1.

Proceed to:

Evaluator delta-confirmation
↓
Critic privilege-escalation review
↓
Arbiter only for new factual disputes
↓
Constraints Reviewer
↓
Fold in Gemini Gap 3 ruling
↓
Return to Kimi for AXIOM_Implementation_v1.12