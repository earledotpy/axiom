# AXIOM_Proposal_Governance_v1.2.md
## Targeted Governance Amendment Proposal — Cycle 3 Patch Revision

**Document Type:** Chief Architect Proposal  
**Status:** Proposed — Targeted Cycle 3 Patch for Ratify-with-Conditions Closure  
**Authoring Role:** GPT-5.5 — Chief Architect  
**Date:** 2026-05-08  
**Supersedes:** `AXIOM_Proposal_Governance_v1.1.md` only where explicitly revised below  
**Revision Authority:** `AXIOM_Synthesis_Governance_v2.md` §8.2  
**Routing Authority:** `AXIOM_Synthesis_Governance_v2.md` §8.3  
**Scope Constraint:** This revision closes only the five mandatory Cycle-3 DeepSeek corrections plus optional SD-019 and SD-024 closures. All v1.1 sections outside §0, §3, §5, §4.2, and §6.5 carry forward unchanged.

---

## 0. Closure Map

### 0.1 Adopted Objection Disposition Matrix Schema

This proposal adopts the following schema for all objection-disposition tables, including this §0 Closure Map:

| Column | Required Meaning |
|---|---|
| Objection ID | Stable identifier assigned by the reviewing role or Synthesis ledger. |
| Raising Role | Panel role or ledger source that raised the item. |
| Subject | Concise description of the issue. |
| Disposition | `Closed`, `Deferred`, `Overruled`, or `Open`. |
| Reason | Specific reason for the disposition. |
| Binding Impact | Whether the disposition preserves, modifies, supersedes, or creates a binding. |
| Required Action | Section or artifact that performs the closure action. |

No additional matrix column may be used to bury unresolved items. If an item is not closed, the `Disposition` cell must say `Open` or `Deferred`; it may not be hidden in a notes field.

### 0.2 Cycle-1 Closure Map

| Objection ID | Raising Role | Subject | Disposition | Reason | Binding Impact | Required Action |
|---|---|---|---|---|---|---|
| D1 | DeepSeek | Delta self-certification loophole | Closed | Delta declaration remains Evaluator-authored but is subjected to a documented objection window, mandatory delta artifact, and reversal path. | GB-002 preserved; GB-003 reinforced. | §3.1 |
| D2 | DeepSeek | Specification debt can be hidden or relabeled | Closed | Open-flagging, append-only debt ledger, and invalid-Synthesis rule prevent silent carry-forward. | GB-004 preserved and operationalized. | §5.1–§5.4 |
| D3 | DeepSeek | Diff Gate unenforceable / restoration coupling insufficient | Closed | Diff Gate now specifies tool, prior-version retrieval, hash manifest, failure mode, and semantic binding check. | GB-003 preserved; no binding text modified. | §4.1–§4.6 |
| D4 | DeepSeek | Integrator identity / zero-trust governance ambiguity | Closed | Integrator role is assigned to Evaluator as gatekeeper and operator as mechanical executor; author cannot self-certify. | CV3 governance application; GB-003 reinforced. | §4.2 |
| D5 | DeepSeek | Retroactive-reopening loophole | Closed | Charter amendment audit is prospective-only and cannot automatically reopen or overturn prior decisions. | No active binding superseded. | §2 |
| C1 | Claude | Status of three v1.1 PROPOSED drafts | Closed | Drafts are formally withdrawn as independent ratification candidates and retained as reviewed source inputs only. | No binding impact. | §10.1 |
| C2 | Claude | Authorship provenance of v1.1 PROPOSED drafts | Closed | Explicit authorship statement records Evaluator-authored drafts and Architect-authored revision proposal. | No binding impact. | §10.2 |
| C3 | Claude | Specification-debt deferral authority and gate enforcement | Closed | Formal deferral record schema and gate-failure rule defined; unresolved debt at its gate blocks advancement. | GB-004 operationalized. | §5.3–§5.4 |
| C4 | Claude | Supersession reconciliation between binding sections | Closed | Single rule adopted: Active Bindings supersession language controls; mirrors do not supersede. | All AB/CB/GB bindings preserved. | §8.1 |
| C5 | Claude | Cross-cutting artifact protocol extension must be a panel motion | Closed | Six artifact classes are proposed through an explicit panel motion; no extension is treated as ratified before consensus. | GB-001 preserved; proposed extension isolated. | §6 |
| Q1 | Qwen | Discard B1–B22 numbering | Closed | Constraints Register correction rejects B-numbering as canonical and uses AB/CB/GB IDs only. | All 33 active bindings preserved. | §8.2 |
| Q2 | Qwen | Complete crosswalk using original binding IDs | Closed | All AB-001 through AB-007, CB-001 through CB-022, and GB-001 through GB-004 are restated verbatim. | No silent modification. | §8.3 |
| Q3 | Qwen | PROPOSED runtime invariants must be isolated from active bindings | Closed | Non-binding proposed constraints are segregated and may not appear in the binding crosswalk until ratified. | No new binding issued. | §8.4 |
| Q4 | Qwen | Supersession clause must be preserved | Closed | Supersession requires explicit later ruling; mirror/crosswalk text cannot supersede. | Active Bindings source-of-truth preserved. | §8.1 |
| K1 | Kimi | Objection Disposition Matrix schema undefined | Closed | Schema adopted and used by this §0 Closure Map. | No binding impact. | §0.1 |
| K2 | Kimi | Specification debt canonical storage location and format unspecified | Closed | `AXIOM_Specification_Debt.md` designated as canonical append-only ledger with schema. | GB-004 operationalized. | §5.2 |
| K3 | Kimi | Synthesis workflow naming, trigger, storage underspecified | Closed | Naming convention, trigger condition, and storage/upload requirement defined. | No binding impact. | §9.1 |
| K4 | Kimi | CV2 approval mechanism for sanitization tasks unspecified | Closed | Approval mechanism is documentation/process-based: Active Binding, ratified spec, or Synthesis-authorized scope. | No runtime cost; CB bindings untouched. | §7.1 |
| K5 | Kimi | CV5 infrastructure guardrail enforcement unspecified | Closed | Guardrail enforcement is assigned to implementation-stage registries, schemas, and structured logs; governance ratification adds no runtime infrastructure. | AB-006 cross-referenced; CB-001/CB-002 untouched. | §7.2 |
| K6 | Kimi | Binding crosswalk maintenance owner and validation step unspecified | Closed | Evaluator owns synthesis-time validation; binding issuers own source rulings; Architect restates relevant bindings. | Active Bindings maintenance preserved. | §8.5 |
| K7 | Kimi | Active Bindings filename and alias convention unspecified | Closed | Versioned canonical filename pattern and plain-copy alias convention specified. | No binding text modified. | §9.2 |
| K8 | Kimi | Charter amendment 30-day audit operationalization unspecified | Closed | Trigger, artifact, storage, and outcome path defined; audit is prospective-only. | D5 closure reinforced. | §2.2 |
| K9 | Kimi | Cross-cutting artifact ownership edges and physical creation semantics unresolved | Closed | Six classes enumerated; uniform ownership retained; operator physical creation separated from authorship. | GB-001 preserved. | §6.1–§6.3 |
| K10 | Kimi | Canonical filenames registry absent | Closed | `AXIOM_Canonical_Filenames.md` designated; Evaluator maintains it at Synthesis time. | Supports GB-003. | §9.3 |
| K11 | Kimi | Delta criterion #6 depends on Diff Gate implementation | Closed | Sequencing rule states delta criterion cannot be satisfied until §4 Diff Gate artifacts exist. | GB-002/GB-003 operationalized. | §3.4 |
| SD-001 | Synthesis / Kimi | Deferral authority for specification-debt items | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §5.3–§5.4 |
| SD-002 | Synthesis / Kimi | Authorship provenance of v1.1 PROPOSED drafts | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §10.2 |
| SD-003 | Synthesis / Kimi | §4.3 ↔ §7.3 supersession reconciliation | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §8.1 |
| SD-004 | Synthesis / Kimi | Status of GB-001 protocol extension — proposed vs. ratified | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §6.1 |
| SD-005 | Synthesis / Kimi | Identity of integration verification role | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §4.2 |
| SD-006 | Synthesis / Kimi | Self-flagging mechanism for unrecorded specification gaps | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §5.1 |
| SD-007 | Synthesis / Kimi | Kimi implementability review of Synthesis structure, Diff Gate, and binding crosswalk | Closed | Procedural deliverable was filed; substantive Kimi gaps are closed by SD-008 through SD-018. | No binding text modified unless explicitly cross-referenced as preserved. | §1.4 |
| SD-008 | Synthesis / Kimi | Objection Disposition Matrix schema | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §0.1 |
| SD-009 | Synthesis / Kimi | Specification debt canonical storage location and format | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §5.2 |
| SD-010 | Synthesis / Kimi | Synthesis workflow specification — naming, trigger, storage | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §9.1 |
| SD-011 | Synthesis / Kimi | CV2 panel-approval mechanism for sanitization tasks | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §7.1 |
| SD-012 | Synthesis / Kimi | CV5 infrastructure guardrail enforcement specifics | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §7.2 |
| SD-013 | Synthesis / Kimi | Constraints Register crosswalk maintenance and validation | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §8.5 |
| SD-014 | Synthesis / Kimi | Active Bindings filename standardization and alias maintenance | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §9.2 |
| SD-015 | Synthesis / Kimi | Charter amendment 30-day audit operationalization | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §2.2 |
| SD-016 | Synthesis / Kimi | Cross-cutting protocol artifact-type ownership edges | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §6 |
| SD-017 | Synthesis / Kimi | Canonical filenames registry build | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §9.3 |
| SD-018 | Synthesis / Kimi | Delta-confirmation criterion #6 ↔ §4.6 Diff Gate dependency | Closed | Closed in this revision; no Cycle-1 SD item is deferred. | No binding text modified unless explicitly cross-referenced as preserved. | §3.4 |

**Closure statement:** Every listed Cycle-1 objection and every specification-debt item SD-001 through SD-018 is closed in this revision. No Cycle-1 specification-debt item is deferred.

### 0.3 Cycle-3 Patch Closure Map

| Objection ID | Raising Role | Subject | Disposition | Reason | Binding Impact | Required Action |
|---|---|---|---|---|---|---|
| D1.A | DeepSeek | Hold-on-implementation rule absent from delta-confirmation | Closed | §3.3 now bars manual execution, code writing, and file modification based on a delta-confirmed revision until the objection window closes without objection; violation permanently invalidates the delta and triggers full panel review of both the revision and governance breach. | GB-002 and GB-003 preserved and hardened; no active binding text modified. | §3.3 |
| D1.B | DeepSeek | Objection window gameable by operator timing | Closed | §3.3 now closes the window only when all reviewing roles acknowledge no objection or 72 hours elapse, whichever is earlier. | GB-002 preserved; no active binding text modified. | §3.3 |
| D1.C | DeepSeek | Objection grounds could dismiss valid security objections | Closed | §3.3 now includes the Critic catch-all ground for any change reasonably believed to affect a Core Value or security property, even if not caught by the checklist. | CV1/CV3/CV6 protected; no active binding text modified. | §3.3 |
| D2.A | DeepSeek | Specification-debt flag-spam dismissal path absent | Closed | §5.6 creates a one-cycle no-objection dismissal path for trivial debt-ledger flags. | GB-004 preserved and operationalized; no active binding text modified. | §5.6 |
| D2.B | DeepSeek | Evaluator-as-single-point-of-failure in debt tracking | Closed | §5.7 requires every Synthesis to affirm that its open-issue list matches `AXIOM_Specification_Debt.md` and permits any panel member or operator to file a discrepancy flag. | GB-004 preserved and operationalized; no active binding text modified. | §5.7 |
| SD-019 | Cycle 2 Synthesis | Cross-cutting protocol class-list rationale absent | Closed | §6.5 records that v1.1 narrows the motion to concrete, reviewable artifact classes instead of treating draft phrasing as binding. | GB-001 preserved; no active binding text modified. | §6.5 |
| SD-024 | Cycle 2 Synthesis / Kimi | Kimi-as-alternate-gatekeeper tension | Closed | §4.2 reassigns alternate Diff Gate gatekeeper authority from Kimi to the Arbiter when the Evaluator authored the candidate revision, preventing the implementation packager from certifying its own packaged gate. | GB-003 reinforced; no active binding text modified. | §4.2 |

**Cycle-3 closure statement:** D1.A, D1.B, D1.C, D2.A, and D2.B are closed in this revision. Optional closures SD-019 and SD-024 are also closed. No Cycle-2 SD item advances to closure-required status in this patch; Cycle-2 SD items remain at cycle 1 of 2 unless explicitly closed above.

---

## 1. Revision Disposition

### 1.1 Executive Recommendation

The Chief Architect continues to recommend adoption of the governance amendment package after the closures in this document are accepted by full panel review.

The core recommendation from v1 remains unchanged: the governance package is directionally correct, but the Active Bindings registry must remain authoritative and the Constraints Register must not replace it with a parallel numbering scheme.

### 1.2 No New Architectural Scope

This proposal introduces no new runtime component, agent role, coordination mechanism, trust boundary, model behavior, provider behavior, or persistence behavior. The new mechanisms specified here are governance-process mechanisms required by Cycle-1 closure: matrix schema, debt ledger format, Diff Gate procedure, prior-version retrieval, and review routing.

### 1.3 Full Panel Cycle Status

Cycle 2 is a full panel review, not a delta-confirmation cycle. Delta eligibility remains unavailable because the closure revision adds governance mechanisms and operationalizes integration controls.

### 1.4 SD-007 Closure

SD-007 is closed because Kimi's implementability review was filed and incorporated into `AXIOM_Synthesis_Governance_v1_1.md`. The procedural debt item required the review to exist, not for that review to be unconditional. Kimi's substantive findings are represented and closed as K1–K11 and SD-008 through SD-018.

---

## 2. Constitutional Closure: Prospective-Only Charter Audit

### 2.1 Replacement Rule for Charter Amendment Audit

The 30-day Charter amendment audit is **prospective-only**. It may identify prior decisions that would have been handled differently under the amended Charter, but it does not automatically reopen, invalidate, relitigate, or overturn those decisions.

A prior decision may be reopened only if a new panel motion is filed and full panel consensus agrees that reopening is necessary. “Substantive equivalence,” “spirit of the rule,” or similar reasoning is insufficient to bypass this requirement.

### 2.2 Operationalization of the 30-Day Audit

After a Charter amendment is ratified, the operator creates a reminder for 30 calendar days after ratification. The Evaluator authors:

`AXIOM_Charter_Amendment_Audit_<YYYYMMDD>.md`

The audit artifact is stored beside the Synthesis documents and uploaded in fresh panel chats until the audit is closed. The artifact contains:

| Field | Required Content |
|---|---|
| Amendment reviewed | Charter version and section amended. |
| Review window | Exact date range reviewed. |
| Decisions flagged | Prior decisions that would have been routed differently under the amended Charter. |
| Recommended outcome | `No action`, `panel review recommended`, or `new motion required`. |
| Final status | Evaluator synthesis result after panel review, if any. |

The audit may flag decisions. It may not create bindings, supersede bindings, or alter ratified artifacts.

---

## 3. Delta-Confirmation Enforcement

### 3.1 Enforcing Role

The Quality Evaluator declares delta eligibility in the Synthesis document. That declaration is not self-executing. It becomes actionable only after the objection window in §3.3 closes without valid escalation.

### 3.2 Delta Artifact

Every delta-confirmation produces a short artifact:

`AXIOM_Delta_Confirmation_<ProposalName>_v<N>.md`

Required fields:

| Field | Required Content |
|---|---|
| Proposal under delta review | Filename and version. |
| Prior approved artifact | Filename, archive path, and SHA256 hash. |
| Authorized change list | Exact sections/lines/objects allowed to change. |
| Delta eligibility checklist | Each eligibility criterion marked Pass/Fail with one-sentence reason. |
| Diff Gate result | Path to diff output and pass/fail. |
| Binding check result | AB/CB/GB IDs checked and pass/fail. |
| Objection window | Start time, end time, and filed objections if any. |
| Final determination | `Delta confirmed`, `Escalated to full cycle`, or `Invalid`. |

### 3.3 Objection Window

The operator posts the delta artifact and revised proposal to every active panel role. The objection window closes only after either:

1. every reviewing role explicitly records no objection; or
2. 72 hours have elapsed after the operator posts the artifact, with no filed objection.

This is an all-roles-acknowledge OR 72-hours-elapsed rule, whichever occurs earlier. A shorter window may not be substituted by operator timing, informal availability assumptions, or partial-role acknowledgement.

No manual execution, code writing, or file modification based on a delta-confirmed revision may begin until the objection window closes without objection. Violation invalidates the delta permanently and triggers full panel review of both the revision and the governance breach.

A filed objection must cite at least one objection ground. Valid grounds include:

1. a delta-eligibility criterion allegedly violated;
2. a security or trust-boundary concern raised by DeepSeek;
3. a runtime, RAM, thread, or budget concern raised by Qwen;
4. a new factual claim raised by Gemini;
5. a coherence, binding, or artifact-integrity concern raised by the Evaluator;
6. any change that the Critic reasonably believes could affect a Core Value or security property, even if not caught by the delta-eligibility checklist.

A Critic objection under ground 6 is valid for routing purposes and cannot be dismissed inside the delta path. The revision must move to full panel review, where the objection is resolved by the normal panel sequence.

If any valid objection is filed, the delta route terminates and the revision moves to a full panel cycle.

### 3.4 Delta Reversal Procedure

If a panel member discovers after delta confirmation that a delta criterion was violated, the prior delta artifact is marked:

`Invalidated — full panel review required`

The affected revision is frozen. The next cycle is full panel review. No downstream implementation plan may rely on the invalidated delta confirmation.

### 3.5 Diff Gate Dependency

Delta eligibility criterion #6 is satisfied only by the Integration Diff Gate in §4. Until §4 tooling, prior-version retrieval, hash verification, binding cross-check, and failure mode are available, no revision may be delta-confirmed.

---

## 4. Integration Diff Gate and Integrator Role

### 4.1 Tooling Decision

The Integration Diff Gate uses a small Python script built on the Python standard-library `difflib` module to produce unified text diffs between the prior approved artifact and the candidate revision.

This choice is adopted because it has negligible pre-implementation execution cost, requires no long-running service, does not consume API tokens, and can be packaged by Kimi as an operator-executable script. Gemini may verify factual compatibility claims during Cycle 2, per Routing.

### 4.2 Integrator Role Identity

The integrator model is:

| Function | Assigned Role |
|---|---|
| Mechanical file copying, backup creation, command execution | Human Operator |
| Diff Gate gatekeeping and pass/fail certification | Quality Evaluator |
| Alternate Diff Gate gatekeeping when the Evaluator authored the candidate revision | Research and Knowledge Arbiter |
| Implementation packaging of the diff script and operator steps | Kimi |
| Adversarial challenge to the gate result | DeepSeek |
| Factual challenge to tooling claims | Gemini |
| Feasibility challenge to tooling burden | Qwen |

**Decision:** Keep the Evaluator as standing Diff Gate gatekeeper and reassign the alternate gatekeeper from Kimi to the Research and Knowledge Arbiter when the Evaluator authored the candidate revision.

**Reasoning:** Kimi packages implementation plans and should not also certify the gate that validates the packaged integration process. The Evaluator already owns Synthesis, coherence checking, and final review, so the Evaluator remains the correct standing gatekeeper when not authoring the candidate artifact. When the Evaluator is the author, the Arbiter is the least-conflicted alternate because the alternate certification is mechanical: prior artifact identity, hash presence, authorized-change comparison, and binding-text preservation. This does not convert the Arbiter into an architectural decision-maker. DeepSeek retains adversarial challenge authority; Qwen retains feasibility challenge authority; Kimi retains packaging authority.

**Anti-self-certification rule:** The author of a candidate revision may not certify its Diff Gate result. If the Evaluator authored the candidate revision under review, the Research and Knowledge Arbiter serves as alternate Diff Gate gatekeeper for that artifact only. The alternate assignment and reason must be recorded in the Synthesis.

### 4.3 Prior-Version Retrieval Mechanism

The source of truth for a prior version is the last panel-ratified artifact copied into:

`AXIOM_Archive/<YYYYMMDD_HHMMSS>/<filename>`

Each archive directory contains:

`MANIFEST.sha256`

The manifest records SHA256 hashes for every archived artifact. A candidate revision may be compared only against an archived prior version whose hash matches the manifest.

If the archive copy is missing, hash-mismatched, or ambiguous, the Diff Gate fails closed. The revision cannot proceed through delta-confirmation and must enter full panel review with explicit restoration instructions.

### 4.4 Authorized Change List

Every integration pass must include an Authorized Change List before editing begins. The list identifies:

| Field | Required Content |
|---|---|
| Artifact | Filename being revised. |
| Authorized section(s) | Headings, line ranges, object names, or table rows allowed to change. |
| Authorized purpose | Exact Synthesis item or panel instruction authorizing the edit. |
| Ratified text to preserve | Code blocks, schemas, regex, binding rows, filenames, values, and rule orderings that must remain character-identical. |
| Required verification | Diff check, binding check, schema check, filename check, or other relevant test. |

Any change outside the Authorized Change List is an integration failure unless it is strictly required to repair a formatting break caused by an authorized edit and is explicitly recorded.

### 4.5 Binding Cross-Check Method

The binding check is not ID-existence-only. The Evaluator verifies:

1. every active ID appears where required;
2. source cycle is unchanged;
3. status is unchanged;
4. binding text is character-identical when restated verbatim;
5. any paraphrase or mirror text does not weaken, rename, omit, or supersede the binding.

If exact text and paraphrase conflict, the exact text in `AXIOM_Active_Bindings_v1_0.md` controls unless explicitly superseded by later panel ruling.

### 4.6 Diff Gate Failure Mode

A Diff Gate failure has one of four dispositions:

| Failure Type | Required Response |
|---|---|
| Unauthorized change outside scope | Return to author for targeted repair; no delta available. |
| Missing prior artifact or hash mismatch | Full panel review required; no delta available. |
| Binding text mismatch | Restore binding text verbatim or obtain explicit supersession ruling. |
| Canonical filename/path mismatch | Restore canonical filename/path or file a panel motion to change it. |

No implementation plan may proceed from a candidate revision with an unresolved Diff Gate failure.

---

## 5. Specification Debt System

### 5.1 Open-Flagging Mechanism

Any panel member may file an `OPEN-GAP` item when a proposal contains a labeled component without mechanism, a referenced field without schema, a claimed property without enforcement point, a role without owner, or a process without artifact.

The Evaluator must include every filed `OPEN-GAP` in the next Synthesis open-issue list. If the Evaluator omits an openly filed gap, the Synthesis is incomplete and must be returned for correction.

### 5.2 Canonical Storage Location

The canonical specification-debt ledger is:

`AXIOM_Specification_Debt.md`

It is a discrete append-only ledger stored beside the four-document spine and uploaded in every fresh panel chat. It is not part of the Active Bindings registry and may not be used to supersede bindings.

### 5.3 Debt Ledger Schema

Each debt item uses this schema:

| Field | Required Content |
|---|---|
| Debt ID | Stable `SD-###` identifier. |
| Source | Proposal, Synthesis, role review, or panel cycle that opened the item. |
| Subject | Concise statement of the gap. |
| Severity | `Blocking`, `Medium`, `Low-Medium`, or `Low`. |
| Cycle Count | Number of cycles the gap has carried unresolved. |
| Status | `Open`, `Closed`, `Deferred`, or `Superseded`. |
| Closure Section / Artifact | Where the item is closed or deferred. |
| Notes | Residual risk, dependencies, or next gate. |

### 5.4 Formal Deferral Record

A debt item may be deferred only with a five-element record:

| Element | Required Content |
|---|---|
| 1. Debt ID | Stable `SD-###` identifier. |
| 2. Deferred Scope | Exact portion of the gap not resolved now. |
| 3. Deferral Rationale | Why closure now would produce worse design, false precision, or premature complexity. |
| 4. Residual Risk and Core Value Acknowledgement | Explicit risk carried forward and which Core Value tolerates or is strained by the deferral. |
| 5. Closure Gate, Owner, and Deadline | Concrete future event that forces closure, the responsible role, and the latest cycle by which closure is required. |

If the named closure gate passes and the debt remains unresolved, the affected proposal is blocked from entering implementation. The Evaluator returns it to the Architect regardless of other progress.

### 5.5 Cycle-1 SD Disposition

No Cycle-1 specification-debt item is deferred in this revision. SD-001 through SD-018 are closed in §0.2 and the sections cross-referenced there.

### 5.6 Trivial-Flag Dismissal Path

A panel member may motion to dismiss a debt-ledger flag as trivial. If no role objects within one cycle, the dismissal closes the flag.

A dismissal motion must identify the debt ID, quote the ledger subject line, and state why the issue is trivial rather than unresolved specification debt. If any role objects within the cycle, the debt item remains open and proceeds under the normal §5.3 ledger schema and §5.4 deferral rules. The dismissal path may not be used for blocking debt, binding-text drift, security-boundary ambiguity, or any item already marked closure-required.

### 5.7 Synthesis-vs-Ledger Cross-Check

The Evaluator's Synthesis must include an affirmative statement that the Synthesis open-issue list matches the `AXIOM_Specification_Debt.md` ledger. Any panel member or operator may compare the two and file a discrepancy flag.

A discrepancy flag must cite the Synthesis section, the debt-ledger entry or missing entry, and the alleged mismatch. Until the discrepancy is resolved, the Synthesis may not be treated as a complete closure record for that cycle. The discrepancy flag is itself entered into `AXIOM_Specification_Debt.md` unless corrected immediately as a clerical error in the same Synthesis cycle.

---

## 6. Cross-Cutting Artifact Protocol Extension Motion

### 6.1 Status of This Section

This section is a **proposed panel motion**, not a ratified extension. It preserves GB-001 unless and until full panel consensus ratifies the extension.

### 6.2 Six Artifact Classes Covered by the Proposed Extension

The proposed extension applies to these six classes:

1. calibration test sets;
2. validation corpora;
3. security regression suites;
4. sandbox escape test suites;
5. integration regression test datasets;
6. policy, manifest, and schema validation datasets.

### 6.3 Ownership Rule

The uniform ownership rule from GB-001 remains the default for all six classes:

| Responsibility | Owner |
|---|---|
| Primary authorship | Gemini |
| Adversarial review | DeepSeek |
| Coherence and final acceptance review | Claude |
| Feasibility review | Qwen |
| Implementation packaging | Kimi |
| Physical file creation | Human Operator |

**Decision:** Do not assign primary authorship of security regression suites or sandbox escape test suites to DeepSeek in this revision.

**Reasoning:** DeepSeek's adversarial input is essential, but GB-001 already records that initial assignment of cross-cutting artifact authorship to the Critic violates separation of duties. A modified ownership model may be proposed later, but it would need explicit full-panel consensus and binding update. This proposal does not silently supersede GB-001.

### 6.4 Physical Creation Semantics

“Physical file creation” means the operator writes the file to disk, copies text, runs file-generation commands, or uploads the artifact. It does not confer authorship, review authority, or design judgment.

### 6.5 Class-List Rationale

The v1.1 class list is intentionally framed as a proposed motion rather than a direct promotion of the earlier draft language. The shift from the draft wording to the six enumerated classes narrows the extension to concrete artifact types the panel already encountered or can review without speculative expansion: calibration test sets, validation corpora, security regression suites, sandbox escape test suites, integration regression test datasets, and policy/manifest/schema validation datasets. This preserves GB-001 while making the extension auditable before ratification.

---

## 7. Core Values Operational Clarifications

### 7.1 CV2 — Local Model Sanitization Approval Mechanism

The local model remains in lane when used for routing, private data handling, embeddings, and sanitization. “Panel-approved sanitization task” means a sanitization use that is authorized by at least one of the following:

1. an active binding;
2. a panel-ratified design specification;
3. a Synthesis-authorized revision scope.

No per-task runtime panel approval is required. This is a documentation/process approval mechanism only. It does not add a runtime registry, thread, database table, API call, or model invocation.

The local model may classify whether content is safe to pass. It may not decide whether a plan is good, override manifests, expand its own tool permissions, or approve high-risk actions without deterministic policy backstops.

### 7.2 CV5 — Infrastructure Guardrail Enforcement

The CV5 clarification that deterministic infrastructure is not agent coordination is accepted with an implementation-stage enforcement requirement:

| Guardrail | Required Implementation-Stage Artifact |
|---|---|
| Schema enforcement | Kimi must define the relevant schema validation point before queue-writing implementation proceeds. Manifest-file validation remains subject to AB-006. |
| Structured logging | Kimi must specify structured JSON log fields for queue writes, including task ID, component ID, actor role, field changed, old status when applicable, new status when applicable, and timestamp. |
| Field-assignment registry | Kimi must create or reference `AXIOM_Field_Assignment_Register.md` before implementing task-queue write permissions. |

These requirements are not runtime infrastructure at governance-ratification time. They create no new process, thread, API budget, or model load.

---

## 8. Constraints Register and Active Bindings Corrections

### 8.1 Supersession Rule

`AXIOM_Active_Bindings_v1_0.md` remains authoritative for active binding text and status.

A Constraints Register mirror, Charter reference, Core Values note, proposal crosswalk, or Synthesis summary does not supersede an active binding. Supersession requires a later panel ruling that explicitly cites the prior binding ID and states the replacement or supersession rationale.

### 8.2 Rejection of B1–B22 as Canonical Binding IDs

The proposed Constraints Register's `B1–B22` numbering must be withdrawn as a canonical binding scheme. The Constraints Register may mirror active bindings, but the canonical IDs remain:

- `AB-001` through `AB-007`;
- `CB-001` through `CB-022`;
- `GB-001` through `GB-004`.

### 8.3 Verbatim Active Binding Crosswalk

The following rows are restated verbatim from `AXIOM_Active_Bindings_v1_0.md`. They are not renamed, shortened, silently corrected, or superseded.

## Arbiter Bindings (Factual)

These are factual rulings from Gemini. They state how external technology actually behaves on the target environment. They are binding unless contradicted by new evidence.

| ID | Source Cycle | Ruling | Status |
|---|---|---|---|
| AB-001 | v1.2 | `subprocess.Popen` does not provide network isolation on Windows. Genuine sandbox network isolation requires a dedicated user account with a Windows Defender Firewall outbound-deny rule scoped to that SID, OR AppContainer with `internetClient` capability dropped. Windows Job Object + restricted token alone does NOT block network sockets. | Active |
| AB-002 | v1.4 | SQLite must be configured with `PRAGMA journal_mode=WAL` and an explicit `busy_timeout` (5–10 seconds). | Active |
| AB-003 | v1.9 | Sandbox wall-clock enforcement requires `subprocess.run(timeout=60)` (or thread timer) alongside the Windows Job Object. The Job Object alone enforces only RAM. | Active |
| AB-004 | v1.11 | Thinking-mode determination for `qwen3:4b` via Ollama must inspect the `parameters` field of `/api/show` response only. The `template` and `system` fields are not authoritative. Pattern: `(?i)^\s*think\s+false\s*$`. Function returns `'disabled'` on match, `'unknown'` on absence. State `'enabled'` is reserved for future Arbiter ruling. | Active |
| AB-005 | v1.11.3 | NetworkGateway must disable automatic HTTP redirect following (`allow_redirects=False` for Python `requests`, equivalent for other clients) and traverse redirect chains manually, applying allowlist enforcement at each hop. | Active |
| AB-006 | v1.11.3 | JSON Schema validation for manifest files must use a draft-07-or-later validator with `additionalProperties: false` enforced at every object level. | Active |
| AB-007 | v1.11.3 | sqlite-vec virtual table declaration uses `vec0` syntax with explicit dimension and distance metric. | Active |

---

## Constraints Bindings (Feasibility)

These are conditions issued by Qwen as part of feasibility approval. They are binding implementation constraints that the Architect must restate and Kimi must encode.

### Execution Model

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-001 | v1.7 | Sequential execution enforced. No two cognitive tasks run concurrently. | Active |
| CB-002 | v1.7 | Maximum four threads: main supervisor, Telegram gateway, Scheduler, Bootstrap worker. | Active |

### Local Model

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-003 | v1.7 | `qwen3:4b` remains Q4-quantized and memory-mapped via Ollama. | Active |
| CB-004 | v1.11.4 | ModelGateway must include `"think": false` in every local Ollama `/api/chat` and `/api/generate` request and reject any caller attempting to override. | Active |

### Sandbox

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-005 | v1.7 | Sandbox execution capped at 256 MB via Windows Job Object. | Active |
| CB-006 | v1.8.1 | Sandbox execution capped at 60 seconds wall clock. | Active |

### Persistence

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-007 | v1.7 | sqlite-vec batch limit of 100 vectors per query. | Active |
| CB-008 | v1.11.3 | SQLite cache_size = 32 MiB (`PRAGMA cache_size = -32768`). | Active |
| CB-009 | (pre-rebuild research) | Memory dedup uses pre-insertion cosine similarity check at threshold ≈0.92. | Active |

### Coordination and Budgets

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-010 | v1.7 | Context bundles capped at 500 KB serialized. | Active |
| CB-011 | v1.10 | Token estimation: 2.0× safety margin for calibrated paths, 1.5× for fallback paths. Manifest `max_estimated_input_tokens` ≥ 2× expected actual prompt size. | Active |
| CB-012 | v1.10 | PolicyEngine is stateless. No per-task or per-session mutable state in the engine itself. | Active |

### Security Gates

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-013 | v1.10 | Calibration test set must be authored before PlanInjectionScanner safe-pass is enabled. Safe-pass disabled until calibration passes. | Active |
| CB-014 | v1.10 | Model fingerprint mismatch immediately disables safe-pass for the remainder of the session. | Active |
| CB-015 | v1.10 | Pre-decision (not periodic) fingerprint verification before any classifier-dependent safe-pass decision. | Active |
| CB-016 | v1.11.4 | Tool capability map SHA256-fingerprinted at boot; modification blocks autonomous operation. | Active |
| CB-017 | v1.11.4 | Manifest `max_response_bytes` has a schema-level ceiling (5–10 MB recommended). | Active |
| CB-018 | v1.11.4 | Manifest `allowed_tools` and `forbidden_tools` constrained to canonical tool IDs (schema enum or ManifestBinder validation). | Active |
| CB-019 | v1.11.4 | PolicyEngine fails closed on missing policy fields (deny-all). | Active |

### Operator Recovery

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-020 | v1.11.4 | Telegram operator whitelist may not be deactivated, made empty, or modified without full panel consent and a recorded session_event. | Active |

### Web Search

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-021 | v1.11.3 | Web search remains disabled until Brave Search API access is operationally confirmed. | Active |

### Cloud Cascade

| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-022 | v1.3 (Evaluator-derived from cancellation discussion) | Per-call timeout: 30 seconds for Cerebras, with cascade fallback on timeout. | Active |

---

## Charter Bindings (Governance)

These are charter-grade rulings about how the panel itself operates. They emerged during the build and are now codified in Charter v1.1.

| ID | Source Cycle | Ruling | Status |
|---|---|---|---|
| GB-001 | v1.9 | Cross-cutting artifact ownership: Gemini primary author / DeepSeek adversarial / Claude coherence / Qwen feasibility / Kimi packaging / operator file creation. Initial assignment of authorship to the Critic violates separation of duties. | Active (codified in Charter v1.1) |
| GB-002 | v1.7 → v1.13 cumulative | Delta-confirmation cycles are authorized when the revision introduces no new component, factual claim, or runtime impact and touches no Core Value or Constraints entry. | Active (codified in Charter v1.1) |
| GB-003 | v1.13 | Implementation revisions follow Integration Discipline: restate only authorized sections, preserve panel-ratified content verbatim, integration verification gate before delta-confirmation. | Active (codified in Charter v1.1) |
| GB-004 | v1.7 cumulative | Specification gaps that carry across two cycles become specification debt and are closure-required for the next revision. | Active (codified in Charter v1.1) |

---

### 8.4 Isolation of Proposed Runtime Invariants

Any runtime invariant not present in the active binding list above must be labeled `PROPOSED` until ratified. It may not appear in the active binding crosswalk, may not receive an `AB-*`, `CB-*`, or `GB-*` ID, and may not be enforced as binding until the required panel process completes.

`PRAGMA synchronous=FULL` remains non-binding unless Qwen issues a feasibility condition or full panel consensus ratifies it. This proposal does not elevate it.

### 8.5 Crosswalk Maintenance and Validation

| Responsibility | Owner |
|---|---|
| Source factual ruling text | Gemini for AB items. |
| Source feasibility condition text | Qwen for CB items. |
| Source governance binding text | Synthesis / full panel for GB items. |
| Crosswalk completeness check | Evaluator during every Synthesis. |
| Proposal restatement of relevant bindings | Architect. |
| Implementation encoding of relevant bindings | Kimi. |

The Evaluator's Synthesis must include a binding validation statement for every full panel cycle. The validation must check all active IDs and must identify omissions, status drift, or text drift.

---

## 9. Synthesis Workflow and Governance File Conventions

### 9.1 Synthesis Workflow

Synthesis filenames follow this pattern:

`AXIOM_Synthesis_<Domain>_v<Cycle>_<Revision>.md`

Examples:

- `AXIOM_Synthesis_Governance_v1_1.md`
- `AXIOM_Synthesis_Governance_v1_1_Routing.md`

The Evaluator initiates Synthesis at the end of every full panel cycle when at least one panel input has been filed. If no valid objection exists, the Synthesis records that fact and may recommend ratification or implementation queue entry. If one or more valid objections exist, the Synthesis authorizes revision scope.

Synthesis artifacts are stored beside the four-document spine and uploaded in every fresh chat involving the affected proposal until superseded.

### 9.2 Active Bindings Filename Convention

The canonical versioned filename pattern is:

`AXIOM_Active_Bindings_v<MAJOR>_<MINOR>.md`

The convenience alias is:

`AXIOM_Active_Bindings.md`

The alias is a plain copy of the latest versioned file, not a symlink. Older versioned files are preserved. When a new active-binding version is ratified, the operator preserves the old version, writes the new versioned file, and overwrites the alias with a copy of the new version.

### 9.3 Canonical Filenames Registry

The canonical filenames registry is:

`AXIOM_Canonical_Filenames.md`

The Evaluator maintains it during Synthesis. It is populated incrementally as artifacts become ratified. Initial population must include filenames referenced in:

1. `AXIOM_Active_Bindings_v1_0.md`;
2. the active Panel Charter;
3. the active Core Values document;
4. the active Constraints Register;
5. ratified proposal and Synthesis artifacts.

A canonical filename change requires explicit panel authorization and an update to the registry.

---

## 10. Status and Authorship of the v1.1 PROPOSED Drafts

### 10.1 Formal Withdrawal of the Three v1.1 PROPOSED Drafts

The following files are formally withdrawn as independent ratification candidates:

- `AXIOM_Panel_Charter_v1_1_PROPOSED.md`
- `AXIOM_Core_Values_v1_1_PROPOSED.md`
- `AXIOM_Constraints_Register_v1_1_PROPOSED.md`

They remain reviewed source inputs for the governance amendment process. They do not become canonical documents by implication, citation, or partial adoption. If the panel ratifies the governance amendment package, clean replacement documents must be produced through the implementation/integration path under §4.

### 10.2 Authorship Statement

The three v1.1 PROPOSED drafts were authored by Claude — Quality and Coherence Evaluator — as draft amendments derived from retrospective analysis of the v1.0 → v1.13 build sequence.

`AXIOM_Proposal_Governance_v1.md` and this `AXIOM_Proposal_Governance_v1.1.md` are authored by GPT-5.5 — Chief Architect — as proposal artifacts for panel review.

The human operator provided files, prompts, execution, and routing. The operator is not the author of the governance content and does not cast design votes.

---

## 11. Required Next Panel Reviews

Cycle 2 is a full panel review, not a delta-confirmation cycle.

> Cycle 2 review scope is governed by `AXIOM_Synthesis_Governance_v1_1_Routing.md`. Each role reviews per the scope specified for that role. Items marked "carries forward unchanged" in the Routing document are not re-litigated in this cycle.

Minimum required checks:

| Role | Required Cycle-2 Focus |
|---|---|
| Evaluator | Closure verification for D/C/Q/K items and SD-001 through SD-018; binding drift check; Core Value conflict check. |
| DeepSeek | Adversarial review of delta enforcement, Diff Gate, integrator assignment, debt ledger, and prospective-only audit closure. |
| Gemini | Factual review of tooling claims introduced by §4 and any incidental external-technology claims. |
| Qwen | Confirmation that closures remain governance/process only and preserve all active CB conditions. |
| Kimi | Implementability review of matrix schema, debt ledger, Diff Gate procedure, prior-version retrieval, filename registry, and operator-executable steps. |

---

## 12. Ratification Preconditions

This proposal is ready for ratification only when the next Synthesis records all of the following:

1. all Cycle-1 objections D1–D5, C1–C5, Q1–Q4, and K1–K11 are closed;
2. all Cycle-1 specification-debt items SD-001 through SD-018 are closed, with no unresolved blocking debt;
3. all 33 active bindings remain present and text-identical where restated verbatim;
4. the three v1.1 PROPOSED drafts remain formally withdrawn unless the panel separately directs clean replacement document generation;
5. the full panel affirmatively concurs under the Charter amendment standard.

---

## 13. Architect Final Disposition for v1.1

The Chief Architect submits `AXIOM_Proposal_Governance_v1.1.md` as a targeted closure revision.

Architect decisions made explicitly in this revision:

| Decision Point | Architect Decision | Reason |
|---|---|---|
| Integrator role identity | Evaluator gatekeeper / operator executor; Kimi packages. | Preserves non-author certification while avoiding Kimi self-certification of implementation packaging. |
| Diff Gate tooling | Python `difflib` unified diff script. | Lightweight, pre-implementation only, no runtime burden. |
| Prior-version retrieval | Timestamped archive directory with SHA256 manifest. | Gives deterministic prior artifact selection and fails closed on ambiguity. |
| Specification-debt storage | Separate append-only `AXIOM_Specification_Debt.md`. | Prevents debt from scattering through proposals, Synthesis files, and binding registries. |
| v1.1 PROPOSED draft status | Formally withdrawn as ratification candidates. | Cleaner than pretending conversation-uploaded drafts are project-knowledge canonical artifacts. |
| Cross-cutting artifact ownership | Uniform GB-001 ownership retained for six proposed classes. | Avoids silent modification of GB-001 and preserves separation of duties. |

No active binding is modified, superseded, or newly issued by this proposal.

---

*End of AXIOM_Proposal_Governance_v1.1.md*
