# OQ-005: Claude Code Pivot Feasibility Determination — Unified Local CLI Orchestrator

**Auditor**: Claude Code  
**Date**: 2026-05-27  
**Document under review**: `governance/05_handoffs/AI Agent CLI Research Plan.md`  
**Related thread**: OQ-005 (Shared Pool Implementation Model)  
**Role lens**: Governance Auditor and Specification Critic  

---

## What "the pivot" is

OQ-005 began as a *governance role* change: grant Codex, Claude Code, and Antigravity shared implementation authority inside AXIOM to relieve Codex rate-limit stalls. That draft was assessed `defer` by all three advisory council members, by the Claude Code audit, and by the Codex feasibility check.

The "AI Agent CLI Research Plan" pivots away from a role reassignment to a **technical build**: a unified local orchestrator that drives the three vendor CLIs (Claude Code, Codex, Antigravity) via PTY automation under flat-rate consumer subscriptions, in headless auto-approve loops, to bypass per-token API billing.

Same root problem (rate limits / cost). Fundamentally different — and far larger — mechanism.

---

## The determination cannot be made until one question is answered

The document never states its relationship to AXIOM. It carries no QuestionID, no panel-member byline, does not follow the Runbook proposal format, and does not mention AXIOM anywhere. Feasibility is undefined until Jeremy disambiguates which of these is intended:

| Interpretation | What it means | Feasibility |
| --- | --- | --- |
| **(a) Replace** | The orchestrator supersedes AXIOM | Outside Claude Code's audit scope — this is an Operator direction-setting decision, not a governance change to audit. See note below. |
| **(b) Inside** | Built within AXIOM, under its governance and runtime posture | **Not feasible.** Directly contradicts AXIOM's core invariants (detailed below). |
| **(c) Alongside** | A separate project that coexists with AXIOM | Technically constructible, but blocked by Terms-of-Service violation (detailed below), and out of scope for AXIOM governance except where it touches this repo. |

**"Is the pivot feasible?" cannot be answered as "yes" or "no" — it is "feasible for what?"** This document does not say. That ambiguity is itself the first finding.

If the intent is (a) — replacing AXIOM with a system built on the opposite safety philosophy — that is a strategic decision reserved to the Operator (AB-001). Claude Code's role is to flag it as such, not to audit it as if it were an AXIOM change.

---

## Finding 1 — As an AXIOM-internal build (interpretation b), the plan triggers the explicit prohibition list

`CLAUDE.md` enumerates items that may not be implemented, enabled, *or even test-driven* without Jeremy's explicit authorization. The plan triggers, at minimum, five of them:

| Prohibited item | Where the plan invokes it |
| --- | --- |
| Autonomous operation | "highly autonomous multi-agent development workflow"; the Ralph Loop; `lauren vibe` continuous background loop (§4.1, Lauren, Strategic Recommendations) |
| The agent layer | The orchestrator *is* a multi-agent control plane (entire document) |
| A persistent scheduler service | "local background daemon"; "continuous background loop" (§2.1, §4) |
| Automatic scheduler→executor integration | Supervisor-worker auto-routing; Handoff/Assign/Send primitives (§ orchestrators, §4.1) |
| Real cloud model calls | Claude Code, Codex, and Antigravity are all cloud-backed models |

AXIOM's foundational guarantee is the inverse of this plan: *no tool runs unless a signed, schema-validated manifest authorizes it*, and the healthy steady state is `autonomous_allowed = False`. The plan's design goal is headless auto-approval (`--full-auto`, `approval_policy = "never"`, `--dangerously-skip-permissions`) and unattended loops. These are not reconcilable. Making the plan fit interpretation (b) would require dismantling AXIOM's core identity, not amending a binding.

---

## Finding 2 — Independent of governance, the plan's central mechanism breaches platform Terms of Service

This is a **separate block** from the governance finding and stands even if AXIOM's invariants were not in play.

The document's own "Mitigating the Risk of Telemetry Bans" section states:

- "Anthropic actively blocks accounts that route automated programmatic traffic through consumer Claude.ai web sessions via unofficial tools."
- "Antigravity terms explicitly state that using third-party wrapper software or tools to access the service is a breach of the agreement and may result in account termination."

The plan's premise — programmatically driving consumer flat-rate subscriptions to bypass API billing — is the conduct those terms prohibit. The proposed mitigation — "add randomized delays between execution phases to simulate human developer speeds" — is **detection evasion** intended to avoid the platforms' enforcement.

As the Governance Auditor running as Claude Code, I decline to recommend implementing detection-evasion against the Terms of Service of the platform AXIOM and this panel run on. This applies regardless of how the prior question is disambiguated. The operational risk is also concrete: account termination would remove the very capacity the plan is trying to preserve.

---

## Finding 3 — The document is not yet a proposal under the governance standard (AB-015)

Even setting aside the two blocks above, the document does not meet the bar to enter the decision workflow:

- It does not answer the Runbook "Proposal Format" questions (what decision is requested, what files/bindings/runtime are affected, binding vs. advisory vs. implementation, what evidence supports it, who owns the next step).
- Per AB-015, evidence must be separated from assumption. The document presents AI-generated survey content — including citation-paste artifacts (e.g., `[span_44](start_span)`), internally inconsistent claims (default model stated as "Claude 4.6 Sonnet" in one section and "Claude 3.5 Sonnet" in another), and unverified third-party framework descriptions — as established fact. This is a category-level evidence problem, not a list of individual errors to debunk.

It is reading material / research input, not a decision-ready proposal. Treating it as the latter would skip the evidence-separation discipline the panel relies on.

*Inference (labeled per AB-015):* my judgment is that the document was generated by an external model survey and pasted in without panel adaptation. The lack of byline and QuestionID supports this but does not prove it.

---

## Finding 4 — AB-016 naming (minor, non-blocking)

The file `AI Agent CLI Research Plan.md` does not follow the `<QuestionID>_<PanelMember>_<DocType>.md` convention required for handoff artifacts. Recommend renaming if it is retained in the handoff record.

---

## Relationship to the existing OQ-005 disposition

This is **not** the narrow pilot the panel recommended. The Codex feasibility check and the advisory council pointed toward a *smaller* scope: `OQ-005A` — a bounded Codex + Antigravity implementation pilot, Claude Code retained as auditor, protected-file carve-outs, a verification gate. The research plan moves in the opposite direction: a *larger*, autonomous, permission-bypassing, ToS-evading system. It does not respond to the deferral feedback; it changes the subject.

---

## Recommended Disposition

Claude Code recommends one of the following, depending on Jeremy's intent:

1. **If this is meant to live inside or be built by AXIOM (interpretation b):** **Reject.** It is governance-infeasible (Finding 1) and ToS-infeasible (Finding 2). No precondition set can reconcile it with AXIOM's fail-closed, non-autonomous, manifest-gated identity without abandoning that identity.

2. **If this is a strategic question about replacing AXIOM (interpretation a):** **Return to Operator.** This is a direction-setting decision reserved to Jeremy under AB-001, not a governance change for Claude Code to audit. Claude Code's only finding here is that adopting a subscription-bypass, auto-approval orchestrator would be philosophically opposite to AXIOM's reason for existing, and would carry the ToS exposure in Finding 2.

3. **If this is exploratory research only (interpretation c or "just reading"):** **Advisory / no action.** Retain as research input, rename per AB-016, and do not route it into the decision workflow until it is rewritten as a proper proposal that answers the Runbook format questions and separates evidence from assumption (Finding 3).

In all three cases, the rate-limit problem that motivated OQ-005 remains open and is better served by the previously-recommended `OQ-005A` narrow pilot than by this pivot.

---

## Open Questions for Jeremy

1. **Discriminator question:** Is this orchestrator intended to replace AXIOM, be built inside AXIOM, or run as a separate project? The feasibility answer depends entirely on this.
2. Are you willing to operate consumer subscriptions in a way the Anthropic and Google terms (per the document itself) describe as account-terminating conduct?
3. If the goal is purely rate-limit relief, should the panel return to the recommended `OQ-005A` narrow pilot rather than this broader build?

---

*Filed by Claude Code as Governance Auditor per AB-004 and CLAUDE.governance.md.*  
*Determination: feasibility is conditional on the discriminator question; as an AXIOM-internal build it is not feasible.*
