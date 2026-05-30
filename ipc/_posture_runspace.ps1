# _posture_runspace.ps1 — Posture cache refresher (runs as a runspace inside ipc_service.ps1)
# Polls the 7-step autonomous gate every 10s and writes posture_cache.json.

$cacheFile = "C:\axiom\ipc\posture_cache.json"
$logFile   = "C:\axiom\ipc\posture_daemon.log"

function Write-PostureLog {
    param([string]$Msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
}

$pythonScript = @'
from axiom.security.autonomous_gate_panel import get_autonomous_gate_status
import json, sys
from datetime import datetime, timezone
try:
    data = get_autonomous_gate_status()
    result = data.to_dict()
    result['_timestamp'] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e), '_timestamp': datetime.now(timezone.utc).isoformat()}), file=sys.stderr)
    sys.exit(1)
'@

Write-PostureLog "Posture runspace started"

$refreshCount = 0
while ($true) {
    try {
        $refreshCount++
        $output = $pythonScript | python -c $pythonScript 2>$null
        if (-not [string]::IsNullOrWhiteSpace($output)) {
            $parsed = $output | ConvertFrom-Json -ErrorAction Stop
            $tempFile = "$cacheFile.tmp"
            $output | Out-File -FilePath $tempFile -Force -Encoding UTF8
            Move-Item -Path $tempFile -Destination $cacheFile -Force -ErrorAction Stop
            if ($refreshCount % 6 -eq 0) {
                Write-PostureLog "Cache updated (refresh #$refreshCount)"
            }
        }
    } catch {
        Write-PostureLog "ERROR in posture refresh: $_"
    }
    Start-Sleep -Seconds 10
}
