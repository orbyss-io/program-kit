---
artifact-kind: program-kit-design-category
category: feature-model
status: active
last-updated: 2026-07-31
active-batch: FTR-B02
parent-ledger: DESIGN.md
---

# Program Kit Design — Feature Model

## 1. Category objective

Define the thinnest enforceable .NET feature model needed for Program Kit to
generate, identify, inspect, and integrate C# software through target-specific
CShells mechanics without imposing a universal runtime or consumer architecture.

The accepted boundary is:

- The portable unit is the versioned software-definition bundle governed by
  `DEC-015`, not a feature implementation or its source code.
- A feature is a target-specific implemented software unit with stable identity
  and purpose. Its record references contracts, interfaces, artifacts, target
  profiles, provenance, and evidence rather than duplicating them.
- CShells is the .NET target mechanism. A .NET feature selected for host
  participation uses the applicable CShells contract for registration and DI
  participation. Pure contract packages, infrastructure definitions, assets,
  and other non-host artifacts are not forced to implement `CShells.IFeature`.
- A contract defines versioned meaning, schema, invariants, and compatibility.
  An interface is a governed feature-to-consumer boundary that references
  contracts. Intake interfaces collect intent. Bindings map canonical meaning
  to provider, target, framework, or runtime mechanics.
- Features and interfaces have distinct identities and permit many-to-many
  relationships. Consumers may adopt stricter cardinality policies.
- Program Kit owns immutable identity, provenance, mapping, evidence, and
  diagnostic integrity. Consumers own architecture and composition policy.
- Portable software definitions and canonical contracts cross target
  boundaries; feature implementations and their runtime mechanics do not.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `FTR-B01` | `FTR-001`, `FTR-003`, `FTR-004`, `FTR-015`–`FTR-017` | `completed` | Thin target-specific feature identity, semantic boundaries, cardinality, kernel ownership, and portability accepted by `DEC-013`. |
| `FTR-B02` | `FTR-002`, `FTR-005`–`FTR-007` | `active` | Resolve the exact CShells support matrix, exposed-surface representation, terminology, and component boundary. |
| `FTR-B03` | `FTR-008`–`FTR-012` | `queued` | Resolve identity scope, versioning, relationships, and implementation selection without imposing architecture. |
| `FTR-B04` | `FTR-013`–`FTR-014` | `queued` | Define the minimum records and how consumer-defined contracts and rules are referenced. |

## 3. Accepted batch: Thin feature boundary

### FTR-001 — Exact role of `CShells.IFeature`

- **Status:** `accepted`
- **Previous state:** `DEC-012` treated CShells as prior art behind an optional
  projection adapter. A later candidate incorrectly proposed that every
  generated .NET feature must implement `CShells.IFeature`.
- **Accepted answer:** CShells is a target-specific .NET construction and host
  participation mechanism. A selected .NET host-participation profile requires
  the applicable CShells contract. Artifacts that do not participate in a host
  are not forced through that runtime marker. Program Kit owns the portable
  software definition, generation manifest, identities, provenance, and
  evidence; CShells owns the selected .NET mechanism.
- **Determinism consequence:** The CShells package, generator, SDK, rules, and
  selected target profile are exact construction inputs. `FTR-002` remains open
  for the supported version matrix, dependency placement, conformance suite,
  diagnostics, and migration policy.
- **Accepted decision:** `DEC-013`.

### FTR-003 — Minimum meaning of feature

- **Status:** `accepted`
- **Accepted answer:** A feature is a target-specific implemented software unit
  with stable identity and purpose. Its minimal record identifies its target,
  artifacts, declared provided and required interfaces, implementation
  provenance, and applicable evidence through references to separately governed
  artifacts. The feature is not the portable bundle and does not duplicate its
  design, contracts, configuration, infrastructure, or evidence.
- **Consumer boundary:** Program Kit does not intrinsically prohibit feature
  inheritance, direct feature references, cycles, nesting, or composition.
  Consumer policy may do so. Methods and helpers are not independently governed
  features unless explicitly declared or generated as such.
- **Accepted decision:** `DEC-013`.

### FTR-004 — Interface and contract vocabulary

- **Status:** `accepted`
- **Accepted axiom:** An interface is the governed semantic boundary between a
  feature and a consumer; it is not necessarily a CLR interface.
- **Accepted vocabulary:**
  - A **contract** defines versioned meaning, schema, invariants, and
    compatibility rules.
  - An **interface** is a feature's governed boundary to a consumer and
    references one or more contracts.
  - An **intake interface** collects intent from a human, AI session, or another
    capability.
  - A **canonical contract** carries normalized portable meaning within a named
    contract family, version, and profile.
  - A **binding** maps canonical meaning to provider, target, framework, or
    runtime mechanics.
- **Core boundary:** Program Kit records stable identities and explicit
  references among these objects. Contract packages and selected capabilities
  own role vocabularies, schemas, transports, provider semantics, and technical
  bindings. The core does not prescribe mediator, messaging, registry,
  configuration, endpoint, CLI, or middleware choices.
- **Accepted decision:** `DEC-013`, constrained by `DEC-016` and `DEC-017`.

### FTR-015 — Feature and interface identity cardinality

- **Status:** `accepted`
- **Accepted answer:** Features and interfaces have separate stable identities.
  A feature may provide or require multiple interfaces; an interface may
  reference multiple compatible contract facets; multiple features may
  implement the same canonical contract; and one feature may implement several
  contracts. Every implementation binding is explicit and versioned. Program
  Kit imposes no universal primary-contract or one-to-one cardinality rule.
  Consumers may adopt stricter policies.
- **Accepted decision:** `DEC-013`.

### FTR-016 — Immutable kernel and consumer policy

- **Status:** `accepted`
- **Program Kit kernel:** The kernel enforces valid unambiguous identity;
  explicit resolvable references or explicit unknown state; exact input and
  version provenance; public-contract-only capability composition; traceable
  non-lossy normalization; declared support envelopes; required artifact and
  evidence existence; explicit unknown, unsupported, incomplete, and unavailable
  states; and truthful fail-closed diagnostics and admission.
- **Consumer policy:** Consumers own architecture, inheritance, project
  structure, domain boundaries, dependency styles, messaging, middleware,
  framework choices, feature composition, and any stricter cardinality or
  relationship rules. Default policy profiles remain advisory until explicitly
  selected and version-pinned; no policy may override kernel invariants.
- **Accepted decision:** `DEC-013`, constrained by `DEC-014`, `DEC-016`,
  `DEC-018`, and `DEC-019`.

### FTR-017 — Cross-target boundary

- **Status:** `accepted`
- **Accepted answer:** Feature implementations and runtime mechanics are
  target-specific. Portable software definitions and canonical contracts cross
  target boundaries. A target capability consumes an explicit view of the
  software-definition bundle, generates target-native mechanics, and preserves
  lineage to accepted intent, contracts, inputs, and evidence.
- **Consequence:** Future React, Node, WordPress, or other targets must prove
  explicit mappings and target rules. They do not force a universal runtime
  abstraction into the .NET/CShells model.
- **Accepted decision:** `DEC-013`, constrained by `DEC-015`–`DEC-018`.

## 4. Category decisions

| Decision | Status | Summary |
|---|---|---|
| `DEC-012` | `superseded` | The optional-projection framing overgeneralized the feature model and understated CShells as the intended .NET mechanism. |
| `DEC-013` | `accepted` | Program Kit uses a thin target-specific feature model: the portable software-definition bundle is distinct from implemented features; CShells supplies selected .NET host mechanics; interfaces, contracts, intake, and bindings are distinct; feature/interface relationships are many-to-many; the kernel owns integrity while consumers own architecture; and cross-target reuse occurs through software definitions, contracts, and explicit capabilities rather than a universal runtime model. |

## 5. Active batch: CShells support and component vocabulary

`FTR-B02` now resolves the implementation-facing details that `FTR-B01`
deliberately did not decide:

- `FTR-002`: the exact supported CShells packages, generators, versions,
  dependency placement, conformance suite, diagnostics, and migrations;
- `FTR-005`: how one feature records several exposed or required surfaces
  without importing a universal role taxonomy into core;
- `FTR-006`: the minimal distinctions among feature, operation, component,
  module, package, service, extension, and application; and
- `FTR-007`: whether a component is only an artifact or packaging boundary, or
  may also carry separately governed semantic identity.

No `FTR-B02` answer is implied by accepting `DEC-013`.

## 6. Revision record

- The human rejected the generic contract/implementation/component ontology,
  built-in cross-domain bridge policy, and built-in interface-role taxonomy.
- Product Identity decisions then established the portable software-definition
  bundle, deterministic capability mappings, canonical contract ownership,
  deterministic construction, and semantic admissibility boundaries.
- The human accepted all six consolidated `FTR-B01` recommendations. `DEC-013`
  now replaces the earlier candidate with the exact thin target-specific model.
- Git history preserves rejected and superseded candidates; they are not current
  design.
