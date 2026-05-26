# Recommended AXIOM Terminal Applications

Core:

```powershell
winget install -e --id Microsoft.PowerShell
winget install -e --id Microsoft.WindowsTerminal
winget install -e --id Git.Git
winget install -e --id zyedidia.micro
```

Optional:

```powershell
winget install -e --id JanDeDobbeleer.OhMyPosh
winget install -e --id Microsoft.VisualStudioCode
```

Recommended role split:

- Windows Terminal: visual shell host.
- PowerShell 7: operator shell.
- micro: terminal-native edits.
- Git: source-control inspection and diffs.
- Oh My Posh: optional prompt renderer if you want richer glyphs.
- VS Code: optional fallback for larger edits; not required for terminal-first work.
