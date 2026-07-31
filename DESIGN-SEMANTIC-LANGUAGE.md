---
artifact-kind: program-kit-design-category
category: semantic-language-and-bounded-contexts
status: active
last-updated: 2026-07-31
active-batch: SEM-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Semantic Language and Bounded Contexts

## 1. Category objective

Define how human-approved meaning is represented canonically, extended by
consumers, compiled into target-specific implementations, bounded by authority
and contract scope, and proven against actual artifacts without turning Program
Kit into a universal domain language or runtime framework.

The active work must preserve these accepted constraints:

- Program Kit v1 is a semantic development toolchain, not a new programming
  language (`DEC-009`).
- The portable unit is a software-definition bundle with a canonical root
  manifest and separately governed linked artifacts (`DEC-015`).
- Core owns contract mechanics while versioned packages own platform and
  consumer semantics (`DEC-017`).
- Capability mappings support canonical-first and provider-first intake without
  silent loss of meaning (`DEC-016`).
- Only human-approved meaning supported by applicable fresh evidence is admitted
  as semantically understood (`DEC-019`, `DEC-023`).
- The kernel is the trusted non-bypassable product core; the CLI is its primary
  public application layer. Neither is an implicit generated-runtime dependency.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `SEM-B00` | `SEM-013`–`SEM-014` | `completed` | Provider/canonical intake and semantic admissibility accepted by `DEC-016` and `DEC-019`. |
| `SEM-B01` | `SEM-001`–`SEM-004`, `SEM-007`–`SEM-008` | `active` | Resolve the semantic model, authored projections, canonical representation, declarative boundary, and build/runtime presence. |
| `SEM-B02` | `SEM-005`–`SEM-006` | `queued` | Define consumer-owned vocabulary extension without core changes. |
| `SEM-B03` | `SEM-009`–`SEM-012` | `queued` | Define graph federation, cross-authority ownership, disagreement resolution, and the bounded implementation context. |

## 3. Accepted prior decisions

### SEM-013 — Provider-native and canonical intake

**Status:** `accepted`

Provider-first and canonical-first intake are both supported through explicit,
versioned, support-bounded capability contracts. Normalization is traceable and
fails closed when meaning is incomplete or cannot be represented. Provider-first
selection remains bound until an explicit migration. Governed by `DEC-016`.

### SEM-014 — Semantic admissibility

**Status:** `accepted`

Program Kit claims understanding only for governance-relevant meaning that is
human-approved, traceable to declared contracts, and supported by applicable
fresh evidence. Unknown, inferred-only, omitted, stale, drifted, or unverified
behavior remains explicit and cannot be admitted as understood. Governed by
`DEC-019` and evaluated through `DEC-023`.

## 4. Active batch: Semantic model and execution boundary

`SEM-B01` resolves:

- `SEM-001`: whether the semantic layer has a formal grammar, type system,
  validator, or compiler without contradicting the accepted non-language claim;
- `SEM-002`: the primary authored form;
- `SEM-003`: the single canonical representation behind multiple projections;
- `SEM-004`: whether governed definitions must remain declarative and
  non-Turing-complete;
- `SEM-007`: whether the semantic layer exists at build time, runtime, or both;
  and
- `SEM-008`: whether generated artifacts must carry the semantic model or may
  compile meaning into code, contracts, metadata, and evidence.

No answer is implied merely by activating this batch. Recommendations will be
recorded separately and remain unaccepted until human confirmation.

## 5. Revision record

- Created after Feature Model closed under `DEC-023`.
- Imported only accepted cross-category constraints; no queued Semantic Language
  answer was promoted silently.
