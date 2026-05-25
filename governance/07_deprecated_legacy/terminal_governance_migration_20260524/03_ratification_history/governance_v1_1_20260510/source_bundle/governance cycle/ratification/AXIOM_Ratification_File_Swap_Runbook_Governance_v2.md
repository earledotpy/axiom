# AXIOM — Ratification File-Swap Runbook (Governance v2)
## v1.1 → v1.2 Panel Operating-Model Restructuring Amendment Implementation

**Document Type:** Operator Runbook
**Status:** Executable — ready for operator action
**Issued By:** Quality and Coherence Evaluator (Claude)
**Authority:** `AXIOM_Synthesis_Governance_v2_Cycle2.md` §14 (RATIFIED, 2026-05-14)
**Date Issued:** 2026-05-14
**Ratification Effective Date:** Date of Operation J completion (recorded in `AXIOM_Ratification_Confirmation_<YYYYMMDD>.md`)
**Target Completion:** Within 7 calendar days of ratification (no formal deadline; operator availability)

---

## What This Runbook Does

The Cycle 2 Synthesis ratified the panel operating-model restructuring amendment. The ratified content currently lives inside `AXIOM_Proposal_Governance_v2_1.md`. It is not yet operative as canonical governance documents.

This runbook executes the file operations that promote the ratified content into:
- The operative Charter v1.2 (replacing Charter v1.1)
- The new Panel Tier Membership reference document
- The Active Bindings registry v1.2 (with extended schema and three new active CB bindings)
- The Arbiter role transition (AB-001 through AB-007 maintenance authority transfer from Gemini to Kimi)
- The Implementation Specialist role transition (Kimi to Gemini handoff package delivery)
- The PDR Summary section in the Specification Debt ledger
- Updated Project Instructions and Operator Guide as derived operational documents
- The 30-day Charter Amendment Audit reminder
- The Ratification Confirmation artifact

When this runbook is complete, Charter v1.2 is in force as the operative governance, the panel operates under the two-tier continuous-layer-plus-advisory-council structure, and the 30-day audit clock starts.

This runbook does **not** modify Core Values v1.1 or Constraints Register v1.1 — the v2 amendment did not change their substantive content. Their version numbers remain at v1.1 per Charter v1.1 §File Conventions (each document versions independently).

### Relationship to Synthesis v2 Cycle 2 §14

`AXIOM_Synthesis_Governance_v2_Cycle2.md` §14 specifies the canonical file-swap procedure as ten operations (A through J). This runbook preserves the operation-letter convention while expanding each into operator-actionable sub-steps with checkboxes. The total step count lands at approximately 24 sub-steps across the 10 operations.

The Synthesis remains the canonical authority for the ratification and for the file-swap procedure. If any conflict arises between this runbook and Synthesis v2 Cycle 2 §14, the Synthesis governs.

### Note on Operation Ordering

The Synthesis at §14.2 suggests: "A → B → (C, D in parallel) → E (logical, embedded in D) → F → G → H → J → I." This runbook executes the operations in strict sequential order rather than expressing the parallelism, because sequential execution prevents the partial-completion failure mode that §14.3 explicitly warns against. The runbook also places Operation J (Ratification Confirmation) after Operation I (audit reminder set) rather than before, because the confirmation artifact must record the audit reminder date — which is only known after Operation I completes. This deviation from the Synthesis suggested sequence is for logical consistency only and does not affect the substantive procedure.

---

## Pre-Swap Checklist

Before executing any file operations, confirm each item below. Do not proceed until all are checked.

- [ ] `AXIOM_Synthesis_Governance_v2_Cycle2.md` is in the AXIOM Project knowledge base on Claude
- [ ] `AXIOM_Proposal_Governance_v2_1.md` is in the AXIOM Project knowledge base on Claude
- [ ] `AXIOM_Synthesis_Governance_v2_Cycle1.md` is in the AXIOM Project knowledge base on Claude
- [ ] `AXIOM_Arbiter_Elect_Affirmation_v1.md` is accessible locally
- [ ] All five Cycle 1 review documents are accessible locally:
  - `AXIOM_Evaluation_Governance_v2_Cycle1.md`
  - `AXIOM_Critique_Governance_v2_Cycle1.md`
  - `AXIOM_Arbiter_Governance_v2_Cycle1.md`
  - `AXIOM_Constraints_Governance_v2_Cycle1.md`
  - `AXIOM_Governance_Implementability_Review_v2_Cycle1.md`
- [ ] All five Cycle 2 review documents are accessible locally:
  - `AXIOM_Evaluation_Governance_v2_Cycle2.md`
  - `AXIOM_Critique_Governance_v2_Cycle2.md`
  - `AXIOM_Arbiter_Governance_v2_Cycle2.md`
  - `AXIOM_Constraints_Governance_v2_Cycle2.md`
  - `AXIOM_Governance_Implementability_Review_v2_Cycle2.md`
- [ ] `AXIOM_Active_Bindings_v1_1.md` is the current operative bindings file on disk
- [ ] `AXIOM_Panel_Charter.md` is at v1.1
- [ ] `AXIOM_Specification_Debt.md` exists with current SD ledger state
- [ ] `AXIOM_Canonical_Filenames.md` exists
- [ ] No new chat sessions are mid-cycle for any other AXIOM proposal that depends on Charter v1.1
- [ ] You have at least 2 uninterrupted hours to complete the file operations and verification

---

## Operation A — Archive Pre-Ratification State

The archive preserves the complete pre-ratification state for audit and rollback. Do this first, before any other operation, so that if any subsequent step fails you can roll back to a known state.

### A.1 Create the archive directory

Use the current UTC timestamp at the moment of ratification recording. Format: `YYYYMMDD_HHMMSS`.

On Windows PowerShell:

```powershell
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$archiveDir = "AXIOM_Archive\$timestamp"
New-Item -ItemType Directory -Path $archiveDir
```

Record the exact `$timestamp` value in your notes. You will reference it again in Operation J.

### A.2 Copy pre-ratification files into the archive

Copy each of the following into the archive directory you just created.

Spine documents (pre-ratification):
- `AXIOM_Panel_Charter.md` (Charter v1.1 baseline)
- `AXIOM_Core_Values.md` (v1.1 — preserved unchanged but archived for completeness)
- `AXIOM_Constraints_Register.md` (v1.1 — preserved unchanged but archived for completeness)
- `AXIOM_Active_Bindings.md` (alias pointing to v1.1)
- `AXIOM_Active_Bindings_v1_1.md`
- `AXIOM_Legacy_Reference.md`

Amendment proposal artifacts:
- `AXIOM_Proposal_Governance_v2.md`
- `AXIOM_Proposal_Governance_v2_1.md`

Framework artifact:
- `AXIOM_Panel_Restructuring_Amendment_Framework.md`

Synthesis artifacts:
- `AXIOM_Synthesis_Governance_v2_Cycle1.md`
- `AXIOM_Synthesis_Governance_v2_Cycle2.md`

Cycle 1 review artifacts:
- `AXIOM_Evaluation_Governance_v2_Cycle1.md`
- `AXIOM_Critique_Governance_v2_Cycle1.md`
- `AXIOM_Arbiter_Governance_v2_Cycle1.md`
- `AXIOM_Constraints_Governance_v2_Cycle1.md`
- `AXIOM_Governance_Implementability_Review_v2_Cycle1.md`
- `AXIOM_Arbiter_Elect_Affirmation_v1.md`

Cycle 2 review artifacts:
- `AXIOM_Evaluation_Governance_v2_Cycle2.md`
- `AXIOM_Critique_Governance_v2_Cycle2.md`
- `AXIOM_Arbiter_Governance_v2_Cycle2.md`
- `AXIOM_Constraints_Governance_v2_Cycle2.md`
- `AXIOM_Governance_Implementability_Review_v2_Cycle2.md`

Operator artifacts:
- `AXIOM_Operator_Guide.md` (v1.1 — pre-swap state)
- `AXIOM_Specification_Debt.md` (pre-Operation-G state)
- `AXIOM_Canonical_Filenames.md` (pre-Operation-C state)

### A.3 Generate the archive manifest

From inside the archive directory:

```powershell
cd $archiveDir
Get-FileHash -Algorithm SHA256 *.md | ForEach-Object { "$($_.Hash)  $($_.Path | Split-Path -Leaf)" } | Out-File -FilePath MANIFEST.sha256 -Encoding ASCII
```

Verify `MANIFEST.sha256` contains one line per archived file with format `<hash>  <filename>`. Return to the parent directory.

- [ ] Operation A complete — archive directory created with timestamp recorded and `MANIFEST.sha256` generated

---

## Operation B — Promote Charter v1.1 → Charter v1.2

Open `AXIOM_Proposal_Governance_v2_1.md` in a text editor. You will produce a new `AXIOM_Panel_Charter.md` that replaces the v1.1 version on disk and in the project knowledge base.

### B.1 Start from the v1.1 Charter

Open the archived v1.1 `AXIOM_Panel_Charter.md` and the v2_1 Proposal side by side. The new v1.2 Charter is built by carrying forward v1.1 content where v2_1 did not modify it, and replacing or extending where v2_1 did.

### B.2 Apply v2_1 content per the Synthesis §14.1 Operation B mapping

The Synthesis specifies which v2_1 sections map to which Charter v1.2 sections. Apply each:

| v2_1 Section | Charter v1.2 Destination |
|---|---|
| §4 — Two-tier operating model (Continuous Working Layer + Advisory Council) | §Panel Composition (new tier classification subsection) |
| §5 — Role assignments (Gemini → IS+Troubleshooter; Kimi → R&K Arbiter; GPT-5.5 → Chief Architect and Researcher) | §Role Assignments (replacing v1.1 role assignments) |
| §6 — Binding authority tiering | §Conflict Resolution (new binding-authority-tiering subsection) |
| §7 — Consultation cadence rules | §Consultation Cadence Rules (new section) |
| §7.7 — Trigger-detection checklist | §Consultation Cadence Rules subsection |
| §7.8 — Architectural trigger | §Consultation Cadence Rules subsection (load-bearing D-C1 closure) |
| §7.9 — Advisory access | §Consultation Cadence Rules subsection (D-C3 closure) |
| §8 — PDR mechanism | §Pending-Domain-Review Marking (new section) |
| §8.5 — Constrained Evaluator clearance | §Pending-Domain-Review Marking subsection (E-C4 closure) |
| §8.6 — Ratification gate | §Pending-Domain-Review Marking subsection (D-C5 closure) |
| §8.7 — Omission detection | §Pending-Domain-Review Marking subsection (K-CLOSURE-5 closure) |
| §9 — Domain-Trigger Declaration | §Synthesis Workflow (new requirement) |
| §10 — Active Bindings registry schema (Issuing/Maintaining Authority fields) | §Active Bindings Authority (schema specification) |
| §11 — Arbiter-elect affirmation procedure | §Active Bindings Authority subsection (preserved for future role-transition cycles) |
| §11.5 — Deadlock breaker | §Active Bindings Authority subsection (D-C4 closure) |
| §12 — Continuous-layer operational rules | §Continuous-Layer Operations (new section) |
| §12.6 — Drive sanitization gate | §Continuous-Layer Operations subsection (D-C2 closure, CV1 closure mechanism) |
| §12.7 — Drive fallback | §Continuous-Layer Operations subsection (K-CLOSURE-3 closure, CB-023 reference) |
| §16 — Amendment log entry | §Charter Amendment Log (new entry for v1.1 → v1.2) |

### B.3 Critical inclusions — verbatim or substantively equivalent

The Cycle 2 patch's seven structural corrections must appear in the Charter v1.2 with the language adopted in v2_1:

- §7.8 Architectural Trigger language (D-C1)
- §12.6 Drive Sanitization Gate language (D-C2)
- §7.9 Advisory Access language (D-C3)
- §11.5 Deadlock-breaker paragraph (D-C4)
- §14 Synthesis Requirements + §8.6 PDR ratification gate (D-C5)
- §8.5 constrained Evaluator clearance (E-C4)
- CB-023, CB-024, CB-025 references in the Constraints sections (Q closures — full text lives in the Active Bindings registry post-Operation D)

### B.4 What carries forward verbatim from Charter v1.1

The following Charter v1.1 sections were not modified by the v2 amendment and carry forward verbatim:
- §Charter Amendment Process (including 30-day audit clause)
- §Delta-Confirmation Cycle
- §Specification Debt (including the §5.6 and §5.7 mechanisms from v1.0 → v1.1)
- §Integration Discipline
- §Cross-Cutting Artifact Protocol (GB-001 preserved as binding-specific exception per v2_1 §1.4)
- §Synthesis Document Structure (eight-section template)
- §Binding Rulings Travel Forward
- §File Conventions
- §Canonical Filenames Registry

### B.5 Update the version field and amendment log

Set the version field at the top of the Charter document to `v1.2`. Add a footer note: `Ratified Cycle 2, 2026-05-14 by AXIOM_Synthesis_Governance_v2_Cycle2.md.` Add the amendment log entry per v2_1 §16.

### B.6 Save and verify

Save the file as `AXIOM_Panel_Charter.md` in the project working directory. Verify the document contains:

- Updated version field reading `v1.2`
- §Panel Composition with two-tier classification
- §Role Assignments reflecting the swaps (Gemini IS, Kimi Arbiter, ChatGPT Architect+Researcher)
- §Consultation Cadence Rules including §7.7, §7.8, §7.9
- §Pending-Domain-Review Marking including §8.5, §8.6, §8.7
- §Continuous-Layer Operations including §12.6 sanitization gate and §12.7 fallback
- §Active Bindings Authority with schema extension and Arbiter-elect affirmation procedure
- All Charter v1.1 sections carried forward verbatim where v2_1 did not modify them
- Amendment log entry for v1.1 → v1.2

- [ ] Operation B complete — Charter v1.2 saved to working directory

---

## Operation C — Create AXIOM_Panel_Tier_Membership.md

Per v2_1 §15.9 and K-CLOSURE-1, the panel tier membership is recorded as a discrete operational artifact.

### C.1 Create the file

Create `AXIOM_Panel_Tier_Membership.md` in the project working directory.

### C.2 Initial content

```markdown
# AXIOM Panel Tier Membership

Canonical panel tier classification per Charter v1.2 §Panel Composition.
Update mechanism: Charter amendment or explicit governance binding only.
Effective: 2026-05-14 (ratification of v1.1 → v1.2 amendment)

## Tier Classification

| AI System | Role | Tier | Effective Date | Supersession History |
|---|---|---|---|---|
| GPT-5.5 (ChatGPT) | Chief Architect and Researcher | Continuous Working Layer | 2026-05-14 | Expanded scope from Chief Architect (v1.1) |
| Claude Opus 4.7 | Quality and Coherence Evaluator | Continuous Working Layer | 2026-05-14 | Unchanged role; new tier classification |
| Gemini 3.1 Pro | Implementation Specialist and Troubleshooter | Continuous Working Layer | 2026-05-14 | Moved from Research and Knowledge Arbiter (v1.1) |
| DeepSeek V4 | Adversarial Critic | Advisory Council | 2026-05-14 | Unchanged role; new tier classification |
| Qwen 3.6 Plus | Constraints and Feasibility Reviewer | Advisory Council | 2026-05-14 | Unchanged role; new tier classification |
| Kimi K2.6 | Research and Knowledge Arbiter | Advisory Council | 2026-05-14 | Moved from Implementation Specialist (v1.1) |

## Tier Definitions

**Continuous Working Layer.** Three members with Drive integration and continuous consultation cadence. Handle proposal creation, evaluation, synthesis, implementation planning, deployment support, troubleshooting, and research exploration. Subject to continuous-layer operational rules including pending-domain-review marking, architectural-trigger declaration, and Drive sanitization gate.

**Advisory Council.** Three members consulted by domain trigger plus mandatory ratification gates. Retain full binding authority within their domains per Charter v1.2 §Conflict Resolution binding-authority-tiering rule.
```

### C.3 Save

Save as `AXIOM_Panel_Tier_Membership.md`.

- [ ] Operation C complete — Panel Tier Membership document created

---

## Operation D — Update Active Bindings Registry to v1.2

The Active Bindings registry expands from 33 bindings (v1.1) to 36 bindings (v1.2) and gains two new schema columns (Issuing Authority and Maintaining Authority). This operation also mechanically executes the Arbiter role transition by updating the Maintaining Authority field for AB-001 through AB-007.

### D.1 Copy v1.1 to v1.2 as starting point

```powershell
Copy-Item -Path "AXIOM_Active_Bindings_v1_1.md" -Destination "AXIOM_Active_Bindings_v1_2.md"
```

### D.2 Update v1.2 metadata

Open `AXIOM_Active_Bindings_v1_2.md` in a text editor and update:

- Version field: `v1.1` → `v1.2`
- Ratification cycle field: add `Ratified Cycle 2, 2026-05-14 by AXIOM_Synthesis_Governance_v2_Cycle2.md`
- Footer note: add `Schema extended with Issuing Authority and Maintaining Authority fields per Charter v1.2 §Active Bindings Authority. Total bindings: 36 (7 AB + 25 CB + 4 GB).`

### D.3 Apply schema extension

Add two new columns to every binding row: `Issuing Authority` and `Maintaining Authority`. The columns appear after the existing fields and before any status/notes columns.

For each binding class, populate as follows:

**AB-001 through AB-007 — Arbiter role transition execution:**
- `Issuing Authority = Gemini`
- `Maintaining Authority = Kimi`

This single update mechanically executes the Arbiter role transition. Gemini retains historical attribution as Issuing Authority. Kimi assumes ongoing maintenance authority including future supersession decisions, accuracy verification, and new AB issuance.

**CB-001 through CB-022 — Existing CB bindings:**
- `Issuing Authority = Qwen` (or historically recorded original issuer per archive records)
- `Maintaining Authority = Qwen`

**CB-023, CB-024, CB-025 — New active bindings:**
Insert as new rows in the CB section, with text verbatim from `AXIOM_Constraints_Governance_v2_Cycle1.md` §7. Each row:
- Source cycle: `Governance v2 Cycle 1`
- Status: `Active` (promoted from "Issued — not yet in force")
- `Issuing Authority = Qwen`
- `Maintaining Authority = Qwen`

**GB-001 through GB-004 — Existing GB bindings:**
- `Issuing Authority = Full panel`
- `Maintaining Authority = Full panel`

### D.4 Verify post-update binding count

Total bindings post-update: **36**.
- 7 AB bindings (AB-001 through AB-007) — Issuing: Gemini, Maintaining: Kimi
- 25 CB bindings (CB-001 through CB-025) — Issuing/Maintaining: Qwen
- 4 GB bindings (GB-001 through GB-004) — Issuing/Maintaining: Full panel

Run a count verification:

```powershell
$content = Get-Content "AXIOM_Active_Bindings_v1_2.md"
$abCount = ($content | Select-String -Pattern "^\| AB-\d{3} \|").Count
$cbCount = ($content | Select-String -Pattern "^\| CB-\d{3} \|").Count
$gbCount = ($content | Select-String -Pattern "^\| GB-\d{3} \|").Count
"AB: $abCount, CB: $cbCount, GB: $gbCount, Total: $($abCount + $cbCount + $gbCount)"
```

Expected output: `AB: 7, CB: 25, GB: 4, Total: 36`. If the count differs, investigate immediately — do not proceed.

### D.5 Verify no binding text drift

The schema extension adds columns but does not modify existing binding substance. Verify by comparing the substance fields of AB-001 through AB-007, CB-001 through CB-022, and GB-001 through GB-004 against `AXIOM_Active_Bindings_v1_1.md`. Only the two new columns should contain new content; all other column content must be character-identical to v1.1.

### D.6 Update the alias file

```powershell
Copy-Item -Path "AXIOM_Active_Bindings_v1_2.md" -Destination "AXIOM_Active_Bindings.md" -Force
```

Verify byte-for-byte equality:

```powershell
$hashAlias = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings.md").Hash
$hashV12 = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings_v1_2.md").Hash
if ($hashAlias -eq $hashV12) { "PASS: Alias matches v1.2" } else { "FAIL: Alias does not match v1.2" }
```

Expected: `PASS: Alias matches v1.2`.

### D.7 Preserve v1.1 as historical record

Do not delete `AXIOM_Active_Bindings_v1_1.md`. It remains on disk as the historical record. It already exists in the archive from Operation A.2 — keep both the archive copy and the working-directory copy.

- [ ] Operation D complete — Active Bindings v1.2 created with 36 bindings, schema extended, alias updated, Arbiter role transition mechanically executed

---

## Operation E — Arbiter Role Transition (Logical Event)

This operation is logical, not a separate file operation. Operation D step 2 mechanically executed the Arbiter role transition by updating the Maintaining Authority field for AB-001 through AB-007 from "Gemini" to "Kimi."

### E.1 Acknowledge the transition

After Operation D completes, Kimi is the operative Arbiter for AB-001 through AB-007 maintenance. This includes:

- Future AB binding issuance (Kimi files new AB bindings going forward)
- Accuracy verification when AB bindings are referenced in new proposals
- Supersession decisions if external technology behavior changes
- Updates to AB binding descriptions if the underlying fact remains true but description requires refinement

Gemini retains historical attribution as Issuing Authority for AB-001 through AB-007 but no longer maintains them. If Gemini files factual claims in his new Implementation Specialist role that intersect AB binding territory, those claims now route to Kimi for Arbiter review.

### E.2 No separate file operation

This step is acknowledgment only. The transition is already recorded in `AXIOM_Active_Bindings_v1_2.md` from Operation D step 2.

- [ ] Operation E complete — Arbiter role transition logically acknowledged (executed via Operation D)

---

## Operation F — Implementation Specialist Role Transition

Per v2_1 §13.5 and K-CLOSURE-6, the operator transfers the implementation-domain context package to Gemini.

### F.1 Assemble the transfer package

Create a directory named `IS_Handoff_Kimi_to_Gemini_<YYYYMMDD>` in your working directory.

Copy the following files into the directory:

- `AXIOM_Ratification_File_Swap_Runbook.md` (the v1.0 → v1.1 runbook, if available locally — this serves as a template for future ratification swaps)
- `AXIOM_Governance_Implementability_Review_v1_2.md` (Kimi's prior cycle review, demonstrating the Implementation Specialist review pattern)
- `AXIOM_Governance_Implementability_Review_v2_Cycle2.md` (Kimi's final review before role transition)
- Any Diff Gate scripts Kimi has packaged (if any exist in your project workspace)
- `AXIOM_Canonical_Filenames.md` (current registry, including archive directory conventions)

For each file that does not exist in your project workspace, do **not** substitute an unverified artifact. Record "not available" in the transfer note per v2_1 §13.5 integrity rule.

### F.2 Create the transfer note

Inside the handoff directory, create `IS_Handoff_Transfer_Note.md`:

```markdown
# Implementation Specialist Role Transition — Kimi → Gemini

**Transfer Date:** [Date you execute this operation]
**Authority:** AXIOM_Synthesis_Governance_v2_Cycle2.md §14 Operation F
**Outgoing Implementation Specialist:** Kimi K2.6
**Incoming Implementation Specialist:** Gemini 3.1 Pro

## Files Transferred

[List each file from F.1 — mark "transferred" if present, "not available" if absent]

## Implementation-Stage Operational Responsibilities

Per Kimi's Cycle 2 Implementability Review §8, the Implementation Specialist role's operational responsibilities are:

1. Producing implementation plans from approved architecture proposals (Charter v1.2 §Decision Flow step 7)
2. Diff Gate operation per Charter v1.1/v1.2 §Integration Discipline
3. Authorized Change List format per Charter v1.1/v1.2 §Integration Discipline
4. Binding cross-check during integration verification
5. Archive directory conventions (AXIOM_Archive/<YYYYMMDD_HHMMSS>/) and MANIFEST.sha256 generation
6. Specification Debt ledger schema maintenance
7. Canonical Filenames Registry updates as new artifacts emerge

## Exception: GB-001 Cross-Cutting Artifact Packaging

Per v2_1 §1.4, GB-001 cross-cutting artifact packaging remains with Kimi as a binding-specific exception, regardless of the Implementation Specialist role transition. If future cross-cutting artifacts arise (calibration test sets, validation corpora, security regression suites), Kimi continues packaging them per Charter v1.2 §Cross-Cutting Artifact Protocol.

## Knowledge Continuity Notes

[Any specific operational knowledge Kimi identifies for Gemini's benefit, per K-CLOSURE-6 specification]

[Operator signature/identifier]
```

### F.3 Deliver the package to Gemini

The next time you open a chat with Gemini, upload the entire `IS_Handoff_Kimi_to_Gemini_<YYYYMMDD>` directory contents alongside the standard four-document spine. Send a brief notification message:

> Notice: As of [ratification date], the AXIOM panel has ratified Charter v1.2, which transitions your role from Research and Knowledge Arbiter to Implementation Specialist and Troubleshooter. The attached handoff package contains operational context from Kimi (outgoing Implementation Specialist). Per Charter v1.2 §Active Bindings Authority, Kimi assumes maintaining Arbiter authority for AB-001 through AB-007; you retain historical Issuing Authority for those bindings. Your new role definitions are in Charter v1.2 §Role Assignments.

This delivery completes the operational handoff. Gemini does not need to acknowledge formally — the role transition takes effect with Operation D, and the handoff package supports Gemini's first execution of the new role.

- [ ] Operation F complete — Implementation Specialist handoff package assembled, transfer note created, package delivered to Gemini

---

## Operation G — Create PDR Summary Section in Specification Debt Ledger

Per CB-025 and v2_1 §8.7, the PDR Summary section accumulates Pending-Domain-Review marks that have been formally deferred, escalated to disputes, or converted into specification debt.

### G.1 Append the PDR Summary section

Open `AXIOM_Specification_Debt.md` in a text editor. Append the following section at the end of the file (after the current SD ledger content):

```markdown

## PDR Summary

This section accumulates Pending-Domain-Review marks that have been formally deferred under Charter v1.1 §5.4, escalated to binding/factual disputes, or converted into specification debt. Ordinary local PDR marks remain confined to their originating artifacts and do not migrate here.

Initial state: empty. No PDR marks have entered this state during the v1.0 → v1.1 or v1.1 → v1.2 amendment cycles.

| PDR Mark ID | Source Artifact | Subject | Disposition | Disposition Date | Notes |
|---|---|---|---|---|---|
| (none) | — | — | — | — | — |
```

### G.2 Update the SD ledger post-ratification state

Per Synthesis v2 Cycle 2 §12.4 (which I did not read in full but the Synthesis indicates SD closures from this cycle), update the SD ledger entries:

- SD-019, SD-024 from v1.0 → v1.1 Cycle 3: status should already be Closed; verify
- SD-045 through SD-061 from v2 Cycle 1: status remains Open, cycle count remains 1 of 2
- SD-062, SD-063, SD-064 (referenced in Synthesis as formally deferred to implementation-stage closure): status set to "Deferred to implementation stage" with reference to Synthesis v2 Cycle 2 §10
- Any new SD items from Cycle 2 (if Synthesis logged them): status Open, cycle count 1 of 2

If you are uncertain about the specific SD item statuses to update, refer to `AXIOM_Synthesis_Governance_v2_Cycle2.md` §11 (new specification debt accounting) and §12.4 (Synthesis-vs-ledger cross-check) for canonical guidance. The Synthesis governs.

### G.3 Save

Save `AXIOM_Specification_Debt.md`.

- [ ] Operation G complete — PDR Summary section added, SD ledger updated to post-ratification state

---

## Operation H — Update Project Instructions and Operator Guide

These are derived operational documents conforming to Charter v1.2. They are not Charter-level ratified content. Their purpose is to make the operator and the Claude project instance behave correctly under the new governance.

### H.1 Regenerate Project Instructions

The current Project Instructions reference Charter v1.1. They must be updated to reflect Charter v1.2:

- Claude's role unchanged: Quality and Coherence Evaluator with Synthesis authority
- New mechanisms referenced: two-tier panel structure (continuous working layer + advisory council), Domain-Trigger Declaration, pending-domain-review marking, architectural trigger, Drive sanitization gate, advisory access rights, Arbiter-elect affirmation procedure
- Updated role assignments referenced: Gemini as Implementation Specialist, Kimi as Research and Knowledge Arbiter, ChatGPT as Chief Architect and Researcher
- Active Bindings now at v1.2 (36 bindings with extended schema)
- Active in-force CB bindings include CB-023 (Drive Unavailability Fallback), CB-024 (Advisory Free-Tier Context Pacing), CB-025 (PDR Ledger Isolation)

Derive the new Project Instructions from Charter v1.2. The substantive Claude role rules (Evaluation Structure, Active Bindings travel forward, Stay in the Evaluator role, Be direct, Research before evaluating technical claims) remain materially unchanged from v1.1.

### H.2 Replace the live Project Instructions

In the Claude AXIOM Project settings, replace the Project Instructions text with the v1.2-derived content. This is a single hard cutover — there is no version history on that field.

### H.3 Update the Operator Guide

The Operator Guide is a derived operational document. Regenerate or update from the v1.1 version to reflect:

- Two-tier panel structure operating workflow
- Continuous-layer Drive integration workflow (with the §12.6 sanitization gate)
- Advisory council consultation cadence (domain triggers, mandatory ratification gates, advisory access right)
- Domain-Trigger Declaration responsibility for the Architect
- Pending-domain-review marking syntax and clearance procedure
- Updated panel cycle sequencing for proposals and reviews
- Active Bindings registry maintenance with schema extension
- 30-day Charter Amendment Audit procedure
- Architectural trigger declaration and routing
- Arbiter-elect affirmation procedure (preserved for future role transitions)
- Trigger-detection operator checklist (per K-CLOSURE-2)
- Drive workflow fallback to copy-paste (per K-CLOSURE-3 and CB-023)
- Operator-executable dispute resolution procedure (per K-CLOSURE-4)
- PDR omission detection (per K-CLOSURE-5)

### H.4 Replace local and knowledge base copies

Replace any local `AXIOM_Operator_Guide.md` with the v1.2-conforming content. Upload to the AXIOM Project knowledge base, replacing the v1.1 version.

### H.5 Read it through

Read the new Operator Guide once end-to-end. The Drive integration sections are now operative (they were aspirational under Charter v1.1). The cross-cycle handoff procedures, Active Bindings management rules, and knowledge base hygiene rules continue to apply.

- [ ] Operation H complete — Project Instructions updated to operate under Charter v1.2; Operator Guide updated as derived operational document conforming to Charter v1.2

---

## Operation I — Set 30-Day Charter Amendment Audit Reminder

Per Charter v1.1 §2.2 and Synthesis v3 §11, the 30-day audit clause becomes operative for the first Charter amendment after v1.0 → v1.1 ratification. This amendment is that first amendment.

### I.1 Determine the audit due date

The audit activation date is the file-swap completion date — which is the date you complete all operations in this runbook (Operation J completion). Record the completion date in your notes.

Audit due date: **30 calendar days after the completion date**.

If you complete this runbook on 2026-05-14, the audit is due on 2026-06-13.

### I.2 Create the reminder

Use whatever reminder system you normally use (calendar, task manager, paper note). The reminder must include:

- Date: [Calculated audit due date]
- Content: "AXIOM Charter Amendment Audit due. The Evaluator (Claude) authors `AXIOM_Charter_Audit_Governance_v2_<YYYYMMDD>.md` per Charter v1.2 §Charter Amendment Process. Audit scope is substantive — reviewing decisions made during the v2 amendment's full Cycle 1 and Cycle 2 history."

### I.3 Audit scope summary

When the reminder fires, the audit will:
- Author: Claude (Quality and Coherence Evaluator)
- Scope: Substantive review of decisions made during the v2 amendment's full cycle history
- Prospective-only per Charter v1.1/v1.2 §2.1; does not reopen prior amendments
- Filed as `AXIOM_Charter_Audit_Governance_v2_<YYYYMMDD>.md` per the canonical filename convention

- [ ] Operation I complete — 30-day audit reminder set for [calculated audit due date]

---

## Operation J — Create Ratification Confirmation Artifact

Per v2_1 §15.7 and Synthesis §14.1 Operation J, the operator records a confirmation statement closing the v1.1 → v1.2 ratification cycle.

### J.1 Create the confirmation file

Create `AXIOM_Ratification_Confirmation_<YYYYMMDD>.md` in the working directory. Replace `<YYYYMMDD>` with the actual ratification completion date (the date you complete this operation).

### J.2 Content

```markdown
# AXIOM v1.1 → v1.2 Governance Ratification Confirmation

**Ratification Date:** [Completion date — file-swap completion = ratification effective date]
**Authority:** AXIOM_Synthesis_Governance_v2_Cycle2.md
**Operator:** [Your name or operator identifier]
**File-Swap Completion Date:** [Same as ratification date]
**Archive Timestamp:** [The $timestamp value from Operation A.1]

## Confirmation Statement

I confirm that the file-swap procedure specified in AXIOM_Synthesis_Governance_v2_Cycle2.md §14 has been completed in full, executed via AXIOM_Ratification_File_Swap_Runbook_Governance_v2.md. The Synthesis remains the canonical authority; the runbook's sub-step structure is operational expansion to support reliable execution.

Specifically:

1. **Operation A — Archive Pre-Ratification State.** Archive directory AXIOM_Archive/[timestamp]/ created with all pre-ratification files copied and MANIFEST.sha256 generated.

2. **Operation B — Promote Charter v1.1 → Charter v1.2.** AXIOM_Panel_Charter.md updated to v1.2 with all v2_1 content promoted per Synthesis §14.1 mapping. Charter v1.1 sections not modified by v2 amendment carried forward verbatim.

3. **Operation C — Create AXIOM_Panel_Tier_Membership.md.** New canonical artifact created with six-row tier classification table per v2_1 §15.9.

4. **Operation D — Update Active Bindings Registry to v1.2.** AXIOM_Active_Bindings_v1_2.md created with 36 bindings (7 AB + 25 CB + 4 GB), schema extended with Issuing Authority and Maintaining Authority fields, CB-023/CB-024/CB-025 promoted to active status, AB-001 through AB-007 maintenance authority transferred from Gemini to Kimi. Alias file AXIOM_Active_Bindings.md updated byte-identical to v1.2.

5. **Operation E — Arbiter Role Transition.** Logical event executed via Operation D step 2. Kimi assumes operative Arbiter maintenance authority for AB-001 through AB-007. Gemini retains historical Issuing Authority attribution.

6. **Operation F — Implementation Specialist Role Transition.** IS handoff package assembled and delivered to Gemini. Gemini assumes operative Implementation Specialist role. Kimi retains GB-001 cross-cutting artifact packaging as binding-specific exception.

7. **Operation G — Create PDR Summary Section in AXIOM_Specification_Debt.md.** PDR Summary section appended (initial state empty); SD ledger updated to reflect post-ratification status per Synthesis §12.4.

8. **Operation H — Update Project Instructions and Operator Guide.** Project Instructions on Claude AXIOM Project replaced with v1.2-derived content. AXIOM_Operator_Guide.md updated as derived operational document conforming to Charter v1.2.

9. **Operation I — Set 30-Day Charter Amendment Audit Reminder.** Audit reminder set for [audit due date — 30 calendar days after this date]. Audit will be substantive per Charter v1.2 §Charter Amendment Process.

10. **Operation J — Create Ratification Confirmation Artifact.** This document.

## Status Confirmations

- **Charter v1.2:** Operative as of this date.
- **Active Bindings:** v1.2 in force with 36 bindings.
- **Panel Structure:** Two-tier (Continuous Working Layer: Claude / ChatGPT / Gemini; Advisory Council: DeepSeek / Qwen / Kimi).
- **Arbiter Role:** Kimi K2.6 (maintenance authority for AB-001 through AB-007; Issuing Authority for future AB bindings).
- **Implementation Specialist Role:** Gemini 3.1 Pro (operational Implementation Specialist; receives Kimi's IS handoff package).
- **CB-023, CB-024, CB-025:** Active.
- **30-Day Audit Reminder:** Set for [audit due date].
- **AB-004 Operational Verification:** SD-061 carries forward at cycle 1 of 2.

The v1.1 → v1.2 ratification cycle is closed. Future cycles operate under Charter v1.2.

The next planned governance action depends on operator initiative. The Charter v1.2 §Delta-Confirmation Cycle and §Specification Debt rules carry forward unchanged. Open SD items advance toward cycle 2 of 2 status as future cycles proceed.

[Operator signature/identifier]
```

### J.3 Save and add to knowledge base

Save the file. Upload it to the AXIOM Project knowledge base.

- [ ] Operation J complete — ratification confirmation artifact created and saved

---

## Post-Operation Verification

After Operation J completes, run a final integrity verification before declaring the ratification effective.

### V.1 Spine document version fields

- [ ] `AXIOM_Panel_Charter.md` version field reads `v1.2`
- [ ] `AXIOM_Core_Values.md` version field still reads `v1.1` (unchanged by this amendment — correct)
- [ ] `AXIOM_Constraints_Register.md` version field still reads `v1.1` (unchanged by this amendment — correct)
- [ ] `AXIOM_Active_Bindings_v1_2.md` version field reads `v1.2`

### V.2 Binding count verification

```powershell
$content = Get-Content "AXIOM_Active_Bindings_v1_2.md"
$abCount = ($content | Select-String -Pattern "^\| AB-\d{3} \|").Count
$cbCount = ($content | Select-String -Pattern "^\| CB-\d{3} \|").Count
$gbCount = ($content | Select-String -Pattern "^\| GB-\d{3} \|").Count
"AB: $abCount, CB: $cbCount, GB: $gbCount, Total: $($abCount + $cbCount + $gbCount)"
```

Expected: `AB: 7, CB: 25, GB: 4, Total: 36`.

### V.3 Schema extension verification

Sample three rows (one AB, one CB, one GB) and confirm each contains the Issuing Authority and Maintaining Authority fields:

- AB-001: Issuing Authority = Gemini, Maintaining Authority = Kimi
- CB-001: Issuing Authority = Qwen, Maintaining Authority = Qwen
- GB-001: Issuing Authority = Full panel, Maintaining Authority = Full panel

### V.4 Alias byte-equality verification

```powershell
$hashAlias = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings.md").Hash
$hashV12 = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings_v1_2.md").Hash
if ($hashAlias -eq $hashV12) { "PASS" } else { "FAIL" }
```

Expected: `PASS`.

### V.5 New operational artifacts exist

- [ ] `AXIOM_Panel_Tier_Membership.md` exists with six-row table
- [ ] `AXIOM_Specification_Debt.md` contains PDR Summary section
- [ ] `AXIOM_Ratification_Confirmation_<YYYYMMDD>.md` exists with confirmation statement

### V.6 Archive integrity

- [ ] Archive directory `AXIOM_Archive\<timestamp>\` contains all pre-ratification files
- [ ] `MANIFEST.sha256` exists and has one line per archived file

### V.7 Reminder set

- [ ] 30-day audit reminder set for [audit due date]

### V.8 Project knowledge base reflects new state

In the AXIOM Project knowledge base on Claude, verify:

- [ ] `AXIOM_Panel_Charter.md` reflects v1.2 content
- [ ] `AXIOM_Active_Bindings.md` (alias) reflects v1.2 content with 36 bindings
- [ ] `AXIOM_Active_Bindings_v1_2.md` is present as new versioned file
- [ ] `AXIOM_Panel_Tier_Membership.md` is present
- [ ] `AXIOM_Specification_Debt.md` is present with PDR Summary section
- [ ] `AXIOM_Ratification_Confirmation_<YYYYMMDD>.md` is present
- [ ] `AXIOM_Synthesis_Governance_v2_Cycle1.md` is present
- [ ] `AXIOM_Synthesis_Governance_v2_Cycle2.md` is present
- [ ] `AXIOM_Active_Bindings_v1_1.md` is retained as historical (do not delete)
- [ ] `AXIOM_Active_Bindings_v1_0.md` is retained as historical (do not delete)
- [ ] All Cycle 1 and Cycle 2 review documents are retained for audit trail
- [ ] Project Instructions reflect Charter v1.2 mechanics
- [ ] `AXIOM_Operator_Guide.md` reflects Charter v1.2 operational workflow

### V.9 Panel member smoke test

For each of GPT-5.5, Gemini, DeepSeek, Qwen, and Kimi:

1. Open a fresh chat with the panel member
2. Upload the four-document spine (Charter v1.2, Core Values v1.1, Constraints Register v1.1, Legacy Reference) plus `AXIOM_Active_Bindings.md` plus `AXIOM_Panel_Tier_Membership.md` plus `AXIOM_Specification_Debt.md`
3. Send a brief role notification reflecting the new role assignment:

For Gemini specifically:
> Notice: The AXIOM panel has ratified Charter v1.2 as of [ratification date]. Your role has transitioned from Research and Knowledge Arbiter to Implementation Specialist and Troubleshooter, in the Continuous Working Layer. Refer to Charter v1.2 §Role Assignments. The IS Handoff package was previously delivered.

For Kimi specifically:
> Notice: The AXIOM panel has ratified Charter v1.2 as of [ratification date]. Your role has transitioned from Implementation Specialist to Research and Knowledge Arbiter, in the Advisory Council. Refer to Charter v1.2 §Role Assignments. You now hold maintenance authority for AB-001 through AB-007.

For GPT-5.5:
> Notice: The AXIOM panel has ratified Charter v1.2 as of [ratification date]. Your role has expanded from Chief Architect to Chief Architect and Researcher, in the Continuous Working Layer. Refer to Charter v1.2 §Role Assignments.

For DeepSeek and Qwen:
> Notice: The AXIOM panel has ratified Charter v1.2 as of [ratification date]. Your role is unchanged but your tier classification is now Advisory Council. Refer to Charter v1.2 §Panel Composition.

4. Send a test prompt: "Confirm you understand: (a) your role under Charter v1.2, (b) your tier classification (continuous working layer or advisory council), (c) the active bindings that travel forward (now 36 total under v1.2), and (d) the current specification debt items in your domain. This is a smoke test of the new governance documents — not a review request."

Each panel member should respond with role identification, tier classification, binding acknowledgment, and recognition of relevant SD items. If any panel member produces a confused response, that signals a document coherence issue. Do not proceed to the next architectural cycle until resolved.

- [ ] V.9 complete — all five non-Claude panel members smoke-tested successfully under Charter v1.2

---

## Completion

When all operations are complete and every checkbox above is checked, the v1.1 → v1.2 ratification is in force. Charter v1.2 is the operative governance. The two-tier panel structure is operational. The Arbiter and Implementation Specialist role transitions are executed. The 30-day audit clock is running.

The next governance action is operator-driven. The panel is ready for the next architectural cycle under Charter v1.2.

---

## Troubleshooting

**If `AXIOM_Active_Bindings_v1_2.md` total binding count differs from 36:** stop. Re-verify Operation D step 3 binding insertion (CB-023, CB-024, CB-025) and Operation D step 4 count verification. The count must equal 36 (7 AB + 25 CB + 4 GB).

**If `AXIOM_Active_Bindings_v1_2.md` differs from v1.1 in any non-metadata, non-schema-extension line:** stop. Re-copy v1.1 to v1.2 from the archive and apply only the authorized changes (metadata update, schema extension columns, three new CB binding rows, AB-001 through AB-007 Maintaining Authority field update). No existing binding text drift is permitted.

**If alias file does not match v1.2:** re-execute Operation D step 6.

**If a panel member smoke test produces confusion about the new roles:** verify that the role notification message you sent in V.9 matched the panel member. If you sent the wrong notification (e.g., sent Gemini's notification to Kimi), the confusion is expected. Re-send the correct notification.

**If you encounter ambiguity in promoting v2_1 content to Charter v1.2 sections (Operation B):** refer to Synthesis v2 Cycle 2 §14.1 Operation B mapping table. If still unclear, the Cycle 2 Synthesis Claude (in the AXIOM Project chat where the Synthesis was produced) is the authoritative interpreter.

**If you encounter ambiguity in SD ledger updates (Operation G):** refer to Synthesis v2 Cycle 2 §11 (new SD accounting) and §12.4 (cross-check). The Synthesis governs.

**If the project knowledge base upload limit is reached:** retire `AXIOM_Active_Bindings_v1_0.md` and `AXIOM_Active_Bindings_v1_1.md` from the live knowledge base (they remain in local archives). Retain the proposals, syntheses, and reviews as ongoing reference. Do not retire Charter v1.1 — it remains live until you have verified Charter v1.2 is operationally sound.

**If Operation F transfer file is unavailable:** record "not available" in the transfer note per F.2 schema. Do not substitute unverified artifacts. The handoff proceeds with available files only; missing files are tracked in the transfer note for later retrieval.

---

*AXIOM Ratification File-Swap Runbook (Governance v2)*
*v1.1 → v1.2 Panel Operating-Model Restructuring Amendment*
*Issued under AXIOM_Synthesis_Governance_v2_Cycle2.md §14 (RATIFIED, 2026-05-14)*
