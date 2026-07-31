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
| `FTR-B01` | `FTR-001`, `FTR-003`, `FTR-004`, `FTR-015`–`FTR-017` | `active` | Refine contract, implementation, dependency, and interface-facet boundaries. |
| `FTR-B02` | `FTR-002`, `FTR-005`–`FTR-007` | `queued` | Resolve package ownership, facets, terminology, and component semantics. |
| `FTR-B03` | `FTR-008`–`FTR-012` | `queued` | Resolve identity, versioning, relations, and multiple implementations. |
| `FTR-B04` | `FTR-013`–`FTR-014` | `queued` | Define the minimum feature record and multidimensional contract set. |

`FTR-002` now concerns whether and when Program Kit ships a first-party,
version-pinned CShells projection adapter and conformance suite.

## 3. Active batch: Feature primitive

### FTR-001 — Status of `CShells.IFeature`

- **Status:** `accepted`
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
- **Human input:** The ownership recommendation was accepted, with the explicit
  requirement that deterministic CShells generation understand its syntax and
  rules through an adapter.
- **Agent synthesis:** Any selected CShells target requires an explicit,
  version-pinned projection adapter containing the syntax, conventions,
  generation rules, conformance validation, diagnostic mapping, and migration
  knowledge for supported CShells versions. The canonical Program Kit model
  remains independently owned and does not depend on that adapter.
- **Consequences and tensions:** Adapter and CShells versions become exact
  generation inputs. Projects not selecting CShells do not load the adapter.
- **Accepted decision:** `DEC-012`.

### FTR-003 — What qualifies as a feature

- **Status:** `follow-up`
- **Question:** Is a feature specifically a concrete implementation, with its
  independently identifiable capability contract modeled as a separate object?
  What is the exact cardinality among contract, feature, and component?
- **Why it matters:** Treating capability and implementation as the same object
  prevents multiple implementations and creates implementation-to-implementation
  coupling. Treating every contract as a feature hides what is actually built.
- **Human input:** A feature is an actual implementation. Interfaces specify
  contracts. Features must not consume other features directly; they work
  together through contracts. Every contract may have different implementations.
  The consumer-meaning threshold remains substantially correct.
- **Agent synthesis:** Separate three concepts: a feature contract is the stable
  semantic capability and consumer boundary; a feature implementation is a
  concrete realization of a feature contract; and a component is the packaging,
  source, or deployment boundary containing one or more implementations and
  artifacts. Semantic dependency edges target required contracts, never feature
  implementations. Methods and helpers remain implementation details.
- **Consequences and tensions:** `FTR-015` asks for the exact cardinality and
  naming rules. `FTR-016` asks how contract mediation changes across domains.
- **Decision needed:** Confirm or refine this three-concept model and the rule
  that feature implementations never depend directly on one another.

### FTR-004 — Meaning of “every feature is an interface”

- **Status:** `follow-up`
- **Question:** How should Program Kit model the roles, audiences, directions,
  and bindings of an interface without prescribing the consumer's middleware?
- **Why it matters:** Contribution points, messages, configuration, endpoints,
  and CLI commands are different semantic surfaces. MediatR, service buses, DI
  registries, HTTP, configuration providers, and CLI frameworks are mechanisms,
  not universal semantics.
- **Human input:** The semantic-boundary definition is accepted. Internal
  interfaces may provide contributions, messages, webhooks, or other roles, but
  consumer-owned domains must control their mechanics. Configuration, options,
  behavioral switches, endpoints, and CLI commands are exposed surfaces of a
  feature. The archived design over-prescribed mediator, messaging, and events.
- **Agent synthesis:** This becomes simpler by modeling interface facets along
  independent dimensions: provided or required direction; semantic role;
  audience or visibility; contract and version; and selected technical binding.
  Configuration, operations, contributions, notifications, endpoints, and
  commands are roles. CLR, HTTP, a service bus, a registry, appsettings, or a
  CLI framework are replaceable bindings. Public versus internal is an audience
  dimension, not a separate kind of feature.
- **Consequences and tensions:** Program Kit defines the stable role vocabulary,
  contracts, traces, and compatibility rules. Consumer domains or explicit
  extensions select and govern the mechanisms. `FTR-017` asks for confirmation
  of this dimensional facet model.
- **Decision needed:** Confirm or refine the role/audience/direction/binding
  separation.


### FTR-015 — Contract, feature, and component cardinality

- **Status:** `follow-up`
- **Origin:** The human separated contracts from actual feature implementations
  and noted that every contract may be implemented differently.
- **Question:** Should one feature implementation realize exactly one primary
  feature contract, may it realize several, and how many feature implementations
  may a component contain?
- **Recommendation:** One feature contract may have many alternative feature
  implementations. Each feature implementation has exactly one primary feature
  contract and may expose several interface facets under it. A component may
  package one or more feature implementations and their artifacts. A separately
  identifiable capability becomes another feature contract rather than a hidden
  secondary identity on the same feature.
- **Why it matters:** This gives selection, replacement, impact, and migration a
  stable unit while allowing one package or deployment unit to contain several
  cohesive features.
- **Decision needed:** Accept or refine this cardinality.

### FTR-016 — Contract-mediated and cross-domain dependencies

- **Status:** `follow-up`
- **Origin:** Features must not consume features directly. The human also valued
  the prohibited sibling-domain rule and explicit bridges from the Domain
  Semantic Engine design.
- **Question:** When may one bounded domain reference another domain's contracts
  directly, and when must an explicit bridge or adapter mediate them?
- **Recommendation:** No semantic edge ever targets another feature
  implementation. Within one bounded domain, implementations may require its
  governed contracts directly. Across sibling bounded domains, default to a
  consumer-owned required contract plus an explicit bridge that translates
  between both domains' contracts. Direct sharing is allowed only when both
  sides deliberately adopt a separately governed neutral or public protocol.
  Contract-only `<domain>.Core` packages may expose a domain's contracts, but do
  not by themselves authorize sibling semantic coupling.
- **Why it matters:** This retains strict domain isolation without generating
  pointless adapters when both sides genuinely share the same protocol.
- **Decision needed:** Accept this default-and-exception rule, or require a
  bridge for every sibling-domain interaction without exception.

### FTR-017 — Interface facet dimensions

- **Status:** `follow-up`
- **Origin:** The human accepted interfaces as governed semantic boundaries but
  rejected prescribing mediator, messaging, event, registry, or transport
  implementations in the Program Kit core.
- **Question:** Should every interface facet be described independently by
  direction, semantic role, audience, contract/version, and selected binding?
- **Recommendation:** Yes. Direction is provided or required. Roles initially
  include configuration, operation, query, contribution, notification,
  management, endpoint, and command, and remain explicitly versioned. Audience
  describes feature, domain, host, operator, external system, or public exposure.
  Bindings such as CLR, HTTP, service bus, registry, appsettings, or CLI are
  replaceable mechanisms selected by consumer domains or explicit extensions.
- **Why it matters:** The semantic model stays enforceable and integration-aware
  without turning Program Kit into a middleware framework.
- **Decision needed:** Accept the dimensional model; the exact initial role
  vocabulary can be refined later in `FTR-005` and `FTR-014`.
## 4. Category decisions

| Decision | Status | Summary |
|---|---|---|
| `DEC-012` | `accepted` | CShells is prior art; selected CShells generation uses an explicit, pinned projection adapter while Program Kit owns the canonical model. |
