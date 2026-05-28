# Layer 2: Panel Structure Conventions — Codex Implementation Brief

**From**: Claude Code (Governance Auditor)
**To**: Codex (Implementation Specialist)
**Date**: 2026-05-28
**ADR-0006 path**: Jeremy-directed shorter path — no Antigravity planning step required
**Branch**: create new branch from master, e.g. `codex/layer2-panel-structure`

---

## Goal

Apply consistent visual panel structure to all operator-facing terminal
commands so each panel matches the design language in
`ui/terminal/docs/axiom-console-mockup.html`. No layout changes, no
Spectre.Console, no side-by-side rendering — this is linear output only.
Every panel gets a `▌ TITLE` header, a dim rule separator, and `▸` section
leaders. Nothing else changes.

---

## Boundary

- **Touch only**: `ui/terminal/modules/` files listed below
- **Do not touch**: any Python runtime, manifests, governance files, tests,
  `axiom/`, `tools/`
- **Do not add**: new DB queries, new modules, new commands, Spectre.Console
- Terminal modules are not in the pytest suite — no test changes needed

---

## Step 1 — Update shared helpers in `39-operator-ui.ps1`

Three functions change. No others.

### `Write-AxiomUiTitle` — add `▌` prefix, dim rule, optional Meta

**Current:**
```powershell
function Write-AxiomUiTitle {
    param([Parameter(Mandatory = $true)][string]$Title)

    Write-Host ""
    Write-Host $Title -ForegroundColor Green
    Write-Host ("=" * $Title.Length) -ForegroundColor Green
    Write-Host ""
}
```

**New:**
```powershell
function Write-AxiomUiTitle {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [string]$Meta = ""
    )

    Write-Host ""
    Write-Host "▌ " -NoNewline -ForegroundColor Green
    Write-Host $Title -NoNewline -ForegroundColor Green
    if ($Meta) {
        Write-Host "    $Meta" -ForegroundColor DarkGray
    } else {
        Write-Host ""
    }
    Write-Host ("  " + ("─" * 70)) -ForegroundColor DarkGray
}
```

### `Write-AxiomUiSection` — add `▸` prefix

**Current:**
```powershell
function Write-AxiomUiSection {
    param([Parameter(Mandatory = $true)][string]$Title)

    Write-Host ""
    Write-Host $Title -ForegroundColor DarkGreen
}
```

**New:**
```powershell
function Write-AxiomUiSection {
    param([Parameter(Mandatory = $true)][string]$Title)

    Write-Host ""
    Write-Host "  ▸ $Title" -ForegroundColor DarkGreen
}
```

### `Write-AxiomUiRule` — new function, add after `Write-AxiomUiSection`

```powershell
function Write-AxiomUiRule {
    Write-Host ("  " + ("─" * 68)) -ForegroundColor DarkGray
}
```

---

## Step 2 — Update each panel module's title line

Every module currently renders its title as a bare `Write-Host "AXIOM X"` +
`Write-Host "===="` pair. Replace each pair with a single
`Write-AxiomUiTitle` call. The `Write-AxiomUiTitle` call takes care of the
blank line before, the `▌` prefix, and the dim rule — do not add extra
`Write-Host ""` lines around it.

### `39-now.ps1`

Find and replace the `Write-AxiomUiTitle "AXIOM NOW"` call (line 252).
`Write-AxiomUiTitle` already called here — just add the Meta argument.
The session ID is available later in the function after the DB query, so
use a static meta string here:

```powershell
Write-AxiomUiTitle "AXIOM NOW" "operator-critical state"
```

Also replace each bare `Write-Host "Section name" -ForegroundColor DarkGreen`
that is NOT already going through `Write-AxiomUiSection` with a
`Write-AxiomUiSection` call. In `axiom-now` the section at line 349
("Next action") uses `Write-AxiomUiSection` — that is already correct.

### `58-operator-commands.ps1`

Replace the `Write-AxiomUiTitle "AXIOM OPERATOR COMMANDS"` call with:
```powershell
Write-AxiomUiTitle "OPERATOR COMMAND LEDGER" "append-only · hash-chained"
```

### `40-dashboard.ps1`

Lines 369–370:
```powershell
# Remove these two lines:
Write-Host "AXIOM DASHBOARD" -ForegroundColor Green
Write-Host "===============" -ForegroundColor Green
# Replace with:
Write-AxiomUiTitle "AXIOM DASHBOARD" "session:$($session.session_id)"
```

Note: `$session` is fetched before this line (line ~384 in the current
file). If the title is rendered before the session query, use
`"read-only · fail-closed"` as the static meta instead.

Each bare `Write-Host "Section name" -ForegroundColor DarkGreen` section
header (lines 396, 410, 429, 443, 463, 480, 500, 515) → replace with
`Write-AxiomUiSection "Section name"`.

### `41-readiness.ps1`

Lines 328–329:
```powershell
Write-Host "AXIOM EXECUTION READINESS" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "EXECUTION READINESS" "30+ checks · read-only"
```

The "Next safe commands:" section header (line 468) → replace with:
```powershell
Write-AxiomUiSection "Next safe commands"
```

### `44-queue.ps1`

Lines 294–295:
```powershell
Write-Host "AXIOM TASK QUEUE" -ForegroundColor Green
Write-Host "================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "TASK QUEUE" "manifest-bound · operator-dispatched"
```

Each bare `Write-Host "Section" -ForegroundColor DarkGreen` (Session,
Counts by status, Interpretation, Next safe commands) → replace with
`Write-AxiomUiSection`.

### `45-model.ps1`

Lines 286–287:
```powershell
Write-Host "AXIOM MODEL PROFILE / TRUST BOUNDARY" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "MODEL PROFILE / TRUST" "candidate registration"
```

Any bare `DarkGreen` section headers in the function body → replace with
`Write-AxiomUiSection`.

### `46-manifests.ps1`

Lines 321–322:
```powershell
Write-Host "AXIOM MANIFEST / TOOL-CAPABILITY INTEGRITY" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "MANIFEST INTEGRITY" "SHA256 · active manifests"
```

### `47-budget.ps1`

Lines 431–432:
```powershell
Write-Host "AXIOM BUDGET / RESOURCE USAGE" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "BUDGET / RESOURCE USAGE" "provider usage · read-only"
```

### `48-events.ps1`

Lines 364–365:
```powershell
Write-Host "AXIOM EVENTS" -ForegroundColor Green
Write-Host "============" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "LIVE EVENT STREAM" "session events · security events"
```

### `57-task.ps1`

Lines 459–460:
```powershell
Write-Host "AXIOM TASK DETAIL" -ForegroundColor Green
Write-Host "=================" -ForegroundColor Green
```
Replace with:
```powershell
Write-AxiomUiTitle "TASK DETAIL" "read-only · lifecycle + security"
```

---

## Step 3 — Add `Write-AxiomUiRule` between major data groups

In the panels that have multiple data groups (dashboard, queue, events),
add a `Write-AxiomUiRule` call between groups to match the `hr.soft`
dashed separators in the mockup. Use judgment — one rule between each
named section is enough. Do not add rules inside single-topic sections.

Example in `40-dashboard.ps1`: add `Write-AxiomUiRule` between
"Latest session" and "Supervisor / heartbeat", and between each subsequent
named section.

---

## Step 4 — Remove any orphaned `Write-Host "==="` lines

After the title replacements, scan each modified file for remaining bare
`Write-Host "===="` or `Write-Host "---"` separators that are now
redundant (since `Write-AxiomUiTitle` already renders the dim rule). Remove
them. Do not remove section separators that are part of table headers
(e.g. `----` column dividers in `axiom-queue`'s task table).

---

## What the result looks like

Before:
```
AXIOM DASHBOARD
===============
```

After:
```
▌ AXIOM DASHBOARD    session:42
  ──────────────────────────────────────────────────────────────────────
```

Before (section header):
```
Latest session
```

After:
```
  ▸ Latest session
```

---

## Verification

After implementation, load the terminal profile and run each affected
panel command to visually confirm the new structure renders without errors.
Then run `axiom-doctor` to confirm no module load failures.

```powershell
# Load profile (adjust path as needed)
$env:AXIOM_ROOT = "C:\axiom"
$env:AXIOM_STARTUP_BANNER = "0"
. "C:\axiom\ui\terminal\profile\profile-axiom.ps1"

# Run each affected panel
axiom-now
axiom-dashboard
axiom-readiness
axiom-queue
axiom-model
axiom-manifests
axiom-budget
axiom-events
axiom-operator-commands

# Health check
axiom-doctor
```

No pytest run required — terminal modules are not in the test suite.
Claude Code will visual-verify and run `axiom-doctor` before reporting
to Jeremy.

---

## Rollback

All changes are in `ui/terminal/modules/` only. If any panel breaks, the
rollback is `git checkout HEAD -- ui/terminal/modules/<file>.ps1` for the
affected file. No DB state, no manifest registration, no runtime effect.
