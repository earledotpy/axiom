# ============================================================
# AXIOM Persistent Autonomous Posture Daemon
# File: C:\axiom\ipc\posture_daemon.ps1
#
# Purpose:
#   Background service that refreshes 7-step autonomous gate
#   status every 10 seconds and caches it to disk.
#   Enables fast non-blocking reads by dashboard panels.
#
# Lifecycle:
#   - Start once during system bootstrap
#   - Runs indefinitely until killed
#   - PID stored at C:\axiom\ipc\posture_daemon.pid
#   - Cache file: C:\axiom\ipc\posture_cache.json
# ============================================================

$cacheFile = "C:\axiom\ipc\posture_cache.json"
$pidFile = "C:\axiom\ipc\posture_daemon.pid"
$logFile = "C:\axiom\ipc\posture_daemon.log"

function Log-Message {
    param([string]$Msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Msg"
    Write-Host $logLine
    Add-Content -Path $logFile -Value $logLine -ErrorAction SilentlyContinue
}

function Refresh-PostureCache {
    try {
        $python = @'
from axiom.security.autonomous_gate_panel import get_autonomous_gate_status
import json
import sys

try:
    data = get_autonomous_gate_status()
    result = data.to_dict()
    result['_timestamp'] = __import__('datetime').datetime.now(
        __import__('datetime').timezone.utc
    ).isoformat()
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({
        'error': str(e),
        '_timestamp': __import__('datetime').datetime.now(
            __import__('datetime').timezone.utc
        ).isoformat()
    }, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
'@

        $output = $python | python -c $python 2>$null

        if ([string]::IsNullOrWhiteSpace($output)) {
            Log-Message "ERROR: Empty output from posture check"
            return
        }

        # Validate JSON before writing
        $parsed = $output | ConvertFrom-Json
        if (-not $parsed) {
            Log-Message "ERROR: Invalid JSON from posture check"
            return
        }

        # Atomic write: temp file -> move
        $tempFile = "$cacheFile.tmp"
        $output | Out-File -FilePath $tempFile -Force -Encoding UTF8

        Move-Item -Path $tempFile -Destination $cacheFile -Force -ErrorAction Stop

        Log-Message "Cache updated ($(($parsed.steps | Measure-Object).Count) steps)"
    }
    catch {
        Log-Message "ERROR during cache refresh: $_"
    }
}

function Start-PostureDaemon {
    Log-Message "Posture daemon starting (PID: $PID)"
    $PID | Out-File -FilePath $pidFile -Force

    Log-Message "Cache file: $cacheFile"
    Log-Message "Refresh interval: 10 seconds"

    $refreshCount = 0

    while ($true) {
        try {
            $refreshCount++
            Refresh-PostureCache
        }
        catch {
            Log-Message "ERROR in refresh loop: $_"
        }

        Start-Sleep -Seconds 10
    }
}

# Entry point
Start-PostureDaemon
