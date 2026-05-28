# Advisory Review: OQ-005 (Shared Pool Implementation)

Advisor: Qwen
Date: 2026-05-27
Requested by: Jeremy
Recommended disposition: Advisory only

## Summary

The transition from a single-agent implementation model to a shared pool across Codex, Claude Code, and Antigravity addresses a documented operational constraint (API rate-limiting) but introduces non-trivial architectural and governance complexities. While operationally justified, this shift requires strict serialization controls, automated quality gates, and preserved audit separation to prevent design drift, concurrency conflicts, and erosion of AXIOM's fail-closed posture. The proposal should proceed only after implementing explicit technical and procedural safeguards.

## Assumptions

- AXIOM's canonical operating posture (`fail_closed_non_autonomous`, `safe_pass_enabled=False`) remains unchanged and will govern all artifact processing.
- All three agents operate exclusively via terminal-native CLI surfaces with explicit operator invocation; no inter-agent messaging or autonomous chaining is introduced.
- The existing `plan_injection_scanner` and state machine workflows will continue to route all artifacts through deterministic, manifest-driven gates.
- Jeremy retains final approval authority for binding governance updates and repository merges.

## Findings

1. **Risk Analysis (Architectural, Reliability, Design-Drift):** Granting concurrent write access across a single repository introduces race conditions, merge conflicts, and potential corruption of tightly coupled modules (e.g., `axiom/core/state_machine.py`, `axiom/persistence/schema.sql`). Without a serialization or task-locking mechanism, parallel modifications may yield silent integration failures. Architectural drift is highly probable if domain-specific conventions (exception handling, import structures, module boundaries) are not enforced programmatically. Mitigation requires file-scope ownership matrices, atomic commit policies, and a mandatory pre-merge validation gate.

2. **Quality & Style Control:** Reliance on textual guidelines is insufficient for multi-agent consistency. AXIOM must enforce machine-readable style and structural rules via a unified linter/formatter configuration (e.g., `ruff`, `isort`, `black`) integrated into the build pipeline. Explicit absolute imports, 4-space indentation, and domain-specific exception patterns must be codified as CI/CD or scanner-level checks. A pre-commit hook or terminal CLI validation step should reject non-compliant artifacts before they enter the state machine, ensuring that stylistic degradation does not compromise maintainability.

3. **Audit Integrity:** Assigning implementation authority to Claude Code while retaining its Governance Auditor charter creates a structural conflict of interest. Audit independence cannot be maintained if an agent validates its own commits. To preserve integrity, AXIOM must implement a cross-validation exclusion rule: Claude Code is prohibited from auditing artifacts it authored or modified. Alternatively, implementation authority for Claude Code should be restricted to non-governance, non-core architecture files, preserving its primary auditor function for critical system components. Formalizing this constraint in the updated Panel Role Charter is mandatory.

4. **Safety Implications:** Expanding implementation authority does not inherently violate AXIOM's local-first, fail-closed, or non-autonomous boundaries, provided the following conditions hold: (a) no agent is granted autonomous execution, network access beyond the local Ollama gateway, or safe-pass routing; (b) all artifacts are processed through the existing `plan_injection_scanner` with `safe_pass_enabled=False`, ensuring high-risk outputs are quarantined and ordinary outputs are routed to `checkpoint_blocked` pending human input; and (c) CLI surfaces are explicitly configured to require operator invocation for each discrete task. The primary safety risk is implicit autonomy if CLI adapters are misconfigured to chain tasks or bypass the manifest-driven workflow. Strict adherence to the existing state machine and artifact disposition logic must be preserved without exception.

## Risks

- Concurrent file modification leading to unstable repository states and corrupted schema definitions.
- Gradual erosion of architectural consistency without enforced, automated linting and structural validation gates.
- Compromised audit trail due to role conflation for Claude Code, reducing governance oversight effectiveness.
- Potential drift toward implicit autonomy if CLI surfaces or scheduler logic inadvertently enable task chaining or bypass human-in-the-loop checkpoints.

## Recommendation

Approve the shared pool model conditionally, contingent upon the implementation of the following safeguards prior to binding ratification:
1. Establish explicit file-scope ownership and task-locking conventions to prevent concurrent modification conflicts.
2. Integrate a unified, machine-readable linter/formatter configuration as a mandatory pre-commit or scanner validation gate.
3. Implement a cross-validation exclusion rule for Claude Code to preserve audit independence, or restrict its implementation scope accordingly.
4. Codify these constraints in updated bindings (`AB-003`, `AB-004`, `AB-005`), the Panel Role Charter, and CLI surface documentation.
5. Maintain strict adherence to the canonical `plan_injection_scanner` workflow and state machine transitions, ensuring all artifacts require explicit operator input before proceeding.

## Binding Impact

Should this become AXIOM binding governance?

Answer: Yes (conditional)

Reason: The operational necessity of mitigating rate-limit bottlenecks justifies the architectural shift, but the expansion of implementation authority fundamentally alters role boundaries and repository access patterns. Formalizing the shift as binding governance is required to prevent uncontrolled design drift, provided that the recommended serialization, quality enforcement, and audit separation safeguards are ratified concurrently.

## Questions For Jeremy

- Should AXIOM formalize a file-scope ownership matrix or task-locking mechanism to prevent concurrent modification conflicts across the three agents during active development cycles?
- Do you prefer to enforce a strict cross-audit exclusion rule (where Claude Code cannot validate its own commits) or restrict Claude Code's implementation scope to preserve its independent auditor function over core architecture files?