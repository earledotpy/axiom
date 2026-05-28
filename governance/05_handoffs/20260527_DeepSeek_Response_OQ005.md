# Advisory Review: OQ-005 – Shared Pool Implementation Model

Advisor: DeepSeek  
Date: 2026-05-27  
Requested by: Jeremy  
Recommended disposition: **Defer until audit‑independence, quality‑control, and safety‑enforcement mechanisms are concrete and binding**

## Summary

The proposal would expand implementation authority from Codex alone to a shared pool of Codex, Claude Code, and Antigravity, intending to mitigate rate‑limit bottlenecks.  While the operational rationale is understandable, the change creates immediate governance risk by putting the Governance Auditor (Claude Code) into an implementer role, blurs the Architect/implementer boundary, and introduces code‑drift and safety‑surface risks that must be fully addressed before this can become binding governance.

## Assumptions

- The three terminal agents operate against different API backends (OpenAI, Anthropic, Google) – otherwise the rate‑limit mitigation is ineffective.  
- The operator (Jeremy) will still review and approve every change before it lands in the main branch.  
- The AXIOM runtime (safety boundary, fail‑closed posture, non‑autonomy) cannot be altered by any agent without explicit operator approval; the proposal does **not** grant autonomy.  
- The existing governance definitions (AB‑003, AB‑004, AB‑005) are the only bindings that would be modified; no other live‑spine documents are touched.  
- The agents will only execute pre‑defined CLI harnesses; they will not be given direct terminal access beyond what the operator observes.

## Findings

1. **Audit independence is fatally compromised**  
   AB‑004 designates Claude Code as Governance Auditor.  If Claude Code also implements code, it cannot audit its own changes without an irreconcilable conflict.  The proposal asks “how can we maintain audit independence?” but offers no mechanism.  Simply declaring independence is not sufficient; structural separation is required.

2. **Style and quality drift are likely without automated enforcement**  
   Three independent agents, each with distinct “personalities,” will produce inconsistent idioms unless strict, machine‑enforced rules are in place.  The proposal mentions updating AGENTS.md, but advisory guidelines are not enforcement.

3. **Architect/implementer boundary erodes**  
   AB‑005 makes Antigravity the Chief Architect and Researcher.  Giving Antigravity blanket implementation authority risks diluting the architectural‑oversight function – the same mind that designs may bias towards implementation shortcuts.

4. **Safety surface expands silently**  
   Although the runtime remains fail‑closed and non‑autonomous, every new line of code written by an agent could inadvertently introduce a dependency, a network call, or a logical path that weakens the boundary.  With three writers, the burden of review on the operator grows, increasing the chance that a violation slips through.

5. **Rate‑limit mitigation may be incomplete**  
   If the bottleneck is a single API endpoint (e.g., the same OpenAI organisation), adding more agents won’t help.  The proposal does not confirm that the three agents use separate rate‑limit pools.

## Risks

- **Governance decay:** The auditor implementing code destroys the credibility of future audits.  An attacker or bug could later leverage an auditor‑authored change that passes audit by default.  
- **Design fragmentation:** Without a single implementation steward, the codebase may develop competing patterns, making maintenance and security reasoning harder.  
- **Inadvertent autonomy:** A seemingly innocent helper function added by an agent could bypass the non‑autonomous guard if the operator misses it during review.  
- **Operator overload:** Tripling the number of change sources without a corresponding increase in automated gating increases the risk of operator fatigue and oversight failure.

## Recommendation

**Defer** the binding governance changes until the following concrete safeguards are designed, documented, and accepted by Jeremy:

- **Separate audit from implementation:**  
  Either Claude Code remains auditor‑only (no implementation authority), or a new dedicated auditor role is created for all changes that Claude Code authored.  The governance bindings must explicitly forbid Claude Code from auditing its own commits.

- **Automated quality gates:**  
  Pre‑commit / CI hooks that enforce style (e.g., Black, isort, mypy), architectural rules (e.g., no `import requests` outside approved modules), and safety lints (e.g., `bandit` for high‑risk patterns) must run on every proposed change from any agent and block merging on violation.

- **Explicit safety test suite:**  
  Every agent‑authored change must pass a “non‑autonomy” test suite that verifies the canonical posture (fail‑closed, local‑only, no network side‑effects) remains intact.

- **Architectural oversight role preserved:**  
  Antigravity may implement, but all structural changes (new modules, new dependencies, new API surfaces) must carry an architectural‑approval sign‑off from the Architect function – which could be Antigravity itself, but the decision must be recorded separately from the implementation commit.

- **Rate‑limit root‑cause verification:**  
  Confirm that the rate‑limit bottleneck is truly per‑agent and cannot be solved by adjusting the existing Codex‑only workflow (e.g., retry logic, queuing).  If all agents share the same underlying API quota, the proposal gives no benefit.

## Binding Impact

Should this become AXIOM binding governance?

Answer: **Not yet**

Reason:  
The proposal creates a material governance risk by dissolving the separation between the Governance Auditor and implementers, and it lacks any concrete enforcement mechanism for code quality, style, architecture, or safety.  Until those gaps are closed with mandatory, automated, and tested safeguards, making this binding would lower the overall security posture of AXIOM.

## Questions For Jeremy

- Do the three agents (Codex, Claude Code, Antigravity) use completely separate API subscriptions / rate‑limit pools, or could the bottleneck simply shift to a shared quota?  
- Is the implementation bottleneck currently on Codex’s *thinking* capacity (i.e., too slow to plan/build) or only on raw API rate‑limits?  If the former, parallelisation may not be the right lever.  
- Would you consider a narrower variant where only Codex and Antigravity gain implementation authority, while Claude Code remains the pure auditor, as an acceptable mitigation for rate limits?  
- What, if any, automated enforcement (linting, test suites, architectural fitness functions) do you plan to require before an agent‑authored change can be merged?