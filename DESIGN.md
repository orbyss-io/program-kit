---
artifact-kind: program-kit-design-convergence-ledger
status: active
authority: human-led
implementation-authority: none
created: 2026-07-31
last-updated: 2026-07-31
active-category: product-identity
active-batch: PID-B01
constitution-proposal: .specify/memory/constitution.md
---

# Program Kit Design Convergence

## 1. Purpose

This is the durable, repository-root record of the product discovery that must
converge before Program Kit is designed or implemented. It exists so that
questions, answers, contradictions, consequences, and newly discovered
questions survive across sessions.

This ledger is not an implementation specification and does not authorize
implementation. The constitution is also still a proposal. A statement becomes
accepted product design only through the decision process defined below.

## 2. Authority and convergence method

The human product owner has final authority over product intent. The agent may
analyze answers, expose ambiguity, identify conflicts, propose precise wording,
and generate follow-up questions. It may not silently turn an inference into a
decision.

Every discovery item has a stable identifier. Its status is one of:

| Status | Meaning |
|---|---|
| `open` | Asked or queued, with no sufficient answer yet. |
| `answered` | A human answer is recorded, but its consequences have not converged. |
| `follow-up` | The answer created or exposed another blocking question. |
| `candidate-decision` | Precise decision wording is ready for human confirmation. |
| `accepted` | The human explicitly accepted the candidate decision. |
| `rejected` | The human explicitly rejected the candidate decision. |
| `deferred` | Deliberately postponed with a recorded boundary and revisit trigger. |
| `superseded` | Replaced by another identified item; history remains visible. |

The following rules apply:

1. Record human input separately from agent synthesis.
2. Preserve the meaning of human input; quote it when exact wording matters.
3. Record derived implications, tensions, and assumptions as non-authoritative
   until confirmed.
4. Give every emergent question a new stable ID. Never rewrite history to make
   it appear that the question was known earlier.
5. Never mark a decision `accepted` merely because the human answered a
   question. First present the precise decision and its important consequences.
6. Close a category only when it has no blocking `open` or `follow-up` items and
   every candidate decision is accepted or explicitly deferred.
7. If a later answer conflicts with an accepted decision, record the conflict
   and reopen or supersede the decision explicitly.
8. Implementation work begins only after the required product categories and
   the constitution have converged and the human authorizes implementation.

## 3. Evidence, founding intent, and provisional synthesis

Source roles, the recovered founding intent, and non-authoritative synthesis are
recorded in [`DESIGN-FOUNDATIONS.md`](DESIGN-FOUNDATIONS.md).

## 6. Category register

| Category | ID prefix | Status | Known items | Notes |
|---|---:|---|---:|---|
| Product identity | `PID` | `active` | 8 | Current category; batch `PID-B01` is active. |
| Feature model | `FTR` | `queued` | 13 | Begins after product identity converges. |
| Semantic language and bounded contexts | `SEM` | `queued` | 12 | May be reshaped by identity and feature answers. |
| Extensions and composition | `EXT` | `queued` | 12 | Includes the deferred question of governed Spec Kit composition. |
| Determinism and generated artifacts | `DET` | `queued` | 9 | Exact reproducibility and ownership boundaries. |
| Diagnostics and AI guidance | `DIA` | `queued` | 16 | Founding concern; may gain questions from every category. |
| Dependencies, impact, and migration | `MIG` | `queued` | 12 | Graph truth, compatibility, closure, and evidence. |
| Governance, enforcement, and self-hosting | `GOV` | `queued` | 12 | Human authority and executable integrity. |
| First vertical slice | `VSL` | `queued` | 8 | Must prove the accepted product identity honestly. |

Counts are a live snapshot, not a quota. New questions are expected.

## 7. Active category: Product identity

Product Identity is recorded by batch in
[`DESIGN-PRODUCT-IDENTITY.md`](DESIGN-PRODUCT-IDENTITY.md). Batch `PID-B01`
is active.

## 8. Queued question catalog

The complete queued discovery horizon is preserved in
[`DESIGN-QUESTION-CATALOG.md`](DESIGN-QUESTION-CATALOG.md). The live ledger
records active answers, consequences, emergent questions, and decisions.

## 9. Decision register

No product-design decisions have been accepted yet.

| Decision ID | Source questions | Status | Decision | Accepted on |
|---|---|---|---|---|
| — | — | — | — | — |

## 10. Emergent-question register

New items receive the next stable ID within the relevant category and cite the
answer or tension that created them.

| Question ID | Origin | Status | Question |
|---|---|---|---|
| `PID-008` | Human warning that archived Program Kit duplicated work better owned by Spec Kit | `follow-up` | Define the exact responsibility seam between Spec Kit and Program Kit. |
| `EXT-012` | Possible future exported capabilities combining Spec Kit techniques and Program Kit mechanics | `deferred` | Define a governed, explicit, non-circular composition model after product identity converges. |

## 11. Session log

### 2026-07-31 — Ledger established

- Recorded the founding product narrative and diagnostics emphasis.
- Established the human-led convergence method and explicit decision states.
- Preserved 100 initial questions across nine categories.
- Activated Product Identity batch `PID-B01` (`PID-001`, `PID-002`, `PID-008`).
- No product-design decision was marked accepted.
- Recorded the human's warning that the archived product crossed into Spec Kit's
  responsibilities. Added `PID-008` for the product boundary and deferred
  `EXT-012` for possible governed composition with Spec Kit techniques.
