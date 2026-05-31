param(
    [Parameter(Mandatory)][ValidateSet("codex","antigravity","claude")][string]$To,
    [string]$From = "claude",
    [Parameter(Mandatory)][string]$Subject,
    [string]$Body = "",
    [string]$Type = "ai-prompt",
    [string]$ConversationId = ""
)

$inbox     = "C:\axiom\ipc\to_$To.md"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$entry = @"

---
FROM: $From
TO: $To
TIME: $timestamp
SUBJECT: $Subject

$Body
"@

# Named mutex per inbox — one per agent, OS-managed, auto-releases on crash.
# Mirrors Axiom's per-task one-running invariant: only one writer at a time.
$mutex = [System.Threading.Mutex]::new($false, "Global\AxiomIPC_$To")
try {
    $null = $mutex.WaitOne(5000)
    Add-Content -Path $inbox -Value $entry -Encoding UTF8
    # Index in SQLite — both writes inside the mutex so they're atomic together
    & python "C:\axiom\ipc\ipc_db.py" write `
        --from            $From `
        --to              $To `
        --subject         $Subject `
        --time            $timestamp `
        --body            $Body `
        --type            $Type `
        --conversation-id $ConversationId 2>$null | Out-Null
} finally {
    try { $mutex.ReleaseMutex() } catch {}
    $mutex.Dispose()
}

& "$PSScriptRoot\notify.ps1" -Title "IPC > $To" -Message $Subject
Write-Host "[ipc] sent to ${To}: $Subject"
