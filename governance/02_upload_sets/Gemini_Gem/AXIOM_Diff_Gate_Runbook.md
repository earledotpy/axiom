# AXIOM — Diff Gate Runbook
## Operator-Executable Integration Verification Procedure

**Document Type:** Cross-Cutting Operational Artifact — GB-001 Packaging Authority
**Status:** Active — Ratified under Charter v1.1 §4 (Integration Diff Gate and Integrator Role)
**Version:** 1.0
**Authoring Role:** Kimi K2.6 — Implementation Specialist (packaging authority per GB-001)
**Date:** 2026-05-15
**Operative Governance:** Charter v1.1 §4, Core Values v1.1, Constraints Register v1.1, Active Bindings v1.1
**Target Environment:** Windows 11, Python 3.12, Intel Celeron N4500, 8 GB RAM

---

## §0 Purpose and Scope

This runbook defines the operator-executable procedure for performing the Integration Diff Gate on AXIOM governance and implementation artifacts. The Diff Gate is a Charter v1.1 §4.1 governance mechanism that verifies candidate revisions against prior approved artifacts before they proceed to delta-confirmation or full panel review.

**What this runbook does:**
- Provides step-by-step operator instructions for running the Diff Gate
- Defines the Python script specification (standard-library only, negligible execution cost)
- Specifies the Authorized Change List format
- Documents the binding cross-check method
- Defines the four failure-mode dispositions

**What this runbook does not do:**
- Make architectural decisions (Architect's domain)
- Certify Diff Gate pass/fail (Evaluator's domain per Charter v1.1 §4.2)
- Verify factual claims about external technology (Arbiter's domain)
- Assess hardware feasibility (Constraints Reviewer's domain)

---

## §1 Diff Gate Prerequisites

### §1.1 Required Files

Before running the Diff Gate, the operator must have:

| File | Purpose | Source |
|---|---|---|
| Prior approved artifact | Source of truth for comparison | `AXIOM_Archive/<YYYYMMDD_HHMMSS>/<filename>` |
| `MANIFEST.sha256` | Hash verification for prior artifact integrity | Same archive directory |
| Candidate revision | The proposed new version | Current working directory or uploaded document |
| Authorized Change List (ACL) | Sections/lines/objects allowed to change | Provided by the author of the candidate revision |
| Active Bindings registry | For binding cross-check | `AXIOM_Active_Bindings.md` (alias to current version) |

### §1.2 Required Tools

| Tool | Version | Purpose |
|---|---|---|
| Python 3.12 | As specified in Constraints Register | Execute Diff Gate script |
| `difflib` module | Python standard library | Generate unified text diffs |
| `hashlib` module | Python standard library | SHA256 hash verification |
| `pathlib` module | Python standard library | Cross-platform path handling |
| PowerShell or Command Prompt | Windows built-in | Execute commands, file operations |

**No external dependencies.** The script uses Python standard library only. No pip install required. No network access required.

### §1.3 Environment Setup

```powershell
# Verify Python is available
python --version
# Expected: Python 3.12.x

# Verify difflib is available (standard library, should never fail)
python -c "import difflib; print('difflib OK')"
```

---

## §2 Diff Gate Script Specification

### §2.1 Script Location

Save the Diff Gate script as:

```text
.\tools\axiom_diff_gate.py
```

(If AXIOM relocates the working directory, adjust path accordingly. The script location must be recorded in `AXIOM_Canonical_Filenames.md`.)

### §2.2 Script Source Code

The script uses Python standard library only. Key functions:

- `sha256_file(filepath)` — computes SHA256 hash of a file
- `verify_manifest(archive_dir, filename)` — verifies prior artifact against MANIFEST.sha256
- `generate_diff(prior_path, candidate_path, output_path)` — generates unified diff
- `check_binding_preservation(prior_path, candidate_path, binding_ids)` — checks binding IDs appear in both files
- `run_diff_gate(...)` — executes full Diff Gate procedure and returns JSON result
- `main()` — CLI entry point for operator execution

**Script characteristics:**

| Characteristic | Value | Rationale |
|---|---|---|
| External dependencies | None | Standard library only per Charter v1.1 §4.1 |
| Execution time | <5 seconds for files up to 1 MB | Negligible cost per Charter v1.1 §4.1 |
| RAM usage | <50 MB | Fits within 2.0–2.3 GB headroom |
| Network access | None | No network required |
| API tokens consumed | Zero | No model invocation |
| Windows compatibility | Yes | Uses pathlib for cross-platform paths |
| Output format | Unified diff (text) + JSON result | Human-readable diff + machine-parseable result |

### §2.3 Operator Execution Example

```powershell
# Run the Diff Gate
python .\tools\axiom_diff_gate.py `
    "AXIOM_Archive\20260510_143000" `
    "AXIOM_Panel_Charter.md" `
    "AXIOM_Panel_Charter_v1_2.md" `
    "diff_output" `
    AB-001 AB-002 AB-003 CB-001 CB-002 GB-001

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Error "Diff Gate FAILED. See diff_gate_result_*.json for details."
    exit 1
}
Write-Host "Diff Gate PASSED."
```

---

## §3 Operator Execution Procedure

### §3.1 Step-by-Step Diff Gate Execution

#### Step 1: Locate Prior Approved Artifact

```powershell
# Identify the archive directory for the prior approved version
$archiveDir = "AXIOM_Archive\20260510_143000"  # Example — use actual timestamp

# Verify the archive directory exists
if (-not (Test-Path $archiveDir)) {
    Write-Error "Archive directory not found: $archiveDir"
    exit 1
}

# Verify MANIFEST.sha256 exists
$manifest = Join-Path $archiveDir "MANIFEST.sha256"
if (-not (Test-Path $manifest)) {
    Write-Error "MANIFEST.sha256 not found in archive"
    exit 1
}
```

#### Step 2: Verify Prior Artifact Hash

```powershell
# Read MANIFEST.sha256 to find expected hash for target file
Get-Content $manifest | Select-String "AXIOM_Panel_Charter.md"
# Expected output: <hash>  AXIOM_Panel_Charter.md

# Verify actual hash matches
$expectedHash = (Get-Content $manifest | Select-String "AXIOM_Panel_Charter.md").Line.Split()[0]
$actualHash = (Get-FileHash (Join-Path $archiveDir "AXIOM_Panel_Charter.md") -Algorithm SHA256).Hash

if ($expectedHash -ne $actualHash) {
    Write-Error "Hash mismatch! Diff Gate fails closed."
    exit 1
}
Write-Host "Hash verified: $actualHash"
```

#### Step 3: Prepare Candidate Revision

Ensure the candidate revision file is saved in the working directory with a versioned filename:

```text
AXIOM_Panel_Charter_v1_2.md
```

#### Step 4: Obtain Authorized Change List

The author of the candidate revision must provide an ACL before editing begins. The ACL format is specified in §4 of this runbook.

**The operator does not create the ACL.** The operator verifies that an ACL exists and matches the diff output.

#### Step 5: Execute Diff Gate Script

```powershell
# Run the Diff Gate
python .\tools\axiom_diff_gate.py `
    "AXIOM_Archive\20260510_143000" `
    "AXIOM_Panel_Charter.md" `
    "AXIOM_Panel_Charter_v1_2.md" `
    "diff_output" `
    AB-001 AB-002 AB-003 CB-001 CB-002 GB-001

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Error "Diff Gate FAILED. See diff_gate_result_*.json for details."
    exit 1
}
Write-Host "Diff Gate PASSED."
```

#### Step 6: Review Diff Output

```powershell
# Open the generated diff file
$diffFile = Get-ChildItem "diff_output\diff_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
notepad $diffFile.FullName
```

The operator reviews the diff to verify:
- Changes are within the Authorized Change List scope
- No unauthorized sections were modified
- Binding text is preserved character-identical
- Ratified text (code blocks, schemas, regex, filenames, values, rule orderings) is unchanged

#### Step 7: Cross-Check Against Authorized Change List

Compare the diff output line-by-line against the ACL:

| Diff Finding | ACL Authorization | Operator Action |
|---|---|---|
| Change in authorized section | Listed in ACL | Mark as expected |
| Change in unauthorized section | Not listed in ACL | Flag as integration failure |
| Formatting break caused by authorized edit | N/A — strictly required | Record explicitly in operator notes |
| Binding text modified | Should never be in ACL | Flag as binding mismatch |

#### Step 8: Record Result

The operator records the Diff Gate result in the cycle notes:

```markdown
## Diff Gate Result — Cycle N
| Field | Value |
|---|---|
| Artifact | AXIOM_Panel_Charter.md |
| Prior version | v1.1 (archive 20260510_143000) |
| Candidate version | v1.2 |
| Hash verification | PASS / FAIL |
| Diff generated | Yes — filename |
| Binding preservation | PASS / FAIL |
| ACL compliance | PASS / FAIL |
| Unauthorized changes | None / Listed |
| Operator | <operator name> |
| Date | <timestamp> |
```

### §3.2 Diff Gate Failure Modes

Per Charter v1.1 §4.6, a Diff Gate failure has one of four dispositions:

| Failure Type | Detection Method | Required Response |
|---|---|---|
| **Unauthorized change outside scope** | Diff shows changes in sections not listed in ACL | Return to author for targeted repair; no delta available. |
| **Missing prior artifact or hash mismatch** | `MANIFEST.sha256` missing, or hash does not match | Full panel review required; no delta available. |
| **Binding text mismatch** | Binding ID found in prior but not in candidate, or text differs | Restore binding text verbatim or obtain explicit supersession ruling. |
| **Canonical filename/path mismatch** | Candidate filename does not match canonical registry | Restore canonical filename/path or file a panel motion to change it. |

**No implementation plan may proceed from a candidate revision with an unresolved Diff Gate failure.**

---

## §4 Authorized Change List (ACL) Format

### §4.1 ACL Purpose

Every integration pass must include an ACL before editing begins. The ACL is authored by the candidate revision's author (typically the Architect or a continuous-layer role) and verified by the operator during Diff Gate execution.

### §4.2 ACL Schema

The ACL is a markdown table with these columns:

| Field | Required Content |
|---|---|
| **Artifact** | Filename being revised. Must match Canonical Filenames Registry entry. |
| **Authorized section(s)** | Headings, line ranges, object names, or table rows allowed to change. Must be specific enough that the operator can verify against diff output. |
| **Authorized purpose** | Exact Synthesis item or panel instruction authorizing the edit. Cite Synthesis section, SD ID, or binding ID. |
| **Ratified text to preserve** | Code blocks, schemas, regex, binding rows, filenames, values, and rule orderings that must remain character-identical. The operator verifies these against diff output. |
| **Required verification** | Diff check, binding check, schema check, filename check, or other relevant test. The operator performs the specified verification. |

### §4.3 ACL Example

```markdown
## Authorized Change List — AXIOM_Panel_Charter.md v1.1 → v1.2

| Artifact | Authorized Section(s) | Authorized Purpose | Ratified Text to Preserve | Required Verification |
|---|---|---|---|---|
| AXIOM_Panel_Charter.md | §4.1 (Tooling Decision) through §4.6 (Diff Gate Failure Mode) | Synthesis Governance v3 §10.1 — Integration Diff Gate adoption | Python standard-library `difflib` module reference; `MANIFEST.sha256` format; archive directory structure `AXIOM_Archive/<YYYYMMDD_HHMMSS>/` | Diff check + binding check |
| AXIOM_Panel_Charter.md | §7.2 (Integrator Role Identity table) | Synthesis Governance v3 §10.1 — Role assignment correction | Anti-self-certification rule text; alternate gatekeeper assignment | Diff check |
| AXIOM_Panel_Charter.md | §9.3 (Canonical Filenames Registry) | Synthesis Governance v3 §10.2 — Filename registry population | All filenames listed in §9.3 initial population | Filename check |
```

### §4.4 ACL Validation Rules

1. **ACL must exist before editing begins.** If the author begins editing without an ACL, the Diff Gate fails closed.
2. **ACL must cite specific authorization.** Vague references like "per Synthesis" are insufficient. Cite section, SD ID, or binding ID.
3. **Ratified text to preserve must be quoted verbatim.** The operator compares the quoted text against the diff output.
4. **Any change outside the ACL is an integration failure** unless it is strictly required to repair a formatting break caused by an authorized edit and is explicitly recorded.

---

## §5 Binding Cross-Check Method

### §5.1 Cross-Check Scope

The binding cross-check verifies that the candidate revision preserves all active bindings referenced in the prior artifact.

### §5.2 Cross-Check Steps

1. **Identify relevant bindings.** From the prior artifact, extract all AB, CB, and GB IDs referenced.
2. **Verify presence in candidate.** Each ID must appear in the candidate revision.
3. **Verify source cycle unchanged.** The "Source Cycle" field for each binding must match the prior artifact.
4. **Verify status unchanged.** The "Status" field must remain "Active" (or other ratified status).
5. **Verify binding text character-identical.** When restated verbatim, the binding text must match character-for-character.
6. **Verify paraphrase accuracy.** If the candidate paraphrases or mirrors binding text, the paraphrase must not weaken, rename, omit, or supersede the binding.

### §5.3 Conflict Resolution

If exact text and paraphrase conflict:
- The exact text in `AXIOM_Active_Bindings_v1_1.md` (or current versioned file) **controls**.
- The paraphrase is treated as a **binding text mismatch** (Diff Gate failure type 3).
- Resolution: restore exact text verbatim or obtain explicit supersession ruling from the Arbiter (AB), Constraints Reviewer (CB), or full panel (GB).

### §5.4 Automated Binding Check

The Diff Gate script supports automated binding presence checking:

```powershell
# Example: Check specific binding IDs
python axiom_diff_gate.py `
    "AXIOM_Archive\20260510_143000" `
    "AXIOM_Panel_Charter.md" `
    "AXIOM_Panel_Charter_v1_2.md" `
    "diff_output" `
    AB-001 AB-002 AB-003 CB-001 CB-002 GB-001 GB-002
```

The script reports each binding ID as PRESERVED or MISSING. A MISSING result triggers failure type 3 (binding text mismatch).

**Note:** Automated checking verifies presence only. Character-identical verification requires operator review of the diff output.

---

## §6 Archive Directory Structure

### §6.1 Canonical Archive Path

```text
AXIOM_Archive/
└── <YYYYMMDD_HHMMSS>/
    ├── MANIFEST.sha256
    ├── AXIOM_Panel_Charter.md
    ├── AXIOM_Core_Values.md
    ├── AXIOM_Constraints_Register.md
    ├── AXIOM_Active_Bindings_v1_1.md
    ├── <other ratified artifacts>
```

### §6.2 MANIFEST.sha256 Format

```text
<SHA256_hash>  <filename>
<SHA256_hash>  <filename>
...
```

Example:
```text
a1b2c3d4e5f6...  AXIOM_Panel_Charter.md
7890abcdef12...  AXIOM_Core_Values.md
```

### §6.3 Archive Creation Procedure

After ratification, the operator creates a new archive directory:

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "AXIOM_Archive\$timestamp"
New-Item -ItemType Directory -Path $archiveDir

# Copy ratified artifacts
Copy-Item "AXIOM_Panel_Charter.md" $archiveDir
Copy-Item "AXIOM_Core_Values.md" $archiveDir
# ... copy all ratified artifacts

# Generate MANIFEST.sha256
$files = Get-ChildItem $archiveDir -File | Where-Object { $_.Name -ne "MANIFEST.sha256" }
$manifest = @()
foreach ($file in $files) {
    $hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash
    $manifest += "$hash  $($file.Name)"
}
$manifest | Out-File (Join-Path $archiveDir "MANIFEST.sha256") -Encoding utf8

Write-Host "Archive created: $archiveDir"
```

---

## §7 Diff Gate Certification

### §7.1 Gatekeeper Role

Per Charter v1.1 §4.2:

| Function | Assigned Role |
|---|---|
| Mechanical file copying, backup creation, command execution | Human Operator |
| Diff Gate gatekeeping and pass/fail certification | Quality Evaluator (Claude) |
| Alternate Diff Gate gatekeeper when Evaluator authored candidate | Research and Knowledge Arbiter (Kimi after ratification; Gemini during this cycle) |
| Implementation packaging of diff script and operator steps | Kimi (this runbook) |
| Adversarial challenge to gate result | DeepSeek |
| Factual challenge to tooling claims | Gemini (current Arbiter) / Kimi (after ratification) |
| Feasibility challenge to tooling burden | Qwen |

### §7.2 Anti-Self-Certification Rule

The author of a candidate revision may not certify its Diff Gate result. If the Evaluator authored the candidate revision under review, the Research and Knowledge Arbiter serves as alternate Diff Gate gatekeeper for that artifact only.

### §7.3 Certification Record

When the Evaluator certifies a Diff Gate pass, the certification is recorded as:

```markdown
## Diff Gate Certification — Cycle N
| Field | Value |
|---|---|
| Artifact | <filename> |
| Prior version | <version> (archive <timestamp>) |
| Candidate version | <version> |
| Gatekeeper | <Evaluator or alternate Arbiter> |
| Certification date | <timestamp> |
| Diff output reviewed | Yes |
| ACL compliance verified | Yes |
| Binding preservation verified | Yes |
| Unauthorized changes | None |
| Certification | PASS |
```

---

## §8 Maintenance

### §8.1 Runbook Updates

This runbook is a cross-cutting artifact per GB-001. Updates require:
- **Primary authorship:** Gemini (after ratification) or Kimi (until ratification)
- **Adversarial review:** DeepSeek
- **Coherence review:** Claude
- **Feasibility review:** Qwen
- **Packaging:** Kimi (until ratification) or Gemini (after ratification)
- **Operator file creation:** Human Operator

### §8.2 Version History

| Version | Date | Change | Author |
|---|---|---|---|
| 1.0 | 2026-05-15 | Initial packaging | Kimi K2.6 |

---

*AXIOM Diff Gate Runbook — Version 1.0*
*Packaged under Charter v1.1 §4.1 and GB-001*
*Author: Kimi K2.6 — Implementation Specialist*
*Date: 2026-05-15*
