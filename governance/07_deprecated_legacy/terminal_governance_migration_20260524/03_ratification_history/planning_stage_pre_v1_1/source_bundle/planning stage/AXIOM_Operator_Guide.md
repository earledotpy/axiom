# AXIOM — Operator Guide
## Complete Setup and First Session Workflow

**Document Type:** Operational Reference  
**Status:** Active  
**Version:** 1.0  
**Scope:** Project setup, initial AI engagement sequence, panel cycle workflow  

---

## Your Role as Operator

You are the physical abstraction layer. You:
- Copy prompts and paste them into each AI system
- Copy responses and bring them back to the next system in the flow
- Execute file operations, write code to disk, run tests
- Report results back to the panel

You do not make design decisions. You do not editorialize on responses. You deliver outputs between systems accurately and completely.

---

## Part 1 — One-Time Setup

### Step 1 — Create the AXIOM Claude Project

1. Open Claude (claude.ai)
2. Click **Projects** in the left sidebar
3. Click **Create Project**
4. Name it: `AXIOM`
5. Do not add anything else yet

### Step 2 — Add Project Instructions

1. Inside the AXIOM Project, find **Project Instructions** (or "Edit Instructions")
2. Paste the full contents of `AXIOM_Project_Instructions.md`
3. Save

### Step 3 — Upload Knowledge Base Documents

Upload in this order — order matters for RAG retrieval priority:

1. `AXIOM_Panel_Charter.md`
2. `AXIOM_Constraints_Register.md`
3. `AXIOM_Core_Values.md`
4. `AXIOM_Legacy_Reference.md`

### Step 4 — Prepare the Other Five AI Systems

For each system below, open a new conversation and upload the four documents listed. Do this before the first panel session begins.

**Documents to upload to every system:**
- `AXIOM_Panel_Charter.md`
- `AXIOM_Constraints_Register.md`
- `AXIOM_Core_Values.md`
- `AXIOM_Legacy_Reference.md`

Do **not** upload `AXIOM_Project_Instructions.md` to any system other than Claude.

**Systems to prepare:**

| System | Where to Open |
|---|---|
| GPT-5.5 | chatgpt.com — new conversation |
| Gemini 3.1 Pro | gemini.google.com — new conversation |
| DeepSeek V4 | chat.deepseek.com — new conversation |
| Qwen 3.6 Plus | chat.qwen.ai or qwenlm.github.io — new conversation |
| Kimi K2.6 | kimi.moonshot.cn — new conversation |

Keep each conversation open in its own browser tab. You will return to each one throughout the session.

---

## Part 2 — Initial Role Briefing for Each System

Before the first design question is asked, each system receives a role briefing. This is a one-time message sent after uploading the documents.

Send these verbatim. Do not paraphrase.

---

**GPT-5.5 — Chief Architect briefing:**

> You are the Chief Architect on the AXIOM design panel. The attached documents define the panel structure, hard constraints, core values, and legacy build history. Your role is to produce initial architecture proposals when design questions are raised. You do not make unilateral decisions — all proposals are reviewed by the full panel before acceptance. You break architectural deadlocks when the panel cannot reach consensus. When I say "Architect: [question or directive]", that is your cue to produce a proposal. Confirm you have read the documents and understand your role.

---

**Gemini 3.1 Pro — Research Arbiter briefing:**

> You are the Research and Knowledge Arbiter on the AXIOM design panel. The attached documents define the panel structure, hard constraints, core values, and legacy build history. Your role is to verify factual claims about external tools, libraries, APIs, and current technology state. You settle factual disputes between panel members. Your rulings on factual matters are binding unless contradicted by new evidence. When I say "Arbiter: [claim or dispute]", that is your cue to verify and rule. Confirm you have read the documents and understand your role.

---

**DeepSeek V4 — Adversarial Critic briefing:**

> You are the Adversarial Critic on the AXIOM design panel. The attached documents define the panel structure, hard constraints, core values, and legacy build history. Your role is to challenge every proposal brought to you. Find failure modes, edge cases, unstated assumptions, and security weaknesses. Your objections require supporting reasoning — bare assertions are not accepted. Your objections are overruled only if both the Research Arbiter and the Constraints Reviewer find them unsupported by evidence. When I say "Critic: [proposal]", that is your cue to challenge it. Confirm you have read the documents and understand your role.

---

**Qwen 3.6 Plus — Constraints Reviewer briefing:**

> You are the Constraints and Feasibility Reviewer on the AXIOM design panel. The attached documents define the panel structure, hard constraints, core values, and legacy build history. Your role is to evaluate every proposal against the physical hardware constraints and budget limits in the Constraints Register. Perform RAM accounting and API budget math. Flag proposals that cannot run on the target hardware. Your hardware feasibility rulings are binding and can only be overturned by full panel consensus with written rationale. When I say "Constraints: [proposal]", that is your cue to evaluate feasibility. Confirm you have read the documents and understand your role.

---

**Kimi K2.6 — Implementation Specialist briefing:**

> You are the Implementation Specialist on the AXIOM design panel. The attached documents define the panel structure, hard constraints, core values, and legacy build history. Your role is to translate approved designs into concrete, executable implementation plans — step-by-step specifications that a human operator can execute. You identify implementation-level gaps in approved designs. You do not override approved architectural decisions. You only produce implementation plans for proposals that have passed full panel review. When I say "Implement: [approved proposal]", that is your cue to produce an implementation plan. Confirm you have read the documents and understand your role.

---

Wait for each system to confirm before proceeding to the first panel session.

---

## Part 3 — First Panel Session

The first session produces the initial AXIOM architecture proposal. It runs one full panel cycle.

### Cycle Overview

```
Step 1: Architect proposes
Step 2: Evaluator checks coherence (Claude — in the AXIOM Project)
Step 3: Critic challenges (DeepSeek)
Step 4: Arbiter verifies facts (Gemini)
Step 5: Constraints reviews feasibility (Qwen)
Step 6: If approved — Architect revises if needed, then Specialist plans (Kimi)
Step 7: Save outputs to AXIOM knowledge base
```

---

### Step 1 — Architect Proposes

Go to GPT-5.5. Send:

> Architect: Produce the initial ground-up architecture proposal for AXIOM — an autonomous multi-agent AI system running on a Celeron N4500, 8GB RAM, Windows 11, no GPU, with a Telegram interface and free-tier API budget. Do not inherit the ToonTown architecture by default. Evaluate each component on its merits against the constraints and core values. Begin with the four highest-level decisions: agent hierarchy structure, coordination model, persistence layer, and execution model. Produce a structured proposal — not an essay.

Copy the full response. Save it as `AXIOM_Proposal_v1.md` on your machine.

---

### Step 2 — Evaluator Reviews (Claude — AXIOM Project)

Open the AXIOM Project in Claude. Start a new chat. Send:

> Evaluator role: Review the following architecture proposal from the Chief Architect. Check for logical consistency, internal coherence, and conflicts with the Core Values in the knowledge base. State what holds, what fails, and what must be resolved before this proposal can proceed.
>
> [Paste GPT-5.5 full response here]

Copy Claude's full evaluation. Save it as `AXIOM_Evaluation_v1.md`.

---

### Step 3 — Critic Challenges (DeepSeek)

Go to DeepSeek. Send:

> Critic: Challenge the following architecture proposal. Find failure modes, edge cases, security weaknesses, and unstated assumptions. Support each objection with reasoning.
>
> [Paste GPT-5.5 full response here]

Copy DeepSeek's full response. Save it as `AXIOM_Critique_v1.md`.

---

### Step 4 — Arbiter Verifies (Gemini)

Go to Gemini. Send:

> Arbiter: Verify the factual claims in the following architecture proposal. Check tool availability, library compatibility, API availability, and any technical claims that may have changed since training. Rule on each claim.
>
> [Paste GPT-5.5 full response here]

Copy Gemini's full response. Save it as `AXIOM_Arbiter_v1.md`.

---

### Step 5 — Constraints Reviews (Qwen)

Go to Qwen. Send:

> Constraints: Evaluate the following architecture proposal against the Constraints Register. Perform RAM accounting for all runtime components. Flag anything that cannot run on Celeron N4500, 8GB RAM, Windows 11 with no GPU. Approve or block with explicit reasoning.
>
> [Paste GPT-5.5 full response here]

Copy Qwen's full response. Save it as `AXIOM_Constraints_v1.md`.

---

### Step 6 — Synthesise and Resolve

Return to Claude AXIOM Project. Start a new chat. Send:

> Evaluator role: The full panel has reviewed the Architect's proposal. Below are the outputs from each panel member. Identify: (1) which objections are valid and must be resolved, (2) which objections are overruled and why, (3) what the Architect must revise before the proposal can be approved, (4) whether the proposal can proceed to implementation planning or must return to the Architect.
>
> EVALUATION:
> [Paste AXIOM_Evaluation_v1.md]
>
> CRITIQUE:
> [Paste AXIOM_Critique_v1.md]
>
> ARBITER RULING:
> [Paste AXIOM_Arbiter_v1.md]
>
> CONSTRAINTS RULING:
> [Paste AXIOM_Constraints_v1.md]

---

### If Revisions Are Required

Return to GPT-5.5. Send:

> Architect: The panel has reviewed your proposal. The following must be resolved before approval:
>
> [Paste Claude's synthesis — the list of required revisions only]
>
> Produce a revised proposal addressing these points.

Run the revised proposal through Steps 2–6 again. Repeat until Claude's synthesis concludes the proposal can proceed.

---

### Step 7 — If Approved: Implementation Plan

Go to Kimi. Send:

> Implement: The following architecture proposal has been approved by the AXIOM panel. Produce a concrete, step-by-step implementation plan the human operator can execute. Identify the first three implementation tasks in sequence. Flag any gaps in the approved design that need panel clarification before implementation can begin.
>
> [Paste the final approved proposal]

Copy Kimi's full response. Save it as `AXIOM_Implementation_v1.md`.

---

### Step 8 — Save Session Outputs to AXIOM Knowledge Base

At the end of every panel session, upload the session outputs to the AXIOM Project knowledge base in Claude:

- `AXIOM_Proposal_v[N].md` — the approved proposal from this session
- `AXIOM_Implementation_v[N].md` — the implementation plan from this session

Do not upload draft files, rejected proposals, or intermediate critique documents. Keep the knowledge base clean — approved outputs only.

---

## Part 4 — Subsequent Sessions

Every session after the first follows the same panel cycle. The opening prompt to Claude changes to orient Claude to where the build is.

**Opening prompt for follow-up sessions (Claude AXIOM Project):**

> Evaluator role. Current session: [brief description of what is being decided today]. The knowledge base contains the approved proposals and implementation plans from previous sessions. Review [specific document or question] and advise on next steps.

**Opening prompt for GPT-5.5 in follow-up sessions:**

> Architect: [Brief description of what was decided last session]. The current open question is [specific design question]. Produce a proposal.

All other systems receive the same pattern: role prefix, brief context, specific question.

---

## Part 5 — Keeping the Panel in Sync

Each AI system has its own conversation and no memory of other systems' conversations. You are the synchronisation layer.

**Rules for keeping the panel in sync:**

- Always paste the full relevant output when sending to a new system — never summarise
- When a proposal is revised, send the revised version to all reviewing systems, not just the one that flagged the issue
- When a factual ruling is made by Gemini, include it in subsequent prompts to all systems: "The Arbiter has ruled that [X]. This is binding."
- When a constraints ruling is made by Qwen, include it in subsequent prompts: "The Constraints Reviewer has ruled that [X]. This is binding."
- Binding rulings travel with the proposal through every subsequent step

---

## Part 6 — File Naming Convention

All session outputs follow this naming pattern:

`AXIOM_[Type]_v[SessionNumber].[ext]`

| Type | Description |
|---|---|
| Proposal | Architecture proposal from Architect |
| Evaluation | Coherence review from Evaluator |
| Critique | Adversarial challenge from Critic |
| Arbiter | Factual ruling from Arbiter |
| Constraints | Feasibility ruling from Constraints Reviewer |
| Synthesis | Combined panel review from Evaluator |
| Implementation | Execution plan from Implementation Specialist |
| Decision | Final approved decision record |

Session numbers increment per full panel cycle, not per conversation.

---

## Quick Reference — Panel Cue Words

| Cue | System | Action |
|---|---|---|
| `Architect: [directive]` | GPT-5.5 | Produce proposal |
| `Evaluator role: [proposal]` | Claude (AXIOM Project) | Review coherence |
| `Critic: [proposal]` | DeepSeek | Challenge proposal |
| `Arbiter: [claim]` | Gemini | Verify and rule |
| `Constraints: [proposal]` | Qwen | Feasibility check |
| `Implement: [approved proposal]` | Kimi | Produce implementation plan |

---

*AXIOM Operator Guide — Version 1.0 — May 2026*
