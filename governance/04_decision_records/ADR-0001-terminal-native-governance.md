# ADR-0001: Terminal-Native Governance Model

Status: Approved
Date: 2026-05-24
Operator: Jeremy

## Decision

AXIOM governance now uses a terminal-native active surface centered on `governance/01_live_spine/`, with CLI role adapters in `governance/02_cli_surfaces/` and advisory council packets in `governance/03_advisory_council/`.

## Reason

The previous governance structure was optimized for chat-application upload workflows. Active AXIOM development now happens through terminal CLIs, so the live governance set should be smaller, clearer, and easier for local agents to read before acting.

## Impact

Legacy chat-era governance files are preserved under `governance/07_deprecated_legacy/`. Historical archives remain preserved under `governance/06_archives/`. Active governance decisions should be recorded as ADR files and reflected in the live spine.
