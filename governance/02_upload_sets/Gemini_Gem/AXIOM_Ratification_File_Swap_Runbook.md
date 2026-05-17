# AXIOM — Ratification File-Swap Runbook
## v1.0 → v1.1 Governance Amendment Implementation

**Document Type:** Operator Runbook
**Status:** Executable — ready for operator action
**Issued By:** Quality and Coherence Evaluator (Claude)
**Authority:** `AXIOM_Synthesis_Governance_v3.md` §12 (RATIFIED)
**Date Issued:** 2026-05-10
**Ratification Date:** 2026-05-10
**Target Completion:** Within 7 calendar days of ratification (no formal deadline; operator availability)

---

## What This Runbook Does

The Cycle 3 Synthesis ratified the governance amendment package. The ratified content currently lives inside `AXIOM_Proposal_Governance_v1.2.md`. It is not yet operative as canonical governance documents.

This runbook executes the file operations that promote the ratified content into the operative Charter v1.1, Core Values v1.1, Constraints Register v1.1, version-bumped Active Bindings registry, new Specification Debt ledger, and new Canonical Filenames registry. When this runbook is complete, the v1.1 amendment is in force as the operative governance, and the project is ready for the next architectural cycle under the new Charter.

This runbook does **not** include the panel restructuring proposal. That is a separate amendment (Artifact 2) that runs through its own panel cycle after this file swap completes.

### Relationship to Synthesis v3 §12

`AXIOM_Synthesis_Governance_v3.md` §12.2 specifies the canonical file-swap procedure in ten steps. This runbook expands that procedure to fifteen sequential steps. The additional steps (12 — Project Instructions update; 13 — Operator Guide update; 14 — panel-member smoke testing; 15 — ratification confirmation recording) are **operational expansions intended to support reliable operator execution**. They are not new ratification conditions and do not modify the ratification ruling.

The Synthesis remains the canonical authority for the ratification and for the file-swap procedure. If any conflict arises between this runbook and Synthesis v3 §12, the Synthesis governs.

---

## Pre-Swap Checklist

Before executing any file operations, confirm each item below. Do not proceed until all are checked.

- [ ] `AXIOM_Synthesis_Governance_v3.md` is in the AXIOM Project knowledge base on Claude
- [ ] `AXIOM_Proposal_Governance_v1.2.md` is in the AXIOM Project knowledge base on Claude
- [ ] All five Cycle 3 review documents are accessible locally:
  - `AXIOM_Evaluation_Governance_v1_2.md`
  - `AXIOM_Critique_Governance_v1_2.md`
  - `AXIOM_Arbiter_Governance_v1_2.md`
  - `AXIOM_Constraints_Governance_v1_2.md`
  - `AXIOM_Governance_Implementability_Review_v1_2.md`
- [ ] `AXIOM_Active_Bindings_v1_0.md` is the current bindings file on disk
- [ ] No new chat sessions are mid-cycle for any other AXIOM proposal that depends on Charter v1.0
- [ ] You have at least 90 uninterrupted minutes to complete the file operations and verification

---

## Step 1 — Create the Archive Directory and Snapshot Pre-Ratification State

The archive preserves the complete pre-ratification state for audit. Do this first, before any other operation, so that if any subsequent step fails you can roll back to a known state.

### 1.1 Create the archive directory

Use the current UTC timestamp at the moment of ratification recording. Format: `YYYYMMDD_HHMMSS`. For 2026-05-10 at the time you execute this, use whatever the current UTC time is.

On Windows PowerShell:

```powershell
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$archiveDir = "AXIOM_Archive\$timestamp"
New-Item -ItemType Directory -Path $archiveDir
```

Record the exact `$timestamp` value in your notes. You will reference it again in Step 10.

### 1.2 Copy pre-ratification files into the archive

Copy each of the following into the archive directory you just created. Use Copy-Item or your file manager; do not move them — originals remain in place until later steps.

Spine documents (v1.0):
- `AXIOM_Panel_Charter.md`
- `AXIOM_Core_Values.md`
- `AXIOM_Constraints_Register.md`
- `AXIOM_Active_Bindings_v1_0.md`
- `AXIOM_Active_Bindings.md` (alias file, if it exists)
- `AXIOM_Legacy_Reference.md`

Amendment proposal artifacts:
- `AXIOM_Proposal_Governance_v1.md`
- `AXIOM_Proposal_Governance_v1_1.md`
- `AXIOM_Proposal_Governance_v1_2.md`

Synthesis artifacts:
- `AXIOM_Synthesis_Governance_v1_1.md`
- `AXIOM_Synthesis_Governance_v1_1_Routing.md`
- `AXIOM_Synthesis_Governance_v2.md`
- `AXIOM_Synthesis_Governance_v3.md`

Cycle 1 review artifacts:
- `AXIOM_Evaluation_Governance_v1.md`
- `AXIOM_Critique_Governance_v1.md`
- `AXIOM_Arbiter_Governance_v1.md`
- `AXIOM_Constraints_Governance_v1.md`
- `AXIOM_Governance_Implementability_Review.md`

Cycle 2 review artifacts:
- `AXIOM_Evaluation_Governance_v1_1.md`
- `AXIOM_Critique_Governance_v1_1.md`
- `AXIOM_Arbiter_Governance_v1_1.md`
- `AXIOM_Constraints_Governance_v1_1.md`
- `AXIOM_Governance_Implementability_Review_v1_1.md`

Cycle 3 review artifacts:
- `AXIOM_Evaluation_Governance_v1_2.md`
- `AXIOM_Critique_Governance_v1_2.md`
- `AXIOM_Arbiter_Governance_v1_2.md`
- `AXIOM_Constraints_Governance_v1_2.md`
- `AXIOM_Governance_Implementability_Review_v1_2.md`

Operator artifacts:
- `AXIOM_Operator_Guide.md`
- `AXIOM_Project_Instructions.md` (your local copy if maintained)

### 1.3 Generate the archive manifest

From inside the archive directory:

```powershell
cd $archiveDir
Get-FileHash -Algorithm SHA256 *.md | ForEach-Object { "$($_.Hash)  $($_.Path | Split-Path -Leaf)" } | Out-File -FilePath MANIFEST.sha256 -Encoding ASCII
```

Verify `MANIFEST.sha256` contains one line per archived file with format `<hash>  <filename>`. Return to the parent directory before proceeding.

- [ ] Step 1 complete — archive directory created with timestamp recorded and `MANIFEST.sha256` generated

---

## Step 2 — Promote v1.2 Content into Charter v1.1

Open `AXIOM_Proposal_Governance_v1.2.md` in a text editor. You will produce a new `AXIOM_Panel_Charter.md` that replaces the v1.0 version on disk and in the project knowledge base.

### 2.1 Start from the v1.0 Charter

Open the archived v1.0 `AXIOM_Panel_Charter.md` and the v1.2 Proposal side by side. The new v1.1 Charter is built by carrying forward v1.0 content where v1.2 did not modify it, and replacing or extending where v1.2 did.

### 2.2 Apply v1.2 content per the Synthesis v3 §12.2 mapping

The Synthesis specifies which v1.2 sections map to which Charter sections. Apply each:

| v1.2 Section | Charter v1.1 Destination |
|---|---|
| §2 — Constitutional Closure: Prospective-Only Charter Audit | §Charter Amendment Process and §30-Day Audit |
| §3 — Delta-Confirmation Enforcement (D1.A/B/C corrections) | §Delta-Confirmation Cycle |
| §4 — Integration Diff Gate and Integrator Role | §Integration Discipline |
| §4.1 — Synthesis structure mandate (eight-section template) | §Synthesis Document Structure |
| §4.2 — Alternate gatekeeper assignment (SD-024 closure) | §Integration Discipline subsection on Diff Gate role assignment |
| §5 — Specification Debt System (D2.A/B corrections included) | §Specification Debt |
| §6 — Cross-Cutting Artifact Protocol Extension | Flagged as **proposed panel motion not yet ratified**; do NOT promote to active GB-001 extension |
| §6.5 — Cross-cutting protocol class-list rationale (SD-019 closure) | Same section as §6, included as part of the proposed motion documentation |
| §8 — Constraints Register and Active Bindings Corrections | §Conflict Resolution and §Active Bindings Authority |
| §9 — Synthesis Workflow and Governance File Conventions | §Synthesis Workflow, §File Conventions, §Canonical Filenames Registry |

### 2.3 Critical inclusions

The Cycle 3 patch added §5.6 (trivial-flag dismissal motion) and §5.7 (Synthesis-vs-ledger cross-check). Both must be present in the Charter §Specification Debt section verbatim from v1.2.

The §3.3 corrections (D1.A hold-on-implementation, D1.B 72-hour window, D1.C catch-all objection ground) must be present in the Charter §Delta-Confirmation Cycle section verbatim from v1.2.

### 2.4 Update the version field

Set the version field at the top of the Charter document to `v1.1`. Add a footer note: `Ratified Cycle 3, 2026-05-10 by AXIOM_Synthesis_Governance_v3.md.`

### 2.5 Save and verify

Save the file as `AXIOM_Panel_Charter.md` in the project working directory. Verify the document contains:

- Updated version field reading `v1.1`
- §Delta-Confirmation Cycle with the D1.A, D1.B, D1.C corrections present
- §Specification Debt with §5.6 dismissal motion and §5.7 cross-check present
- §6 marked as proposed motion not yet ratified
- All v1.0 sections that v1.2 did not modify carried forward verbatim

- [ ] Step 2 complete — Charter v1.1 saved to working directory

---

## Step 3 — Promote v1.2 Content into Core Values v1.1

The v1.2 proposal includes Core Values clarifications in §7. These promote into the Core Values document, not the Charter.

### 3.1 Start from the v1.0 Core Values

Open the archived v1.0 `AXIOM_Core_Values.md`. You will produce a new `AXIOM_Core_Values.md` that adds the v1.2 operational clarifications.

### 3.2 Apply v1.2 §7 clarifications

Per Synthesis v3 §12.2 Step 3:

**CV2 §7.1 — Panel-approved sanitization mechanism.** Add the v1.2 §7.1 language defining when sanitization tasks may be assigned to the local model, the three approval paths (active binding / ratified spec / Synthesis-authorized scope), and the anti-overreach paragraph stating that the local model may classify safety but may not decide plan quality.

**CV5 §7.2 — Implementation-stage guardrail enforcement requirements.** Add the v1.2 §7.2 language specifying that field-assignment registries, per-write schema validation, and structured logging are implementation-stage requirements enforced by Kimi at implementation time, not at governance ratification time.

**CV3 application to governance.** Reference v1.2 §4.2's anti-self-certification rule for the Diff Gate. This is a CV3 application to governance procedure: the Evaluator does not certify the Diff Gate output for a revision the Evaluator authored.

### 3.3 What does not change

CV1, CV4, CV6 carry forward verbatim from v1.0. Do not modify them.

### 3.4 Update the version field

Set the version field to `v1.1`. Add the same ratification footer note as the Charter.

### 3.5 Save and verify

Save as `AXIOM_Core_Values.md` in the project working directory. Verify CV2 contains the §7.1 sanitization mechanism, CV5 contains the §7.2 implementation guardrails, CV3 contains the anti-self-certification reference, and CV1/CV4/CV6 are unchanged from v1.0.

- [ ] Step 3 complete — Core Values v1.1 saved to working directory

---

## Step 4 — Rebuild Constraints Register v1.1

The Constraints Register is rebuilt from v1.2 §8, which corrected the binding crosswalk and supersession rules.

### 4.1 Start from the v1.0 Constraints Register

Open the archived v1.0 `AXIOM_Constraints_Register.md`. The new v1.1 version applies the v1.2 §8 corrections.

### 4.2 Apply v1.2 §8 corrections

**§8.1 — Supersession rule.** Add the v1.2 §8.1 language: mirroring a binding into the Constraints Register does not supersede the source binding. Only an explicit panel motion citing the prior binding can supersede it.

**§8.2 — Rejection of B1–B22 numbering.** Add the v1.2 §8.2 language: the B1–B22 parallel numbering scheme proposed in v1 is rejected. Only the original AB-*, CB-*, GB-* IDs are canonical.

**§8.3 — Verbatim crosswalk of all 33 active bindings.** Include the complete crosswalk of all 33 bindings using AB-001 through AB-007, CB-001 through CB-022, and GB-001 through GB-004 IDs, character-identical to `AXIOM_Active_Bindings_v1_0.md`. No parallel B-* numbering scheme.

**§8.4 — Isolation of PROPOSED runtime invariants.** Add the v1.2 §8.4 language: `PRAGMA synchronous=FULL` and any other proposed-but-not-binding runtime invariants are isolated from active bindings. They remain PROPOSED and do not appear in the binding crosswalk.

**§8.5 — Maintenance ownership table.** Add the v1.2 §8.5 maintenance ownership table specifying which role maintains which binding class.

### 4.3 Update the version field

Set the version field to `v1.1`. Add the ratification footer note.

### 4.4 Save and verify

Save as `AXIOM_Constraints_Register.md` in the project working directory. Verify §8 contains the five corrections and the complete crosswalk of 33 bindings.

- [ ] Step 4 complete — Constraints Register v1.1 saved to working directory

---

## Step 5 — Update Active Bindings Registry to v1.1

The Active Bindings registry version-bumps from v1.0 to v1.1. The binding set does not expand. All 33 bindings carry forward verbatim.

### 5.1 Copy v1.0 to v1.1

```powershell
Copy-Item -Path "AXIOM_Active_Bindings_v1_0.md" -Destination "AXIOM_Active_Bindings_v1_1.md"
```

### 5.2 Edit v1.1 metadata only

Open `AXIOM_Active_Bindings_v1_1.md` in a text editor and update:

- Version field: `v1.0` → `v1.1`
- Ratification cycle field: add `Ratified Cycle 3, 2026-05-10 by AXIOM_Synthesis_Governance_v3.md`
- Footer note: add `Bindings now operate under Charter v1.1 governance rules. Binding set unchanged from v1.0.`

### 5.3 Do not modify any binding text

All 33 binding rows must remain character-identical to v1.0. Do not edit any AB, CB, or GB entry. No new bindings are added. The Synthesis explicitly ruled no new GB bindings issued at ratification.

### 5.4 Verify

Compare `AXIOM_Active_Bindings_v1_0.md` and `AXIOM_Active_Bindings_v1_1.md` line by line. Only the version field, ratification cycle field, and footer note should differ. All 33 binding rows must be identical.

```powershell
# Compare files (PowerShell):
Compare-Object -ReferenceObject (Get-Content "AXIOM_Active_Bindings_v1_0.md") -DifferenceObject (Get-Content "AXIOM_Active_Bindings_v1_1.md")
```

The differences should be limited to metadata lines (3–5 lines max). If any binding row appears in the diff output, you have an error — re-copy v1.0 to v1.1 and start over.

- [ ] Step 5 complete — `AXIOM_Active_Bindings_v1_1.md` saved with 33 bindings character-identical to v1.0

---

## Step 6 — Maintain the Alias File

Per Charter v1.1 §9.2, the `AXIOM_Active_Bindings.md` alias is a plain copy of the latest versioned file. Not a symlink — Windows file system compatibility requires a true copy.

### 6.1 Overwrite the alias

```powershell
Copy-Item -Path "AXIOM_Active_Bindings_v1_1.md" -Destination "AXIOM_Active_Bindings.md" -Force
```

### 6.2 Preserve v1.0 as historical record

Do **not** delete `AXIOM_Active_Bindings_v1_0.md`. It remains on disk as the historical record. It already exists in the archive directory from Step 1 — keep both the archive copy and the working-directory copy.

### 6.3 Verify byte-for-byte equality of alias

```powershell
$hashAlias = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings.md").Hash
$hashV11 = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings_v1_1.md").Hash
if ($hashAlias -eq $hashV11) { "Alias matches v1.1" } else { "MISMATCH — alias does not equal v1.1" }
```

Expected output: `Alias matches v1.1`.

- [ ] Step 6 complete — alias matches v1.1 byte-for-byte; v1.0 historical record preserved

---

## Step 7 — Create the Specification Debt Ledger

Charter v1.1 §5.2 specifies the canonical specification-debt ledger as a discrete append-only file. Create it now with the current debt items at ratification.

### 7.1 Create the file

Create `AXIOM_Specification_Debt.md` in the working directory. Use the §5.3 schema:

| Field | Description |
|---|---|
| Debt ID | SD-### unique identifier |
| Source | Synthesis document or review that opened the item |
| Subject | Brief description |
| Severity | LOW / LOW-MEDIUM / MEDIUM / BLOCKING |
| Cycle Count | "1 of 2" / "2 of 2" / "Closed" |
| Status | Open / Closed / Deferred |
| Closure Section/Artifact | Document and section where closure occurred (if closed) |
| Notes | Additional context |

### 7.2 Initial population

Per Synthesis v3 §9.2 and §9.1:

**Cycle 2 SD items still open (cycle 1 of 2):** SD-020, SD-021, SD-022, SD-023, SD-025, SD-026, SD-027, SD-028, SD-029, SD-030, SD-031, SD-032, SD-033, SD-034. Source for each: `AXIOM_Synthesis_Governance_v2.md §6.1`. Status: Open.

**Cycle 2 SD items closed in Cycle 3:**
- SD-019 — Cross-cutting protocol class-list rationale. Status: Closed. Closure Section: `AXIOM_Proposal_Governance_v1.2.md §6.5`.
- SD-024 — Alternate gatekeeper role tension. Status: Closed. Closure Section: `AXIOM_Proposal_Governance_v1.2.md §4.2`.

**Cycle 3 SD items (cycle 1 of 2):** SD-035 through SD-044. Source for each: `AXIOM_Synthesis_Governance_v3.md §9.1`. Status: Open. Refer to the Synthesis v3 §9.1 table for subjects and severities.

**Cycle 1 SD items (historical):** SD-001 through SD-018 may be recorded with Status `Closed (Cycle 2)` for completeness, or omitted from the active ledger with a note that they are recorded in `AXIOM_Synthesis_Governance_v1_1.md`. Operator choice; either is procedurally valid.

### 7.3 Add the ledger header

Include at the top of the file:

```
# AXIOM Specification Debt Ledger
Canonical specification-debt registry per Charter v1.1 §5.2.
Append-only. Closures are recorded by updating the Status field, not by removing rows.
Initial population: 2026-05-10 at v1.0 → v1.1 ratification.
```

### 7.4 Save and verify

Verify the ledger contains all Cycle 2 and Cycle 3 SD items with correct status. Cycle 1 SD items either present as historical or referenced via note.

- [ ] Step 7 complete — `AXIOM_Specification_Debt.md` created with initial population

---

## Step 8 — Create the Canonical Filenames Registry

Charter v1.1 §9.3 requires a Canonical Filenames Registry. The Evaluator maintains it during future Synthesis cycles. Initial population is incremental and does not need to be exhaustive at ratification.

### 8.1 Create the file

Create `AXIOM_Canonical_Filenames.md` in the working directory.

### 8.2 Initial population

Include at minimum:

```
# AXIOM Canonical Filenames Registry
Canonical filename registry per Charter v1.1 §9.3.
Maintained by the Quality and Coherence Evaluator during Synthesis cycles.
Initial population: 2026-05-10 at v1.0 → v1.1 ratification.

## Spine Documents
- AXIOM_Panel_Charter.md            — current operative Charter
- AXIOM_Core_Values.md              — current operative Core Values
- AXIOM_Constraints_Register.md     — current operative Constraints Register
- AXIOM_Active_Bindings.md          — alias to latest versioned active bindings
- AXIOM_Legacy_Reference.md         — pre-AXIOM build context

## Versioned Bindings Files
- AXIOM_Active_Bindings_v1_0.md     — historical (pre-Charter-v1.1)
- AXIOM_Active_Bindings_v1_1.md     — current canonical (Charter v1.1 era)

## Living Registries
- AXIOM_Specification_Debt.md       — append-only debt ledger
- AXIOM_Canonical_Filenames.md      — this file (self-reference)

## Archive
- AXIOM_Archive/                    — directory containing pre-ratification snapshots

## Filename Patterns (For Future Artifacts)
- AXIOM_Proposal_<Domain>_v<N>.md
- AXIOM_Synthesis_<Domain>_v<Cycle>_<Revision>.md
- AXIOM_Evaluation_<Domain>_v<N>.md
- AXIOM_Critique_<Domain>_v<N>.md
- AXIOM_Arbiter_<Domain>_v<N>.md
- AXIOM_Constraints_<Domain>_v<N>.md
- AXIOM_Implementation_<Domain>_v<N>.md (or Implementability_Review for governance)
- AXIOM_Delta_Confirmation_<ProposalName>_v<N>.md
- AXIOM_Charter_Amendment_Audit_<YYYYMMDD>.md

## Implementation-Stage Files (Charter v1.1 §7.2 / CV5 — Created When AXIOM System Is Built)
- AXIOM_Field_Assignment_Register.md
```

### 8.3 Save

Save as `AXIOM_Canonical_Filenames.md`.

- [ ] Step 8 complete — Canonical Filenames Registry created with initial population

---

## Step 9 — Set the 30-Day Charter Amendment Audit Reminder

Charter v1.1 §2.2 specifies a 30-calendar-day audit cadence following each Charter ratification.

### 9.1 Calculate the audit date

Ratification date: 2026-05-10. Audit due: 2026-06-09.

### 9.2 Create the reminder

Use whatever reminder system the operator normally uses (calendar, task manager, paper note). The reminder must include:

- Date: 2026-06-09
- Content: "Charter Amendment Audit due. The Evaluator authors `AXIOM_Charter_Amendment_Audit_20260609.md` per Charter v1.1 §2.2."

### 9.3 What the audit actually does for v1.0 → v1.1

Per Synthesis v3 §11, the audit's first subject is the **next** Charter amendment, not v1.0 → v1.1 itself. The 30-day reminder for v1.0 → v1.1 produces an audit artifact that records: "No audit-eligible amendment in scope; clause becomes operative for next Charter amendment."

This is technically a no-op for v1.0 → v1.1 but operationalizes the reminder cadence for future Charter amendments. When the panel restructuring amendment (Artifact 2) ratifies, the audit clause becomes operative for it, and the audit due 30 days after that ratification will have substantive scope.

- [ ] Step 9 complete — 30-day audit reminder set for 2026-06-09

---

## Step 10 — Verify the Swap

Run a basic integrity check before declaring the swap complete.

### 10.1 Spine document version fields

- [ ] `AXIOM_Panel_Charter.md` version field reads `v1.1`
- [ ] `AXIOM_Core_Values.md` version field reads `v1.1`
- [ ] `AXIOM_Constraints_Register.md` version field reads `v1.1`
- [ ] `AXIOM_Active_Bindings_v1_1.md` version field reads `v1.1`

### 10.2 Binding preservation

Run the comparison again:

```powershell
$diff = Compare-Object -ReferenceObject (Get-Content "AXIOM_Active_Bindings_v1_0.md") -DifferenceObject (Get-Content "AXIOM_Active_Bindings_v1_1.md")
$diff | Where-Object { $_.InputObject -notmatch "v1\.0|v1\.1|Ratified Cycle 3|2026-05-10|Bindings now operate" }
```

The filtered output should be empty. If any line appears in the output, you have unauthorized binding modification — investigate immediately.

### 10.3 Alias match

```powershell
$hashAlias = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings.md").Hash
$hashV11 = (Get-FileHash -Algorithm SHA256 "AXIOM_Active_Bindings_v1_1.md").Hash
if ($hashAlias -eq $hashV11) { "PASS: Alias matches v1.1" } else { "FAIL: Alias does not match v1.1" }
```

Expected: `PASS: Alias matches v1.1`.

### 10.4 New living registries exist

- [ ] `AXIOM_Specification_Debt.md` exists with all Cycle 2 (open) and Cycle 3 SD items at cycle 1 of 2, plus SD-019 and SD-024 marked Closed
- [ ] `AXIOM_Canonical_Filenames.md` exists with initial population

### 10.5 Archive integrity

- [ ] Archive directory `AXIOM_Archive\<timestamp>\` contains all pre-ratification files
- [ ] `MANIFEST.sha256` exists and has one line per archived file

### 10.6 Reminder set

- [ ] 30-day audit reminder set for 2026-06-09

If all checks pass, the file swap is complete. If any check fails, do not proceed to Step 11 until the failure is investigated and resolved.

- [ ] Step 10 complete — all integrity checks pass

---

## Step 11 — Update the AXIOM Project Knowledge Base on Claude

The Claude project knowledge base must reflect the new ratified state so future panel chats use v1.1 documents.

### 11.1 Files to replace

In the AXIOM Project knowledge base, replace:

- [ ] `AXIOM_Panel_Charter.md` (v1.0 → v1.1)
- [ ] `AXIOM_Core_Values.md` (v1.0 → v1.1)
- [ ] `AXIOM_Constraints_Register.md` (v1.0 → v1.1)
- [ ] `AXIOM_Active_Bindings.md` (alias, still same filename, now points to v1.1 content)

### 11.2 Files to add

Add these new files to the knowledge base:

- [ ] `AXIOM_Active_Bindings_v1_1.md` — new versioned canonical file
- [ ] `AXIOM_Specification_Debt.md` — new living registry
- [ ] `AXIOM_Canonical_Filenames.md` — new living registry
- [ ] `AXIOM_Synthesis_Governance_v3.md` — required upload for any future panel chat involving the governance amendment until superseded

### 11.3 Files to retain

Do not delete these from the knowledge base — they remain for historical reference:

- All v1.0 → v1.1 cycle artifacts (proposals v1, v1.1, v1.2; Synthesis v1.1, v2, v3; all Cycle 1/2/3 reviews; Routing Addendum)
- `AXIOM_Active_Bindings_v1_0.md` (historical)
- `AXIOM_Legacy_Reference.md`

### 11.4 Verify the new spine

After the knowledge base update, the four-document spine for fresh chats is:

1. `AXIOM_Panel_Charter.md` (now v1.1)
2. `AXIOM_Core_Values.md` (now v1.1)
3. `AXIOM_Constraints_Register.md` (now v1.1)
4. `AXIOM_Active_Bindings.md` (alias, now points to v1.1 content)

Plus required uploads per Charter v1.1:

- `AXIOM_Specification_Debt.md`
- `AXIOM_Canonical_Filenames.md`
- Active Synthesis documents per the Routing rules

- [ ] Step 11 complete — Claude project knowledge base updated

---

## Step 12 — Update Project Instructions

The Project Instructions field in the AXIOM Project on Claude must be updated so that the project's Claude instance operates under Charter v1.1 mechanics rather than v1.0.

The Project Instructions are a **derived operational document**. They are not Charter-level ratified content. Their purpose is to make the Claude instance in the project behave correctly under the ratified governance. They are updated as a downstream consequence of ratification, not as part of the ratified proposal package.

### 12.1 Locate or regenerate the working draft

A working draft of Project Instructions conforming to Charter v1.1 (`AXIOM_Project_Instructions_v1_1_PROPOSED.md`) was produced earlier in this conversation. If you still have it locally, you can use it as the starting point for the live update.

If you do not have it locally, regenerate by deriving from the ratified Charter v1.1: the Project Instructions must reference Charter v1.1 §Delta-Confirmation Cycle, §Specification Debt, §Integration Discipline, §Synthesis Document Structure, and §Active Bindings Authority. The Claude role within the project (Quality and Coherence Evaluator with Synthesis authority) and the operational rules (Evaluation Structure, Active Bindings travel forward, Stay in the Evaluator role, Be direct) remain materially unchanged from v1.0.

Before pasting into the live project, review the draft once against the now-operative Charter v1.1 to confirm it does not reference any pre-ratification language (for example, references to "proposed Charter v1.1" should be updated to "Charter v1.1").

### 12.2 Replace the live Project Instructions

In the Claude AXIOM Project settings, replace the Project Instructions text with the reviewed v1.1 content. This is a single hard cutover — there is no version history on that field.

### 12.3 Verify

Open a fresh chat in the AXIOM Project and confirm that the Project Instructions reference Charter v1.1 mechanisms (delta-confirmation cycles, specification debt, Active Bindings, Integration Discipline, Synthesis as a named step) and that no language refers to v1.1 as "proposed" or "pending."

- [ ] Step 12 complete — Project Instructions updated to operate under Charter v1.1

---

## Step 13 — Update Operator Guide

The Operator Guide is a **derived operational document** describing how the human operator works with the panel under Charter v1.1. Like the Project Instructions, it is not Charter-level ratified content. It is downstream operational documentation that must conform to the ratified governance baseline.

### 13.1 Locate or regenerate the working draft

A working draft of Operator Guide v1.1 (`AXIOM_Operator_Guide_v1_1_PROPOSED.md`) was produced earlier in this conversation. If you have it locally, use it as the starting point.

If you do not have it locally, regenerate from the ratified Charter v1.1: the Operator Guide must describe the cycle workflow under Charter v1.1 §Delta-Confirmation Cycle, the chat-handoff procedure with Active Bindings carry-forward, the knowledge base hygiene rules, the cross-cutting artifact production workflow, the integration-discipline procedure for returning revisions, and the file naming conventions including Synthesis document patterns.

Note: The Operator Guide working draft was produced before the formal amendment cycle and includes content that the ratification did not modify. It does not require re-derivation in full — only verification that no section references pre-ratification language. Review for any references to "proposed Charter v1.1" or "pending amendment" and update to operative-Charter language.

### 13.2 Replace the local operator guide

Replace any local `AXIOM_Operator_Guide.md` with the reviewed v1.1 content.

### 13.3 Add to knowledge base

Upload the new Operator Guide to the AXIOM Project knowledge base, replacing the v1.0 version.

### 13.4 Read it through

Read the new Operator Guide once end-to-end. Note that the Drive integration sections do not apply yet — those will activate only after the Artifact 2 restructuring amendment ratifies and is implemented. The cross-cycle handoff procedures, Active Bindings management rules, and knowledge base hygiene rules apply immediately under Charter v1.1.

- [ ] Step 13 complete — Operator Guide updated to operate under Charter v1.1, locally and in knowledge base

---

## Step 14 — Smoke-Test the New Spine

Before the next architectural cycle, verify that each non-Claude panel member can read the new v1.1 documents coherently.

### 14.1 Test each panel member

For each of GPT-5.5, Gemini, DeepSeek, Qwen, and Kimi:

1. Open a fresh chat with the panel member.
2. Upload the new four-document spine plus `AXIOM_Active_Bindings.md` (alias) plus `AXIOM_Specification_Debt.md`.
3. Send the role briefing verbatim per `AXIOM_Operator_Guide_v1_1.md` §Part 2.
4. Send this test prompt: "Confirm you understand: (a) the Charter version, (b) your role under it, (c) the active bindings that travel forward with proposals, and (d) the current specification debt items in your domain. This is a smoke test of the new governance documents — not a review request."

### 14.2 Expected outcome

Each panel member should respond with:

- Identification of Charter v1.1 as the operative document
- Restatement of their role per the Charter
- Acknowledgment that the 33 active bindings travel forward
- Recognition of the Specification Debt ledger

If any panel member produces a confused response, that signals a document coherence issue. Do not proceed to the next architectural cycle until resolved.

- [ ] Step 14 complete — all five non-Claude panel members smoke-tested successfully

---

## Step 15 — Record the Ratification Confirmation

Per Synthesis v3 §12.4, the operator records a confirmation statement closing the v1.0 → v1.1 ratification cycle.

### 15.1 Create the confirmation file

Create `AXIOM_Ratification_Confirmation_20260510.md` in the working directory.

### 15.2 Content

```
# AXIOM v1.0 → v1.1 Governance Ratification Confirmation

**Ratification Date:** 2026-05-10
**Authority:** AXIOM_Synthesis_Governance_v3.md
**Operator:** [Your name or operator identifier]
**File-Swap Completion Date:** [Date you complete this runbook]

## Confirmation Statement

I confirm that the file-swap procedure specified in AXIOM_Synthesis_Governance_v3.md §12.2 has been completed in full, with the runbook's operational expansions (Steps 12 through 15) executed as supporting work to ensure reliable execution. The Synthesis remains the canonical authority; the runbook's added steps are not new ratification conditions.

Specifically:

1. All fifteen steps of the AXIOM Ratification File-Swap Runbook executed.
2. Archive directory AXIOM_Archive/[timestamp]/ created with MANIFEST.sha256.
3. AXIOM_Panel_Charter.md updated to v1.1 (canonical content from AXIOM_Proposal_Governance_v1.2.md).
4. AXIOM_Core_Values.md updated to v1.1 (canonical content from AXIOM_Proposal_Governance_v1.2.md).
5. AXIOM_Constraints_Register.md updated to v1.1 (canonical content from AXIOM_Proposal_Governance_v1.2.md).
6. AXIOM_Active_Bindings_v1_1.md created with all 33 bindings character-identical to v1.0.
7. AXIOM_Active_Bindings.md alias updated to v1.1 content.
8. AXIOM_Specification_Debt.md created with Cycle 2 and Cycle 3 SD items.
9. AXIOM_Canonical_Filenames.md created with initial population.
10. 30-day Charter Amendment Audit reminder set for 2026-06-09.
11. Claude AXIOM Project knowledge base updated to v1.1 spine.
12. AXIOM_Project_Instructions updated as derived operational document conforming to Charter v1.1.
13. AXIOM_Operator_Guide.md updated as derived operational document conforming to Charter v1.1.
14. All five non-Claude panel members smoke-tested on the new spine.

The v1.0 → v1.1 ratification cycle is closed. Future cycles operate under Charter v1.1.

The next planned governance action is the panel restructuring amendment (Artifact 2), to be drafted as a framework by the Evaluator and formalized as a proposal by the Chief Architect under Charter v1.1 §Charter Amendment Process.

[Operator signature/identifier]
```

### 15.3 Save and add to knowledge base

Save the file and upload it to the AXIOM Project knowledge base.

- [ ] Step 15 complete — ratification confirmation recorded

---

## Completion

When all fifteen steps are complete and every checkbox above is checked, the v1.0 → v1.1 ratification is in force. The amendment is operative governance. The next governance work is the panel restructuring amendment.

The amendment that produced this ratification is now law. The work that established the law has earned its place in the audit trail. Move forward.

---

## Troubleshooting

**If a Cycle 2 or Cycle 3 SD item subject does not match the Synthesis v3 §9.1 table:** check Synthesis v3 §9.1 for the canonical subjects. The Synthesis is the canonical authority for SD ID assignment per Charter v1.1 §5.1.

**If `AXIOM_Active_Bindings_v1_1.md` differs from v1.0 in any non-metadata line:** stop. Re-copy v1.0 to v1.1 from the archive and apply only metadata changes. The Synthesis is explicit: no binding text changes at v1.0 → v1.1.

**If a panel member smoke-test produces confusion about Kimi or Gemini roles:** that is expected and not a swap problem. Under Charter v1.1, Kimi is still Implementation Specialist and Gemini is still Arbiter. The role swap proposed in Artifact 2 is not yet ratified and does not apply.

**If you encounter ambiguity in promoting v1.2 content to Charter v1.1 sections (Step 2):** refer to Synthesis v3 §12.2 Step 2 mapping table. If still unclear, the Cycle 3 Evaluator (Claude in the AXIOM Project chat where Synthesis v3 was produced) is the authoritative interpreter.

**If the project knowledge base upload limit is reached:** retire `AXIOM_Active_Bindings_v1_0.md` and the v1.0 spine documents from the live knowledge base (they exist in the local archive). Retain the proposals, syntheses, and reviews as ongoing reference.

---

*AXIOM Ratification File-Swap Runbook — v1.0 → v1.1*
*Issued under AXIOM_Synthesis_Governance_v3.md §12 (RATIFIED, 2026-05-10)*
