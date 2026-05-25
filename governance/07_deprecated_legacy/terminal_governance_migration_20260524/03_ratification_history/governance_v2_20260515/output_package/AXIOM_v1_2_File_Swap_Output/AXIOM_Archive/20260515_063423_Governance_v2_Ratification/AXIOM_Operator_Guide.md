# AXIOM — Operator Guide
## Setup, Workflow, and Cross-Chat Continuity

**Document Type:** Operational Reference
**Status:** Active operational guidance under Charter v1.1
**Version:** 1.1
**Supersedes:** v1.0 (May 2026)
**Scope:** Project setup, panel cycle workflow, delta cycles, chat handoffs, knowledge base hygiene
**Authority Note:** This file derives from the ratified governance baseline. It is not Charter-level ratified content and does not supersede the Charter, Core Values, Constraints Register, Active Bindings, Synthesis documents, or Specification Debt ledger.

---

## What changed in v1.1

v1.0 described a clean linear panel cycle and assumed each panel session would end before chat context exhaustion. Practice showed this assumption was wrong by v1.7. v1.1 adds:

- **Delta-confirmation cycle workflow** (skipping non-affected reviewers when authorized)
- **Synthesis as an explicit named step** (it was happening on every cycle but wasn't in v1.0)
- **Chat-exhaustion handoff procedure** (full file lists, not "brief description")
- **Active Bindings document** maintained in the knowledge base
- **Knowledge base hygiene rules** for what to keep and what to retire
- **Cross-cutting artifact production workflow** (calibration test sets, validation corpora)

---

## Your Role as Operator

You are the physical abstraction layer. You:
- Copy prompts and paste them into each AI system
- Copy responses and bring them back to the next system in the flow
- Execute file operations, write code to disk, run tests
- Report results back to the panel
- **Maintain the knowledge base** — including retiring superseded documents and tracking active bindings

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

1. Inside the AXIOM Project, find **Project Instructions**
2. Paste the full contents of `AXIOM_Project_Instructions.md`
3. Save

### Step 3 — Upload Knowledge Base Documents

Upload in this order — order matters for RAG retrieval priority:

1. `AXIOM_Panel_Charter.md`
2. `AXIOM_Constraints_Register.md`
3. `AXIOM_Core_Values.md`
4. `AXIOM_Legacy_Reference.md`
5. `AXIOM_Active_Bindings.md` (new — see §Active Bindings)

### Step 4 — Prepare the Other Five AI Systems

For each system below, open a new conversation and upload the four documents listed. Do this before the first panel session begins.

**Documents to upload to every system:**
- `AXIOM_Panel_Charter.md`
- `AXIOM_Constraints_Register.md`
- `AXIOM_Core_Values.md`
- `AXIOM_Legacy_Reference.md`
- `AXIOM_Active_Bindings.md`

Do **not** upload `AXIOM_Project_Instructions.md` to any system other than Claude.

**Systems to prepare:**

| System | Where to Open |
|---|---|
| GPT-5.5 | chatgpt.com — new conversation |
| Gemini 3.1 Pro | gemini.google.com — new conversation |
| DeepSeek V4 | chat.deepseek.com — new conversation |
| Qwen 3.6 Plus | chat.qwen.ai or qwenlm.github.io — new conversation |
| Kimi K2.6 | kimi.moonshot.cn — new conversation |

Keep each conversation open in its own browser tab.

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

**Important:** Role briefings are one-shot per chat. Every time you open a new conversation with a panel member (because the prior chat hit context limits), you must re-send the briefing.

---

## Part 3 — Active Bindings (NEW IN v1.1)

Maintain a single document in the knowledge base named `AXIOM_Active_Bindings.md`. This document tracks every Arbiter ruling and every Constraints binding condition currently in force.

**Format:**

```markdown
# AXIOM Active Bindings

## Arbiter Bindings (Factual)
| ID | Source Cycle | Ruling | Status |
|---|---|---|---|
| AB-001 | v1.2 | subprocess.Popen does not isolate network on Windows | Active |
| AB-002 | v1.11 | qwen3:4b thinking-mode inferred via /api/show parameters field only | Active |
| ... | ... | ... | ... |

## Constraints Bindings (Feasibility)
| ID | Source Cycle | Condition | Status |
|---|---|---|---|
| CB-001 | v1.7 | Sequential execution; max 4 threads | Active |
| CB-002 | v1.7 | qwen3:4b Q4 mmap | Active |
| ... | ... | ... | ... |
```

**When to update:** Every time a new Arbiter ruling is filed or a new Qwen binding condition is issued. Add it. Never delete; mark as `Superseded by [ID]` if a later ruling overrides.

**When to upload:** Every fresh chat with any panel member. The bindings travel with the proposal — see Charter §Binding Rulings Travel Forward.

This document now exists as `AXIOM_Active_Bindings.md`, an alias to the latest versioned active-bindings file. Upload it with every fresh panel chat.

---

## Part 4 — The Full Panel Cycle

### Cycle Overview

```
Step 1: Architect proposes               (GPT-5.5)
Step 2: Evaluator checks coherence       (Claude)
Step 3: Critic challenges                (DeepSeek)
Step 4: Arbiter verifies facts           (Gemini)
Step 5: Constraints reviews feasibility  (Qwen)
Step 6: Evaluator synthesizes panel output  ← NAMED IN v1.1
Step 7: If approved — Specialist plans   (Kimi)
Step 8: Evaluator delta-confirms plan    (Claude)
Step 9: Save outputs to knowledge base
```

(Steps 1–5 are unchanged from v1.0. Step 6 is now an explicit named deliverable. Step 8 is new.)

### Step 1 — Architect Proposes

Send to GPT-5.5:

> Architect: [Specific design directive or revision instructions]. Active bindings travel forward — see uploaded `AXIOM_Active_Bindings.md`. Produce a structured proposal — not an essay.

Save response as `AXIOM_Proposal_v[N].md`.

### Step 2 — Evaluator Reviews (Claude — AXIOM Project)

> Evaluator role: Review the following architecture proposal from the Chief Architect. Check for logical consistency, internal coherence, and conflicts with the Core Values in the knowledge base. State what holds, what fails, and what must be resolved before this proposal can proceed.
>
> [Paste GPT-5.5 full response here]

Save as `AXIOM_Evaluation_v[N].md`.

### Step 3 — Critic Challenges (DeepSeek)

> Critic: Challenge the following architecture proposal. Find failure modes, edge cases, security weaknesses, and unstated assumptions. Support each objection with reasoning.
>
> [Paste GPT-5.5 full response]

Save as `AXIOM_Critique_v[N].md`.

### Step 4 — Arbiter Verifies (Gemini)

> Arbiter: Verify the factual claims in the following architecture proposal. Check tool availability, library compatibility, API availability, and any technical claims that may have changed since training. Rule on each claim.
>
> [Paste GPT-5.5 full response]

Save as `AXIOM_Arbiter_v[N].md`. **If any new factual ruling is issued, add it to `AXIOM_Active_Bindings.md` immediately.**

### Step 5 — Constraints Reviews (Qwen)

> Constraints: Evaluate the following architecture proposal against the Constraints Register and active bindings. Perform RAM accounting for all runtime components. Flag anything that cannot run on Celeron N4500, 8GB RAM, Windows 11 with no GPU. Approve or block with explicit reasoning. Issue any new binding conditions explicitly.
>
> [Paste GPT-5.5 full response]

Save as `AXIOM_Constraints_v[N].md`. **If any new binding condition is issued, add it to `AXIOM_Active_Bindings.md` immediately.**

### Step 6 — Synthesis (Claude — AXIOM Project, new chat) — NAMED IN v1.1

> Evaluator role: The full panel has reviewed the Architect's proposal. Below are the outputs from each panel member. Identify: (1) which objections are valid and must be resolved, (2) which objections are overruled and why, (3) what the Architect must revise before the proposal can be approved, (4) whether the proposal can proceed to implementation planning or must return to the Architect. (5) Whether the next cycle qualifies as a delta-confirmation cycle per Charter §Delta-Confirmation Cycle, and if so, which roles are skippable.
>
> EVALUATION:
> [Paste AXIOM_Evaluation_v[N].md]
>
> CRITIQUE:
> [Paste AXIOM_Critique_v[N].md]
>
> ARBITER RULING:
> [Paste AXIOM_Arbiter_v[N].md]
>
> CONSTRAINTS RULING:
> [Paste AXIOM_Constraints_v[N].md]

Save as `AXIOM_Synthesis_v[N].md`.

### If Revisions Are Required

Send back to Architect (same chat if context permits, new chat per §Chat Handoff if not):

> Architect: The panel has reviewed your proposal. The following must be resolved before approval:
>
> [Paste the synthesis revision list — items only, not full synthesis]
>
> Produce a revised proposal addressing these points.

Run the revised proposal through Steps 2–6 again — **but per the synthesis declaration, some steps may be skippable as a delta cycle.** See §Part 5.

### Step 7 — If Approved: Implementation Plan

> Implement: The following architecture proposal has been approved by the AXIOM panel. Active bindings travel forward — see uploaded `AXIOM_Active_Bindings.md`. Produce a concrete, step-by-step implementation plan the human operator can execute. Identify the first three implementation tasks in sequence. Flag any gaps in the approved design that need panel clarification before implementation can begin.
>
> [Paste the final approved proposal stack]

Save as `AXIOM_Implementation_v[N].md`.

### Step 8 — Evaluator Delta-Confirms Implementation Plan (NEW IN v1.1)

> Evaluator role: Delta-confirm the following implementation plan against the approved proposal stack and active bindings. Verify: (1) every authorized requirement is present, (2) no panel-ratified content has been silently modified during integration (Charter §Integration Discipline), (3) gaps Kimi flagged are surfaced for panel resolution and not silently invented.
>
> [Paste implementation plan]

Save as `AXIOM_Evaluation_Implementation_v[N].md`. If issues are found, return to Kimi with explicit scope statement (see §Returning Implementation Plans).

### Step 9 — Save Session Outputs

Upload to the AXIOM Project knowledge base:

- `AXIOM_Proposal_v[N].md` (final approved version of this cycle)
- `AXIOM_Implementation_v[N].md` (current Kimi plan)
- `AXIOM_Active_Bindings.md` (updated)

**Knowledge base hygiene** — see §Part 7.

---

## Part 5 — Delta-Confirmation Cycles (NEW IN v1.1)

When the synthesis declares the next cycle a delta cycle, only some panel roles run.

### Eligibility (per Charter §Delta-Confirmation Cycle)

A delta cycle is authorized only when the revision:
1. Introduces no new component, module, or coordination mechanism
2. Introduces no new factual claim about external technology
3. Does not change RAM, thread count, or API budget
4. Does not touch any Core Value or Constraints Register entry

### Workflow

**Always run:**
- Architect produces the targeted revision
- Evaluator delta-confirms

**Conditionally run:**
- Critic, only if the revision could introduce new attack surface or fails to resolve prior objections cleanly
- Arbiter, only if a new factual claim is introduced
- Constraints, only if RAM/threads/budget shift

The synthesis document declares which roles are skipped and why. If a "skippable" role is run anyway out of caution, that's fine — over-review is never wrong; under-review is.

### When a Delta Cycle Surfaces a Blocking Issue

It immediately escalates to a full cycle on the next revision. The synthesis records this escalation explicitly.

---

## Part 6 — Chat Handoffs (NEW IN v1.1)

Chat context exhaustion is the most common operational friction. Treat any chat with one of the panel members as a finite resource — when context gets tight, the next session needs a clean handoff.

### When to start a fresh chat

- Context is visibly degrading (responses feel lossy, reference earlier content incorrectly)
- The chat is approaching platform limits
- You are switching to a substantively different design question

### Fresh-chat upload list

Every new chat with a panel member requires the full briefing context:

**Always:**
1. `AXIOM_Panel_Charter.md`
2. `AXIOM_Constraints_Register.md`
3. `AXIOM_Core_Values.md`
4. `AXIOM_Legacy_Reference.md`
5. `AXIOM_Active_Bindings.md`

**Plus, depending on which panel member:**

| Panel member | Additional uploads |
|---|---|
| Architect (new cycle) | The most recent approved proposal as the spine |
| Architect (revision cycle) | The most recent approved proposal + Critic/Arbiter/Constraints/Synthesis from current cycle |
| Critic | The proposal under review |
| Arbiter | The proposal under review |
| Constraints | The proposal under review |
| Evaluator (Claude — but here you should just continue or open a new project chat) | Project knowledge already has it; upload only the current-cycle artifacts being reviewed |
| Implementation Specialist | Full approved proposal stack from current architecture cycle + bindings + prior implementation plan if revising |

### Re-send the role briefing verbatim

A new conversation has no memory of role context. The role briefing from §Part 2 is mandatory before any cue prompt.

### Handoff prompt template

Replace v1.0's "brief description + open question" template with this:

> [Role briefing verbatim — see Part 2]
>
> Wait for confirmation.
>
> ---
>
> [Then send:]
>
> [Role cue]: The panel completed [previous milestone]. Active bindings travel forward — see uploaded `AXIOM_Active_Bindings.md`. The current open questions are:
>
> 1. [Question 1 with full context]
> 2. [Question 2 with full context]
> 3. [Question 3 with full context]
>
> Produce [the specific deliverable].

Real handoffs frequently have multiple open questions. The v1.0 template assumed one. Don't compress.

---

## Part 7 — Knowledge Base Hygiene

### What to keep

- All approved `AXIOM_Proposal_v[N].md` files in the chain (later versions reference earlier ones)
- The current `AXIOM_Implementation_v[N].md`
- All Arbiter rulings that are still active (not yet superseded)
- All Constraints rulings that are still active
- The current `AXIOM_Active_Bindings.md`
- Synthesis documents for any cycle whose decisions are still in force

### What to retire

- Superseded implementation plans (v1.11 superseded by v1.12 superseded by v1.13 — keep only the current canonical plan)
- Critique and Evaluation documents from cycles whose proposals were further revised (the Synthesis is the durable record; the inputs are working drafts)
- Draft proposals that were never approved
- Arbiter or Constraints rulings explicitly superseded by later rulings

### What to never retire

- Anything in `AXIOM_Active_Bindings.md`
- The Charter, Core Values, Constraints Register, Legacy Reference (the four-document spine)
- Synthesis documents — these are the audit trail of how decisions were made

### When in doubt, keep it

Disk space is cheap; reconstructing a lost ruling is expensive. The retire list above is for active project knowledge — keep an archive on disk regardless.

---

## Part 8 — Cross-Cutting Artifact Production (NEW IN v1.1)

When a proposal requires an artifact that spans multiple panel roles (calibration test set, validation corpus, security regression suite), follow Charter §Cross-Cutting Artifact Protocol:

1. **Gemini (primary author).** Drafts the artifact based on factual ground truth.
2. **DeepSeek (adversarial review).** Identifies gaps, weak samples, missing attack vectors.
3. **Claude (coherence review).** Verifies consistency with the proposal it serves.
4. **Qwen (feasibility review).** Confirms volume and runtime cost fit the constraints.
5. **Kimi (implementation packaging).** Specifies file format, schema, integration with the implementation plan.
6. **Operator (file creation).** Writes the artifact to disk in the specified format.

**This is a multi-session workflow.** Plan accordingly. The calibration test set workflow added 3+ panel sessions to the v1.10 → v1.12 path.

---

## Part 9 — Returning Implementation Plans

When the Evaluator returns Kimi's implementation plan for revision (Step 8 produced blocking issues), use a **scoped revision instruction** rather than an open-ended request. Per Charter §Integration Discipline:

> Implement: AXIOM Implementation Plan v[N+1] — targeted revision of v[N].
>
> The following defects must be repaired:
>
> Defect 1 — [exact location, exact current state, exact required change]
> Defect 2 — [exact location, exact current state, exact required change]
> ...
>
> Out of scope for v[N+1]:
> - All other sections (carry forward verbatim)
> - Architecture spine changes (none authorized)
> - Re-Critic, re-Arbiter, re-Constraints cycle (none required)
>
> Produce v[N+1] as a delta document. After production, the Evaluator will perform delta-confirmation only.

This template prevents the "integration regression" failure mode that occurred in v1.13 — where authorized fixes were correctly applied but unauthorized changes silently appeared in adjacent sections.

---

## Part 10 — File Naming Convention (UPDATED IN v1.1)

`AXIOM_[Type]_v[Version].[ext]`

| Type | Description |
|---|---|
| Proposal | Architecture proposal from Architect |
| Evaluation | Coherence review from Evaluator |
| Critique | Adversarial challenge from Critic |
| Arbiter | Factual ruling from Arbiter |
| Constraints | Feasibility ruling from Constraints Reviewer |
| Synthesis | Combined panel review from Evaluator |
| Implementation | Execution plan from Implementation Specialist |
| Evaluation_Implementation | Delta-confirmation review of the implementation plan |
| Active_Bindings | Running registry of Arbiter and Constraints bindings |

**Version numbers** track the proposal cycle, not chat sessions. Sub-revisions use dotted notation: `v1.7` → `v1.7.1` (patch) → `v1.8` (next major revision after full review). This pattern emerged organically and works.

---

## Part 11 — Quick Reference: Panel Cue Words

| Cue | System | Action |
|---|---|---|
| `Architect: [directive]` | GPT-5.5 | Produce or revise proposal |
| `Evaluator role: [proposal]` | Claude (AXIOM Project) | Review coherence |
| `Evaluator role: [synthesis prompt]` | Claude (AXIOM Project) | Synthesize panel output |
| `Critic: [proposal]` | DeepSeek | Challenge proposal |
| `Arbiter: [claim]` | Gemini | Verify and rule |
| `Constraints: [proposal]` | Qwen | Feasibility check |
| `Implement: [approved proposal]` | Kimi | Produce implementation plan |
| `Implement: [revision instructions]` | Kimi | Targeted implementation revision |

---

## Part 12 — Common Operator Pitfalls (NEW IN v1.1)

Patterns observed during v1.0 → v1.13 that cost time:

**Pitfall 1: Compressing handoffs.** Using v1.0's "brief description" template when the real situation has 3+ open questions and multiple binding rulings to carry forward. Always upload the full context.

**Pitfall 2: Forgetting to add a new binding to `AXIOM_Active_Bindings.md`.** Bindings filed mid-cycle and forgotten by the next session. The fix is to update the file the moment a binding is issued, not at end-of-session.

**Pitfall 3: Running a full cycle when a delta cycle was authorized.** Wastes Critic/Arbiter/Constraints time and produces noise. Trust the synthesis declaration.

**Pitfall 4: Running a delta cycle when a full cycle was warranted.** Misses real issues. If Critic, Arbiter, or Constraints want to review, let them.

**Pitfall 5: Deleting "old" documents prematurely.** Especially Synthesis documents — those are the audit trail. Retire to archive, don't delete.

**Pitfall 6: Skipping the role briefing on a fresh chat.** Panel members behave differently without role context. The briefing is not optional.

**Pitfall 7: Editorializing on responses between panel members.** Your job is delivery. If you have a question about a response, ask the panel member who produced it.

---

## Part 13 — Amendment Log

| Version | Date | Section | Change | Authority |
|---|---|---|---|---|
| 1.0 | May 2026 | — | Initial guide | Founding |
| 1.1 | May 2026 | §3 Active Bindings | New section | Operator-acceptable |
| 1.1 | May 2026 | §5 Delta Cycles | New section | Mirrors Charter v1.1 |
| 1.1 | May 2026 | §6 Chat Handoffs | New section | Operator-acceptable |
| 1.1 | May 2026 | §7 Knowledge Base Hygiene | New section | Operator-acceptable |
| 1.1 | May 2026 | §8 Cross-Cutting Artifacts | New section | Mirrors Charter v1.1 |
| 1.1 | May 2026 | §9 Returning Implementation Plans | New section | Mirrors Charter v1.1 |
| 1.1 | May 2026 | §12 Common Pitfalls | New section | Operator-acceptable |

The Operator Guide is operational documentation, not panel governance. Sections that mirror Charter or Constraints amendments take effect when those amendments do. Sections marked "Operator-acceptable" can take effect on operator decision alone.

---

*AXIOM Operator Guide — Version 1.1 — May 2026 — derived operational guidance under Charter v1.1*
