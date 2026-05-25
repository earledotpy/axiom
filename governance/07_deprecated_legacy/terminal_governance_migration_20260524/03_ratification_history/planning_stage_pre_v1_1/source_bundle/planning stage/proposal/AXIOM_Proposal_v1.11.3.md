AXIOM Proposal v1.11.3 — Operator-Control Capability Patch

Status

Proposal version: v1.11.3
Type: Targeted patch to v1.11.2
Scope: Operator-control privilege boundary, redirect semantics, commit_batch_id lifecycle
Architecture spine changed: No
Gap 3 included: No — qwen3:4b thinking-mode inference remains routed to Gemini

The Evaluator approved the direction of v1.11.2 but identified one remaining schema-level privilege surface: role manifests can still declare arbitrary operator-control commands unless the JSON Schema prevents it. The Evaluator also requested small cleanup on redirect semantics and commit_batch_id lifecycle. 


---

1. Required Fix — Operator-Control Privilege Boundary

Problem

In v1.11.2, allowed_capabilities.operator_control.allowed_commands exists in both role manifests and operator-control manifests.

That creates this bad path:

role.goal_planner.v1
  allowed_commands = ["shutdown_after_current"]
  allowed_tools = ["session_controller.shutdown_after_current"]

The schema would accept it, and PolicyEngine could authorize a role agent to perform an operator-only command.

That violates AXIOM’s zero-trust boundary. Role manifests must not be able to express operator-control authority at all.


---

2. Architect Ruling

Decision A — Role manifests may not declare operator commands

For every manifest_type = "role":

"allowed_capabilities": {
  "operator_control": {
    "allowed_commands": []
  }
}

must be enforced.

No role manifest may declare:

"allowed_commands": ["status"]

or any other non-empty command list.

Decision B — Operator-control manifests must bind exactly one command

For every manifest_type = "operator_control":

"operator_command": {
  "command_name": "status"
}

must match:

"allowed_capabilities": {
  "operator_control": {
    "allowed_commands": ["status"]
  }
}

No operator-control manifest may declare more than one command, no different command, and no empty list.

Decision C — ManifestBinder enforces cross-field equality

Pure JSON Schema 2020-12 is not reliable for cross-field equality between operator_command.command_name and allowed_capabilities.operator_control.allowed_commands[0] without implementation-specific extensions.

Therefore the security boundary is enforced in two layers:

1. JSON Schema enforces role manifests have allowed_commands.maxItems = 0.


2. ManifestBinder enforces operator-control manifests have allowed_commands == [operator_command.command_name].



Failure at either layer blocks registration.


---

3. JSON Schema Patch

Add the following constraints to the manifest schema.

{
  "$defs": {
    "role_manifest": {
      "allOf": [
        {
          "properties": {
            "allowed_capabilities": {
              "properties": {
                "operator_control": {
                  "properties": {
                    "allowed_commands": {
                      "maxItems": 0
                    }
                  }
                }
              }
            }
          }
        }
      ]
    },
    "operator_control_manifest": {
      "allOf": [
        {
          "properties": {
            "allowed_capabilities": {
              "properties": {
                "operator_control": {
                  "properties": {
                    "allowed_commands": {
                      "minItems": 1,
                      "maxItems": 1
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}

This does not fully prove equality for operator-control manifests, but it prevents multi-command operator manifests and leaves only the single-command equality check to ManifestBinder.


---

4. ManifestBinder Registration Rule

ManifestBinder must run this validation before manifest fingerprint registration:

def validate_operator_control_binding(manifest: dict) -> None:
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

This validation happens before SHA256 registration. A manifest that fails this rule is never written into manifest_fingerprints.


---

5. Revised Tool Authorization Rule

The v1.11.2 tool authorization rule remains, with one added operator-control guard:

Tool is allowed only if:

1. tool_id ∈ allowed_tools
2. tool_id ∉ forbidden_tools
3. TOOL_CAPABILITY_MAP contains tool_id
4. mapped capability/policy check passes
5. all additional checks pass
6. if tool_id starts with "session_controller.", manifest_type must be "operator_control"

Otherwise deny and log policy denial.

This closes the remaining role-to-operator-control escalation path even if a future schema bug appears.


---

6. Redirect Policy Semantics

Decision

For:

"redirect_policy": "same_host_only"

“same host” means:

redirect target host must exactly equal the originally requested URL host

It does not mean:

same as the allowlist entry pattern

because AXIOM currently does not support wildcard allowlist hosts.

Canonical redirect evaluation

1. Original request must match allowlist.
2. Original request must not match denylist.
3. If redirect occurs:
   a. If redirect_policy = "deny", reject.
   b. If redirect_policy = "same_host_only":
        redirected URL scheme must be https
        redirected URL host must exactly equal original request host
        redirected URL port must equal original request port
        redirected URL path must still match the original allowlist path_prefix
        redirected request must not match denylist
4. Any ambiguity denies the request.

Explicit examples

Allowed:

https://api.search.brave.com/res/v1/web/search?q=test
→
https://api.search.brave.com/res/v1/web/search?q=test&page=2

Denied:

https://api.search.brave.com/res/v1/web/search?q=test
→
https://example.com/collect

Denied:

https://api.search.brave.com/res/v1/web/search?q=test
→
http://api.search.brave.com/res/v1/web/search?q=test

Denied:

https://api.search.brave.com/res/v1/web/search?q=test
→
https://api.search.brave.com/admin


---

7. commit_batch_id Lifecycle

Purpose

commit_batch_id identifies tasks inserted as part of one TaskCommitter atomic commit.

It exists to support auditability and rollback diagnostics for task-tree commits. It is not a scheduling primitive.

Lifecycle

Stage	Rule

Before TaskCommitter	commit_batch_id is NULL.
During TaskCommitter validation	Proposed child tasks exist only in memory; no database rows yet.
On successful commit	Every task inserted from the same approved plan artifact receives the same commit_batch_id.
On commit failure before insert	No task rows are written. Security/session event records failure.
On partial database failure	Transaction rolls back; no partial task tree remains.
After commit	commit_batch_id is immutable.


Format

Canonical format:

cb_<UTC timestamp compact>_<8 char random suffix>

Example:

cb_20260503T174233Z_a91f02bd

Database rule

commit_batch_id remains nullable because root operator-control tasks and pre-commit tasks may not have one.

Add index:

CREATE INDEX IF NOT EXISTS idx_tasks_commit_batch
    ON tasks(commit_batch_id);

Repository rule

Only TaskCommitter may write commit_batch_id.

StateMachine, Scheduler, agents, and tool executors may read it but may not mutate it.


---

8. Added Tests

Kimi v1.12 must add these tests:

test_role_manifest_rejects_nonempty_allowed_commands.py
test_operator_control_manifest_allowed_commands_matches_command_name.py
test_session_controller_tool_requires_operator_control_manifest.py
test_redirect_same_host_only_rejects_different_host.py
test_redirect_same_host_only_rejects_http_downgrade.py
test_redirect_same_host_only_rechecks_path_prefix.py
test_commit_batch_id_assigned_to_atomic_task_tree.py
test_commit_batch_id_immutable_after_insert.py

These are additive to the v1.11.2 test list.


---

9. Deferred Items for Critic / Constraints Reviewer

The following Evaluator-flagged items remain intentionally deferred because they are better reviewed by DeepSeek or Qwen:

Item	Routed to	Reason

scheduler_heartbeat retention	Qwen	Disk growth and runtime storage policy.
memory_items soft-deleted retention	Qwen	Long-term storage growth policy.
DB-level CHECK on tasks.manifest_id	DeepSeek / Architect if challenged	Defense-in-depth tradeoff; v1.11.2 already specifies StateMachine enforcement.
tool_capability_map.py fingerprinting	DeepSeek	Security-boundary hardening question.


These should be carried into Critic review as explicit attack points, not resolved silently here.


---

10. Final v1.11.3 Position

v1.11.3 resolves the Evaluator’s remaining pre-Critic blocker:

Evaluator item	v1.11.3 resolution

Role manifests can declare operator commands	Schema requires role allowed_commands.maxItems = 0; ManifestBinder rejects non-empty role commands.
Operator-control manifest command mismatch	Schema restricts to one command; ManifestBinder enforces allowed_commands == [command_name].
Session-controller tools usable from role manifests	Tool authorization adds session_controller.* requires manifest_type = operator_control.
same_host_only ambiguity	Defined as exact match to original request host, scheme, port, and allowlist path prefix.
commit_batch_id lifecycle missing	Defined as immutable TaskCommitter atomic commit identifier.


Chief Architect recommendation

Attach v1.11.3 as a targeted patch to v1.11.2.

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