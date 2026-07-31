---
artifact-kind: program-kit-design-category
category: feature-model
status: active
last-updated: 2026-07-31
active-batch: FTR-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Feature Model

## 1. Category objective

Define the fundamental semantic unit Program Kit calls a feature, its relation
to interfaces and bounded software components, and the identity, versioning,
composition, implementation, and contract rules required for governed
integration.

The Feature Model must preserve the accepted Product Identity decisions:

- Program Kit produces bounded, contract-evaluated software components.
- Governed integration resolution is the non-negotiable product promise.
- The first implementation is .NET-first without treating CLR concepts as
  universal semantics.
- Program Kit owns its public contracts independently of internal tooling.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `FTR-B01` | `FTR-001`, `FTR-003`, `FTR-004` | `active` | Define the feature primitive and the meaning of “feature as interface.” |
| `FTR-B02` | `FTR-002`, `FTR-005`–`FTR-007` | `queued` | Resolve package ownership, facets, terminology, and component semantics. |
| `FTR-B03` | `FTR-008`–`FTR-012` | `queued` | Resolve identity, versioning, relations, and multiple implementations. |
| `FTR-B04` | `FTR-013`–`FTR-014` | `queued` | Define the minimum feature record and multidimensional contract set. |

`FTR-002` is conditional: its wording will change if `FTR-001` rejects a direct
dependency on CShells.

## 3. Active batch: Feature primitive

### FTR-001 — Status of `CShells.IFeature`

- **Status:** `open`
- **Question:** Is `CShells.IFeature` a canonical foundation that Program Kit
  must retain, or is it valuable prior art whose meaning must be independently
  re-specified?
- **Why it matters:** A direct foundational dependency imports another package's
  identity, versioning, lifecycle, and limitations. Rejecting it entirely could
  discard a concept proven useful in Elsa and in the origin of Program Kit.
- **Current evidence:** The founding narrative identifies `CShells.IFeature` as
  the interface beneath Elsa logical units. The archived Program Kit is
  explicitly prior art rather than source truth, and Program Kit's accepted
  public contracts must remain independently owned.
- **Recommendation:** Treat `CShells.IFeature` as important prior art, not the
  canonical Program Kit contract. Re-specify the feature semantic contract from
  first principles under Program Kit ownership. Later evaluate whether CShells
  can conform through an adapter or projection; do not make the new foundation
  depend directly on it before that evaluation.
- **Decision needed:** Accept, reject, or refine this ownership boundary.

### FTR-003 — What qualifies as a feature

- **Status:** `open`
- **Question:** Does every logical unit qualify as a governed feature, or only a
  capability that is independently identifiable, contract-bearing, selectable,
  composable, replaceable, or consumable?
- **Why it matters:** Calling every method or helper a feature makes the semantic
  graph enormous and unstable. Restricting features to large user-visible units
  would hide the internal contracts and dependencies needed for impact analysis.
- **Current evidence:** The founding intent says that underneath every logical
  unit is a feature. The accepted product identity requires bounded components
  and resolvable integration, which in turn requires stable semantic boundaries.
- **Recommendation:** A feature is any independently identifiable,
  contract-bearing capability with meaning to at least one consumer. Features
  may be internal, external, small, nested, or composed. Incidental methods,
  helpers, and code organization are implementation details unless a consumer
  depends on their governed meaning. This preserves the “every meaningful
  logical unit” insight without governing every line of code.
- **Decision needed:** Confirm whether consumer-meaning and an explicit contract
  are the threshold, or define a broader threshold.

### FTR-004 — Meaning of “every feature is an interface”

- **Status:** `open`
- **Question:** Does interface mean a literal CLR interface, or a governed
  semantic contract that may project to CLR, API, CLI, event, configuration,
  schema, and other technical interfaces?
- **Why it matters:** A literal CLR interpretation would make the semantic model
  .NET-specific and unable to describe several ways one capability meets its
  consumers. A purely abstract interpretation could become too vague to enforce.
- **Current evidence:** Product Identity is .NET-first but not semantically bound
  to CLR concepts. Features must be contract-evaluated and support governed
  integration resolution.
- **Recommendation:** “Interface” means the governed semantic boundary between a
  feature and each consumer. It has explicit contract dimensions and may project
  to one or more technical interfaces. A CLR interface is one possible .NET
  projection, not the feature's canonical identity. Every projection must trace
  back to the same feature contract and declare the facet it exposes.
- **Decision needed:** Accept, reject, or refine this semantic-interface model.

## 4. Category decisions

No Feature Model decisions have been accepted yet.
