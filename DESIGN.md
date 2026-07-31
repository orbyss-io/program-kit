---
artifact-kind: program-kit-design-convergence-ledger
status: active
authority: human-led
implementation-authority: none
created: 2026-07-31
last-updated: 2026-07-31
active-category: feature-model
active-batch: FTR-B01
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
| Product identity | `PID` | `closed` | 11 | All Product Identity decisions accepted on 2026-07-31. |
| Feature model | `FTR` | `active` | 14 | Batch `FTR-B01` defines the feature primitive and semantic interface. |
| Semantic language and bounded contexts | `SEM` | `queued` | 12 | May be reshaped by identity and feature answers. |
| Consumer planning and delivery | `PLN` | `queued` | 4 | Product-owned planning surface; exact concepts and execution boundary unresolved. |
| Extensions and composition | `EXT` | `queued` | 13 | Includes internal Spec Kit reuse and an optional Spec Kit-to-Program Kit bridge. |
| Determinism and generated artifacts | `DET` | `queued` | 10 | Includes the boundary of semi-deterministic behavior. |
| Diagnostics and AI guidance | `DIA` | `queued` | 16 | Founding concern; may gain questions from every category. |
| Dependencies, impact, and migration | `MIG` | `queued` | 12 | Graph truth, compatibility, closure, and evidence. |
| Governance, enforcement, and self-hosting | `GOV` | `queued` | 12 | Human authority and executable integrity. |
| First vertical slice | `VSL` | `queued` | 8 | Must prove the accepted product identity honestly. |

Counts are a live snapshot, not a quota. New questions are expected.

## 7. Category progression

Product Identity is closed and recorded in
[`DESIGN-PRODUCT-IDENTITY.md`](DESIGN-PRODUCT-IDENTITY.md).

Feature Model is active and recorded in
[`DESIGN-FEATURE-MODEL.md`](DESIGN-FEATURE-MODEL.md). Batch `FTR-B01` is active.

## 8. Queued question catalog

The complete queued discovery horizon is preserved in
[`DESIGN-QUESTION-CATALOG.md`](DESIGN-QUESTION-CATALOG.md). The live ledger
records active answers, consequences, emergent questions, and decisions.

## 9. Decision register

Product Identity decisions are accepted; all other categories remain unresolved.

| Decision ID | Source questions | Status | Decision | Accepted on |
|---|---|---|---|---|
| `DEC-001` | `PID-008` | `accepted` | A Program Kit installation exposes an integrated consumer design, planning, and implementation-plan experience without requiring a separate Spec Kit CLI installation. | 2026-07-31 |
| `DEC-002` | `PID-008`, `GOV-001` | `accepted` | Program Kit itself is developed with Spec Kit and does not consume its own planning facilities during this redesign. | 2026-07-31 |
| `DEC-003` | `PID-001` | `accepted` | Program Kit is a human-led, AI-assisted modular software-development tool that translates human intent into bounded, contract-evaluated, semi-deterministic software components; the human contributor retains final authority. | 2026-07-31 |
| `DEC-004` | `PID-002`, `PID-011` | `accepted` | Program Kit's non-negotiable promise is governed integration resolution between Program Kit-built products: direct composition, an explicit adapter or migration, or a precise contract-backed incompatibility result; ambiguity is failure. | 2026-07-31 |
| `DEC-005` | `PID-003`, `PID-010` | `accepted` | Humans, domain experts, developers, and AI may collaborate; the human owns intent and identity-forming approval, while admitted outputs must satisfy currently accepted contracts until explicitly revised and reaccepted. | 2026-07-31 |
| `DEC-006` | `PID-004` | `accepted` | Program Kit v1 implements .NET projections while keeping semantic contracts free of unnecessary .NET-specific meaning; multi-ecosystem implementation is out of scope. | 2026-07-31 |
| `DEC-007` | `PID-005`, `VSL-001` | `accepted` | The first-hour proof links intent, design, work, plan, contract, a real .NET component, actionable diagnostics, governed integration resolution, and repeatability evidence. | 2026-07-31 |
| `DEC-008` | `PID-006` | `accepted` | Program Kit v1 refuses autonomous semantic authority, forced universal composability, ambiguous integration, ambient or unpinned selection, built-in business-domain meaning, multi-ecosystem implementation, runtime dependence on development tooling, and self-hosting during the redesign. | 2026-07-31 |
| `DEC-009` | `PID-007` | `accepted` | Program Kit v1 is a semantic development toolchain, not a new programming language; a language claim requires a formal grammar, type system, compiler semantics, and compatibility model. | 2026-07-31 |
| `DEC-010` | `PID-009`, `EXT-012`, `EXT-013` | `accepted` | Program Kit owns independent public commands, artifacts, diagnostics, and compatibility promises; internal Spec Kit reuse is replaceable, and optional Spec Kit integration may invoke only Program Kit's public contract. | 2026-07-31 |
| `DEC-011` | `EXT-013` | `accepted` | The Spec Kit-to-Program Kit adapter is outside the current design; reconsider it only after Program Kit CLI is implemented, independently usable, and published, as a separate optional adapter. | 2026-07-31 |

## 10. Emergent-question register

New items receive the next stable ID within the relevant category and cite the
answer or tension that created them.

| Question ID | Origin | Status | Question |
|---|---|---|---|
| `PID-008` | Human separated Program Kit's consumer capabilities from the workflow used to build Program Kit itself | `accepted` | Governed by `DEC-001` and `DEC-002`; internal Spec Kit composition is separate. |
| `EXT-012` | Program Kit may internally reuse selected Spec Kit techniques | `open` | Define a governed, explicit, pinned, replaceable, non-circular internal composition model. |
| `EXT-013` | Existing Spec Kit users may benefit from invoking Program Kit at explicit handoff points | `deferred` | Outside current design; revisit only after Program Kit CLI is independently usable and published, then require measurable value and no core coupling. |
| `PID-009` | Consumers must not install a second CLI while Program Kit may reuse Spec Kit internally | `accepted` | Program Kit owns independent public contracts; optional interoperability uses those contracts. |
| `DET-010` | Consumer outcome described as semi-deterministic software components | `follow-up` | Define the exact judgment-to-determinism acceptance boundary. |
| `PLN-001` | Archived planning domain retains serious product value | `open` | Define the canonical planning concepts and lifecycle relations. |
| `PLN-002` | Archived planning implementation is prior art rather than source truth | `open` | Decide which concepts to retain, re-specify, or discard. |
| `PLN-003` | Plans integrate with validations, components, and files | `open` | Define stable links and drift behavior. |
| `PLN-004` | Program Kit enables consumers to design and implement components | `open` | Define the boundary between planning artifacts, orchestration, and execution. |
| `PID-010` | Human contributor named as governing identity in `PID-001` | `accepted` | Human governs intent; currently accepted contracts govern admitted outputs until explicitly revised and reaccepted. |
| `PID-011` | Resolvable integration named as the non-negotiable promise in `PID-002` | `accepted` | Precise irreconcilability is a resolution; universal composability is not promised. |
| `FTR-014` | Bounded components evaluate against a contract | `open` | Define the required contract dimensions. |

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

### 2026-07-31 — Consumer planning boundary refined

- Corrected the earlier assumption that Program Kit necessarily begins after
  Spec Kit planning; Program Kit owns an integrated consumer planning surface.
- Recorded candidate decisions `DEC-001` for the one-install consumer experience
  and `DEC-002` for Spec Kit-only development of Program Kit during the redesign.
- Added Product Identity, Consumer Planning, and semi-determinism follow-ups.
- Did not treat this clarification as an answer to the earlier active batch.

### 2026-07-31 — Product identity answers recorded

- Recorded `PID-001` as answered and created candidate decision `DEC-003`.
- Separated the product category and human authority from the Spec Kit-based
  development method already governed by `DEC-002`.
- Recorded `PID-002` as a follow-up and created candidate `DEC-004` for
  governed integration resolution.
- Revised `PID-008`; it no longer carries the entire internal Spec Kit seam.
- Added `PID-010`, `PID-011`, and `FTR-014` for the remaining ambiguities.
- No candidate decision was marked accepted.

### 2026-07-31 — Product identity closed

- The human explicitly accepted all eight consolidated recommendations.
- Accepted `DEC-001` through `DEC-010`; all eleven Product Identity questions
  are closed.
- Left no active category until the human selects the next discovery category.
- Added `EXT-013` for a possible optional Spec Kit-to-Program Kit bridge.
- Deferred that bridge until standalone Program Kit value is proven; it must
  use only public Program Kit contracts, remain non-circular, and justify its
  cost with measurable workflow value.
- The constitution remains an unratified proposal pending further convergence.

### 2026-07-31 — Feature Model activated

- Accepted `DEC-011`: the Spec Kit adapter is outside the current design and
  may be reconsidered only after Program Kit CLI is independently published.
- Activated Feature Model batch `FTR-B01` with three primitive-defining
  questions; later Feature Model questions remain queued and may be reshaped.
