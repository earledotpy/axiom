# ipc/_posture_runspace.ps1
# Posture cache refresher — dot-sourced inside ipc_service.ps1 runspace.
# Extracted from posture_daemon.ps1; no PID file (lifecycle managed by ipc_service).

$cacheFile = "C:\axiom\ipc\posture_cache.json"
$logFile   = "C:\axiom\ipc\posture_daemon.log"

$python = @'
from axiom.security.autonomous_gate_panel import get_autonomous_gate_status
import json, sys, datetime

try:
    data = get_autonomous_gate_status()
    result = data.to_dict()
    result['_timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e), '_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
'@

function Log-Message {
    param([string]$Msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
}

function Refresh-PostureCache {
    try {
        $output = $python | python -c $python 2>$null
        if ([string]::IsNullOrWhiteSpace($output)) {
            Log-Message "ERROR: empty output from posture check"
            return
        }
        $parsed = $output | ConvertFrom-Json
        if (-not $parsed) {
            Log-Message "ERROR: invalid JSON from posture check"
            return
        }
        # Atomic write: temp → move
        $tmp = "$cacheFile.tmp"
        $output | Out-File -FilePath $tmp -Force -Encoding UTF8
        Move-Item -Path $tmp -Destination $cacheFile -Force -ErrorAction Stop
        Log-Message "Cache updated ($((($parsed.steps | Measure-Object).Count)) steps)"
    } catch {
        Log-Message "ERROR during cache refresh: $_"
    }
}

Log-Message "Posture runspace started — refresh interval: 10s"

while ($true) {
    try { Refresh-PostureCache } catch { Log-Message "ERROR in refresh loop: $_" }
    Start-Sleep -Seconds 10
}
