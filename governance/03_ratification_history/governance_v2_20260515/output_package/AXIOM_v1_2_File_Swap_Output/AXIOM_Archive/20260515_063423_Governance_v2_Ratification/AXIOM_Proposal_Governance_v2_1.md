# AXIOM_Proposal_Governance_v2_1.md
## Cycle 2 Charter Amendment Proposal Revision — Panel Operating-Model Restructuring

**Document Type:** Formal Governance Amendment Proposal  
**Status:** Proposed — Cycle 2 revision for panel review  
**Authoring Role:** GPT-5.5 — Chief Architect  
**Date:** 2026-05-12  
**Subject:** Charter v1.1 → proposed Charter v1.2 operating-model amendment  
**Primary Source Framework:** `AXIOM_Panel_Restructuring_Amendment_Framework.md`  
**Operative Governance at Entry:** Charter v1.1, Core Values v1.1, Constraints Register v1.1, Active Bindings v1.1  
**Reviewing Panel:** Current six-member Charter v1.1 panel operating under current roles until this amendment is ratified; Cycle 2 review follows the Synthesis-authorized closure route  

---

## §0 Closure Map

Cycle 2 revision entry records every Cycle 1 objection, condition, and closure item identified in `AXIOM_Synthesis_Governance_v2_Cycle1.md` §3.1, §10, and §14.1. This table uses the Objection Disposition Matrix schema established under Charter v1.1. Cycle 1 specification-debt items remain `Open — cycle 1 of 2`; this revision records where each item is addressed or routed, not a same-cycle closure of the debt ledger.

| Item ID | Source | Required Closure | Proposal Section | Disposition | Notes |
|---|---|---|---|---|---|
| D-C1 | DeepSeek Critique Cycle 1 §7 / Synthesis §10.1 | Add architectural trigger requiring full Advisory Council review for proposals modifying AXIOM system architecture. | §7.8; §9; §14 | Closed in this revision. | Adopted as load-bearing structural correction. Evaluator may not rule architectural triggers not engaged. |
| D-C2 | DeepSeek Critique Cycle 1 §6 / Synthesis §10.1 | Add Shared-Drive content sanitization and access-control rule. | §12.6; §12.7; §14 | Closed in this revision. | Also closes Evaluator E-C3 at proposal-text level by defining the shared-document security boundary. |
| D-C3 | DeepSeek Critique Cycle 1 §9 / Synthesis §10.1 | Add advisory access to in-progress work and missed-trigger objection path. | §7.9; §8.7; §14 | Closed in this revision. | Advisory access compliance added to Synthesis requirements. |
| D-C4 | DeepSeek Critique Cycle 1 §9 / Synthesis §10.1 | Add affirmation deadlock breaker for future Disputed AB outcomes. | §11.5; §11.7 | Closed in this revision. | Cycle 1 produced no Disputed AB items; rule is preventive for future affirmation cycles. |
| D-C5 | DeepSeek Critique Cycle 1 §9 / Synthesis §10.1 | Add mandatory PDR Clearance Cross-Check in Synthesis. | §8.6; §14 | Closed in this revision. | Synthesis without the cross-check table is incomplete. |
| E-C1 | Evaluator Review Cycle 1 §1.1 / Synthesis §10.2 | Clarify “all six panel members” means all six regardless of tier classification. | §7.5 | Closed in this revision. | Applies post-ratification as well as during this amendment cycle. |
| E-C2 | Evaluator Review Cycle 1 §1.3 / Synthesis §10.2 | Confirm AB-001 through AB-007 Maintaining Authority remains Gemini until file-swap completes; add extended-schema sample rows. | §10.3; §10.9; §15.3 | Closed in this revision. | Transition recorded at file swap; Kimi does not become Maintaining Authority merely by affirmation. |
| E-C3 | Evaluator Review Cycle 1 §2 / Synthesis §3.1 | Define continuous-layer shared-document security model. | §12.6; §12.7 | Closed in this revision. | Uses local-model sanitization lane under CV2 §7.1; Drive-only documents are non-authoritative. |
| E-C4 | Evaluator Review Cycle 1 §2 / Synthesis §10.1 | Constrain Evaluator “trigger not engaged” clearance authority. | §8.5; §7.9 | Closed in this revision. | Claims inside advisory domains route to advisory consultation or specification debt, not unilateral clearance. |
| E-C5 | Evaluator Review Cycle 1 §5.1 / Synthesis §10.2 | Require verbatim quote or explicit hash/character-count for “Current Binding Text Preserved?” | §11.4 | Closed in this revision. | Prevents bare Yes/No affirmation. |
| K-CLOSURE-1 | Kimi IS Review Cycle 1 §2.1 / Synthesis §10.2 | Add `AXIOM_Panel_Tier_Membership.md` to Canonical Filenames Registry and specify update mechanism. | §15.5; §15.9 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Update requires Charter amendment or governance binding. |
| K-CLOSURE-2 | Kimi IS Review Cycle 1 §3.1 / Synthesis §10.2 | Add operator trigger-detection checklist with keyword/pattern examples. | §7.7; §7.8; §8.7 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Coordinates ordinary domain triggers with architectural trigger. |
| K-CLOSURE-3 | Kimi IS Review Cycle 1 §4 / Synthesis §10.2 | Specify Drive fallback and mobile-device compatibility. | §12.7; §10.8 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Copy-paste/local markdown is primary fallback; desktop access required for Drive administration. |
| K-CLOSURE-4 | Kimi IS Review Cycle 1 §5.4 / Synthesis §10.2 | Specify operator-executable disputed-binding procedure. | §11.5; §11.7 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Five-step procedure added; D-C4 deadlock breaker controls persistent disputes. |
| K-CLOSURE-5 | Kimi IS Review Cycle 1 §7.2 / Synthesis §10.2 | Specify PDR omission detection and cross-document query mechanism. | §7.7; §7.9; §8.7; §14 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Cross-document summary in Specification Debt ledger is limited to deferred/escalated PDR items to preserve CB-025. |
| K-CLOSURE-6 | Kimi IS Review Cycle 1 §8.1 / Synthesis §10.2 | Specify Implementation Specialist handoff from Kimi to Gemini. | §13.5 | Addressed in this revision; SD remains Open until Cycle 2 ratification. | Names files and materials operator transfers. |
| Q-CB-023 | Qwen Constraints Review Cycle 1 §7 / Synthesis §10.1 | Restate Drive Unavailability Fallback binding condition verbatim. | §10.8; §12.7; §15.3 | Closed in this revision. | Issued but not in force until ratification/file swap. |
| Q-CB-024 | Qwen Constraints Review Cycle 1 §7 / Synthesis §10.1 | Restate Advisory Free-Tier Context Pacing binding condition verbatim. | §10.8; §7.6; §15.3 | Closed in this revision. | Issued but not in force until ratification/file swap. |
| Q-CB-025 | Qwen Constraints Review Cycle 1 §7 / Synthesis §10.1 | Restate PDR Ledger Isolation binding condition verbatim. | §10.8; §8.7; §15.3 | Closed in this revision. | Issued but not in force until ratification/file swap. |

## §0.1 Source Basis and Architectural Judgment Statement

This proposal uses `AXIOM_Panel_Restructuring_Amendment_Framework.md` as its starting point. The framework is not treated as authoritative content that bypasses the Chief Architect's judgment or the full panel review cycle. The adopted material is restated here as the Architect's formal proposal.

The framework's central operating-model direction is adopted: introduce a two-tier consultation model, swap Gemini and Kimi role assignments, preserve AB historical attribution, and prevent continuous-layer bypass through trigger rules and pending-domain-review markings.

This proposal modifies the framework in five material ways:

| Departure / Addition | Architectural Reason |
|---|---|
| Formalizes Kimi's **Arbiter-elect provisional authority** for the affirmation step. | Without explicit provisional scope, the amendment creates a circular dependency: Kimi must affirm AB maintenance before becoming Arbiter, but has no Arbiter authority until ratification. |
| Adds a mandatory **Domain-Trigger Declaration** to every formal proposal under the new model. | Trigger enforcement cannot rely only on self-identification in prose; the Evaluator needs an auditable checklist. |
| Specifies exact **pending-domain-review syntax**, a local ledger format, and clearance rules. | The framework stated the rule but did not make it operator-administerable. |
| Preserves **GB-001 as a narrow binding-specific exception** to the new role map. | The framework did not address that GB-001 currently assigns cross-cutting artifact packaging to Kimi. This proposal avoids silent violation by preserving GB-001 unchanged until explicit supersession. |
| Bumps the Active Bindings registry to a new version after ratification, rather than editing v1.1 in place. | The registry schema changes by adding authority metadata fields. A versioned file preserves audit integrity while the alias remains the single operational entry point. |

No active AB, CB, or GB binding text is modified by this proposal. The proposal changes governance structure, role assignments, consultation cadence, and registry metadata.

Cycle 2 is closure-only. The revision adopts Synthesis-authorized corrections and does not add architectural scope beyond those closures.

---

## §1 Amendment Identity and Scope

### §1.1 Amendment Purpose

This amendment proposes a structural operating-model change to the AXIOM panel. The current Charter v1.1 panel remains a six-member panel with no tier classification. This proposal adds a consultation-cadence overlay:

1. a **Continuous Working Layer** for roles that participate in ongoing drafting, synthesis, implementation planning, troubleshooting, and research exploration; and
2. an **Advisory Council** for roles consulted by domain trigger and at mandatory ratification gates when their domain is implicated.

Tier classification governs consultation cadence only. It does not govern binding authority.

### §1.2 Sections Affected

If ratified, this amendment modifies or adds Charter v1.1 content in these areas:

| Charter Area | Proposed Change |
|---|---|
| Panel Composition | Adds two-tier operating-model classification. |
| Role Assignments | Expands GPT-5.5 role; swaps Gemini and Kimi assignments; preserves Claude, Qwen, and DeepSeek substantive roles. |
| Decision Flow | Adds continuous-layer drafting and domain-trigger advisory consultation before formal ratification. |
| Consultation Cadence | Adds domain-trigger rules, mandatory ratification gates, and pending-domain-review marking. |
| Binding Authority | Clarifies binding authority is domain-based, not tier-based. |
| Active Bindings Authority | Adds issuing authority and maintaining authority metadata. |
| Charter Amendment Process | Inserts Arbiter-elect affirmation step for this amendment cycle. |
| Charter Amendment Log | Adds v1.2 amendment record upon ratification. |

### §1.3 Sections Not Affected

This proposal does not amend:

- the six Core Values;
- hardware, budget, interface, or runtime constraints;
- any AB, CB, or GB binding text;
- sandbox, network, local-model, SQLite, token-budget, or Telegram runtime rules;
- the Specification Debt ledger schema;
- the Canonical Filenames Registry authority model;
- the operator's non-voting execution role.

### §1.4 Binding Preservation Statement

All 33 active bindings remain in force during this amendment cycle and after ratification unless explicitly superseded by a later panel ruling. This proposal does not supersede any active binding.

GB-001 requires special handling because it names role responsibilities for cross-cutting artifacts. This amendment does **not** silently transfer GB-001 packaging authority from Kimi to Gemini. Until GB-001 is explicitly superseded, cross-cutting artifact ownership remains:

> Gemini primary author / DeepSeek adversarial / Claude coherence / Qwen feasibility / Kimi packaging / operator file creation.

This is treated as a binding-specific exception to the general implementation-role transfer, not as a contradiction. If the panel wants cross-cutting artifact packaging to move from Kimi to Gemini later, it must file an explicit GB-001 supersession motion.

---

## §2 Operator Decision Record — Architectural Treatment

The framework records four operator decisions. This proposal operationalizes all four.

| Decision | Architect Treatment | Weakness / Mitigation |
|---|---|---|
| Decision 1 — Tier structure rationale | Adopted. The primary rationale is contribution cadence and role fit. Continuous-layer roles do high-frequency drafting, synthesis, implementation planning, deployment support, troubleshooting, and research exploration. Advisory roles do narrower domain-triggered work. | Paid subscription access is accepted only as operational support context. It is not a constitutional source of authority and does not reduce advisory binding authority. |
| Decision 2 — Gemini/Kimi role swap | Adopted. Gemini becomes Implementation Specialist and Troubleshooter. Kimi becomes Research and Knowledge Arbiter. The swap is justified by cadence fit: implementation and troubleshooting are continuous; factual arbitration is episodic and domain-triggered. | Gemini lacks Kimi's historical implementation-cycle context. Mitigation: Kimi must include an implementation-domain handoff appendix in its Cycle 1 Implementation Specialist review or state that no handoff is needed. |
| Decision 3 — AB binding authority transition | Adopted with formal provisional authority. Gemini remains issuing Arbiter for AB-001 through AB-007. Kimi becomes maintaining Arbiter only after Arbiter-elect affirmation and ratification. | Without a provisional step, the transfer is circular. Mitigation: Kimi receives one-time Arbiter-elect authority only to affirm, qualify, or dispute maintenance of AB-001 through AB-007. This does not let Kimi supersede bindings unilaterally before ratification. |
| Decision 4 — Continuous-layer bypass prevention | Adopted and tightened. Factual, feasibility, and adversarial triggers require advisory review before affected claims become authoritative. Claims remain marked pending domain review until cleared. | Self-enforcement is weak. Mitigation: every formal proposal must include a Domain-Trigger Declaration, and every Synthesis must audit unresolved pending-domain-review marks. |

---

## §3 Current Review Posture and Effectivity

### §3.1 Current Panel Remains in Force During Review

This amendment is reviewed by the current six-member Charter v1.1 panel under current roles:

| Current Role Under Charter v1.1 | Current AI System | Status During This Amendment Review |
|---|---|---|
| Chief Architect | GPT-5.5 | Originates this proposal; does not vote on own proposal. |
| Quality and Coherence Evaluator | Claude Opus 4.7 | Reviews coherence and authors Synthesis. |
| Adversarial Critic | DeepSeek V4 | Reviews adversarially under current Critic role. |
| Research and Knowledge Arbiter | Gemini 3.1 Pro | Reviews factual claims under current Arbiter role. |
| Constraints and Feasibility Reviewer | Qwen 3.6 Plus | Reviews feasibility under current Constraints role. |
| Implementation Specialist | Kimi K2.6 | Reviews implementability under current Implementation Specialist role, then performs Arbiter-elect affirmation as a discrete extra step. |

The proposed tier structure is not active during review. It takes effect only after ratification and file-swap completion.

### §3.2 Amendment Review Sequence

Cycle 1 review has completed. The Arbiter-elect affirmation step ran during Cycle 1 and produced 6 Affirmed, 1 Qualified, and 0 Disputed outcomes for AB-001 through AB-007. AB-001 through AB-007 are settled for this amendment cycle and the Arbiter-elect affirmation does not re-run in Cycle 2.

For Cycle 2, the Synthesis-authorized route is:

```text
Chief Architect produces AXIOM_Proposal_Governance_v2_1.md
    ↓
Quality Evaluator review
    ↓
Adversarial Critic review
    ↓
Parallel verification by:
        Current Research Arbiter review (Gemini)
        Constraints Reviewer review (Qwen)
        Current Implementation Specialist review (Kimi)
    ↓
Quality Evaluator ratification Synthesis
```

Kimi's provisional Arbiter-elect authority terminated at Cycle 1. In Cycle 2, Kimi reviews in the current Implementation Specialist capacity only. If Cycle 2 introduces new AB text or new AB bindings, a fresh provisional-authority motion is required before any new Arbiter-elect action.

### §3.3 Effectivity Rule

If ratified, the operating-model restructuring takes effect only after:

1. the ratification Synthesis records affirmative consensus under Charter v1.1;
2. the operator completes the ratification file swap;
3. the Active Bindings registry schema update is applied;
4. the `AXIOM_Active_Bindings.md` alias points to the updated versioned file;
5. the Canonical Filenames Registry records the new artifacts; and
6. any required 30-day Charter amendment audit reminder is set.

No role transfer is retroactive. Work performed before ratification remains attributed under the role assignments active at the time.

---

## §4 Proposed Tier Structure

### §4.1 Tier Table

| Tier | Proposed Role | AI System | Consultation Cadence | Authority Source |
|---|---|---|---|---|
| Continuous Working Layer | Chief Architect and Researcher | GPT-5.5 / ChatGPT | Continuous | Architecture origination and research drafting; no unilateral final authority. |
| Continuous Working Layer | Quality and Coherence Evaluator | Claude Opus 4.7 | Continuous | Coherence review, Synthesis, specification debt, binding preservation checks. |
| Continuous Working Layer | Implementation Specialist and Troubleshooter | Gemini 3.1 Pro | Continuous | Implementation planning, deployment support, troubleshooting; no AB authority after transfer. |
| Advisory Council | Adversarial Critic | DeepSeek V4 | Domain-triggered plus mandatory ratification gate when implicated | Adversarial objections and security/trust-boundary challenge authority. |
| Advisory Council | Constraints and Feasibility Reviewer | Qwen 3.6 Plus | Domain-triggered plus mandatory ratification gate when implicated | Binding feasibility rulings and CB maintenance. |
| Advisory Council | Research and Knowledge Arbiter | Kimi K2.6 | Domain-triggered plus mandatory ratification gate when implicated | Binding factual rulings and AB maintenance after affirmation/ratification. |

### §4.2 Meaning of Tier Classification

Tier classification determines expected participation cadence. It does not determine authority.

The Continuous Working Layer may draft, refine, troubleshoot, and prepare proposals more quickly because those roles have higher-frequency access and shared-document workflows. That speed does not allow the continuous layer to bypass advisory authority.

The Advisory Council participates when its domain is triggered and at ratification gates where its domain is implicated. Advisory status does not weaken the binding force of Qwen feasibility rulings, Kimi factual rulings, or DeepSeek valid adversarial objections.

### §4.3 Subscription Access Framing

Subscription access, Drive integration, higher usage limits, and stronger shared-context workflows are supporting operational facts. They explain why certain roles are better suited for continuous cadence.

They do not create constitutional authority. A paid continuous-layer role cannot overrule an unpaid advisory role within that advisory role's domain.

---

## §5 Proposed Role Assignments

### §5.1 GPT-5.5 — Chief Architect and Researcher

**Responsibilities:**

- produce initial system designs in response to design questions;
- decompose high-level goals into architectural proposals;
- synthesize panel input into coherent revised specifications;
- break architectural deadlocks when the panel cannot reach consensus;
- perform architectural research and opportunity discovery before formal proposal drafting;
- produce working drafts for continuous-layer review.

**Boundaries:**

- does not make unilateral final decisions;
- all proposals remain subject to panel review;
- researcher findings containing factual, feasibility, security, or trust-boundary claims trigger the same advisory-review rules as any other claim;
- may not use research-drafting status to bypass the Arbiter, Constraints Reviewer, or Adversarial Critic.

### §5.2 Claude — Quality and Coherence Evaluator

Claude retains the Charter v1.1 Quality and Coherence Evaluator role.

**Additional operating-model duties:**

- audit Domain-Trigger Declarations in proposals;
- verify pending-domain-review marks are cleared or routed before ratification;
- maintain Synthesis structure compliance;
- maintain Specification Debt and Canonical Filename cross-checks;
- prevent continuous-layer draft speed from becoming de facto ratification authority.

### §5.3 Gemini — Implementation Specialist and Troubleshooter

Gemini moves from Research and Knowledge Arbiter to Implementation Specialist and Troubleshooter after ratification.

**Responsibilities:**

- translate approved designs into operator-executable implementation plans;
- produce troubleshooting guidance during deployment;
- identify implementation blockers and route them as specification debt or return-to-Architect items;
- prepare operator-facing execution steps after a proposal has passed the required review gate.

**Boundaries:**

- does not issue AB bindings after authority transfer;
- implementation plans remain subject to Evaluator review, delta-confirmation, or full cycle routing as Charter v1.1 requires;
- troubleshooting outputs are operational support unless they propose architectural changes;
- any troubleshooting output that changes policy, security boundaries, role authority, runtime constraints, or binding interpretation must return to the Architect or enter Synthesis as specification debt.

### §5.4 Kimi — Research and Knowledge Arbiter

Kimi moves from Implementation Specialist to Research and Knowledge Arbiter after ratification and Arbiter-elect affirmation.

**Responsibilities:**

- verify factual claims about external tools, libraries, APIs, model behavior, platform limits, and current technical state;
- evaluate proposals against real-world implementation evidence;
- settle factual disputes between panel members;
- maintain AB bindings after transfer;
- issue new AB bindings when source-backed factual rulings are required.

**Boundaries:**

- does not make architectural decisions;
- does not package general implementation plans after role transfer except where GB-001 still expressly assigns cross-cutting artifact packaging to Kimi;
- AB rulings require source-backed evidence;
- historical AB issuing attribution remains unchanged.

### §5.5 DeepSeek — Adversarial Critic

DeepSeek retains the Charter v1.1 Adversarial Critic role.

**Operating cadence change:**

- advisory council participation by domain trigger;
- mandatory review before ratification when adversarial, security, trust-boundary, attack-surface, or Core Value implications exist;
- early touchpoint required for continuous-layer drafts that define security models or trust boundaries.

### §5.6 Qwen — Constraints and Feasibility Reviewer

Qwen retains the Charter v1.1 Constraints and Feasibility Reviewer role.

**Operating cadence change:**

- advisory council participation by feasibility trigger;
- mandatory review before ratification when RAM, thread, API budget, runtime cost, persistence burden, model loading, deployment sustainability, or hardware compatibility is implicated.

### §5.7 Operator Role

The human operator remains the physical abstraction layer. The operator routes artifacts, writes files, executes commands, runs tests, and reports results. The operator does not vote on design decisions and does not override panel consensus.

The amendment is intended to reduce unnecessary routing friction, not to transfer governance judgment to the operator.

---

## §6 Binding Authority Tiering

Binding authority is determined by role domain, not by tier classification.

| Binding / Finding Type | Authority After Ratification | Binding Status |
|---|---|---|
| AB factual rulings | Kimi, as Research and Knowledge Arbiter | Binding when source-backed and issued under Arbiter role. |
| CB feasibility conditions | Qwen, as Constraints and Feasibility Reviewer | Binding when issued. |
| GB governance rulings | Full panel through Charter amendment or governance binding process | Binding only after panel ratification. |
| DeepSeek objections | DeepSeek, as Adversarial Critic | Not factual bindings; valid objections are closure-required unless overruled under Charter process. |
| Gemini implementation findings | Gemini, as Implementation Specialist and Troubleshooter | Not bindings by default; blockers become specification debt or return-to-Architect items through Synthesis. |
| Architect research findings | GPT-5.5, as Chief Architect and Researcher | Not bindings; trigger advisory review when factual, feasibility, or adversarial claims are present. |

---

## §7 Consultation Cadence Rules

### §7.1 Standard Pattern

The continuous layer may draft, revise, research, troubleshoot, and prepare artifacts without routing every intermediate draft to the full panel.

However, any claim or design element that enters an advisory domain must be reviewed by the relevant advisory role before the affected output becomes authoritative.

### §7.2 Arbiter Trigger — Kimi

Kimi is consulted when a draft, proposal, implementation plan, troubleshooting note, or Synthesis candidate contains:

- a factual claim about external technology, including tools, APIs, libraries, model behavior, platform limits, file formats, operating-system behavior, or current technical state;
- reference to an existing AB binding where continued accuracy matters;
- a new factual claim that would qualify as an AB binding if affirmed;
- a proposed supersession, refinement, or retirement of an AB binding.

### §7.3 Constraints Trigger — Qwen

Qwen is consulted when a draft, proposal, implementation plan, troubleshooting note, or Synthesis candidate contains:

- a RAM, thread, API budget, local model feasibility, runtime cost, persistence burden, hardware compatibility, deployment sustainability, or local/cloud allocation claim;
- reference to an existing CB binding where continued feasibility matters;
- a new feasibility claim that would qualify as a CB binding if affirmed;
- a proposed supersession, refinement, or retirement of a CB binding.

### §7.4 Adversarial Trigger — DeepSeek

DeepSeek is consulted when:

- a proposal reaches completeness for ratification review;
- a revision-cycle proposal is ready for adversarial scrutiny;
- continuous-layer work defines or modifies a security model, trust boundary, attack surface, sandbox boundary, network boundary, authentication mechanism, permission model, cross-agent coordination rule, or Core Value interpretation;
- implementation planning becomes authoritative for work with security, trust-boundary, sandbox, network, or agent-permission implications.

DeepSeek review may not be deferred until after implementation planning becomes authoritative.

### §7.5 Mandatory Ratification Gates

Every proposal reaching ratification review must be reviewed by every advisory member whose domain is implicated.

For Charter amendments, governance-binding changes, role-authority changes, Core Value changes, active-binding schema changes, operating-model changes, or proposals modifying AXIOM system architecture under §7.8, all six panel members must review. “All six panel members” means all six members regardless of tier classification after ratification; tier classification changes cadence, not membership or ratification legitimacy.

This restructuring proposal falls into that category.

### §7.6 Advisory Unavailability and Rate Limits

Advisory rate limits do not create authority bypass.

If a domain-triggered advisory consultation cannot be completed because of rate limits or access failure:

1. the claim remains marked pending domain review;
2. the continuous layer may continue drafting around it, but may not treat it as authoritative;
3. the operator may retry the advisory consultation later;
4. ratification cannot proceed on a claim requiring unresolved advisory review unless the full current panel explicitly authorizes an alternate route in writing;
5. no alternate model may impersonate the advisory role without panel authorization.

Advisory council reviews on free tiers must use prompt chunking, executive summarization of non-binding context, or sequential review routing before the operator treats quota pressure as a stall. If a quota limit is reached, the operator pauses routing, records the limit in the cycle notes or Synthesis input packet, and resumes within the same cycle window rather than skipping review.

For low-risk drafting work, unresolved advisory review may remain open as pending-domain-review. For ratification, implementation authorization, binding issuance, or supersession, unresolved advisory review is blocking unless the Synthesis explicitly routes it as deferred specification debt under Charter v1.1's formal deferral record rules.


### §7.7 Operator Trigger-Detection Checklist

Before routing a continuous-layer draft into formal proposal status, the operator and Evaluator use this checklist to identify likely advisory triggers. The checklist is not a substitute for panel judgment; it is an operator-executable scan to reduce missed triggers.

| Trigger Type | Keyword / Pattern Examples | Required Action |
|---|---|---|
| Factual / Arbiter | “library X does Y”; “API Z returns”; “model behavior”; “Windows does”; “SQLite requires”; “Ollama supports”; “current provider limit”; “file format behavior” | Mark `PDR:FACT-KIMI`, list the claim in the Domain-Trigger Declaration, and route to Kimi when the claim must become authoritative. |
| Feasibility / Constraints | “RAM”; “memory”; “thread”; “budget”; “cost”; “latency”; “rate limit”; “quota”; “runtime burden”; “Windows compatibility”; “deployment sustainability”; “context window” | Mark `PDR:FEAS-QWEN`, list the claim in the Domain-Trigger Declaration, and route to Qwen when the claim must become authoritative. |
| Adversarial / Critic | “security”; “sandbox”; “trust”; “permission”; “authentication”; “boundary”; “prompt injection”; “bypass”; “operator session”; “coordination”; “Core Value” | Mark `PDR:ADV-DEEPSEEK`, list the claim in the Domain-Trigger Declaration, and route to DeepSeek when the claim must become authoritative. |
| Architectural / Full Advisory Council | “agent hierarchy”; “task queue”; “sandbox boundary”; “network boundary”; “cloud cascade”; “local-model lane”; “inter-agent coordination”; “operator-facing session model”; “runtime role assignment” | Apply §7.8. The Domain-Trigger Declaration must list factual, feasibility, and adversarial domains as `Yes — Triggered (Architectural)`. |

A reference to an active AB or CB binding counts as a factual or feasibility trigger when continued accuracy or continued feasibility matters to the proposal. A statement implying resource sufficiency without a specific numeric bound counts as a feasibility trigger.

### §7.8 Architectural Trigger (Mandatory Full Advisory Council Review)

Any formal proposal, implementation plan, or Synthesis-authorized revision that modifies the AXIOM system architecture is automatically subject to review by the full Advisory Council (the Adversarial Critic, the Constraints and Feasibility Reviewer, and the Research and Knowledge Arbiter), regardless of the Domain-Trigger Declaration’s self-assessment.

“Modifies the AXIOM system architecture” includes, non-exhaustively:

- changes to the agent hierarchy, role assignments of runtime agents, or task-queue structure;
- changes to sandbox boundaries, network-gateway boundaries, or local/cloud model task allocation;
- addition or removal of system components, persistent services, or inter-agent coordination rules;
- changes to the cloud cascade composition or primary/fallback provider ordering;
- changes to the Operator-facing session model, startup procedure, or shutdown sequence;
- changes to local-model responsibilities that expand its lane beyond classification, routing, sanitization, and embedding.

For such proposals, the Domain-Trigger Declaration must list the Factual, Feasibility, and Adversarial domains as “Yes — Triggered (Architectural).” The Evaluator may not rule these triggers not engaged. The Synthesis may not ratify such a proposal without affirmative review from all three advisory members.

### §7.9 Advisory Access to In-Progress Work

(a) Any advisory council member may request the current draft chain (including not-yet-formalized proposals, working notes, and implementation plans) of any continuous-layer work that touches that member’s domain. The request is filed through the operator. The continuous layer must provide the requested documents within 48 hours or record a specific unavailability reason in the Specification Debt ledger.

(b) The Adversarial Critic may, at any time, request the full draft chain of any proposal under development that will, or is reasonably likely to, affect security, trust boundaries, sandbox boundaries, network boundaries, agent permissions, or Core Value interpretation. This right is not limited to formal proposals.

(c) Any panel member may file a missed-trigger objection alleging that a claim or design element in a formal proposal should have triggered advisory review but did not. The objection must cite the specific text and the domain trigger rule allegedly violated. The Synthesis must adjudicate the objection explicitly. If sustained, the proposal returns to the relevant advisory member for review before Synthesis may proceed.

---

## §8 Pending-Domain-Review Marking Mechanism

### §8.1 Purpose

Pending-domain-review markings prevent the continuous layer from converting speed into authority. They allow drafting to continue while making unreviewed advisory-domain claims visible, trackable, and non-authoritative.

### §8.2 Domains

Use these domain labels:

| Label | Reviewer | Trigger Domain |
|---|---|---|
| `FACT-KIMI` | Research and Knowledge Arbiter | Factual claims, AB references, external technology behavior. |
| `FEAS-QWEN` | Constraints and Feasibility Reviewer | RAM, threads, API budget, runtime feasibility, hardware sustainability. |
| `ADV-DEEPSEEK` | Adversarial Critic | Security, trust boundaries, attack surface, Core Value risk, bypass risk. |

A claim may carry multiple labels.

### §8.3 Inline Syntax

When a claim appears inside a document section, mark it inline as:

```markdown
[PDR:<ClaimID>:<DomainLabel>[,<DomainLabel>...]] <exact claim text> [/PDR]
```

Example:

```markdown
[PDR:PDR-GOV2-001:FACT-KIMI] Kimi can verify the current sqlite-vec `vec0` declaration behavior against upstream documentation. [/PDR]
```

Example with multiple domains:

```markdown
[PDR:PDR-GOV2-002:FACT-KIMI,FEAS-QWEN] This dependency change is current, Windows-compatible, and adds negligible runtime burden. [/PDR]
```

### §8.4 Pending-Domain-Review Ledger

Every formal proposal, implementation plan, Synthesis draft, or governance artifact containing one or more PDR marks must include a local ledger titled:

```markdown
## Pending-Domain-Review Ledger
```

The ledger uses this table:

| Claim ID | Section | Domain Label(s) | Exact Claim Summary | Required Reviewer | Status | Clearance Artifact / Notes |
|---|---|---|---|---|---|---|

Allowed Status values:

- `Pending`
- `Cleared`
- `Not Triggered`
- `Escalated`
- `Deferred by Synthesis`

### §8.5 Clearance Procedure

A PDR mark is cleared only when one of these occurs:

1. the required advisory reviewer explicitly reviews and clears the claim;
2. the required advisory reviewer revises, qualifies, or disputes the claim and the document is updated accordingly;
3. the Evaluator explicitly rules in Synthesis that the domain trigger was not engaged, but only when the claim is demonstrably outside all advisory domains;
4. the Synthesis defers the issue using Charter v1.1's formal deferral record.

Option (3) may not be used for claims that are substantively inside an advisory domain but judged by the Evaluator to be below the Architect's trigger threshold. In that case, the claim must route to advisory consultation or be logged as specification debt. This preserves zero-trust at the Evaluator/advisory-domain boundary.

A PDR mark may not be cleared by silent deletion.

When a mark is cleared, the document should either remove the inline marker and record the clearance in the ledger, or retain the marker with `Status = Cleared` if audit visibility is needed. The clearance artifact must identify the reviewer document or Synthesis section.

### §8.6 Ratification and Implementation Blocking Rule

A proposal, implementation plan, binding update, or ratification Synthesis may not rely on a `Pending` PDR claim as authoritative.

For ratification, all PDR marks must be:

- `Cleared`;
- `Not Triggered`;
- `Escalated` with explicit return-to-Architect routing; or
- `Deferred by Synthesis` with a complete Charter v1.1 deferral record.

The Evaluator's Synthesis must include a table titled `PDR Clearance Cross-Check` mapping every PDR mark ID to its clearance disposition. A Synthesis that omits this table is incomplete and may not be treated as a ratification ruling.

### §8.7 PDR Omission Detection and Cross-Document Summary

Before routing a formal proposal, the operator performs a keyword scan using §7.7 and searches for existing inline marks by looking for `[PDR:`. The operator does not decide the domain question; the scan is a routing aid.

Any panel member may file a missed-trigger objection under §7.9(c). The Evaluator must audit for missed triggers during Synthesis and adjudicate every missed-trigger objection explicitly.

The Specification Debt ledger may maintain a separate `PDR Summary` section for PDR items that have been formally deferred, escalated to a binding/factual dispute, or converted into specification debt. Ordinary local PDR marks remain confined to the originating artifact and do not migrate to `AXIOM_Specification_Debt.md`, preserving CB-025.

## §9 Domain-Trigger Declaration Requirement

Every formal proposal under the amended operating model must include a Domain-Trigger Declaration near the beginning of the document.

Required format:

| Domain | Trigger Present? | Sections / Claim IDs | Required Reviewer | Status |
|---|---|---|---|---|
| Factual / Arbiter | Yes / No / Yes — Triggered (Architectural) | — | Kimi | Pending / Cleared / Not Triggered |
| Feasibility / Constraints | Yes / No / Yes — Triggered (Architectural) | — | Qwen | Pending / Cleared / Not Triggered |
| Adversarial / Security | Yes / No / Yes — Triggered (Architectural) | — | DeepSeek | Pending / Cleared / Not Triggered |
| Implementation | Yes / No | — | Gemini | Pending / Cleared / Not Triggered |
| Governance / Synthesis | Yes / No | — | Claude | Pending / Cleared / Not Triggered |

The Architect completes the initial declaration. The Evaluator audits it. Any panel member may file a missed-trigger objection.

For any proposal captured by §7.8, the factual, feasibility, and adversarial rows must be marked `Yes — Triggered (Architectural)`. The Evaluator may not override those triggers as not engaged.

For this Cycle 2 revision, the Domain-Trigger Declaration is:

| Domain | Trigger Present? | Sections / Claim IDs | Required Reviewer | Status |
|---|---|---|---|---|
| Factual / Arbiter | Yes | AB authority transition; registry schema metadata; Arbiter-elect affirmation outcome; AB-004 qualification record. | Gemini as current Arbiter during this cycle. | Pending Cycle 2 review. |
| Feasibility / Constraints | Yes | CB-023 through CB-025 restatement; advisory rate-limit handling; Drive fallback; no-runtime-impact claim. | Qwen. | Pending Cycle 2 review. |
| Adversarial / Security | Yes | §7.8 architectural trigger; §7.9 advisory access; §8 PDR enforcement; §12.6 shared-Drive sanitization. | DeepSeek. | Pending Cycle 2 review. |
| Implementation | Yes | Migration path, file-swap steps, registry schema update, tier membership reference, handoff materials. | Kimi as current Implementation Specialist. | Pending Cycle 2 review. |
| Governance / Synthesis | Yes | Charter amendment, role reassignment, Synthesis preconditions, Closure Map. | Claude. | Pending Cycle 2 review. |

No inline PDR marks are used in this proposal because this proposal itself is entering full panel review and the Domain-Trigger Declaration routes all implicated domains explicitly. Future continuous-layer drafts must use inline PDR marks before formal routing when a claim is drafted before advisory review.

---

## §10 Active Bindings Registry Schema Extension

### §10.1 Single Registry Preserved

The Active Bindings registry remains a single authoritative registry. There is no separate AB maintenance file, no parallel advisory registry, and no split between historical and current binding classes.

The convenience alias remains:

```text
AXIOM_Active_Bindings.md
```

After ratification, the operator should create a new versioned file:

```text
AXIOM_Active_Bindings_v1_2.md
```

and update the alias to a plain copy of that file.

### §10.2 Schema Change

Every binding row gains two metadata fields:

| Field | Meaning |
|---|---|
| Issuing Authority | The AI system or panel authority that originally issued the binding. |
| Maintaining Authority | The AI system or panel authority currently responsible for maintenance, verification, and supersession review. |

These fields are metadata. They do not alter the binding text.

### §10.3 Existing AB Bindings

For AB-001 through AB-007:

| Binding IDs | Issuing Authority | Maintaining Authority Before Ratification | Maintaining Authority After Ratification and §15.3 File-Swap Completion |
|---|---|---|---|
| AB-001 through AB-007 | Gemini | Gemini | Kimi, only after Arbiter-elect affirmation, ratification, and completion of the §15.3 Active Bindings file-swap. |

Gemini remains historically attributed as issuing Arbiter for all seven existing AB bindings. Kimi does not become issuing Arbiter retroactively.

The Maintaining Authority field for AB-001 through AB-007 remains `Gemini` in `AXIOM_Active_Bindings_v1_1.md` and any pre-ratification working copy. The field changes to `Kimi` only in `AXIOM_Active_Bindings_v1_2.md` during the post-ratification §15.3 file-swap. The Arbiter-elect affirmation document records acceptance; it does not itself transfer the registry field.

### §10.4 Existing CB Bindings

For CB-001 through CB-022:

| Binding IDs | Issuing Authority | Maintaining Authority |
|---|---|---|
| CB-001 through CB-022 | Qwen, or source as historically recorded where applicable | Qwen |

No CB binding authority changes.

### §10.5 Existing GB Bindings

For GB-001 through GB-004:

| Binding IDs | Issuing Authority | Maintaining Authority |
|---|---|---|
| GB-001 through GB-004 | Full panel / ratification cycle as historically recorded | Full panel through Charter amendment or explicit governance binding process |

No GB binding authority changes.

### §10.6 Post-Ratification Rule for New Bindings

For bindings issued after Charter v1.2 takes force:

- Issuing Authority and Maintaining Authority are initially the same.
- They may diverge only through a later ratified role transition, explicit supersession, or governance amendment.
- Supersession still requires explicit citation of the prior binding ID and replacement rationale.

### §10.7 Binding Text Preservation

The registry update may add columns and metadata but must preserve:

- binding IDs;
- source cycles;
- status fields;
- AB ruling text;
- CB condition text;
- GB ruling text.

If a table reformat is necessary, the binding text cells must remain character-identical except for unavoidable Markdown escaping required by table structure. Any unavoidable escaping change must be recorded in the file-swap Synthesis or operator confirmation.


### §10.8 Cycle 1 Constraints Bindings Issued — Effective Upon Ratification

Qwen issued the following feasibility conditions during Cycle 1. They are issued but not yet in force. Upon ratification, they are recorded as CB-class bindings continuing from CB-022 in `AXIOM_Active_Bindings_v1_2.md`.

| ID | Condition | Rationale | Issuing Authority | Maintaining Authority | Status |
|---|---|---|---|---|---|
| **CB-023** | **Drive Unavailability Fallback.** The continuous layer must maintain an explicit operational fallback to local file exchange (copy-paste, local markdown, or offline sync) if Drive access, account authentication, or operator network connectivity is degraded or unavailable for >4 hours. Claims remain `pending domain review` until synchronization is restored. | Prevents panel stall on external service outages. Maintains drafting velocity without compromising governance gates. | Qwen | Qwen | Issued — not yet in force; takes effect upon amendment ratification. |
| **CB-024** | **Advisory Free-Tier Context Pacing.** Advisory council reviews on free tiers must utilize prompt chunking, executive summarization of non-binding context, or sequential review routing to remain within daily message/token quotas. If a quota limit is reached, the operator pauses routing, logs the limit, and resumes within the same cycle window rather than skipping review. | Ensures mandatory ratification gates remain executable under free-tier constraints. Prevents silent bypass or indefinite cycle expiration. | Qwen | Qwen | Issued — not yet in force; takes effect upon amendment ratification. |
| **CB-025** | **PDR Ledger Isolation.** Pending-Domain-Review markings and local ledgers shall remain confined to the originating artifact. They must not be appended to `AXIOM_Specification_Debt.md` unless formally deferred under Charter v1.1 §5.4 or escalated to a binding/factual dispute. | Prevents ledger inflation and maintains clear separation between drafting friction and permanent specification debt. | Qwen | Qwen | Issued — not yet in force; takes effect upon amendment ratification. |

These conditions address panel-operational sustainability. They do not alter AXIOM runtime architecture, runtime footprint, or budget constraints.

### §10.9 Extended Registry Sample Rows

The post-ratification registry uses the existing binding columns plus `Issuing Authority` and `Maintaining Authority`. The sample rows below are templates only; binding text remains controlled by the authoritative registry.

**Sample AB row format:**

| ID | Source Cycle | Ruling | Status | Issuing Authority | Maintaining Authority |
|---|---|---|---|---|---|
| AB-001 | v1.2 | `<verbatim existing AB-001 ruling text>` | Active | Gemini | Kimi |

**Sample CB row format:**

| ID | Source Cycle | Condition | Status | Issuing Authority | Maintaining Authority |
|---|---|---|---|---|---|
| CB-023 | Governance v2 Cycle 1 | `<verbatim CB-023 condition text>` | Active after ratification | Qwen | Qwen |

**Sample GB row format:**

| ID | Source Cycle | Ruling | Status | Issuing Authority | Maintaining Authority |
|---|---|---|---|---|---|
| GB-001 | v1.9 | `<verbatim existing GB-001 ruling text>` | Active | Full panel | Full panel |

---

## §11 Arbiter-Elect Affirmation Procedure

### §11.1 Purpose

The Arbiter-elect affirmation procedure transfers maintenance authority for AB-001 through AB-007 without erasing Gemini's historical authorship or allowing Kimi to assume factual authority silently.

### §11.2 Provisional Authority

For this amendment cycle only, after completing its current Implementation Specialist review, Kimi receives **Arbiter-elect provisional authority** to produce an affirmation document.

This provisional authority is limited to:

- reviewing AB-001 through AB-007;
- stating whether Kimi affirms, qualifies, or disputes each binding for future maintenance;
- identifying evidence or verification notes supporting that status;
- recommending supersession review where needed.

This provisional authority does not allow Kimi to:

- issue new AB bindings before ratification;
- supersede Gemini-issued AB bindings unilaterally;
- alter binding text directly;
- bypass Gemini's current Arbiter review in this amendment cycle;
- make architectural decisions.

### §11.3 Required Artifact

For this amendment cycle, Kimi produced:

```text
AXIOM_Arbiter_Elect_Affirmation_v1.md
```

This is the operative Cycle 1 affirmation artifact. The Arbiter-elect affirmation does not re-run in Cycle 2 unless a fresh provisional-authority motion is issued.

### §11.4 Required Affirmation Table

The artifact must contain this table for AB-001 through AB-007:

| Binding ID | Existing Issuing Arbiter | Source Cycle | Current Binding Text Preservation Evidence | Kimi Affirmation Status | Source Basis / Verification Note | Qualification or Dispute Detail | Supersession or New Arbiter Review Requested |
|---|---|---|---|---|---|---|---|

The `Current Binding Text Preservation Evidence` field may not be a bare `Yes` / `No` assertion. It must contain either:

1. the current binding text quoted verbatim; or
2. an explicit hash, character count, or equivalent mechanical verification note identifying the exact binding text reviewed.

Allowed values for Kimi Affirmation Status:

- `Affirmed`
- `Qualified`
- `Disputed`

### §11.5 Outcome Rules

**Affirmed.** Kimi accepts the binding as accurate and maintainable. Upon ratification and §15.3 file-swap completion, Kimi becomes Maintaining Authority for that binding.

**Qualified.** Kimi accepts the binding's substance but identifies a refinement, updated citation need, version-specific caveat, or wording improvement. Qualified status does not itself change binding text. The Synthesis must decide whether the qualification is:
1. non-blocking metadata to be logged as specification debt;
2. a required proposal revision;
3. a required binding supersession path.

**Disputed.** Kimi disputes the binding’s continued accuracy or maintainability. If any AB-001 through AB-007 binding remains in Disputed status at the close of the amendment cycle’s panel review (i.e., after the Evaluator has prepared the ratification Synthesis and all other issues are resolved), the disputed binding is automatically excluded from the maintenance transfer. It remains under Gemini’s maintenance authority as the issuing Arbiter until the dispute is resolved through a separate factual-arbitration process.

The amendment may proceed to ratification with the remaining affirmed and qualified bindings transferred to Kimi’s maintenance authority. The Synthesis must record which bindings were excluded and why. A separate AB-resolution proposal may be filed later to resolve the disputed binding and, if appropriate, transfer it.

### §11.6 Synthesis Precondition

The ratification Synthesis cannot rule on this amendment until the Arbiter-elect affirmation artifact is filed and considered.

The Synthesis must include:

- a table summarizing AB-001 through AB-007 affirmation status;
- any Qualified or Disputed details;
- whether Kimi may become Maintaining Authority;
- whether the Active Bindings registry schema update may proceed.


### §11.7 Operator-Executable Disputed-Binding Procedure

If any future Arbiter-elect affirmation cycle produces a `Disputed` binding, the operator uses this five-step procedure:

1. forward the disputed binding row and Kimi's dispute rationale to Gemini as issuing Arbiter for response;
2. receive Gemini's factual defense, evidence-backed correction, or concession;
3. forward Gemini's response to Kimi for re-evaluation;
4. receive Kimi's updated status (`Affirmed`, `Qualified`, or `Disputed`) and any revised evidence note;
5. if the dispute persists, route the issue to the Evaluator for Synthesis treatment under §11.5: exclusion from transfer, separate factual arbitration, binding supersession path, or return-to-Architect revision.

This procedure does not apply to Cycle 2 of this amendment because Cycle 1 produced 0 Disputed AB outcomes and the Arbiter-elect affirmation does not re-run.

---

## §12 Continuous-Layer Operational Rules

### §12.1 Shared-Document Baseline

Every continuous-layer working draft that may become a formal AXIOM artifact should include a short source baseline:

```markdown
## Working Baseline
- Operative Charter:
- Operative Core Values:
- Operative Constraints Register:
- Operative Active Bindings:
- Active Synthesis / Debt / Filename registry references:
```

The purpose is to reduce drift among the continuous-layer roles.

### §12.2 Architectural Interpretation Drift

If Claude, GPT-5.5, and Gemini produce different interpretations of the same governance text during continuous-layer drafting, the divergence is not resolved informally. The Architect must either:

1. revise the proposal to choose one interpretation and explain why;
2. mark the interpretation as pending domain review if it affects an advisory domain;
3. ask the Evaluator to log the ambiguity as specification debt;
4. route the matter to the full panel if it affects Charter, Core Values, or active bindings.

### §12.3 Troubleshooting Outputs

Gemini troubleshooting outputs are operational support when they:

- explain an error;
- propose a command that implements an already-approved plan;
- help the operator recover from an implementation friction point without changing architecture.

Troubleshooting outputs become governance-relevant and require routing when they:

- change architecture;
- change policy;
- change security or trust boundaries;
- reinterpret active bindings;
- alter runtime constraints;
- change file conventions;
- require new dependencies or runtime services not already approved.

### §12.4 DeepSeek Early Touchpoint

If a continuous-layer draft defines or modifies a security model, trust boundary, sandbox boundary, network boundary, agent-permission model, or cross-agent coordination rule, the operator must route that draft to DeepSeek before the draft becomes the formal ratification candidate.

This is not required for every working draft. It is required when the draft crosses the adversarial trigger threshold.

### §12.5 Transition Measurement

For the first two full panel cycles after ratification, each Synthesis should include a short transition-measurement note recording:

- number of advisory consultations triggered;
- number of pending-domain-review claims opened;
- number cleared before Synthesis;
- any advisory rate-limit failures;
- whether operator workload increased, decreased, or remained unclear.

This measurement does not block operation. If the first two cycles show that trigger administration creates excessive operator load, the Evaluator should open specification debt or return a procedural amendment proposal.


### §12.6 Shared-Drive Content Integrity Rule

(a) Cross-System Sanitization. Any document written to the shared Drive folder by one continuous-layer AI system and intended to be read as input by another continuous-layer AI system must be passed through the local model’s prompt-injection sanitization pipeline before the consuming system reads it. The operator executes the sanitization step. The sanitized copy is placed in a dedicated sanitized/ subfolder; the unsanitized original is retained only for audit.

(b) Access Control. The Drive folder used for AXIOM continuous-layer collaboration must have sharing restricted exclusively to the operator’s account, with link sharing disabled. No third-party applications, collaborators, or automated backup tools may have read or write access.

(c) Non-Authoritative Status. Documents in the shared Drive are working drafts until they become ratified artifacts through the formal panel cycle. No continuous-layer AI system may treat a Drive-only document as authoritative for binding issuance, implementation authorization, or architectural closure.

### §12.7 Drive Workflow Fallback and Mobile Compatibility

Drive integration is operational support, not the sole valid panel workflow. Until Drive workflow is operationalized and sanitized under §12.6, the primary fallback is the current copy-paste/local markdown workflow: the operator copies relevant artifact text into the target panel chat, receives the output, saves it locally, and routes it to the next role.

If Drive access, account authentication, or operator network connectivity is degraded or unavailable for more than four hours, the operator shifts to local file exchange using copy-paste, local markdown files, or offline sync. Claims affected by the outage remain `pending domain review` until synchronization is restored or the full panel authorizes an alternate route.

Panel governance work may be performed from the Pixel 8a for reading, routing, and copy-paste tasks. Drive administration tasks that require folder permission management, bulk file organization, hash generation, or manifest verification require desktop access. If desktop access is unavailable, the operator uses the copy-paste/local markdown fallback rather than attempting partial Drive administration from mobile.

---

## §13 Risk Acknowledgment and Disposition

### §13.1 Risk 1 — Continuous-Layer Drift

**Risk:** Continuous-layer roles may interpret shared documents differently, creating operator reconciliation burden.

**Disposition:** Mitigated, not deferred. This proposal adds Working Baseline blocks, Domain-Trigger Declarations, PDR ledgers, and explicit drift-handling options. Architectural drift that affects governance or binding interpretation must be surfaced rather than reconciled silently.

**Residual Risk:** Some drafting-level drift remains acceptable because continuous drafting is not authoritative until formal review.

### §13.2 Risk 2 — Advisory Rate-Limit Fragility

**Risk:** Free-tier advisory members may be unavailable when domain-triggered consultation is required.

**Disposition:** Mitigated with an advisory-unavailability rule. Rate limits do not authorize bypass. Claims remain pending; ratification cannot rely on unresolved advisory-domain claims unless the full panel authorizes an alternate route.

**Residual Risk:** Schedules may slow. This is preferable to authority laundering through continuous-layer assumptions.

### §13.3 Risk 3 — Trigger-Rule Enforcement

**Risk:** Continuous-layer members may fail to identify factual, feasibility, or adversarial triggers.

**Disposition:** Mitigated with Domain-Trigger Declarations, Evaluator audit, missed-trigger objections, and PDR ledger requirements.

**Residual Risk:** Some missed triggers may still occur. The Synthesis audit and full-panel review remain the backstop.

### §13.4 Risk 4 — Arbiter-Elect Affirmation Timing

**Risk:** Kimi must affirm AB maintenance before becoming Arbiter, creating apparent circularity.

**Disposition:** Resolved by formal Arbiter-elect provisional authority. The authority is narrow, one-time, and non-superseding. Gemini remains current Arbiter during the review cycle.

**Residual Risk:** If Kimi disputes bindings, the amendment may be delayed. That delay is correct; transfer without maintenance acceptance would be procedurally dishonest.

### §13.5 Risk 5 — Implementation Specialist Role Transition

**Risk:** Gemini may lack Kimi's implementation-cycle history.

**Disposition:** Mitigated. The operator transfers the implementation-domain context package to Gemini after ratification and before Gemini authors its first Implementation Specialist plan. The package includes, at minimum:

- `AXIOM_Ratification_File_Swap_Runbook.md`, if available;
- Kimi's Cycle 3 Implementability Review for the v1.0 → v1.1 governance cycle: `AXIOM_Governance_Implementability_Review_v1_2.md`;
- any Diff Gate scripts Kimi has packaged;
- archive directory conventions, including `AXIOM_Archive/<YYYYMMDD_HHMMSS>/` and `MANIFEST.sha256` expectations;
- the active `AXIOM_Canonical_Filenames.md` registry;
- any implementation-stage notes Kimi identifies in its final pre-transfer review.

If one of the named files does not exist in the project workspace, the operator records `not available` in the transfer note rather than substituting an unverified artifact.

**Residual Risk:** Gemini's first implementation plans may require tighter Evaluator review. This is acceptable because implementation plans already require review under Charter v1.1.

### §13.6 Risk 6 — DeepSeek Adversarial-Review Timing

**Risk:** Continuous-layer drafts may evolve without adversarial input until late in the cycle.

**Disposition:** Mitigated with §7.8 architectural trigger, §7.9 advisory access rights, and a DeepSeek early-touchpoint rule for security, trust-boundary, sandbox, network, agent-permission, Core Value, and coordination-rule changes.

**Residual Risk:** Non-security, non-architectural drafts may still reach DeepSeek only at formal review. That is acceptable because DeepSeek's role is adversarial review, not continuous co-drafting.

### §13.7 Risk 7 — Operator Load on Trigger Administration

**Risk:** PDR marking, trigger tracking, and affirmation artifacts may add operator overhead.

**Disposition:** Mitigated with a two-cycle transition-measurement note in Synthesis. The proposal avoids a separate mandatory transition log to limit new file overhead.

**Residual Risk:** Net operator load remains uncertain until tested. If excessive, the Evaluator should open specification debt after observing real cycle data.

---

## §14 Synthesis Requirements for This Amendment

The ratification Synthesis for this amendment must follow Charter v1.1's required Synthesis structure and must additionally include:

| Required Synthesis Element | Purpose |
|---|---|
| Current-panel-status statement | Confirms the current six-member v1.1 panel reviewed the amendment before the proposed structure took effect. |
| Operator Decision Record disposition | Confirms Decisions 1–4 were adopted, modified, or rejected with reasoning. |
| Seven-risk disposition table | Confirms all seven framework risks were addressed or deliberately deferred. |
| Cycle 1 Closure Map verification | Maps D-C1 through D-C5, E-C1 through E-C5, K-CLOSURE-1 through K-CLOSURE-6, and Q-CB-023 through Q-CB-025 to Cycle 2 dispositions. |
| Arbiter-elect affirmation summary | Confirms Kimi's AB-001 through AB-007 affirmation status before ratification and records that the affirmation did not re-run in Cycle 2. |
| PDR-ledger cross-check | Verifies that every PDR mark listed in the proposal's ledger is accounted for with a clearance artifact, deferral record, or escalation; no Pending mark remains unresolved in a domain required for ratification. |
| PDR Clearance Cross-Check table | Maps every PDR mark ID to its clearance disposition. If no PDR marks exist, the Synthesis records `None present` explicitly. |
| Pending-domain-review audit | Confirms no unresolved PDR claim is being used as ratification basis. |
| Missed-trigger objection adjudication | Records every missed-trigger objection, the cited text, the domain trigger rule allegedly violated, and the Synthesis disposition. |
| Advisory access compliance | Confirms that any advisory request for draft access was fulfilled or logged as specification debt with unavailability reason. |
| Binding preservation check | Confirms all AB/CB/GB binding texts remain preserved unless explicitly superseded. |
| CB-023 through CB-025 activation check | Confirms whether the three Qwen-issued CB conditions are authorized for insertion into `AXIOM_Active_Bindings_v1_2.md` upon ratification. |
| GB-001 exception note | Confirms cross-cutting artifact packaging remains governed by GB-001 unless superseded. |
| Active Bindings schema transition authorization | Specifies whether the registry schema update may proceed and how Issuing Authority / Maintaining Authority fields are populated. |
| Delta-confirmation determination | Should state that this amendment is not delta-eligible because it modifies Charter operating structure. |
| 30-day audit instruction | Specifies the audit due date as 30 calendar days after actual ratification. |

The Synthesis cannot issue `RATIFIED` unless the PDR Clearance Cross-Check table is present. The Synthesis cannot issue `RATIFIED` until the Arbiter-elect affirmation artifact exists and is considered; for Cycle 2, the Synthesis records that the Cycle 1 affirmation artifact is the operative artifact and that no re-affirmation was required.

---

## §15 Migration Path After Ratification

If ratified, the operator performs these steps sequentially.

### §15.1 Archive Current State

Create an archive snapshot under:

```text
AXIOM_Archive/<YYYYMMDD_HHMMSS>/
```

Include current operative governance documents, this proposal, all review artifacts, the Arbiter-elect affirmation artifact, the Synthesis, and `MANIFEST.sha256`.

### §15.2 Update Charter

Update:

```text
AXIOM_Panel_Charter.md
```

to Charter v1.2 content reflecting:

- two-tier operating model;
- updated role assignments;
- consultation cadence rules;
- pending-domain-review mechanism;
- binding authority tiering;
- Arbiter-elect affirmation record;
- updated amendment log.

### §15.3 Update Active Bindings Registry

Create:

```text
AXIOM_Active_Bindings_v1_2.md
```

from v1.1, adding Issuing Authority and Maintaining Authority fields while preserving all existing binding text.

During the file-swap:

1. AB-001 through AB-007 retain `Issuing Authority = Gemini`.
2. AB-001 through AB-007 update from `Maintaining Authority = Gemini` to `Maintaining Authority = Kimi` only after the ratification Synthesis authorizes transfer and this file-swap step is executed.
3. CB-001 through CB-022 retain Qwen as maintaining authority according to existing registry treatment.
4. CB-023 through CB-025 are inserted as new CB-class bindings with source cycle `Governance v2 Cycle 1`, status `Active`, `Issuing Authority = Qwen`, and `Maintaining Authority = Qwen`.
5. GB-001 through GB-004 retain full-panel authority and unchanged binding text.

Update:

```text
AXIOM_Active_Bindings.md
```

as a plain copy of `AXIOM_Active_Bindings_v1_2.md`.

### §15.4 Update Constraints Register Maintenance Notes

If the Constraints Register contains a maintenance ownership table, update it to reflect:

- Kimi as Maintaining Authority for AB bindings after affirmation/ratification;
- Qwen as Maintaining Authority for CB bindings;
- full panel as Maintaining Authority for GB bindings.

Do not alter hard constraints or binding text.

### §15.5 Update Canonical Filenames Registry

Add:

```text
AXIOM_Proposal_Governance_v2.md
AXIOM_Proposal_Governance_v2_1.md
AXIOM_Arbiter_Elect_Affirmation_v1.md
AXIOM_Synthesis_Governance_v2_Cycle1.md
AXIOM_Synthesis_Governance_v2_Cycle2.md
AXIOM_Active_Bindings_v1_2.md
AXIOM_Panel_Tier_Membership.md
```

Use the actual Cycle 2 Synthesis filename assigned by the Evaluator if different.

`AXIOM_Panel_Tier_Membership.md` becomes the canonical reference for post-ratification tier membership. It may be updated only by Charter amendment or explicit governance binding; ordinary Synthesis notes, operator convenience edits, or proposal crosswalks do not modify tier membership.

### §15.6 Update Specification Debt Ledger

Append any new specification debt opened during this amendment cycle. Do not remove prior debt entries.

### §15.7 Record Ratification Confirmation

Create a ratification confirmation artifact naming:

- ratification date;
- Synthesis authority;
- file-swap completion date;
- Active Bindings schema update completion;
- AB-001 through AB-007 maintenance transfer status;
- 30-day audit reminder date.

### §15.8 Set 30-Day Audit Reminder

Because this is the first Charter amendment after v1.1 ratification, the Charter v1.1 30-day audit clause applies prospectively to this amendment. The operator sets the audit reminder for 30 calendar days after the actual ratification date.

The audit does not reopen v1.0 → v1.1. It reviews decisions made under this amendment cycle according to Charter v1.1's prospective-only audit rule.


### §15.9 Create Panel Tier Membership Reference

Create:

```text
AXIOM_Panel_Tier_Membership.md
```

with this minimum table:

| Tier | Role | AI System | Consultation Cadence | Authority Notes |
|---|---|---|---|---|
| Continuous Working Layer | Chief Architect and Researcher | GPT-5.5 / ChatGPT | Continuous | Proposal origination and research drafting; no unilateral final authority. |
| Continuous Working Layer | Quality and Coherence Evaluator | Claude Opus 4.7 | Continuous | Coherence review, Synthesis, debt tracking, binding preservation checks. |
| Continuous Working Layer | Implementation Specialist and Troubleshooter | Gemini 3.1 Pro | Continuous | Implementation planning and troubleshooting; no AB authority after transfer. |
| Advisory Council | Adversarial Critic | DeepSeek V4 | Domain-triggered plus mandatory gates | Valid objections closure-required unless overruled under Charter process. |
| Advisory Council | Constraints and Feasibility Reviewer | Qwen 3.6 Plus | Domain-triggered plus mandatory gates | CB rulings binding when issued. |
| Advisory Council | Research and Knowledge Arbiter | Kimi K2.6 | Domain-triggered plus mandatory gates | AB rulings binding when source-backed and issued after role transfer. |

The file is a reference mirror of the ratified Charter. If it conflicts with the Charter or Active Bindings registry, the Charter and Active Bindings registry control.

---

## §16 Proposed Charter Amendment Log Entry

If ratified, add this entry to the Charter Amendment Log:

| Version | Date | Section | Amendment | Rationale | Panel Consensus |
|---|---|---|---|---|---|
| 1.2 | `<ratification date>` | Panel Composition / Role Assignments / Decision Flow / Consultation Cadence / Binding Authority / Active Bindings Authority | Introduced continuous working layer and advisory council operating model; moved Gemini to Implementation Specialist and Troubleshooter; moved Kimi to Research and Knowledge Arbiter after Arbiter-elect affirmation; expanded GPT-5.5 to Chief Architect and Researcher; added pending-domain-review mechanism and active-binding authority metadata. | Aligns role cadence with actual contribution patterns while preserving domain-based binding authority and preventing continuous-layer bypass of advisory review. | `<Synthesis records affirmative consensus or final disposition>` |

---

## §17 Ratification Standard

This amendment requires full Charter amendment review under Charter v1.1. It is not delta-eligible.

Ratification requires affirmative consensus from the reviewing panel under the current Charter v1.1 role assignments. The proposed tier structure does not take effect until ratification.

For Cycle 2, ratification requires all of the following simultaneously:

1. all seven structural corrections identified in Synthesis §10 are adopted: D-C1, D-C2, D-C3, D-C4, D-C5, E-C4, and Q-CB-023 through Q-CB-025 restatement;
2. DeepSeek issues affirmative concurrence or withdraws the Cycle 1 conditional hold;
3. Claude, Gemini, Qwen, and Kimi reaffirm or shift to affirmative concurrence;
4. no new blocking concerns are introduced by this revision;
5. Cycle 1 SD items remain at cycle 1 of 2 unless the Cycle 2 Synthesis lawfully records closure after ratification.

The Chief Architect sponsors this proposal but does not treat it as final. Every panel role may challenge any element. Any objection, qualification, or unresolved risk must be handled through Synthesis before ratification.

---

*End of `AXIOM_Proposal_Governance_v2_1.md`*
