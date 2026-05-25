# AXIOM Advisory Council Context Packet

Status: Active (standing reference)
Owner: Jeremy, Operator
Maintained by: Claude Code (Governance Auditor, AB-004)
Last verified: 2026-05-24

## Purpose

Prepend this packet to every advisory-council request (Kimi, Qwen, DeepSeek). Advisory members work in fresh web-chat sessions with no repository or live-spine access, so they cannot verify code or distinguish live governance from deprecated material. Supplying this context up front eliminates the drift observed during the OQ-001 dry run, where advisors — lacking it — missed code-truth findings, relied on deprecated constraints, and in one case approved a design that violated the fail-closed posture.

Do **not** include the auditor's own critique in an advisory packet: it causes advisors to echo the auditor rather than reason independently. Send the proposal under review plus this packet only.

## 1. Canonical operating posture (the intended steady state — not a defect to fix)

```
operational_mode   = fail_closed_non_autonomous
autonomous_allowed = False
safe_pass_enabled  = False
```

Every integrity mismatch (SHA256, manifest, model fingerprint, operator-control cross-field) fails closed by design. Do **not** treat fail-closed defaults, non-autonomy, or candidate model status as problems to be solved. AXIOM is local-first, fail-closed, and non-autonomous unless Jeremy explicitly approves a binding change (AB-002).

## 2. Live governance authority (cite only these as binding)

- Source of truth: `governance/01_live_spine/` (AB-008). Active bindings are **AB-001 … AB-016** in `AXIOM_Active_Bindings.md`.
- **CB-001 / CB-002 are DEPRECATED.** They exist only under `governance/07_deprecated_legacy/` and `docs/`, and carry no binding force unless Jeremy re-ratifies them into the live spine. Do not use them as design justification.
- `governance/06_archives/` and `governance/07_deprecated_legacy/` are historical/deprecated — not active governance.
- Advisory responses must be markdown, follow the advisory template, be named `YYYYMMDD_<Advisor>_Response_<QuestionID>.md` (AB-007), and are saved under `governance/03_advisory_council/` (AB-010).
- No advisor may convert advice into binding governance; that is Jeremy's sole authority (AB-001, AB-014).

## 3. Load-bearing code facts most often misread

- **Plan injection scanner** (`axiom/security/plan_injection_scanner.py`): with `safe_pass_enabled=False` (default), `scan()` returns `scanner_result = safe_pass_disabled` and routes the artifact to `quarantined` (high-risk) or `checkpoint_blocked` with `parent_task_status = needs_human_input` (ordinary). It returns `passed` **only** when `safe_pass_enabled=True`. Any gate keyed on `scanner_result == 'passed'` is unsatisfiable in the canonical posture. Disposition→task-status transitions are owned by `PlanArtifactScannerService`; do not propose a parallel gate.
- **State machine** (`axiom/core/state_machine.py`): purely *status*-based — 8 statuses (`pending, running, completed, failed, quarantined, needs_human_input, blocked_resource_limit, cancelled`); terminal states have empty transition sets. It has **no concept of task type/class**. Task typing lives in the `tasks` table (`task_class`, `task_type`, `chain_id`) and in agent `required_task_class`. Workflow chaining belongs in the scheduler/dispatcher, not the status FSM.
- **Agent layer** (`axiom/agents/`): `base.py::ManifestBoundAgentExecutor` is an **authorization gate only** (`_get_authorized_task`). The four executors (GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier) plus per-type **manual, operator-invoked** CLI harnesses (`tools/execute_*_task.py`) exist, but there is **no autonomous chaining** and no in-repo model execution wired into a pipeline. Activating autonomous chaining, real model calls, or scheduler→executor integration is **prohibited without Jeremy's explicit authorization.**
- **Model gateway** (`axiom/gateways/model_gateway.py`): every Ollama call is forced `think=False`; `qwen3:4b` stays `registration_status=candidate`, `is_current=0` by design.
- **plan_artifacts schema** (`axiom/persistence/schema.sql`): columns are `artifact_id, task_id, parent_task_id, artifact_type, artifact_status, commit_status, risk_class, scanner_result, checkpoint_verdict, artifact_json, scanner_details_json, checkpoint_details_json, manifest_id, created_at, updated_at`. There is **no `sha256` column**. Valid `artifact_status` values: `draft, scanner_passed, checkpoint_passed, checkpoint_failed, checkpoint_blocked, quarantined, committed` (`needs_human_input` is a task/parent status, not an artifact_status).

## 4. Active governance surface (directory map)

```
governance/
  01_live_spine/        AXIOM_Active_Bindings, _Open_Questions, _Decision_Log,
                        _Governance_Operating_Model, _Current_Context_Packet,
                        _Governance_Runbook, _Panel_Role_Charter   <- SOURCE OF TRUTH (AB-008)
  02_cli_surfaces/      per-CLI role adapters (e.g. claude_code/CLAUDE.governance.md)
  03_advisory_council/  advisory paste packets + responses + this packet
  04_decision_records/  formal decisions (AB-011)
  05_handoffs/          active panel draft proposals/reviews (AB-016)
  06_archives/          historical evidence — NON-binding (AB-013)
  07_deprecated_legacy/ deprecated chat-era material — NON-binding (AB-012)
```

Baseline schema marker: `v1.11.4`. Implementation baseline doc: `AXIOM_Implementation_v1.13.md`.

## 5. Maintenance

When the codebase or bindings change in ways that affect Sections 1–4, the Governance Auditor refreshes this packet and updates "Last verified." Facts here are verified by direct repository reads, not memory.
