# ADR-0005: Retire Deprecated Legacy Tree

Status: Approved
Date: 2026-05-26
Operator: Jeremy

## Decision

AXIOM retires `governance/07_deprecated_legacy/` from the working tree.

Legacy governance evidence remains preserved under `governance/06_archives/` through the existing raw zip imports and the supplemental retirement archive created for legacy files that were not byte-identical to existing archive contents.

## Reason

The active governance source of truth is `governance/01_live_spine/`. Keeping a large unpacked deprecated legacy tree in the working tree created unnecessary ambiguity for humans and tools about which governance files are active.

Before deletion, archive coverage was checked by content hash. Most deprecated legacy files were already covered by existing archives or archive zip entries. The uncovered files were preserved in `governance/06_archives/deprecated_legacy_retirement_20260526/deprecated_legacy_uncovered_supplement_20260526.zip`.

## Impact

Future governance work should consult `governance/01_live_spine/` for current authority and `governance/06_archives/` for historical evidence. The retired `07_deprecated_legacy` path is no longer part of the repository working tree and must not be treated as an active or expected governance source.
