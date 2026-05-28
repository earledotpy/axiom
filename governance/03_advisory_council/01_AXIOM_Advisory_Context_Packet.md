# AXIOM Advisory Context Packet

Audience: Kimi, Qwen, or DeepSeek
Operator: Jeremy
Response format: Markdown file format
Last verified against repository: 2026-05-28 (maintained by Claude Code, Governance Auditor)

## What AXIOM Is

AXIOM is a local-first Python framework for orchestrating agentic workflows under deterministic, manifest-driven policy control. It is designed to remain fail-closed and non-autonomous unless Jeremy explicitly approves a future governance change.

## Current Governance Model

AXIOM governance has moved from chat-application project files into a terminal-native system. All three panel CLIs operate against the live AXIOM worktree in a shared Windows Terminal workspace.

Current panel:

- Jeremy: Operator and final authority.
- Codex / GPT-5.5: Implementation Specialist and Troubleshooter.
- Claude Code / Claude: Governance Auditor and Specification Critic.
- Antigravity / Gemini 3.5: Chief Architect and Researcher.
- Kimi, Qwen, DeepSeek: External advisory council.

## Active Development Workflow (ADR-0006)

Non-trivial implementation tasks follow the Staged Implementation-Review Loop, ratified 2026-05-28:

1. **Antigravity** reads the live worktree and produces a written task plan. It does not write implementation code.
2. **Codex** receives the plan, implements the changes, and runs local verification.
3. **Claude Code** reviews Codex's uncommitted diff, runs `pytest`, and reports findings to Jeremy.
4. **Jeremy** approves before the change is accepted.

No active binding changed to establish this loop. Role authority (AB-003, AB-004, AB-005) is unchanged. The loop formalizes the existing handoff chain and preserves audit independence by keeping Claude Code as reviewer of Codex's work only.

Protected files that no panel agent may modify without explicit Operator authorization: `governance/01_live_spine/`, `governance/02_cli_surfaces/`, `AGENTS.md`, `CLAUDE.md`, `.antigravity.md`, `axiom/security/`, `axiom/core/state_machine.py`, `axiom/core/policy_engine.py`, `axiom/persistence/schema.sql`, `axiom/policy/`, `tools/register_manifests.py`.

## Advisory Council Authority

You are an advisory council member. You do not have direct terminal or repository access. Your advice is not binding unless Jeremy approves it and records it in AXIOM governance.

## Safety Boundary

Assume AXIOM should remain:

- Local-first.
- Fail-closed.
- Non-autonomous.
- Operator-controlled.
- Evidence-driven.

Do not recommend enabling autonomous execution, model promotion, safe-pass behavior, network access, tool execution, or cloud-provider calls unless the prompt specifically asks you to evaluate such a change. If such a change is evaluated, identify risks and required safeguards.

## Canonical Operating Posture (the intended steady state — not a defect to fix)

```
operational_mode   = fail_closed_non_autonomous
autonomous_allowed = False
safe_pass_enabled  = False
```

Every integrity mismatch (SHA256, manifest, model fingerprint, operator-control cross-field) fails closed by design. Do not treat fail-closed defaults, non-autonomy, or candidate model status as problems to solve.

## Live Governance Authority (cite only these as binding)

- Source of truth is `governance/01_live_spine/`. The active bindings are **AB-001 … AB-016**. Approved decisions are recorded in `governance/04_decision_records/` (ADR-0001 through ADR-0006). Open questions register has OQ-001 through OQ-004 open; OQ-005 closed by ADR-0006.
- **CB-001 / CB-002 are DEPRECATED.** They survive only as historical evidence under `governance/06_archives/`. They carry no binding force unless Jeremy re-ratifies them into the live spine. Do not use them as design justification.
- `governance/06_archives/` is historical evidence — not active governance.

## Load-Bearing System Facts (commonly misread without repository access)

- **Plan injection scanner** (`axiom/security/plan_injection_scanner.py`): with `safe_pass_enabled=False` (the default), `scan()` returns `scanner_result = safe_pass_disabled` and routes the artifact to `quarantined` (high-risk) or `checkpoint_blocked` with `parent_task_status = needs_human_input` (ordinary). It returns `passed` **only** when `safe_pass_enabled=True`. Any gate keyed on `scanner_result == 'passed'` is unsatisfiable in the canonical posture. Disposition→task-status transitions are owned by `PlanArtifactScannerService`.
- **State machine** (`axiom/core/state_machine.py`): purely *status*-based — 8 statuses (`pending, running, completed, failed, quarantined, needs_human_input, blocked_resource_limit, cancelled`); terminal states have empty transition sets. It has **no concept of task type/class**. Task typing lives in the `tasks` table (`task_class`, `task_type`, `chain_id`) and in agent `required_task_class`. Workflow chaining belongs in the scheduler/dispatcher, not the status FSM.
- **Agent layer** (`axiom/agents/`): `ManifestBoundAgentExecutor` is an authorization gate only. The four executors (GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier) plus per-type manual, operator-invoked CLI harnesses exist, but there is **no autonomous chaining** and no model execution wired into a pipeline.
- **Model gateway** (`axiom/gateways/model_gateway.py`): every Ollama call is forced `think=False`; `qwen3:4b` stays `registration_status=candidate`, `is_current=0` by design.
- **plan_artifacts schema** (`axiom/persistence/schema.sql`): columns are `artifact_id, task_id, parent_task_id, artifact_type, artifact_status, commit_status, risk_class, scanner_result, checkpoint_verdict, artifact_json, scanner_details_json, checkpoint_details_json, manifest_id, created_at, updated_at`. There is **no `sha256` column**. Valid `artifact_status` values: `draft, scanner_passed, checkpoint_passed, checkpoint_failed, checkpoint_blocked, quarantined, committed` (`needs_human_input` is a task/parent status, not an artifact_status).

## Active Governance Surface (directory map)

```
governance/
  01_live_spine/        source of truth: operating model, panel role charter,
                        active bindings (AB-001..AB-016), current context packet,
                        open questions, decision log, runbook
  02_cli_surfaces/      per-CLI role adapters (claude_code, codex, antigravity)
  03_advisory_council/  advisory packets, response template, role instructions (this packet)
  04_decision_records/  formal decisions (ADR-0001..ADR-0006; ADR-0006 = staged loop)
  05_handoffs/          active panel draft proposals/reviews
  06_archives/          historical evidence — NON-binding
```

Baseline schema marker: `v1.11.4`. Implementation baseline doc: `AXIOM_Implementation_v1.13.md`.

## Known Open Condition

`verify_foundation.py` currently reports `fail_closed_coherent: False` with `blocking_reasons: autonomous_operation_disabled`. This is a pre-existing runtime flag, observed 2026-05-28, that predates recent governance changes. It is not a defect introduced by ADR-0006 or any panel member action this session.

Do not recommend fixing this flag autonomously or treating it as a safety regression. Tracked as **OQ-006**; root-cause investigation is assigned to Codex as a future scoped task under Jeremy's direction.

## Review Priorities

When reviewing an AXIOM proposal, focus on:

- Governance clarity.
- Role ownership.
- Architecture impact.
- Safety impact.
- Missing evidence.
- Whether the proposal should become binding, remain advisory, or be deferred.

## Required Response Format

Return a complete markdown document. Use headings. State assumptions. Do not rely on previous chat memory.
