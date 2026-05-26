# AXIOM Terminal Editor

The default terminal editor target is `micro` because it behaves like a normal text editor while staying inside the terminal.

Install from AXIOM Terminal:

```powershell
axiom-install-editor
```

Or install directly:

```powershell
winget install -e --id zyedidia.micro
```

Set a different editor for the current shell:

```powershell
$env:AXIOM_EDITOR = 'nvim'
```

Use:

```powershell
axiom-edit axiom\core\scheduler.py
axiom-edit-config
axiom-edit-schema
```
