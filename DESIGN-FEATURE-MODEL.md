---
artifact-kind: program-kit-design-category
category: feature-model
status: active
last-updated: 2026-07-31
active-batch: FTR-B04
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
| `FTR-B02` | `FTR-002`, `FTR-005`–`FTR-007` | `completed` | Exact initial CShells profile, multiple-interface representation, minimal vocabulary, and component identity accepted by `DEC-021`. |
| `FTR-B03` | `FTR-008`–`FTR-012` | `completed` | Authority-scoped identity, separate semantic and implementation revisions, typed relations, alternative implementations, and deterministic resolution accepted by `DEC-022`. |
| `FTR-B04` | `FTR-013`–`FTR-014` | `active` | Define the minimum records and how consumer-defined contracts and rules are referenced. |

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
| `DEC-021` | `accepted` | Program Kit v1 begins with an exact .NET 10 and CShells 0.0.28 target profile; features may expose multiple capability-owned interfaces; feature, operation, component, application, package, module, service, and extension are not synonyms; and components have governed identity distinct from their artifacts without duplicating domain contracts. |
| `DEC-022` | `accepted` | Governed identities are authority-scoped and globally unambiguous; semantic feature and implementation revisions are distinct and immutable; relations are explicit and contract-typed; alternative contract implementations retain separate identities; and construction selection produces an exact immutable resolution lock or an actionable unavailable or ambiguous diagnostic. |

## 5. Accepted batch: CShells support and component vocabulary

`FTR-B02` resolved the implementation-facing details that `FTR-B01`
deliberately left open:

- `FTR-002`: the exact supported CShells packages, generators, versions,
  dependency placement, conformance suite, diagnostics, and migrations;
- `FTR-005`: how one feature records several exposed or required surfaces
  without importing a universal role taxonomy into core;
- `FTR-006`: the minimal distinctions among feature, operation, component,
  module, package, service, extension, and application; and
- `FTR-007`: whether a component is only an artifact or packaging boundary, or
  may also carry separately governed semantic identity.

The human accepted all four answers below; they are governed by `DEC-021`.

## 6. Accepted answers

These answers are now authoritative product design unless explicitly reopened
or superseded.

### FTR-002 — One evidence-backed CShells target profile

**Status:** `accepted`
**Accepted answer:** Program Kit v1 initially supports one exact construction
profile: `.NET 10 + CShells 0.0.28`. The profile is a versioned Program Kit
contract and pins package bytes, target framework, compiler/generator inputs,
ABI symbols, emitted syntax, and conformance expectations. A newer CShells
release creates a new profile; it never silently widens this one.

Package placement should be role-specific:

- generated non-web feature libraries reference `CShells.Abstractions 0.0.28`;
- generated web feature libraries reference
  `CShells.AspNetCore.Abstractions 0.0.28`;
- generated generic hosts reference `CShells 0.0.28`;
- generated ASP.NET Core hosts reference `CShells 0.0.28` and
  `CShells.AspNetCore 0.0.28`;
- `CShells.AspNetCore.Testing 0.0.28` is test-only when the applicable testing
  capability is selected; and
- FastEndpoints, storage providers, and other integrations are separately
  selected capability profiles, never implicit core dependencies.

Program Kit owns its generators and analyzers. Those remain build-time
dependencies and do not become runtime dependencies of generated products.
Feature abstraction packages remain declared package dependencies because their
types form part of the implemented feature ABI; full CShells runtime packages
belong only in generated hosts.

Generated hosts use an exact, profile-verified CShells invocation template and
explicit feature assembly/activation selection. Ambient discovery and syntax
copied from an unpinned source branch cannot establish conformance.

The conformance suite must prove at least restore integrity, compilation,
deterministic repeated generation, feature ABI inspection, explicit discovery,
generic-host activation, ASP.NET Core endpoint activation, declared DI
participation, negative invalid-feature cases, and structured diagnostic
results. Diagnostics preserve the Program Kit code, stage, affected identity,
profile and package revisions, evidence, cause, and actionable remediation;
an upstream exception alone is never the user-facing result.

Migration between CShells profiles is an explicit, versioned capability with
preflight and impact evidence. Program Kit never silently rewrites or upgrades a
profile. Until such a migration exists, it reports the exact unsupported edge
and preserves the old definition as readable evidence.

Evidence checked on 2026-07-31: the archived implementation had byte-level
evidence for `0.0.28`, and the official NuGet catalog still identifies `0.0.28`
as the current stable version of the four core packages. This evidence supports
the initial pin but does not make the archived architecture authoritative.

### FTR-005 — Multiple interfaces without a core surface taxonomy

**Status:** `accepted`
**Accepted answer:** Yes, one feature may provide or require any number of
interfaces simultaneously. API, CLI, worker, configuration, event, and internal
are examples owned by target or contract capabilities, not values in a closed
Program Kit enum. Core records only explicit `provides` and `requires`
references among stable feature, interface, contract, and binding identities.

An interface or binding may carry capability-owned typed facets. A single
canonical operation may therefore have HTTP and CLI bindings, while one feature
may participate in service registration, endpoints, background work, and other
mechanics. Consumer policy may require a feature to be split, but the kernel
does not infer that rule from the number or kinds of interfaces.

### FTR-006 — Minimal, non-synonymous vocabulary

**Status:** `accepted`
**Accepted answer:** Use the following minimum distinctions and do not infer
equivalence from names:

| Term | Minimum Program Kit meaning |
|---|---|
| **feature** | A target-specific implemented software unit with stable identity and purpose. |
| **operation** | An optional, contract-owned unit of invocable behavior with governed input, output, failure, and compatibility meaning. Not every interface or feature is operational. |
| **component** | A separately governed target-specific composition and delivery boundary that references its features, interfaces, artifacts, provenance, and evidence. |
| **application** | A constructed composition root that selects components, hosts, target profiles, configuration boundaries, and deployable outputs. |
| **package** | A concrete distribution artifact such as a NuGet package, npm package, archive, or container image; packaging does not create semantic identity by itself. |
| **module** | Consumer-owned architectural vocabulary with no intrinsic kernel behavior. |
| **service** | Consumer-owned domain or runtime vocabulary with no intrinsic kernel behavior; a capability may define a service profile. |
| **extension** | A Program Kit contribution/distribution concept defined by the extension system, not a synonym for feature or component. It contributes only through explicit public capability contracts. |

### FTR-007 — Component identity without duplicated domain semantics

**Status:** `accepted`
**Accepted answer:** A component is more than an artifact boundary and carries
its own stable, versioned identity, purpose, composition, target, lifecycle, and
evidence. That identity is necessary for dependency maps, release boundaries,
impact analysis, diagnostics, replacement, and migration.

A component does not automatically invent a new domain contract. It references
the features, interfaces, contracts, bindings, and artifacts it contains or
exposes. It may contain one feature, several features, or no runtime feature at
all, such as a contracts-only or infrastructure component. Cardinality and
project layout remain consumer-owned. The component descriptor is the governed
boundary; NuGet packages, assemblies, containers, source projects, manifests,
SBOMs, and documentation are its concrete artifacts.

## 7. Accepted batch: Identity, relationships, and implementation selection

`FTR-B03` resolved:

- `FTR-008`: the authority and uniqueness scope of feature identity;
- `FTR-009`: the boundary between a feature revision and an implementation
  revision;
- `FTR-010`: how nesting, composition, specialization, inheritance, and other
  feature relations are represented and validated;
- `FTR-011`: how multiple components may satisfy the same contract without
  conflating component, feature, interface, and contract identity; and
- `FTR-012`: deterministic implementation selection without ambient discovery
  or implicit best-match behavior.

The human accepted all five answers below; they are governed by `DEC-022`.

## 8. Accepted answers

These answers are now authoritative product design unless explicitly reopened
or superseded. They establish identity and resolution mechanics without
prescribing consumer architecture.

### FTR-008 — Authority-scoped identity, globally unambiguous references

**Status:** `accepted`
**Accepted answer:** Every governed object has a canonical identity that is
globally unambiguous by construction, but Program Kit does not operate a global
name registry. Identity is allocated inside an explicit authority-owned
namespace, such as a verified DNS- or URI-backed authority, and includes the
object kind and authority-local name. The complete identifier is the identity;
repository, solution, project, folder, package, and CLR names are locators or
aliases only.

A local alias may improve authoring ergonomics inside one software-definition
bundle, but it must resolve to exactly one canonical identity before validation
or construction. Moving files or repositories does not change identity.
Renaming, splitting, merging, or transferring authority requires explicit
successor, migration, or authority-transfer evidence. A retired identity is
never reassigned to unrelated meaning.

Every reference used for construction resolves to an immutable revision: the
canonical identity plus an exact version and content digest. Human-readable
version ranges may express intake constraints, but resolved construction input
is exact. The schema-design phase must pin one textual grammar and
canonicalization algorithm; this recommendation decides its authority and
uniqueness semantics, not its punctuation.

### FTR-009 — Semantic feature revision versus implementation revision

**Status:** `accepted`
**Accepted answer:** A feature identity has immutable semantic revisions, while
its code and produced artifacts have separately identified implementation
revisions. An admitted implementation revision declares and proves which exact
feature revision it realizes.

A new feature revision is required whenever governance-relevant declared
meaning changes, including purpose, provided or required interfaces, contract
revisions, compatibility claims, configuration meaning, externally observable
guarantees, security or operational guarantees, or applicable mandatory
policy. Compatibility is evaluated and recorded; it is not inferred solely from
a semantic-version label.

An implementation revision is sufficient when source, dependencies, build
inputs, optimization, or artifacts change while the approved feature meaning
and compatibility envelope remain identical and fresh evidence proves
conformance. A defect correction that restores already-declared behavior may be
implementation-only; changing the declared behavior is a feature revision.
Published feature and implementation revisions are immutable. No artifact may
silently replace another under the same version and digest identity.

### FTR-010 — Explicit, contract-typed relations

**Status:** `accepted`
**Accepted answer:** Nesting, composition, specialization, inheritance,
dependency, replacement, and other relations are neither universally allowed
nor universally forbidden. Program Kit core stores an explicit directed
relation whose record names the source revision, target identity or revision
constraint, versioned relation-contract type, provenance, and evidence.

The selected relation contract or consumer policy defines the relation's
semantics, permitted endpoint kinds, cardinality, transitivity, compatibility,
cycle policy, and impact propagation. Core enforces valid identities, resolvable
and pinned contract types, declared constraints, applicable validators,
truthful unknown state, and fail-closed diagnostics. It does not invent domain
meaning or treat differently named relations as synonyms.

CLR inheritance, project references, package dependencies, and inferred call
graphs are implementation evidence, not semantic feature relations by
themselves. A semantic specialization or dependency must be declared and
validated explicitly. Program Kit may ship opt-in default relation profiles;
they become enforceable only when selected and pinned.

### FTR-011 — Alternative contract implementations are first-class

**Status:** `accepted`
**Accepted answer:** Yes, multiple components may contain features that satisfy
the same interface and contract revision. This is required for provider
adapters such as Keycloak and Entra ID implementing a shared canonical OpenID
Connect contract.

Contract satisfaction does not make the components or features identical. Each
component, feature, implementation revision, binding, target profile, support
envelope, and evidence set retains its own identity. Conformance is evaluated
independently. Multiple candidates may coexist in a catalog or even in one
application when the application's explicit composition and runtime contracts
permit it.

Catalog presence is not activation, and satisfying the same contract does not
authorize substitution. Replacement and migration require compatibility and
impact evidence against the consuming graph.

### FTR-012 — Explicit request, deterministic resolution, immutable lock

**Status:** `accepted`
**Accepted answer:** Construction-time implementation selection uses two
separate records:

1. A human-approved selection request names the required interface or contract,
   target profile, constraints, and any provider preference.
2. A deterministic resolution lock records the exact selected component,
   feature revision, implementation revision, binding, package or artifact
   digests, capability revisions, and evidence used.

A human may select the implementation directly. Alternatively, an explicitly
adopted and version-pinned resolution policy may select it deterministically.
Such a policy is valid only inside its declared support envelope, must explain
its result, and must yield exactly one candidate. Zero candidates is
unavailable; more than one candidate is ambiguous. Both are structured
diagnostic results with candidate identities, failed constraints, evidence, and
actionable remediation—not permission to guess, choose the newest package, or
use whatever happens to be installed.

A selected profile may contain a default implementation, but selecting and
pinning that profile is the human approval of its default. Catalog discovery
only enumerates candidates. Runtime implementation switching, if desired, is a
separate consumer-owned runtime contract; it does not weaken construction-time
resolution or the immutable lock.

## 9. Active batch: Minimum records and contract evaluation

`FTR-B04`, the final currently known Feature Model batch, now resolves:

- `FTR-013`: the smallest mandatory feature definition that preserves identity,
  meaning, traceability, evaluation, and actionable diagnostics without
  duplicating linked artifacts; and
- `FTR-014`: the explicit multidimensional contract set against which a bounded
  component is evaluated without requiring every dimension for every component.

No `FTR-B04` answer is implied by accepting `DEC-022`.

## 10. Revision record

- The human rejected the generic contract/implementation/component ontology,
  built-in cross-domain bridge policy, and built-in interface-role taxonomy.
- Product Identity decisions then established the portable software-definition
  bundle, deterministic capability mappings, canonical contract ownership,
  deterministic construction, and semantic admissibility boundaries.
- The human accepted all six consolidated `FTR-B01` recommendations. `DEC-013`
  now replaces the earlier candidate with the exact thin target-specific model.
- The human accepted all four `FTR-B02` recommendations. `DEC-021` governs the
  exact initial CShells profile and component vocabulary; `FTR-B03` is active.
- The human accepted all five `FTR-B03` recommendations. `DEC-022` governs
  identity, revision, relation, alternative implementation, and resolution mechanics.
- Git history preserves rejected and superseded candidates; they are not current
  design.
