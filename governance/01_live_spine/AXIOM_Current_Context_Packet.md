# AXIOM Current Context Packet

Status: Active
Owner: Jeremy, Operator
Effective date: 2026-05-28

## Current Operating Context

AXIOM has moved from chat-application governance files for ChatGPT, Claude, and Gemini into a terminal-native governance model for Codex, Claude Code, and Antigravity. All three CLIs operate against the live AXIOM worktree in a unified Windows Terminal workspace.

Active development follows the Staged Implementation-Review Loop (ADR-0006): Antigravity plans, Codex implements, Claude Code verifies. Jeremy approves at each handoff.

## Current Panel Assignments

- Jeremy: Operator and final authority.
- Codex / GPT-5.5: Implementation Specialist and Troubleshooter.
- Claude Code / Claude: Governance Auditor and Specification Critic.
- Antigravity / Gemini 3.5: Chief Architect and Researcher.
- Kimi, Qwen, DeepSeek: External advisory council, accessed through new online chats.

## Active Development Workflow (ADR-0006)

For non-trivial implementation tasks, the panel follows this loop:

1. **Antigravity** reads the live worktree and produces a written task plan. The plan is the handoff artifact to Codex. Antigravity does not write implementation code.
2. **Codex** receives the plan, implements the changes, and runs local verification.
3. **Claude Code** reviews Codex's uncommitted diff, runs `pytest`, and reports findings to Jeremy.
4. **Jeremy** approves the change before it is accepted.

Jeremy may direct a shorter path (Codex directly) for narrow or well-specified tasks.

## Active Priorities

- Preserve AXIOM's fail-closed, non-autonomous safety posture.
- Follow the Staged Implementation-Review Loop for implementation work.
- Keep legacy governance material preserved in archives but out of the active path.
- Give each AI system enough context to make role-appropriate judgement calls.
- Make advisory council packets complete enough for a fresh chat with no previous context.

## Default Review Questions

When reviewing an AXIOM proposal, answer:

- What decision is being requested?
- Does it affect active bindings, runtime authority, architecture, implementation, or documentation only?
- What are the risks if accepted?
- What evidence is missing?
- Which panel role should own the next step?
- Should the proposal become binding, remain advisory, or be deferred?
