# AXIOM — Operator Guide
## Setup, Workflow, and Cross-Chat Continuity

**Document Type:** Derived Operational Guide  
**Status:** Active — conforms to Charter v1.2  
**Effective Date:** 2026-05-15  
**Authority:** `AXIOM_Panel_Charter.md` v1.2 and `AXIOM_Synthesis_Governance_v2_Cycle2.md`  
**Supersedes:** Charter v1.1-derived Operator Guide

---

## 1. Purpose

This guide tells the operator how to run AXIOM governance and implementation cycles after the v1.1 → v1.2 panel operating-model restructuring amendment.

The Charter remains authoritative. This guide is operational only.

---

## 2. Standard Upload Spine

For every fresh panel chat, upload:

1. `AXIOM_Panel_Charter.md`
2. `AXIOM_Core_Values.md`
3. `AXIOM_Constraints_Register.md`
4. `AXIOM_Legacy_Reference.md`
5. `AXIOM_Active_Bindings.md`
6. `AXIOM_Specification_Debt.md`
7. `AXIOM_Canonical_Filenames.md`
8. `AXIOM_Panel_Tier_Membership.md`
9. Active proposal, Synthesis, review, runbook, or implementation files relevant to the task

Do not delete historical binding files. Keep `AXIOM_Active_Bindings_v1_1.md` and older versions as historical records.

---

## 3. Panel Roles Under Charter v1.2

### Continuous Working Layer

| AI System | Role | Use |
|---|---|---|
| GPT-5.5 / ChatGPT | Chief Architect and Researcher | Architecture proposals, research drafting, revision synthesis |
| Claude Opus 4.7 | Quality and Coherence Evaluator | Synthesis, coherence review, SD ledger, binding preservation |
| Gemini 3.1 Pro | Implementation Specialist and Troubleshooter | Implementation plans, deployment support, troubleshooting |

### Advisory Council

| AI System | Role | Use |
|---|---|---|
| DeepSeek V4 | Adversarial Critic | Security, threat model, trust-boundary, attack-surface challenge |
| Qwen 3.6 Plus | Constraints and Feasibility Reviewer | RAM, thread, API, runtime, budget, local/cloud feasibility |
| Kimi K2.6 | Research and Knowledge Arbiter | Factual claims, tools, APIs, libraries, model behavior, AB maintenance |

Tier classification affects routing cadence, not authority.

---

## 4. Workflow Overview

1. Architect drafts proposal or research note.
2. Evaluator checks coherence, Domain-Trigger Declaration, PDR marks, active bindings, and SD ledger implications.
3. Operator routes to Advisory Council members when triggers are present.
4. Evaluator writes Synthesis.
5. If ratified, Implementation Specialist produces execution plan.
6. Evaluator delta-confirms implementation plan when eligible or routes back to full panel.
7. Operator executes approved file operations or implementation steps.
8. Operator reports exact test/output results back to the panel.

---

## 5. Domain-Trigger Declaration

Every formal proposal should include a Domain-Trigger Declaration:

```markdown
## Domain-Trigger Declaration

| Domain | Triggered? | Reason | Required Reviewer |
|---|---|---|---|
| Factual / Arbiter | Yes/No | ... | Kimi |
| Feasibility / Constraints | Yes/No | ... | Qwen |
| Security / Adversarial | Yes/No | ... | DeepSeek |
| Architectural Trigger | Yes/No | ... | Full Advisory Council if Yes |
```

The Evaluator audits this table. A self-declared `No` does not control if the actual content triggers a domain.

---

## 6. Trigger-Detection Checklist

Route to **Kimi** if the text mentions or depends on:

- external tools, libraries, APIs, operating-system behavior, model behavior, file formats, platform limits, or current technical state;
- AB bindings or proposed AB supersession;
- any claim that would become wrong if the tool/platform changed.

Route to **Qwen** if the text mentions or depends on:

- RAM, CPU, thread count, process count, storage, local/cloud allocation, API quotas, token budgets, runtime cost, hardware compatibility, persistence burden;
- CB bindings or proposed CB supersession.

Route to **DeepSeek** if the text mentions or depends on:

- sandboxing, network boundaries, prompt injection, tool permissions, agent permissions, credential exposure, trust boundaries, attack surface, data exfiltration, policy bypass;
- Core Value impacts;
- adversarial assumptions.

Route to the **full Advisory Council** if the proposal modifies AXIOM architecture, agent hierarchy, task queue, sandbox/network/cloud-cascade boundaries, trust boundaries, persistence model, policy enforcement, role authority, or binding authority.

---

## 7. Pending-Domain-Review Marking

Use this inline syntax:

```markdown
[PDR: <domain>; owner=<Kimi|Qwen|DeepSeek>; reason=<short reason>; status=pending]
```

Local PDR marks stay in the artifact where they arise. Do not append them to `AXIOM_Specification_Debt.md` unless formally deferred, escalated to a binding/factual dispute, or converted into specification debt.

The Evaluator must clear or account for PDR marks before ratification. A proposal cannot use unresolved PDR content as ratification basis.

---

## 8. Advisory Access Procedure

If an Advisory Council member asks for in-progress continuous-layer work:

1. Provide the relevant draft chain or most recent draft plus material prior context.
2. Include the working baseline.
3. State which domain-trigger question the advisory member is reviewing.
4. Log failures to provide access as specification debt if the access failure blocks review.

---

## 9. Drive Workflow and Sanitization Gate

Shared Drive is operational support only. It does not replace formal panel review.

Before one continuous-layer AI consumes a Drive document written by another continuous-layer AI:

1. Save the original unchanged for audit.
2. Run it through the local prompt-injection sanitization pipeline.
3. Place the sanitized copy in a `sanitized/` subfolder.
4. Use the sanitized copy as the input.
5. Keep Drive sharing restricted to the operator account, link sharing disabled.

If Drive, authentication, or network access is degraded for more than four hours, use local file exchange: copy-paste, local markdown files, or offline sync. Claims remain pending domain review until synchronization is restored.

---

## 10. Active Bindings Registry Maintenance

Current binding set: 36 total.

| Class | Count | Maintaining Authority |
|---|---:|---|
| AB | 7 | Kimi |
| CB | 25 | Qwen |
| GB | 4 | Full panel |

Do not edit binding text casually. Supersession requires a later panel ruling that explicitly cites the prior binding ID and replacement rationale.

When updating the registry:

1. Preserve the prior versioned file.
2. Create the new versioned file.
3. Copy the new version over `AXIOM_Active_Bindings.md` as a plain alias.
4. Verify alias byte equality with SHA256.
5. Verify AB/CB/GB counts.

---

## 11. Specification Debt Ledger

`AXIOM_Specification_Debt.md` is append-only in audit principle. Closures update status; rows are not deleted.

Every Synthesis must include a Synthesis-vs-ledger cross-check. Discrepancies block treating the Synthesis as complete unless corrected immediately as clerical error.

PDR marks are not ordinary SD items. CB-025 controls the separation.

---

## 12. Dispute Resolution Procedure for Arbiter-Elect Transitions

If a future Arbiter-elect affirmation marks an inherited AB binding as `Disputed`:

1. The disputed binding is excluded from maintenance transfer.
2. The issuing Arbiter retains maintenance authority for that binding.
3. The amendment may proceed with affirmed and qualified bindings if all other criteria are met.
4. The Synthesis records which binding was excluded and why.
5. A separate factual-arbitration proposal may later resolve the disputed binding.

---

## 13. Implementation Specialist Handoff Procedure

When an Implementation Specialist role transition occurs:

1. Create a handoff directory.
2. Copy available runbooks, prior implementability reviews, Diff Gate scripts, canonical filenames registry, and archive convention notes.
3. Do not substitute missing files. Mark missing files as `not available` in the transfer note.
4. Deliver the package to the incoming Implementation Specialist.
5. Preserve GB-001 exceptions unless explicitly superseded.

---

## 14. 30-Day Charter Amendment Audit

For the Governance v2 amendment, the file-swap completion date is 2026-05-15. The audit reminder date is 2026-06-14.

Reminder text:

```text
AXIOM Charter Amendment Audit due. The Evaluator (Claude) authors AXIOM_Charter_Audit_Governance_v2_20260614.md per Charter v1.2 §Charter Amendment Process. Audit scope is substantive — reviewing decisions made during the v2 amendment's full Cycle 1 and Cycle 2 history.
```

---

## 15. Panel Member Smoke Test

After uploading the v1.2 document set, open fresh chats with GPT-5.5, Gemini, DeepSeek, Qwen, and Kimi.

Send the appropriate role notice, then ask:

```text
Confirm you understand: (a) your role under Charter v1.2, (b) your tier classification, (c) the active bindings that travel forward now total 36 under v1.2, and (d) the current specification debt items in your domain. This is a smoke test of the new governance documents — not a review request.
```

Do not proceed to the next architectural cycle if a panel member misunderstands the role transition or binding authority.

---

## 16. Operator Execution Rule

The operator executes file actions, uploads documents, runs commands, and reports exact outputs. The operator does not make panel decisions, silently repair governance gaps, or skip advisory review because routing is inconvenient.
