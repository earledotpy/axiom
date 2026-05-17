# AXIOM — Panel Restructuring Amendment Framework
## Operating-Model Amendment Proposal — Framework for Chief Architect

**Document Type:** Amendment Framework (Pre-Proposal Working Document)
**Status:** Framework for Architect Use — Not Yet a Formal Proposal
**Authored By:** Quality and Coherence Evaluator (Claude)
**Issued Under:** Charter v1.1 §Charter Amendment Process
**Date Issued:** [Date Operator Sends to Architect]
**Target Architect:** GPT-5.5
**Target Output:** `AXIOM_Proposal_Governance_v2.md`

---

## What This Document Is

This document is a structural amendment framework prepared by the Quality and Coherence Evaluator for the Chief Architect's use. It provides the operator's rationale, the scope of the proposed amendment, the decision record explaining how this rationale was derived, the role-mapping table, the trigger-rule specification, the Arbiter-elect affirmation procedure, and the unresolved risks the formal proposal must address.

**This is not a formal proposal.** It does not enter the panel review cycle in its current form. The Chief Architect (GPT-5.5) receives this framework, exercises architectural judgment over it, and produces the formal `AXIOM_Proposal_Governance_v2.md` that enters the panel cycle for review under Charter v1.1.

**The Architect may.** Adopt the framework's content wholesale into the proposal. Modify any element where architectural judgment finds improvement opportunities. Reject specific elements with explicit reasoning. Add scope the framework did not anticipate. Surface gaps the framework missed.

**The Architect may not.** Treat this framework as authoritative content that bypasses panel review. Frame this document or the operator's preferences as constraints on architectural judgment. Skip rationale that the framework provides. The framework's role is to give the Architect a precise starting point and to surface the operator's decision record. The proposal's role is to be the Architect's own.

This pattern preserves the separation of duties stabilized through the v1.0 → v1.1 cycle. The Evaluator does not originate design proposals. The Architect does.

---

## Operator Decision Record

The operator made four explicit decisions about the structural amendment. These decisions shape the framework's content. The Architect is informed of them not as binding constraints but as context for the operator's intent.

### Decision 1 — Tier structure rationale

The amendment splits the panel into a continuous working layer (Claude, ChatGPT, Gemini) and an advisory council (Qwen, Kimi, DeepSeek). The operator's primary basis is contribution cadence and role fit: continuous-layer roles handle proposal creation, synthesis, implementation planning, deployment support, troubleshooting, and research exploration; advisory roles handle narrower, episodic, domain-triggered work.

The operator's secondary basis is operational capacity: paid access, higher usage limits, and stronger shared-context workflows make Claude, ChatGPT, and Gemini better suited for continuous-layer work. Subscription access is operational support rationale only, not constitutional basis for authority.

### Decision 2 — Gemini and Kimi role swap

Gemini moves from Research and Knowledge Arbiter to Implementation Specialist and Troubleshooter. Kimi moves from Implementation Specialist to Research and Knowledge Arbiter. The operator's rationale is intentional and primary, not incidental: implementation and troubleshooting are continuous-layer functions that benefit from Gemini's Drive-connected continuous presence; Arbiter work is narrower, episodic, and domain-triggered, which fits Kimi's advisory cadence. The swap is a role-cadence decision first and an access decision second.

### Decision 3 — AB binding authority transition

Gemini remains historically attributed as the issuing Arbiter for AB-001 through AB-007. Kimi becomes the maintaining Arbiter only after explicit Arbiter-elect affirmation during the amendment cycle. The Active Bindings registry remains single and authoritative — attribution history and current maintenance authority are audit metadata, not different binding classes.

### Decision 4 — Continuous-layer bypass prevention

The continuous layer is not permitted to make de facto decisions that advisory roles only review afterward. Three trigger rules codify this: factual-claim trigger (Arbiter), feasibility-claim trigger (Constraints), adversarial-review timing (DeepSeek before ratification and before implementation planning becomes authoritative). The operator added one operational sentence specifying that affected claims remain marked "pending domain review" until the relevant advisory role has reviewed them or the Evaluator has explicitly ruled the trigger was not engaged.

---

## Proposed Amendment Scope

The amendment modifies Charter v1.1 in the following sections. The Architect's formal proposal addresses each. Any additional sections the Architect finds necessary are at the Architect's discretion.

**§Panel Composition.** Current Charter v1.1 lists six panel roles without tiering. The amendment introduces a two-tier structure: continuous working layer (three members) and advisory council (three members). Existing role definitions remain authoritative for binding authority; tier classification affects consultation cadence only.

**§Role Assignments.** Three role assignments change:
- Gemini moves from Research and Knowledge Arbiter to Implementation Specialist and Troubleshooter.
- Kimi moves from Implementation Specialist to Research and Knowledge Arbiter.
- ChatGPT expands from Chief Architect to Chief Architect and Researcher (expanded scope for new opportunity discovery, architectural research, and proposal drafting).

Claude (Quality and Coherence Evaluator), Qwen (Constraints and Feasibility Reviewer), and DeepSeek (Adversarial Critic) retain their current role assignments. Their tier classification changes (Claude continuous, Qwen advisory, DeepSeek advisory) without role redefinition.

**§Consultation Cadence Rules.** A new subsection specifies when advisory members are consulted:
- Domain-trigger consultation as the standard pattern.
- Mandatory ratification gates when a proposal reaches ratification and the advisory member's domain is implicated.
- The continuous-layer bypass-prevention rules (factual-claim trigger, feasibility-claim trigger, adversarial-review timing).

**§Binding Authority Tiering.** A new subsection specifies that binding authority is tiered by role domain, not by inner/advisory status:
- Qwen feasibility rulings remain binding when issued.
- Kimi factual Arbiter rulings remain binding when issued with source-backed evidence.
- DeepSeek objections are not factual bindings but valid adversarial objections remain closure-required unless overruled under the Charter process.
- Gemini implementation findings are not bindings by default but implementation blockers can become specification debt or return-to-Architect items through Synthesis.

**§Active Bindings Registry Maintenance.** Updated to reflect that Kimi is the maintaining Arbiter for AB bindings going forward, while Gemini remains historically attributed as the issuing Arbiter for AB-001 through AB-007. Single registry, single authority structure preserved. Maintenance ownership table in the Constraints Register §8.5 is updated correspondingly.

**§Arbiter-Elect Affirmation Procedure.** A new subsection specifies the affirmation step Kimi performs during the amendment cycle before role transfer ratifies. Procedure detailed in the Affirmation section below.

**Charter Amendment Log entry.** Records the v1.1 → v1.2 amendment with rationale and panel consensus signature.

---

## Tier Structure

| Tier | Role | AI System | Drive Integration | Consultation Cadence |
|---|---|---|---|---|
| Continuous Working Layer | Chief Architect and Researcher | GPT-5.5 (ChatGPT) | Yes (paid) | Continuous — proposal creation, research, drafting |
| Continuous Working Layer | Quality and Coherence Evaluator | Claude (Claude.ai) | Yes (paid) | Continuous — review, synthesis, debt tracking |
| Continuous Working Layer | Implementation Specialist and Troubleshooter | Gemini (Gemini Pro) | Yes (paid) | Continuous — implementation plans, deployment support, troubleshooting |
| Advisory Council | Adversarial Critic | DeepSeek (free tier) | No | Domain-triggered + mandatory ratification gate |
| Advisory Council | Constraints and Feasibility Reviewer | Qwen (free tier) | No | Domain-triggered + mandatory ratification gate |
| Advisory Council | Research and Knowledge Arbiter | Kimi (free tier) | No | Domain-triggered + mandatory ratification gate |

**Tier classification governs consultation cadence. It does not govern binding authority.** Advisory council members retain full binding authority within their domains per the binding-authority-tiering rule.

---

## Consultation Cadence Rules

### Standard pattern — domain-triggered consultation

The continuous layer (Architect, Evaluator, Implementation Specialist) handles ongoing design work through Drive-shared documents. When a domain-triggered situation arises, the relevant advisory member is consulted before the affected output is treated as authoritative.

### Domain triggers

**Arbiter (Kimi) is consulted when:**
- A factual claim about external technology is made (tools, APIs, libraries, model behavior, platform limits, file formats, current technical state).
- An existing AB binding is referenced in a context where its continued accuracy matters.
- A new factual claim would qualify as an AB binding if affirmed.

**Constraints (Qwen) is consulted when:**
- A RAM, thread, API budget, local model feasibility, runtime cost, persistence burden, hardware compatibility, or deployment sustainability claim is made.
- An existing CB binding is referenced in a context where its continued accuracy matters.
- A new feasibility claim would qualify as a CB binding if affirmed.

**Adversarial Critic (DeepSeek) is consulted when:**
- A proposal reaches completeness for ratification review.
- A revision-cycle proposal is ready for adversarial scrutiny — not deferred to final ratification gate.
- Continuous-layer work produces a security model, trust boundary specification, or attack surface definition.

### Mandatory ratification gates

Regardless of whether the standard pattern triggered consultation earlier in the cycle, every proposal that reaches ratification review under Charter v1.1 §Synthesis Workflow must be reviewed by every advisory member whose domain is implicated. The ratification Synthesis cannot rule affirmative without each implicated advisory member's affirmative position.

### Pending-domain-review marking

When the continuous layer drafts content containing a factual, feasibility, or adversarial-relevant claim that has not yet been reviewed by the corresponding advisory member, that claim is marked "pending domain review" in the document.

A claim remains marked until either:
- The relevant advisory member reviews the claim and rules on it, or
- The Evaluator explicitly rules in a Synthesis document that the domain trigger was not engaged.

Pending-domain-review claims may be drafted, discussed, and refined in the continuous layer. They may not be the basis for ratification, implementation, or binding issuance until the mark is cleared.

This rule preserves continuous-layer speed without letting speed become authority.

---

## Binding Authority Tiering

Binding authority is determined by role domain, not by tier classification.

**Qwen feasibility rulings (CB bindings) remain binding when issued.** A CB binding takes force the moment Qwen issues it during panel review and persists in the Active Bindings registry until explicitly superseded by a later panel ruling.

**Kimi factual Arbiter rulings (AB bindings) remain binding when issued with source-backed evidence.** AB bindings issued under Kimi's Arbiter authority operate under the same supersession rules as CB bindings.

**DeepSeek objections are not factual bindings.** They are adversarial findings that the Synthesis must rule on. A valid DeepSeek objection is closure-required for the proposal under review unless explicitly overruled by the Synthesis under Charter v1.1 §Conflict Resolution.

**Gemini implementation findings are not bindings by default.** Gemini operates in the continuous layer producing implementation plans, troubleshooting guidance, and deployment support. When Gemini identifies an implementation blocker (a gap that prevents executing an approved proposal), the finding becomes either a specification debt item (logged in the Specification Debt ledger) or a return-to-Architect item (routed back to GPT-5.5 for design revision). Neither path is a binding in the AB/CB/GB sense.

**GB bindings remain panel-ratified governance bindings.** They are issued through Charter amendments under Charter v1.1 §Charter Amendment Process. No tier change affects GB issuance authority.

---

## Active Bindings Registry — Transition Rules

### Historical attribution preserved

AB-001 through AB-007 remain attributed to Gemini as the issuing Arbiter at the time of issuance. The Active Bindings registry records the historical attribution and does not retroactively assign these bindings to Kimi.

### Maintenance authority transferred upon affirmation

Once the amendment ratifies and the Arbiter-elect affirmation procedure (below) completes successfully, Kimi becomes the maintaining Arbiter for AB-001 through AB-007. Maintenance authority includes:

- Verifying continued accuracy of existing AB bindings when they are referenced in new proposals.
- Issuing new AB bindings going forward.
- Ruling on supersession of existing AB bindings if external technology behavior changes.
- Authoring updates to AB binding descriptions if the underlying fact remains true but the description requires refinement.

### Single registry preserved

The Active Bindings registry remains a single file (`AXIOM_Active_Bindings_v1_1.md` with `AXIOM_Active_Bindings.md` alias). Attribution history and current maintenance authority are audit metadata recorded within each binding row — not separate registry tiers.

### Registry schema extension

Each binding row gains two fields:
- **Issuing Authority:** the AI system that originally issued the binding (e.g., "Gemini" for AB-001 through AB-007).
- **Maintaining Authority:** the AI system currently responsible for maintenance (e.g., "Kimi" for AB-001 through AB-007 after affirmation).

For bindings issued after Charter v1.2 takes force, Issuing Authority and Maintaining Authority are the same on issue date. They may diverge over time if future role transitions occur.

---

## Arbiter-Elect Affirmation Procedure

This is a new amendment-cycle step inserted between Kimi's standard Implementation Specialist review of `AXIOM_Proposal_Governance_v2.md` and the final ratification Synthesis. The procedure exists because the proposal transfers Arbiter maintenance authority from Gemini to Kimi for AB-001 through AB-007, and that transfer cannot ratify without Kimi taking explicit ownership of the bindings.

### When the procedure runs

The procedure runs during the panel review cycle for the structural amendment. It happens after Kimi's standard Implementation Specialist review of the amendment proposal and before the ratification Synthesis. It is not a post-ratification step — affirmation must complete before ratification ruling.

### The affirmation deliverable

Kimi produces `AXIOM_Arbiter_Elect_Affirmation_v1.md` (or whatever filename the Canonical Filenames Registry assigns) containing a row-by-row review of AB-001 through AB-007. For each binding, the affirmation includes:

| Field | Description |
|---|---|
| Binding ID | AB-001 through AB-007 |
| Existing Issuing Arbiter | Gemini |
| Source Cycle | The cycle in which Gemini issued the binding (per AXIOM_Active_Bindings registry) |
| Kimi Affirmation Status | Affirmed / Qualified / Disputed |
| Source Basis or Verification Note | What Kimi verified to determine affirmation status — citation to current state of external technology, library documentation, or platform behavior |
| Qualification or Dispute Detail | If Status is Qualified or Disputed, what specifically Kimi finds different from Gemini's original ruling |
| Supersession or New Arbiter Review Requested | Yes / No, with reasoning |

### Affirmation outcomes

Three possible outcomes for each binding:

**Affirmed.** Kimi accepts the binding as still accurate. Upon amendment ratification, Kimi becomes the maintaining Arbiter for this binding.

**Qualified.** Kimi accepts the binding's substance but identifies refinements (e.g., updated library version, additional platform-specific notes). The affirmation document specifies the qualifications. Upon amendment ratification, Kimi becomes the maintaining Arbiter and the binding's description is updated per the qualifications recorded in the Synthesis.

**Disputed.** Kimi disputes the binding's continued accuracy. The structural amendment cannot ratify until the dispute is resolved through the normal Arbiter factual-dispute process. Resolution options:
- Gemini, as issuing Arbiter, may file a defense of the binding citing current evidence. The dispute then runs as a standard factual disagreement requiring panel review.
- Kimi may file a successor binding superseding the disputed one, citing new evidence.
- The panel may motion to retire the binding if both Gemini and Kimi agree the underlying fact no longer holds.

### Affirmation as ratification precondition

The structural amendment's Synthesis cannot rule RATIFIED if any AB-001 through AB-007 binding is in Disputed status. RATIFY-WITH-CONDITIONS is permissible if disputes are scoped and have clear resolution paths. The amendment may also be returned to the Architect with the affirmation document attached as a Cycle-input.

---

## Role Cadence and Expanded Scope Notes

### ChatGPT expanded role

ChatGPT's role expands from Chief Architect to Chief Architect and Researcher. The expansion is operational scope, not authority expansion. ChatGPT remains the originating role for architecture proposals. The "and Researcher" addition means ChatGPT also handles new opportunity discovery (identifying problems the panel should address before they become urgent), architectural research (exploring solution spaces before drafting proposals), and proposal drafting (producing working drafts in the continuous layer that may go through internal Evaluator review before becoming formal proposals).

The Architect should specify in the formal proposal whether "researcher" findings produced by ChatGPT can be used by the Evaluator or Implementation Specialist without triggering domain consultation rules. The framework's recommendation is: if a researcher finding contains factual or feasibility claims, the standard trigger rules apply regardless of which continuous-layer member produced the finding.

### Gemini implementation and troubleshooting role

Gemini's new role covers two related functions: producing operator-executable implementation plans from approved architecture proposals, and providing debugging and deployment support when implementation hits friction. Both functions are continuous-layer activities. The Architect should specify in the formal proposal whether troubleshooting outputs require Synthesis review or operate as Architect-routed operational support.

The framework's recommendation is: implementation plans require Evaluator delta-confirmation as currently specified in Charter v1.1 §Integration Discipline; troubleshooting outputs operate as operational support and do not require Synthesis review unless they propose architectural changes.

### Kimi Arbiter cadence

Kimi's new role is the Arbiter described in Charter v1.1 §Research and Knowledge Arbiter (currently held by Gemini). The role's responsibilities transfer wholesale. The cadence change is that Kimi participates only when triggered by domain rules, not continuously across every cycle. This makes the role compatible with free-tier rate limits while preserving its substantive authority.

### Claude, Qwen, DeepSeek roles unchanged

Claude's role as Quality and Coherence Evaluator and Synthesis authority remains as Charter v1.1 specifies. Qwen's role as Constraints and Feasibility Reviewer remains unchanged. DeepSeek's role as Adversarial Critic remains unchanged. Tier classification changes for Qwen and DeepSeek (both moved to advisory) but their substantive responsibilities are unchanged.

---

## Unresolved Risks

The framework surfaces these risks for the Architect to address in the formal proposal. Each is a known concern with no resolution prescribed by the operator. The Architect's judgment determines how each is handled.

### Risk 1 — Continuous-layer drift

Three AI systems reading from shared Drive folders may interpret the same documents slightly differently and produce drift that the operator must reconcile manually. The pending-domain-review marking rule mitigates substantive drift on factual and feasibility claims, but does not prevent drift on architectural interpretation. The Architect should consider whether the amendment needs a continuous-layer-synchronization mechanism, or whether drift is an acceptable operational trade-off.

### Risk 2 — Advisory rate-limit fragility

The advisory council operates on free-tier subscriptions. If any advisory member's rate limits cause a domain-triggered consultation to fail or stall, the amendment lacks a defined fallback. The Architect should consider whether the proposal needs a rate-limit-handling rule (e.g., scheduled retry, fallback to alternate model, escalation to continuous-layer panel motion).

### Risk 3 — Trigger-rule enforcement

The factual-claim and feasibility-claim trigger rules depend on continuous-layer members correctly identifying when their work product contains a triggering claim. Self-enforcement may be unreliable, especially for ChatGPT's research outputs where the line between speculation and factual claim is contextual. The Architect should consider whether the amendment needs an Evaluator-enforced trigger-detection step in the Synthesis workflow.

### Risk 4 — Arbiter-elect affirmation timing

The affirmation procedure runs during the amendment cycle. If Kimi disputes one or more AB bindings, the structural amendment is blocked. This creates a circular dependency: the amendment cannot ratify until Kimi affirms, but Kimi has no operational authority to be the Arbiter until the amendment ratifies. The framework treats Kimi's affirmation as Arbiter-elect (provisional Arbiter authority for the affirmation step only). The Architect should consider whether the proposal needs to formalize this provisional authority explicitly or treat it as implicit in the affirmation procedure.

### Risk 5 — Implementation Specialist role transition

Gemini's transition to Implementation Specialist requires Gemini to take ownership of implementation work that Kimi has historically performed. There is no implementation-work-in-progress at amendment time (the v1.0 → v1.1 cycle was governance, not implementation), so no in-flight transfer is required. But if the amendment ratifies and the AXIOM system implementation begins shortly after, Gemini will be producing implementation plans without the cycle-by-cycle history that Kimi accumulated. The Architect should consider whether the amendment needs a knowledge-transfer procedure from Kimi to Gemini for implementation-domain context, or whether starting fresh is acceptable.

### Risk 6 — DeepSeek adversarial-review timing

The amendment specifies that DeepSeek reviews complete proposals before ratification and before implementation planning becomes authoritative. This is the current pattern under Charter v1.1. The amendment does not weaken DeepSeek's role. But the continuous-layer's velocity may produce many drafts that never reach DeepSeek before being refined or discarded, which means DeepSeek's adversarial perspective is not informing continuous-layer iteration. The Architect should consider whether the amendment needs a continuous-layer "DeepSeek touchpoint" rule (e.g., adversarial spot-check on any continuous-layer draft that touches security model or trust boundaries).

### Risk 7 — Operator load on trigger-rule administration

The pending-domain-review marking rule, the trigger detection responsibility, and the affirmation procedure all impose new operator overhead. The amendment may reduce overall friction (less copy-paste between AI systems) while adding new friction (more tracking of pending reviews, more triggering decisions). The net effect is uncertain. The Architect should consider whether the amendment needs a transition period during which the operator measures actual friction before treating the new structure as fully operative.

---

## Charter v1.1 Procedural Compliance Notes

The Architect's formal proposal must satisfy Charter v1.1 amendment procedure requirements:

**Closure Map requirement.** The proposal must include a §0 Closure Map for any objection or specification debt item it closes. At first cycle, this is empty (no prior cycle exists for this proposal). At second cycle and beyond, it tracks closures from the prior cycle.

**Synthesis structure.** The Cycle 1 Synthesis for this amendment must follow Charter v1.1 §Synthesis Document Structure (the eight-section template ratified in v1.0 → v1.1).

**Cross-cutting artifact considerations.** This amendment is not a cross-cutting artifact in the GB-001 sense — it modifies governance, not creates calibration corpora or validation datasets. The Cross-Cutting Artifact Protocol does not apply.

**Delta-confirmation eligibility.** This amendment will almost certainly require full panel cycles for both Cycle 1 and any revision cycles. Delta-confirmation fails on the four-condition eligibility test because the amendment touches Charter content by definition.

**30-day audit clause activation.** This is the first Charter amendment after v1.0 → v1.1 ratification. The retroactive 30-day audit clause applies to this amendment. Upon ratification, the audit due 30 days later will have substantive scope reviewing decisions made during this amendment's cycle.

**Charter Amendment Process specifications.** The amendment proceeds under Charter v1.1 §Charter Amendment Process. Affirmative consensus from all panel members is required for ratification. The panel composition during review is the current six-member composition (v1.1 panel structure), not the proposed three-plus-three composition.

**Active Bindings travel forward.** All 33 active bindings from `AXIOM_Active_Bindings_v1_1.md` continue to apply during and after the amendment. The amendment does not modify any binding text — only registry schema and maintenance authority.

---

## Recommended Proposal Structure

The framework recommends but does not require the following structure for `AXIOM_Proposal_Governance_v2.md`. The Architect's judgment determines the actual structure.

**§0 Closure Map.** Empty at Cycle 1 entry. Populated in subsequent cycles per Charter v1.1 §Specification Debt closure-tracking.

**§1 Amendment Identity and Scope.** What the amendment is, what it changes, what it does not change.

**§2 Tier Structure Definition.** The continuous working layer and advisory council, with explicit role assignments and the binding-authority-tiering rule.

**§3 Consultation Cadence Rules.** Domain triggers, mandatory ratification gates, pending-domain-review marking.

**§4 Role Assignments.** New role definitions for each panel member, with explicit notation for which roles change and which do not.

**§5 Active Bindings Registry Schema Extension.** Issuing Authority and Maintaining Authority fields, transition rules, historical attribution preservation.

**§6 Arbiter-Elect Affirmation Procedure.** The procedure Kimi runs during this amendment cycle to take maintenance ownership of AB-001 through AB-007.

**§7 Continuous-Layer Operational Rules.** Drive-shared workflow guidance, trigger-rule enforcement responsibilities, pending-domain-review administration.

**§8 Charter Amendment Log Entry.** The v1.1 → v1.2 entry.

**§9 Risk Acknowledgment.** Explicit treatment of the unresolved risks the framework surfaced and the Architect's chosen handling for each.

**§10 Migration Path.** What the operator does during and after ratification — including the Arbiter-elect affirmation step and any other transition operations.

---

## Closing Note to the Architect

This framework gives you everything the operator decided and everything the Evaluator believes the proposal must address. Use it as a starting point, not a constraint. Where the framework's logic holds, adopt it. Where your architectural judgment finds gaps or improvements, modify or replace. Where you disagree with operator decisions, surface the disagreement in the proposal and let the panel rule.

The proposal you produce will be reviewed by the full six-member panel under Charter v1.1's amendment process. Every panel member can challenge any element. Affirmative consensus from all members is the threshold for ratification. The amendment is not adopted because the operator wants it; it is adopted because the panel, including its adversarial role, finds it sound.

When you produce `AXIOM_Proposal_Governance_v2.md`, file it as the Cycle 1 input and the operator routes it into panel review per the standard sequence: Evaluator → Critic → Arbiter → Constraints → Implementation Specialist → Arbiter-Elect Affirmation (this is the new step inserted before Synthesis) → Synthesis.

The Evaluator awaits your proposal.

---

*AXIOM Panel Restructuring Amendment Framework*
*Issued under Charter v1.1 §Charter Amendment Process*
*Authored by Quality and Coherence Evaluator (Claude)*
*Not a formal proposal — framework for Chief Architect use only*
