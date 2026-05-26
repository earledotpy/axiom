# AXIOM Terminal Changelog

Purpose: track AXIOM Terminal suite changes separately from AXIOM runtime implementation.

Boundary: this changelog describes terminal UI/operator-surface changes only. Runtime state changes, model trust, safe-pass, scheduler behavior, manifests, and task lifecycle changes belong in AXIOM runtime handoff/snapshot artifacts.

## Current Terminal Phase

AXIOM Terminal is being expanded as a read-mostly operator interface for implementation work.

Core boundary:

- Read-only visibility may live directly in terminal modules.
- Terminal documentation/changelog updates may write under `C:\axiom\ui\terminal\docs`.
- State-changing AXIOM runtime behavior must live in approved AXIOM runtime/tools first.
- Terminal modules must not bypass policy, audit, safe-pass, manifests, model trust, scheduler gates, or operator-control gates.

## Implemented Terminal Work

- T1: cleaned command surface and registry discipline baseline.
- T2: added `axiom-dashboard`.
- T3: added `axiom-readiness`.
- T4: added `axiom-registry`.
- T5: added visual-mode switching.
- T6: added `axiom-queue`.
- T7: added `axiom-model`.
- T8: added `axiom-manifests`.
- T9: added `axiom-budget`.
- T10: added `axiom-events`.
- T11: consolidated `axiom-doctor`.
- T12: added `axiom-terminal-report`.
- T13: added changelog/update-note discipline.

## Notes

Add new entries using:

```powershell
axiom-terminal-note "short note here"

## 2026-05-20T22:09:29-06:00 — T13

T13 added AXIOM Terminal changelog/update-note discipline. This writes only to terminal documentation and does not mutate AXIOM runtime state.

