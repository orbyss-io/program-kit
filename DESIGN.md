---
artifact-kind: program-kit-design-convergence-ledger
status: active
authority: human-led
implementation-authority: none
created: 2026-07-31
last-updated: 2026-07-31
active-category: feature-model
active-batch: FTR-B03
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
| Product identity | `PID` | `closed` | 19 | All five batches and accepted decisions `DEC-001`–`DEC-011`, `DEC-014`–`DEC-020` are closed. |
| Feature model | `FTR` | `active` | 17 | `FTR-B01` and `FTR-B02` are accepted by `DEC-013` and `DEC-021`; `FTR-B03` now resolves identity, relations, and implementation selection. |
| Semantic language and bounded contexts | `SEM` | `queued` | 14 | `SEM-013` and `SEM-014` are accepted; remaining questions are queued. |
| Consumer planning and delivery | `PLN` | `queued` | 4 | Product-owned planning surface; exact concepts and execution boundary unresolved. |
| Extensions and composition | `EXT` | `queued` | 13 | Includes internal Spec Kit reuse and an optional Spec Kit-to-Program Kit bridge. |
| Determinism and generated artifacts | `DET` | `queued` | 10 | `DET-010` is accepted; remaining deterministic-generation questions are queued. |
| Diagnostics and AI guidance | `DIA` | `queued` | 16 | Founding concern; may gain questions from every category. |
| Dependencies, impact, and migration | `MIG` | `queued` | 12 | Graph truth, compatibility, closure, and evidence. |
| Governance, enforcement, and self-hosting | `GOV` | `queued` | 12 | Human authority and executable integrity. |
| First vertical slice | `VSL` | `queued` | 8 | Must prove the accepted product identity honestly. |

Counts are a live snapshot, not a quota. New questions are expected.

## 7. Category progression

Product Identity is closed and recorded in
[`DESIGN-PRODUCT-IDENTITY.md`](DESIGN-PRODUCT-IDENTITY.md). The human accepted
all six consolidated recommendations and the qualified product expression.

Feature Model is active at its accepted thin target-specific boundary in
[`DESIGN-FEATURE-MODEL.md`](DESIGN-FEATURE-MODEL.md). Batches `FTR-B01` and
`FTR-B02` are complete and `FTR-B03` is active.

## 8. Queued question catalog

The complete queued discovery horizon is preserved in
[`DESIGN-QUESTION-CATALOG.md`](DESIGN-QUESTION-CATALOG.md). The live ledger
records active answers, consequences, emergent questions, and decisions.

## 9. Decision register

Decisions `DEC-001`–`DEC-011` and `DEC-013`–`DEC-021` are accepted. `DEC-012`
is superseded. Feature Model convergence continues with identity, relations,
and implementation selection.

| Decision ID | Source questions | Status | Decision | Accepted on |
|---|---|---|---|---|
| `DEC-001` | `PID-008` | `accepted` | A Program Kit installation exposes an integrated consumer design, planning, and implementation-plan experience without requiring a separate Spec Kit CLI installation. | 2026-07-31 |
| `DEC-002` | `PID-008`, `GOV-001` | `accepted` | Program Kit itself is developed with Spec Kit and does not consume its own planning facilities during this redesign. | 2026-07-31 |
| `DEC-003` | `PID-001` | `accepted` | Program Kit is a human-led, AI-assisted modular software-development tool that translates human intent into bounded, contract-evaluated software components; the human contributor retains final authority. The deterministic construction boundary is refined by `DEC-018`. | 2026-07-31 |
| `DEC-004` | `PID-002`, `PID-011` | `accepted` | Program Kit's non-negotiable promise is governed integration resolution between Program Kit-built products: direct composition, an explicit adapter or migration, or a precise contract-backed incompatibility result; ambiguity is failure. | 2026-07-31 |
| `DEC-005` | `PID-003`, `PID-010` | `accepted` | Humans, domain experts, developers, and AI may collaborate; the human owns intent and identity-forming approval, while admitted outputs must satisfy currently accepted contracts until explicitly revised and reaccepted. | 2026-07-31 |
| `DEC-006` | `PID-004` | `accepted` | Program Kit v1 implements .NET projections while keeping semantic contracts free of unnecessary .NET-specific meaning; multi-ecosystem implementation is out of scope. | 2026-07-31 |
| `DEC-007` | `PID-005`, `VSL-001` | `accepted` | The first-hour proof links intent, design, work, plan, contract, a real .NET component, actionable diagnostics, governed integration resolution, and repeatability evidence. | 2026-07-31 |
| `DEC-008` | `PID-006` | `accepted` | Program Kit v1 refuses autonomous semantic authority, forced universal composability, ambiguous integration, ambient or unpinned selection, built-in business-domain meaning, multi-ecosystem implementation, runtime dependence on development tooling, and self-hosting during the redesign. | 2026-07-31 |
| `DEC-009` | `PID-007` | `accepted` | Program Kit v1 is a semantic development toolchain, not a new programming language; a language claim requires a formal grammar, type system, compiler semantics, and compatibility model. | 2026-07-31 |
| `DEC-010` | `PID-009`, `EXT-012`, `EXT-013` | `accepted` | Program Kit owns independent public commands, artifacts, diagnostics, and compatibility promises; internal Spec Kit reuse is replaceable, and optional Spec Kit integration may invoke only Program Kit's public contract. | 2026-07-31 |
| `DEC-011` | `EXT-013` | `accepted` | The Spec Kit-to-Program Kit adapter is outside the current design; reconsider it only after Program Kit CLI is implemented, independently usable, and published, as a separate optional adapter. | 2026-07-31 |
| `DEC-012` | `FTR-001`, `FTR-002` | `superseded` | The optional-projection framing overgeneralized the feature model and understated CShells as Program Kit's intended .NET feature mechanism. | — |
| `DEC-013` | `FTR-001`, `FTR-003`, `FTR-004`, `FTR-015`–`FTR-017` | `accepted` | Program Kit uses a thin target-specific feature model: the portable bundle is distinct from implemented features; CShells supplies selected .NET host mechanics; interface, contract, intake, and binding are distinct; relationships are many-to-many; the kernel owns integrity while consumers own architecture; and cross-target reuse uses definitions, contracts, and explicit capabilities rather than a universal runtime model. | 2026-07-31 |
| `DEC-014` | `PID-013` | `accepted` | Applications retain thin declarative intent, selection, profile, policy, migration, and provenance truth; reusable mechanics and generic AI guidance live in versioned Program Kit capabilities; governed local guidance cannot override kernel invariants. | 2026-07-31 |
| `DEC-015` | `PID-014` | `accepted` | The portable unit is a versioned software-definition bundle with a canonical root manifest and separately governed linked design, implementation, deployment, and evidence artifacts; source code is a governed artifact rather than the canonical portable semantic unit. | 2026-07-31 |
| `DEC-016` | `PID-015`, `SEM-013` | `accepted` | Explicit capability contracts support canonical-first and provider-first intake, public-contract-only composition, support-bounded mapping, traceable normalization, provider binding until explicit migration, and fail-closed handling of incomplete or unrepresentable meaning. | 2026-07-31 |
| `DEC-017` | `PID-018` | `accepted` | Core owns contract-system mechanics; separately versioned packages own platform semantics; Program Kit ships a small first-party catalog and permits governed third-party families; canonical scope is always a named family, version, and profile. | 2026-07-31 |
| `DEC-018` | `PID-019`, `DET-010` | `accepted` | Program Kit guarantees deterministic construction from complete accepted pinned inputs and evidence-backed contract-conformant integration within declared profiles, while runtime availability, deterministic business behavior, and external systems remain outside the guarantee. | 2026-07-31 |
| `DEC-019` | `SEM-014` | `accepted` | Implementations are admitted only when governance-relevant meaning is human-approved, traceable, and supported by applicable evidence; unknown or unverified behavior may not be presented as semantically understood. | 2026-07-31 |
| `DEC-020` | `PID-012`, `PID-016`, `PID-017` | `accepted` | Program Kit is an AI-provider-neutral development tool producing ordinary deterministically constructed software with no required AI or Program Kit runtime unless selected. Accepted expression: **AI builds it. Human intent governs it.** | 2026-07-31 |
| `DEC-021` | `FTR-002`, `FTR-005`–`FTR-007` | `accepted` | Program Kit v1 begins with one exact `.NET 10 + CShells 0.0.28` construction profile with role-specific dependencies, explicit activation, conformance evidence, structured diagnostics, and explicit migration. Features may provide or require multiple capability-owned interfaces. Core terms remain non-synonymous, and components carry governed identity distinct from concrete artifacts without duplicating domain contracts. | 2026-07-31 |

## 10. Emergent-question register

New items receive the next stable ID within the relevant category and cite the
answer or tension that created them.

| Question ID | Origin | Status | Question |
|---|---|---|---|
| `PID-008` | Human separated Program Kit's consumer capabilities from the workflow used to build Program Kit itself | `accepted` | Governed by `DEC-001` and `DEC-002`; internal Spec Kit composition is separate. |
| `EXT-012` | Program Kit may internally reuse selected Spec Kit techniques | `open` | Define a governed, explicit, pinned, replaceable, non-circular internal composition model. |
| `EXT-013` | Existing Spec Kit users may benefit from invoking Program Kit at explicit handoff points | `deferred` | Outside current design; revisit only after Program Kit CLI is independently usable and published, then require measurable value and no core coupling. |
| `PID-009` | Consumers must not install a second CLI while Program Kit may reuse Spec Kit internally | `accepted` | Program Kit owns independent public contracts; optional interoperability uses those contracts. |
| `DET-010` | Human described generated applications as fully deterministic | `accepted` | Governed by `DEC-018`: deterministic construction and contract-conformant integration are distinct from runtime behavior and availability. |
| `PLN-001` | Archived planning domain retains serious product value | `open` | Define the canonical planning concepts and lifecycle relations. |
| `PLN-002` | Archived planning implementation is prior art rather than source truth | `open` | Decide which concepts to retain, re-specify, or discard. |
| `PLN-003` | Plans integrate with validations, components, and files | `open` | Define stable links and drift behavior. |
| `PLN-004` | Program Kit enables consumers to design and implement components | `open` | Define the boundary between planning artifacts, orchestration, and execution. |
| `PID-010` | Human contributor named as governing identity in `PID-001` | `accepted` | Human governs intent; currently accepted contracts govern admitted outputs until explicitly revised and reaccepted. |
| `PID-011` | Resolvable integration named as the non-negotiable promise in `PID-002` | `accepted` | Precise irreconcilability is a resolution; universal composability is not promised. |
| `PID-012` | Per-application AI instructions create inconsistent development methods and contribution friction | `accepted` | Governed by `DEC-020`: Program Kit is an AI-provider-neutral development tool producing ordinary deterministically constructed software. |
| `PID-013` | Reusable AI foundations should not be copied into every application | `accepted` | Governed by `DEC-014`: applications retain thin declarative truth; reusable guidance remains in versioned capabilities. |
| `PID-014` | NuGet analogy and cross-technology composition introduce a portability promise | `accepted` | Governed by `DEC-015`: the portable unit is a versioned software-definition bundle with a canonical root manifest. |
| `PID-015` | Target projection accepted as a deterministic development-capability mapping | `accepted` | Governed by `DEC-016`: capability mappings are explicit, public, support-bounded, traceable, and fail closed. |
| `PID-016` | The common development method should work whatever the AI model | `accepted` | Governed by `DEC-020`: public workflow contracts are provider-neutral and generated products need no AI runtime. |
| `PID-017` | Program Kit familiarity should transfer across otherwise unfamiliar applications | `accepted` | Governed by `DEC-020`: common platform contracts and development mechanics provide cross-application fluency. |
| `PID-018` | Canonical contracts should glue recurring platform concerns across provider implementations | `accepted` | Governed by `DEC-017`: core owns contract mechanics; versioned packages own platform semantics. |
| `PID-019` | Compatible middleware and token exchanges should be stable, predictable, and always working | `accepted` | Governed by `DEC-018`: no ambiguous mismatch inside the declared support envelope; external runtime failure remains possible. |
| `SEM-013` | Provider capabilities expose familiar consumer contracts before mapping to canonical contracts | `accepted` | Governed by `DEC-016`: canonical-first and provider-first intake preserve traceable meaning and migration boundaries. |
| `SEM-014` | Human governance should understand admitted implementation meaning through the semantic layer | `accepted` | Governed by `DEC-019`: admission requires human-approved, traceable, applicable evidence. |
| `FTR-014` | Bounded components evaluate against a contract | `open` | Define the required contract dimensions. |
| `FTR-015` | The generic contract/implementation/component cardinality model was rejected | `accepted` | Governed by `DEC-013`: feature and interface identities are distinct, relationships may be many-to-many, and consumers may impose stricter cardinality. |
| `FTR-016` | Consumers own architecture rules without control over Program Kit's immutable mechanics | `accepted` | Governed by `DEC-013`: the kernel owns identity, provenance, mapping, evidence, unknown-state, diagnostic, and admission integrity; consumers own architecture. |
| `FTR-017` | Program Kit v1 is specifically .NET/CShells while other targets may be supported later | `accepted` | Governed by `DEC-013`: definitions and contracts cross targets; implementations and runtime mechanics remain target-specific. |

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

### 2026-07-31 — Feature primitive refined

- Accepted `DEC-012`: CShells remains prior art and selected generation uses a
  versioned projection adapter rather than a canonical core dependency.
- Recorded the human distinction between feature contracts and concrete feature
  implementations, with all semantic dependencies targeting contracts.
- Replaced prescribed messaging mechanisms with a candidate dimensional
  interface-facet model.
- Added `FTR-015` through `FTR-017`; `FTR-003` and `FTR-004` remain follow-ups.

### 2026-07-31 — Feature Model boundary corrected

- The human rejected the generic feature-contract ontology, prescribed
  interface-role taxonomy, bridge-only domain policy, and universal cardinality
  rules as consumer architecture rather than Program Kit mechanics.
- Superseded `DEC-012` and recorded `DEC-013` as a candidate, not an accepted
  decision.
- Reframed Program Kit v1 as a thin .NET/CShells feature identity and governed
  interface boundary with consumer-owned semantic and architecture policies.
- Recorded that consumer rules and adopted defaults cannot override Program
  Kit's immutable deterministic, integrity, provenance, and diagnostic kernel.

### 2026-07-31 — Product Identity reopened for uniform AI development

- Recorded the human's product-level concern that per-application AI instruction
  foundations produce inconsistent development methods, duplicated clutter, and
  contributor friction.
- Reopened Product Identity as batch `PID-B05` and added `PID-012` through
  `PID-017` for the common protocol, local/source-truth boundary, portable
  unit, target adapters, model neutrality, and transferable contributor surface.
- Recorded the NuGet analogy and reusable WordPress adapter as intended ecosystem
  direction while retaining non-.NET targets as future stress tests rather than
  v1 implementation commitments.
- Paused Feature Model batch `FTR-B01` because its identity and adapter fields
  depend on the reopened portability boundary.
- No previously accepted decision was changed, and no new recommendation was
  marked accepted.

### 2026-07-31 — Development/runtime and platform-contract boundary refined

- Recorded that Program Kit is an AI-provider-neutral development tool whose
  outputs are ordinary software with no required AI, MCP, or Program Kit runtime.
- Recorded CShells and DI participation as .NET target mechanics; other targets
  use capability-owned native composition mechanisms.
- Recorded deterministic target projection as an accepted concept while leaving
  the exact capability mapping contract unresolved.
- Added `PID-018` for canonical platform-contract ownership and profiles and
  `PID-019` for the evidence-backed meaning of stable, predictable integration.
- Added `SEM-013` after the human distinguished provider-native consumer intake
  from traceable normalization into a canonical platform contract.
- Reframed `DET-010` around deterministic construction rather than claiming
  deterministic human judgment or runtime behavior.
- Recorded the preferred expression **AI builds it. Human intent governs it.**
  with an evidence-backed promise limited to admitted implementations.
- Added `SEM-014` for semantic coverage, admissibility, and the boundary of
  governance without routine source inspection.
- No new product decision was marked accepted.

### 2026-07-31 — Reopened Product Identity recommendations accepted

- The human explicitly accepted all six consolidated recommendations.
- Accepted `DEC-014` through `DEC-019` for application-local truth, the
  portable software-definition bundle, deterministic capability and intake
  mappings, canonical platform-contract ownership, deterministic construction
  and compatibility guarantees, and semantic admissibility.
- Accepted `DEC-020` for the refined AI-provider-neutral development-tool
  identity and the expression **AI builds it. Human intent governs it.**
- Closed `PID-B05`; all nineteen Product Identity questions are now closed.
- Marked linked `DET-010`, `SEM-013`, and `SEM-014` accepted so later
  category work must preserve their already-set boundaries.
- Resumed Feature Model batch `FTR-B01`; candidate `DEC-013` remains
  unaccepted and requires explicit convergence.

### 2026-07-31 — Thin Feature Model boundary accepted

- The human explicitly accepted all six consolidated `FTR-B01`
  recommendations.
- Accepted `DEC-013` for target-specific implemented features, scoped CShells
  host participation, separate interface/contract/intake/binding vocabulary,
  many-to-many identities, immutable kernel integrity, consumer-owned
  architecture, and software-definition-based cross-target portability.
- Completed `FTR-B01` without selecting exact CShells packages or versions;
  those remain in `FTR-002`.
- Activated `FTR-B02` for the CShells support matrix, exposed-surface
  representation, minimal terminology, and component boundary.

### 2026-07-31 — CShells and component boundary accepted

- The human explicitly accepted all four `FTR-B02` recommendations.
- Accepted `DEC-021` for the exact initial `.NET 10 + CShells 0.0.28` profile,
  explicit activation and migration, capability-owned multiple interfaces,
  non-synonymous core terminology, and separately governed component identity.
- Completed `FTR-B02` and activated `FTR-B03` for identity scope, semantic and
  implementation revisioning, typed relationships, alternative
  implementations, and deterministic selection.
