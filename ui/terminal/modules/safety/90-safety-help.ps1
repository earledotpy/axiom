# ============================================================
# AXIOM Terminal Help / Safety / Command Surface
# File: C:\axiom\ui\terminal\modules\90-safety-help.ps1
#
# Purpose:
#   Present a clean primary command surface for AXIOM Terminal.
#
# Boundary:
#   This module must remain non-mutating except for terminal UI/help.
#   It must not enable autonomous execution, safe-pass, model-profile
#   promotion, scheduler execution, gateway calls, sandbox execution,
#   Telegram, automatic agent control, or scheduler-agent behavior.
# ============================================================

if (-not $script:AxiomRoot) {
    $script:AxiomRoot = "C:\axiom"
}

function axiom-help {
    Write-Host ""
    Write-Host "AXIOM TERMINAL" -ForegroundColor Green
    Write-Host "==============" -ForegroundColor Green
    Write-Host ""
    Write-Host "First stop" -ForegroundColor DarkGreen
    Write-Host "  axiom-now                Compact operator-critical state"
    Write-Host "  axiom-preflight          Verify runtime state"
    Write-Host "  axiom-agent-audit        Verify Phase 5 agent boundary"
    Write-Host "  axiom-dashboard          More state detail"
    Write-Host ""
    Write-Host "Inspect" -ForegroundColor DarkGreen
    Write-Host "  axiom-readiness          Readiness checks"
    Write-Host "  axiom-queue              Task queue"
    Write-Host "  axiom-manifests          Manifest and role integrity"
    Write-Host "  axiom-events             Recent events"
    Write-Host "  axiom-operator-commands  Operator command intent ledger"
    Write-Host "  axiom-telegram-gateway   Telegram gateway boundary state"
    Write-Host "  axiom-phase7             Phase 7 acceptance/E2E gate panel"
    Write-Host "  axiom-task-latest        Latest task detail"
    Write-Host ""
    Write-Host "Navigate" -ForegroundColor DarkGreen
    Write-Host "  axiom-docs               Indexed docs/files"
    Write-Host "  axiom-docs agent         Phase 5 agent docs/files"
    Write-Host "  axiom-doc phase8a-release-freeze  Phase 8A docs-only reconciliation"
    Write-Host "  axiom-doc phase9-closeout  Phase 9 bounded manual_noop scheduler-to-executor closeout audit"
    Write-Host "  ae <path>                Edit a file"
    Write-Host "  axiom-find <pattern>     Search project text"
    Write-Host ""
    Write-Host "Boundaries" -ForegroundColor DarkGreen
    Write-Host "  axiom-guard              Active safety boundaries"
    Write-Host "  axiom-system-map         Runtime/tool/UI map"
    Write-Host ""
    Write-Host "More" -ForegroundColor DarkGreen
    Write-Host "  axiom-help-all           Full command catalog"
    Write-Host "  axiom-terminal-test      Terminal UI regression"
    Write-Host "  axiom-registry           Command registry audit"
    Write-Host ""
}

function axiom-help-all {
    Write-Host ""
    Write-Host "AXIOM TERMINAL COMMANDS" -ForegroundColor Green
    Write-Host "=======================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Core" -ForegroundColor DarkGreen
    Write-Host "  axiom                    Enter C:\axiom and activate venv"
    Write-Host "  axiom-help               Show this command surface"
    Write-Host "  axiom-help-all           Show full command catalog"
    Write-Host "  axiom-now                Compact operator-critical state"
    Write-Host "  axiom-doctor             Full AXIOM Terminal environment/self-audit"
    Write-Host "  axiom-registry           Audit terminal command registry coherence"
    Write-Host "  axiom-guard              Show active safety boundaries"
    Write-Host ""

    Write-Host "Editing" -ForegroundColor DarkGreen
    Write-Host "  axiom-edit <path>        Open file in terminal editor"
    Write-Host "  ae <path>                Short alias for axiom-edit"
    Write-Host "  axiom-find <pattern>     Search AXIOM project text"
    Write-Host ""

    Write-Host "Docs / navigation" -ForegroundColor DarkGreen
    Write-Host "  axiom-docs               Show indexed AXIOM docs and key files"
    Write-Host "  axiom-doc <name>         Open indexed doc/file in terminal editor"
    Write-Host "  axiom-doc-path <name>    Print indexed doc/file path"
    Write-Host "  axiom-doc phase8a-release-freeze  Open Phase 8A docs-only reconciliation file"
    Write-Host ""

    Write-Host "Verification" -ForegroundColor DarkGreen
    Write-Host "  axiom-preflight          Foundation + lifecycle audit + execution audit + supervisor health"
    Write-Host "  axiom-status             Foundation verification only"
    Write-Host "  axiom-audit              Lifecycle and execution audits"
    Write-Host "  axiom-policy-audit       Policy/security audit"
    Write-Host "  axiom-agent-audit        Phase 5 agent boundary audit"
    Write-Host "  axiom-operator-command-audit Phase 6 operator command ledger audit"
    Write-Host "  axiom-telegram-gateway-audit Phase 6G Telegram gateway boundary audit"
    Write-Host "  axiom-phase6-audit      Phase 6I closeout and hardening audit"
    Write-Host "  axiom-phase7-inventory  Phase 7A v1.13 acceptance inventory audit"
    Write-Host "  axiom-phase7-acceptance Phase 7B acceptance runner/prerequisite gate"
    Write-Host "  axiom-phase7-e2e-gate Phase 7C full-goal E2E gate audit"
    Write-Host "  axiom-phase7-closeout Phase 7E closeout and hardening audit"
    Write-Host "  axiom-phase9-closeout Phase 9 closeout audit"
    Write-Host "  axiom-health             Supervisor health for latest session"
    Write-Host "  axiom-regression         Full pytest regression: pytest tests -v"
    Write-Host "  axiom-test <args>        Targeted pytest wrapper"
    Write-Host ""
    Write-Host "Architecture maps" -ForegroundColor DarkGreen
    Write-Host "  axiom-system-map         Show AXIOM runtime/tool/UI boundary map"
    Write-Host "  axiom-boundaries         Show terminal/runtime safety boundaries"
    Write-Host "  axiom-runtime-map        Show runtime component map"
    Write-Host "  axiom-terminal-map       Show terminal suite component map"
    Write-Host ""

    Write-Host "State visibility" -ForegroundColor DarkGreen
    Write-Host "  axiom-session            Latest session id / summary"
    Write-Host "  axiom-dashboard          Read-only AXIOM status panel"
    Write-Host "  axiom-readiness          Read-only execution readiness report"
    Write-Host "  axiom-queue              Read-only task queue summary"
    Write-Host "  axiom-model              Read-only model profile status"
    Write-Host "  axiom-manifests          Read-only manifest/tool-capability integrity status"
    Write-Host "  axiom-budget             Read-only provider/resource usage summary"
    Write-Host "  axiom-events             Read-only recent session/security events"
    Write-Host "  axiom-operator-commands  Read-only operator command intent ledger"
    Write-Host "  axiom-telegram-gateway   Read-only Telegram gateway boundary state"
    Write-Host "  axiom-phase7             Read-only Phase 7 acceptance/E2E gate panel"
    Write-Host "  axiom-watch              Refresh read-only AXIOM panels"
    Write-Host "  axiom-watch-once         Show one read-only watch panel refresh"
    Write-Host "  axiom-task <task_id>     Read-only task detail viewer"
    Write-Host "  axiom-task-latest        Show latest task detail"
    Write-Host ""

    Write-Host "Reports" -ForegroundColor DarkGreen
    Write-Host "  axiom-handoff            Generate snapshot, handoff, and bundle"
    Write-Host "  axiom-logs               Show recent AXIOM logs"
    Write-Host "  axiom-terminal-report    Summarize AXIOM Terminal suite state"
    Write-Host "  axiom-terminal-changelog Show AXIOM Terminal changelog"
    Write-Host "  axiom-terminal-note      Append terminal changelog note"
    Write-Host "  axiom-terminal-test      Run AXIOM Terminal suite regression check"
    Write-Host "  axiom-archive-logs       Archive older log files into logs\archive"
    Write-Host ""

    Write-Host "Phase 5 manual/test-only surface" -ForegroundColor DarkGreen
    Write-Host "  axiom-docs agent         Show indexed Phase 5 agent files/docs"
    Write-Host "  axiom-manifests          Verify active role manifests and hashes"
    Write-Host "  axiom-agent-audit        Verify no Phase 5 runtime-call boundary drift"
    Write-Host "  axiom-task-latest        Inspect latest manual agent smoke task"
    Write-Host "  tools\run_manual_agent_foundation_smoke.py is available as an explicit tool, not a shortcut"
    Write-Host ""

    Write-Host "Terminal UI" -ForegroundColor DarkGreen

    Write-Host "  axiom-visual-mode        Show active visual configuration"
    Write-Host "  axiom-visual-native      Use compact native prompt"
    Write-Host "  axiom-visual-dashboard   Use Oh My Posh dashboard prompt"
    Write-Host "  axiom-banner-on          Enable startup status panel"
    Write-Host "  axiom-banner-off         Disable startup status panel"
    Write-Host "  axiom-visual-reset       Reset AXIOM Terminal visual config"
    Write-Host "  axiom-visual             Reprint startup panel"
    Write-Host "  axiom-theme              Show terminal theme guidance/status"
    Write-Host "  axiom-posh-on            Enable Oh My Posh dashboard prompt"
    Write-Host "  axiom-posh-off           Disable Oh My Posh dashboard prompt for session"
    Write-Host "  axiom-posh-test          Diagnose Oh My Posh theme loading"
    Write-Host "  axiom-watch-help         Show watch usage and modes"
    Write-Host ""

    Write-Host "Compatibility aliases still accepted but de-emphasized" -ForegroundColor Yellow
    Write-Host "  axiom-home               Alias-compatible with axiom"
    Write-Host "  axiom-open <path>        Compatibility alias for axiom-edit"
    Write-Host "  np <path>                Legacy editor shortcut; prefer ae"
    Write-Host "  axiom-snapshot           Advanced; axiom-handoff already runs this"
    Write-Host ""

    Write-Host "Do not add direct terminal shortcuts for:" -ForegroundColor Red
    Write-Host "  autonomous operation, safe-pass enablement, model promotion,"
    Write-Host "  real model/cloud calls, real network fetches, sandbox execution,"
    Write-Host "  Telegram/operator control plane, automatic agent control, or automatic scheduler execution."
    Write-Host "  Phase 8A runtime capability, Telegram polling startup, or autonomy enablement."
    Write-Host ""
}

function axiom-guard {
    Write-Host ""
    Write-Host "AXIOM ACTIVE BOUNDARIES" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Current posture:" -ForegroundColor DarkGreen
    Write-Host "  mode: fail_closed_non_autonomous"
    Write-Host "  autonomous operation: blocked by design"
    Write-Host "  safe-pass: bounded Phase 7 readiness may be present; not autonomous authority"
    Write-Host "  current trusted model profile: absent by design"
    Write-Host ""
    Write-Host "Allowed from AXIOM Terminal:" -ForegroundColor DarkGreen
    Write-Host "  - navigation and venv activation"
    Write-Host "  - terminal-native file editing"
    Write-Host "  - read-only project inspection"
    Write-Host "  - read-only SQLite queries"
    Write-Host "  - test execution"
    Write-Host "  - foundation verification"
    Write-Host "  - lifecycle audit"
    Write-Host "  - execution audit"
    Write-Host "  - policy/security audit"
    Write-Host "  - supervisor health"
    Write-Host "  - Phase 5 agent boundary audit"
    Write-Host "  - Phase 6 operator command ledger audit"
    Write-Host "  - Phase 6G Telegram gateway boundary audit"
    Write-Host "  - Phase 6H Telegram gateway read-only state visibility"
    Write-Host "  - Phase 7A acceptance inventory audit"
    Write-Host "  - Phase 7B acceptance runner/prerequisite reporting"
    Write-Host "  - Phase 7C full-goal E2E gate audit"
    Write-Host "  - Phase 7D terminal acceptance/E2E gate visibility"
    Write-Host "  - Phase 7E closeout and hardening audit"
    Write-Host "  - Phase 8A documentation/reconciliation file navigation"
    Write-Host "  - Phase 9 bounded manual_noop scheduler-to-executor closeout audit"
    Write-Host "  - snapshot/handoff generation"
    Write-Host "  - terminal visual/theme management"
    Write-Host "  - Phase 5 manual/test-only agent docs and file visibility"
    Write-Host ""
    Write-Host "Not allowed as direct terminal shortcuts:" -ForegroundColor Yellow
    Write-Host "  - autonomous operation"
    Write-Host "  - safe-pass enablement"
    Write-Host "  - model profile promotion"
    Write-Host "  - real model/cloud calls"
    Write-Host "  - real network fetches"
    Write-Host "  - sandbox process execution"
    Write-Host "  - Telegram/operator control plane"
    Write-Host "  - Telegram envelope processing or confirmation"
    Write-Host "  - automatic agent control"
    Write-Host "  - scheduler-to-agent integration"
    Write-Host "  - general scheduler-to-executor automation beyond bounded manual_noop"
    Write-Host ""
    Write-Host "Rule:" -ForegroundColor DarkGreen
    Write-Host "  Read-only visibility may live in terminal modules."
    Write-Host "  State-changing behavior must live in approved AXIOM tools/runtime first."
    Write-Host ""
}

function axiom-theme {
    Write-Host ""
    Write-Host "AXIOM TERMINAL THEME" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Windows Terminal profile/settings:"
    Write-Host "  C:\axiom\ui\terminal\terminal"
    Write-Host ""
    Write-Host "Assets:"
    Write-Host "  C:\axiom\ui\terminal\assets"
    Write-Host ""
    Write-Host "Oh My Posh themes:"
    Write-Host "  C:\axiom\ui\terminal\themes"
    Write-Host ""
    Write-Host "Recommended font:"
    Write-Host "  0xProto Nerd Font Mono or Cascadia Mono PL"
    Write-Host ""
    Write-Host "Prompt modes:"
    Write-Host "  axiom-posh-on       dashboard prompt"
    Write-Host "  axiom-posh-off      native compact prompt for session"
    Write-Host ""
}

function axiom-command-surface {
    axiom-help
}
