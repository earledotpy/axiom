# Advisory Review: OQ-005 — Shared Pool Implementation Model

**Advisor:** Kimi  
**Date:** 2026-05-27  
**Requested by:** Jeremy  
**Recommended disposition:** Defer (pending pre-conditions)

## Summary

The proposal to transition AXIOM implementation authority from a single agent (Codex) to a shared pool (Codex, Claude Code, Antigravity) addresses a legitimate operational bottleneck—API rate-limiting stalling active development. However, the current proposal lacks sufficient safeguards to prevent audit compromise, architectural design drift, and accidental governance modification. Expanding write access across the entire codebase without domain partitioning, concurrency controls, or audit-rotation protocols would materially weaken the fail-closed, evidence-driven governance model. I recommend deferring binding adoption until mandatory pre-conditions are defined and accepted by the panel.

## Assumptions

- **Current role bindings** (AB-003, AB-004, AB-005) assign implementation authority exclusively to Codex, audit authority to Claude Code, and architecture/research to Antigravity, as reflected in the panel charter.
- The canonical operating posture remains unchanged: `operational_mode = fail_closed_non_autonomous`, `autonomous_allowed = False`, `safe_pass_enabled = False`.
- All agent activity is operator-invoked (Jeremy); the proposal does not introduce autonomous agent dispatch or self-scheduling.
- The local repository is the single source of truth for code state, with no intermediate merge queue or CI/CD pipeline currently protecting it from concurrent edits.
- The `governance/01_live_spine/` directory and security-critical modules (`axiom/security/`, `axiom/core/state_machine.py`) must retain tamper-evident integrity under all operating conditions.

## Findings

- **Rate-limiting is a material constraint.** Codex stalling under active load is a real risk to delivery timelines. A shared pool is a plausible operational mitigation.
- **Role boundaries dissolve without a replacement coordination protocol.** The current specialist model (one implementer, one auditor, one architect) provides clear accountability. The proposal replaces it with a peer pool but does not define how conflicts, sequencing, or ownership are resolved.
- **Audit independence is structurally compromised.** Claude Code serves as the Governance Auditor. Granting Claude Code implementation authority creates a conflict of interest: an agent cannot provide impartial audit of artifacts it authored or modified. This undermines the evidence-driven requirement.
- **No concurrency control is specified.** The AXIOM agent layer (`axiom/agents/`) has no autonomous chaining and no multi-agent task dispatch. Three independent CLI surfaces writing to the same local repository risk merge conflicts, partial writes, or manifest corruption. The state machine’s `blocked_resource_limit` and `needs_human_input` statuses do not address multi-agent file collisions.
- **Governance and security files are exposed.** Without explicit carve-outs, any implementation agent could modify `governance/01_live_spine/`, the plan injection scanner, the model gateway, or the state machine. Because `safe_pass_enabled = False` by default, an integrity mismatch in these modules would fail closed and potentially stall all operations.
- **Quality control is advisory, not enforced.** The proposal updates CLI instructions (`AGENTS.md`, `CLAUDE.md`, `.antigravity.md`) but does not establish an automated, protected linting or style gate. Inconsistent indentation, import style, and exception hierarchies will degrade maintainability.
- **The proposal conflates capability with authority.** All three agents already possess the *capability* to generate code. The question is whether they should possess the *authority* to commit and build across all domains without additional gating.

## Risks

- **Architectural design drift.** Three agents with different training corpora and optimization targets will make divergent architectural decisions (module boundaries, exception patterns, data flow). Over time this produces technical debt and increases the probability of integrity mismatches.
- **Reliability degradation from edit collisions.** Concurrent or interleaved file modifications in the local working tree risk clobbering changes, breaking manifests, or leaving the repository in an unbuildable state. Recovery would require manual operator intervention.
- **Audit capture (performative review).** If Claude Code implements and then audits (or if another agent rubber-stamps Claude Code’s work), the audit function becomes ceremonial. Unsafe changes to security scanners, governance bindings, or the state machine could pass review without genuine scrutiny.
- **Safety boundary creep.** Expanding implementation surface area increases the chance of accidental modification of fail-closed logic. The plan injection scanner, model gateway (`think=False` enforcement), and governance bindings are high-consequence targets that should not be exposed to routine multi-agent editing.
- **Style and structural fragmentation.** Without automated enforcement, code quality will degrade. Each agent will apply its own conventions, making future audits, diffs, and maintenance harder and increasing the risk of subtle bugs (e.g., relative vs. absolute import errors).
- **Operator cognitive load increase.** Jeremy must now track which agent modified which file, in what order, and whether audit rotation was respected. This shifts operational burden from the agent layer to the operator.

## Recommendation

**Defer binding adoption.** The Shared Pool model should not become active governance until the following pre-conditions are implemented and verified:

1. **Domain partitioning.** Assign non-overlapping implementation domains to each agent (e.g., Codex owns task scheduling and build scripts; Antigravity owns model gateways and research modules; Claude Code is excluded from routine implementation). No agent should have default write access to the entire repository.
2. **Governance and security carve-out.** Explicitly prohibit all implementation agents from modifying `governance/01_live_spine/`, `axiom/security/`, `axiom/core/state_machine.py`, and `axiom/persistence/schema.sql`. These remain under single-agent (Codex) or operator-only control with mandatory cross-agent audit.
3. **Audit rotation protocol.** Claude Code must never audit commits for which it was an author or co-author. A second, non-implementing agent (or Jeremy) must audit Claude Code’s work. All audit assignments must be logged in `governance/04_decision_records/`.
4. **Protected automated quality gate.** Introduce a linting and style gate (enforcing 4-space indentation, explicit absolute imports, domain-specific exception hierarchies) that runs before any build. The gate configuration itself must be protected from modification by implementation agents without Jeremy approval.
5. **Concurrency convention.** Establish a technical mechanism to prevent simultaneous edits (e.g., per-agent git branches, a lockfile protocol, or strict serial operator invocation). The state machine or scheduler should be able to detect and surface collision states.

If these pre-conditions are met, the Shared Pool can be piloted on a limited domain with a sunset clause and reviewed after a defined number of commits or a fixed time period.

## Binding Impact

**Should this become AXIOM binding governance?**

**Answer:** Not yet.

**Reason:** The proposal identifies a real operational problem but its current form introduces governance risks that exceed the operational pain it seeks to solve. The erosion of audit independence, the absence of concurrency controls, and the exposure of governance-critical files to multi-agent modification would weaken the fail-closed, evidence-driven model. Binding adoption is appropriate only after domain partitioning, audit rotation, and protected quality gates are implemented, tested, and recorded in the live spine.

## Questions For Jeremy

1. **Domain scope:** Can you define specific, non-overlapping repository domains for each agent rather than granting all three full codebase access?
2. **Audit rotation:** Are you willing to enforce that Claude Code never audits its own commits? If so, which agent (or process) will audit Claude Code’s implementation work?
3. **Concurrency mechanism:** What technical mechanism (git branches, lockfiles, or strict serial invocation) will prevent simultaneous file modifications by multiple CLI surfaces?
4. **Governance protection:** Will you explicitly carve out `governance/01_live_spine/` and `axiom/security/` from the shared pool, leaving them under Codex-only or operator-only control?
5. **Quality automation:** Do you have an automated style/lint gate that is itself protected from agent modification, or is building that gate part of the proposed implementation work?
