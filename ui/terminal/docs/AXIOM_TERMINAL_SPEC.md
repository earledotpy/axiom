# AXIOM Terminal v1.0 Specification

## Purpose

AXIOM Terminal is the operator-facing shell suite for implementing AXIOM. It provides a cohesive terminal appearance, terminal-native editing, and bounded helper commands for verification, auditing, testing, navigation, and report generation.

## Boundary

AXIOM Terminal is not AXIOM runtime. It does not run agents, dispatch autonomous tasks, enable safe-pass, promote model trust, call gateways, or bypass fail-closed conditions.

## Extension model

Add future features as numbered files in:

```text
C:\axiom\ui\terminal\modules
```

Naming convention:

```text
50-feature-name.ps1
```

The profile loads modules in lexical order.

## Appearance model

The appearance layer has two parts:

1. Windows Terminal profile/scheme/background settings.
2. PowerShell prompt, PSReadLine colors, ANSI banner, and AXIOM command affordances.

## Editor model

The terminal editor function prefers:

```text
micro → edit → nano → nvim → vim → Notepad fallback
```

Set an override:

```powershell
$env:AXIOM_EDITOR = 'micro'
```
