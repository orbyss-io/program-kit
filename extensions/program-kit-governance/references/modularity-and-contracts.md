# Modularity, DDD, and contracts

## Vocabulary

- **Bounded context**: a business-language and model-ownership boundary.
- **Core**: one context or cohesive subdomain's stable semantic surface and extension points.
- **Implementation**: activatable behavior that realizes capabilities from one or more Core projects.
- **Provider**: an implementation selected by technology or mechanism, such as PostgreSQL or Excel.
- **Bridge**: consumer-owned translation and adaptation between two contexts.
- **Helper**: opt-in reusable behavior that may depend on Core but is never required by Core.
- **Composition preset**: a convenience package selecting coherent implementations without owning
  their domain behavior.
- **Feature**: a runtime-composable capability identity and activation type exposed to a host.
- **Vertical slice**: one actor, trigger, or intent carried to an observable outcome.
- **Shell**: a runtime isolation and configuration context, such as a tenant, plan, environment, or
  plugin configuration.
- **Endpoint**: a transport adapter exposing one slice through a public protocol contract.

These concepts are related but not interchangeable. A feature identity is not a project layer, a
shell is not a bounded context, an endpoint is not a composition root, and one project may expose
more than one runtime feature. Project/package names use domain language and never add `.Feature` as
a generic segment; a feature implementation type may use the `Feature` suffix.

## Proportional domain-driven design

Use strategic DDD to discover bounded contexts, ownership, relationships, and ubiquitous language.
Use aggregates, entities, value objects, domain services, policies, lifecycle models, and semantic
capability interfaces only where business complexity warrants them. Simple transformations and CRUD
behavior may remain transaction scripts inside a well-owned slice.

Core behavior is independent of transport, persistence, serialization, dependency injection,
runtime activation, and vendor frameworks. Aggregates protect invariants and transaction boundaries.
Internal aggregates never double as public transport, integration-event, or persistence contracts.

## Core, helper, and implementation packages

An `<Application>.<Context>.Core` may own deliberately stable:

- aggregates, entities, value objects, invariants, policies, errors, and pure domain services;
- domain commands, queries, business results, lifecycle states, transitions, and domain events;
- consumer/provider capabilities, contributor contracts, registry descriptors, and capability keys;
- small dependency-light utilities whose semantics belong to the context; and
- published business-semantic boundary models intended for accepted consumers.

Core excludes runtime feature classes, DI registration, ASP.NET endpoints and wire DTOs, middleware,
ORM/provider types, persistence records and mappings, migrations, serializers, vendor SDKs, and
private implementation interfaces. Do not put a type in Core merely because two implementations use
it today.

Default activatable behavior uses the context name, such as `PriceCalculator.Catalog`. Qualify other
implementations by what they contribute: `.Api`, `.PostgreSql`, `.Import.Excel`, `.Import.Json`, or
another domain term. Use `<Application>.<Consumer>.<Provider>` for a consumer-owned bridge, such as
`PriceCalculator.Forms.Catalog`. A composition preset may reference selected implementations, but
ordinary implementations/providers/bridges never reference peer implementations.

Do not create generic `Domain`, `Contracts`, `Application`, or `Infrastructure` layer projects as the
default topology. Do not create a solution-wide `Core`, `Common`, or `Shared` dependency sink. Split a
Core into cohesive subdomains only when language, consumers, dependency weight, ownership, or change
lifecycle justifies the boundary.

## Semantic capability contracts

Core declares behavior in domain language rather than prescribing repositories, stores, units of
work, generic CRUD, or implementation technology. Prefer names such as `IActiveCatalogItemLookup`,
`ICatalogRevisionLifecycle`, and `IPriceDashboardQueries`.

The unit of abstraction is one cohesive semantic capability and replacement boundary, not one method,
table, aggregate, or current implementation class. One interface may contain multiple methods when
they share purpose, consumer audience, consistency, security, availability, owner, lifecycle, and
credible providers. Split when those axes differ, when support becomes optional, or when a provider
would naturally reject part of the interface. One concrete provider may implement several capability
interfaces.

Do not expose `DbContext`, `DbSet`, `IQueryable`, provider query expressions, storage cursors, or
transaction objects from Core. Express necessary filters, pagination, temporal rules, projections,
and atomic effects in business-semantic request/result types. Do not create an abstraction solely to
mock a framework in a unit test.

## Persistence boundaries

Provider-specific records, mappings, schemas, indexes, migrations, ORM contexts, and query plans stay
private to the provider. A provider maps those records to and from the owning domain or published
boundary model. Direct ORM mapping of a persistence-ignorant Core POCO is also valid when no provider
annotation, storage compromise, lazy-loading behavior, or schema concern shapes or escapes through
that type. The invariant is provider ignorance, not mandatory duplicate classes.

A context never accesses another context's database, schema, ORM context, persistence record, or
internal model. A materialized analytical plane may expose a semantically named query capability
while background workers and provider packages privately own how it is populated.

## Cross-context decision rule

Use a consumer-owned capability and bridge when the consumer needs a synchronous answer in its own
language, meanings differ, the provider is optional, or translation protects either side. Use a
domain event when an owner announces a fact to zero or more independent observers and does not need a
response. Use a named orchestrator/process feature when a workflow owns ordering, state, retries,
compensation, or results across contexts.

A direct Core-to-Core reference is appropriate only when:

1. the dependency is stable business language rather than implementation convenience;
2. translation would add no semantic protection;
3. the provider intentionally publishes the referenced types or capability;
4. the consumer accepts compile-time and compatibility coupling;
5. runtime optionality is not required;
6. the direction matches the accepted Context Map; and
7. an Accepted ADR and architecture test record the exact edge.

Typical valid cases are cohesive subdomains inside one bounded context, a deliberately published
upstream language adopted by a downstream context, or a small jointly owned semantic kernel. Needing
another context's internal aggregate or avoiding a small adapter is never sufficient.

## Domain and integration events

Domain events are immutable past-tense facts owned by a Core. Publish them through a lightweight
abstraction; do not inject a dispatcher into an aggregate or make event delivery part of the business
object model. Activatable implementations register awaited typed handlers. Subscribers are
independent: registration order is not a workflow contract, and an action requiring ordering or a
result belongs in an explicit capability or orchestrator.

In-process domain-event delivery is not durable. It must not claim post-commit survival, background
retry, broker delivery, or cross-process reliability. A durable requirement triggers the Integration
Events architecture backlog. The owning context maps an internal domain event into a versioned
integration contract and atomically records it with the state change through an outbox-capable
provider. Integration design must define at-least-once delivery, idempotency, ordering, retry and
dead-letter behavior, versioning, retention, replay, security, and observability.

## Dependency and ownership rules

- Core references only other explicitly accepted Core packages and lightweight abstractions.
- Helpers reference Core/helpers, never implementations.
- Implementations, providers, and bridges reference Core/helpers, never peer implementations.
- Only composition presets may reference selected runtime implementations/providers/bridges.
- Concrete inheritance is not an automatic exception to implementation isolation. A deliberately
  extensible base must live in Core or a named helper, represent genuine substitutability or an
  owned extension protocol, and have compatibility tests; ordinary reuse uses composition.
- Runtime activation or ordering metadata never grants compile-time access to implementation state.
- Cross-context shared writes, stores, or transactions require an Accepted ADR.
- Business behavior never resolves dependencies through a service locator.
- Public API, event, and schema contracts are versioned independently from internal aggregates.
- Framework registration interfaces live in deliberately lightweight framework abstractions.

## Runtime and HTTP ownership

The external host and selected Program Kit web runtime own authentication mechanisms, standard
middleware ordering, common Problem Details/correlation/security-header infrastructure, CORS and
OpenAPI infrastructure. Deployment configuration supplies provider
authority, audience, origins, claim mappings, and limits.

Each `.Api` implementation owns its route groups, wire models, endpoint-specific validation and
bounds, OpenAPI metadata, stable application permission identities, and policy/rate requirements.
Provider roles and token shapes are normalized by the host boundary; endpoints do not parse them.
Keep three owners distinct: deployment selects provider-role/scope mappings, the Program Kit
authentication feature normalizes and evaluates dynamic `permission:<identity>` policies, and the
owning application/domain capability evaluates resource/state/effect rules. Do not duplicate either
of the first two in a consumer feature. For a no-effect probe, the endpoint policy is the complete
authorization decision; for a protected business effect it is only the outer gate.
Do not create an application-root `Administration.Api` or `Platform.WebBoundary` project merely to
repeat generic host plumbing.

## Enforcement evidence

Record a Context Map, Core/module catalog, runtime feature catalog, slice catalog, semantic capability
table, event catalog, data ownership, and allowed dependency graph. `runtimeComposition` inventories
exact direct project/package references, project roles, selected feature identities, and every
capability-to-implementation binding. Enforce names, edges, cycles, public compatibility, capability
implementations, activation, provider-model leakage, endpoint authorization metadata, and data
ownership in CI.
