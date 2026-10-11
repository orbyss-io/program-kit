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
First classify evidenced subdomains as Core (product differentiation), Supporting (necessary but
not differentiating), or Generic (commodity/managed mechanism). A bounded context is not a synonym
for a subdomain: draw it where a model, language, owner, lifecycle, or consistency boundary changes.
Record responsibilities, non-responsibilities, language, data, invariants, lifecycle, separation
rationale, and split triggers. Challenge boundaries named after pages, nouns, history/access, or
cross-cutting concerns unless evidence demonstrates an independently owned model.
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

<!-- program-kit:decision-rule compilation-responsibilities -->
Separate Core, runtime implementation, API and provider compilation projects when those responsibilities exist.
Core owns stable contracts and pure policies, never persistence-calling orchestration or runtime effects.
Role names, namespaces, one package or deployment do not waive separation. Declare actual responsibilities
and complete capability bindings; a graph pass establishes structural consistency, not semantic correctness.
Empty repositories and pure Core utilities need no invented runtime projects.
Features register their own services and lifecycle contributions. A provider contributes its schema
preparation through the selected existing lifecycle interface; the application owns policy/signing
admission and managed workers. Deployment configuration selects implementations. When the affected
design includes initialization, admission or managed workers, inspect the captured consumer's
versioned publisher knowledge before choosing the mechanism with `publisher_knowledge.py
--target .` and focused CShells/Foundation Tasks facts. Missing historical knowledge calls for repair of
that exact profile, never adoption of today's default.
For the reviewed Foundation Tasks 0.3.1 / CShells 0.0.30-preview.159 baseline, the provider
registers `AddShellInitializer<PrepareSchema>(LifecyclePhase.Prepare)` and owns its provider scope;
application policy/signing admission uses an explicitly ordered `Default` initializer. Foundation's
manager contributes in `Start`, awaits scoped `IStartupTask` work, then starts shell-singleton workers.
Use fresh application-owned scopes per worker iteration. Read `CShells.Abstractions --fact README.md`
and Foundation Tasks' `FoundationTasksFeature.cs` / `ShellTaskManager.cs` through the exact selected
publisher route before adapting this example to another baseline. Required preparation/admission
exceptions prevent activation; lifecycle subscribers swallow failures and cannot provide that gate.
Use explicit lifecycle phases for required ordering and failure admission, preserving scoped startup,
fresh worker scopes and bounded cancellation/drain. DI/discovery order, constructors, root
BackgroundService behavior and lifecycle notifications cannot establish required admission. Awaited
business events support independent reactions to immutable facts; subscriber order and zero-subscriber
delivery do not establish an ordered mandatory workflow. Where lifecycle contributions remove a
cross-feature call, add no new interface; otherwise define the cohesive provider-neutral capability at
its semantic boundary, keeping schema/ORM details private to the provider.
Composition is an optional reusable selection preset, not a default layer or an owner for foreign
tasks/provider initialization. Record its concrete responsibility and rationale in existing planned
responsibilities, and review its source ownership. Packaging collects selected runtime closures
directly; an aggregate library is not needed to gather dependencies.
<!-- /program-kit:decision-rule -->

Composition selects implementations; it does not contain the domain or provider implementations it selects.
A capability belongs to Core and its runtime implementation belongs to a distinct implementation,
provider or bridge project.

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
boundary model. Persistence entities are separate provider-owned types, including persistence-ignorant
POCOs used by EF. Do not directly map Core models as ORM entities. Keep their storage representation,
equality/tracking behavior and schema evolution independent of public business semantics.

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

For every cross-context edge, record upstream and downstream, Context Map patterns, synchronous
capability/event/orchestrator mode, contract and contract owner, translation/ACL policy and bridge,
data owner, consistency owner, failure owner, and atomicity. Partnership and Shared Kernel are not
neutral defaults; require explicit accepted evidence. Cross-context atomic writes remain unresolved
until an ADR justifies the consistency and failure semantics.

Managed capability coverage describes a mechanism, never automatic ownership of consumer meaning.
Program Kit Forms owns reusable schema/rendering/validation/editor/lookup/action mechanisms. A
calculator's form configuration, item references, pricing/VAT meaning, quantification visibility,
publication, and workflow are consumer semantics. Keep them in consumer-owned contexts/modules and
connect them to the mechanism through a named semantic profile and adapter/bridge.

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

### API evolution evidence

The existing OpenAPI registry, exporter, normalized baseline, oasdiff and locked client generator
remain the contract pipeline. Record affected operations, registered contracts, baseline references,
typed DTO/parser/schema checks, compatibility cases and version decisions in the existing plan/tasks.
No api-proof dossier or separate verification-plan is required. Task generation schedules contract
and compatibility checks before dependent work; it does not execute them before saving tasks.
A new API may declare an absent baseline during design, but delivery needs the generated initial baseline.
Never create a second baseline simply because evidence is stale or a compatibility check fails.

Review strict request admission and tolerant response consumption according to the supported wire
contract. Test old clients, stored snapshots, approved converters/variants, canonical identity and
denied inputs as applicable; a structural OpenAPI diff cannot prove semantic compatibility. Preserve
operation IDs, names and schema behavior during folder-only refactors. Breaking changes need the
accepted version/migration/deprecation policy and removal conditions, not a silent baseline refresh.
Keep API route/document versions, NuGet versions, persistence schema versions, form schema versions
and canonical identity versions distinct. Introduce parallel V1/V2 namespaces/routes only for an
actual supported compatibility boundary. Evaluate runtime version negotiation separately when needed.

API Evolve v1.0.0 was evaluated at upstream commit `ca528b093120d3e10c50c3a5c6179577e8264852`
on 2026-09-13. Its manifest fails the installed Spec Kit validator (`requires.speckit_version`
missing); commands/hooks are agent instruction documents, and its baseline/task/release mutations
overlap this pipeline. Do not install or invoke it as a required gate in this version. Retain the
useful compatibility questions above; reconsider adoption only with verified compatible hooks,
one baseline authority, current proof and no feature-triggered release side effects.

The external host and selected Program Kit web runtime own authentication mechanisms, standard
middleware ordering, common Problem Details/correlation/security-header infrastructure, CORS and
OpenAPI infrastructure. Deployment configuration supplies provider
authority, audience, origins, claim mappings, and limits.

Each `.Api` implementation owns its route groups, wire models, endpoint-specific validation and
bounds, OpenAPI metadata, stable application permission identities, and policy/rate requirements.
Provider roles and token shapes are normalized by the host boundary; endpoints do not parse them.
<!-- program-kit:decision-rule authorization-ownership -->
Keep three owners distinct: deployment selects provider-role/scope mappings, the Program Kit
authentication feature normalizes and evaluates dynamic `permission:<identity>` policies, and the
owning application/domain capability evaluates resource/state/effect rules. Do not duplicate either
of the first two or reparse canonical permission claims in a consumer feature. For a no-effect probe, the endpoint policy is the complete
authorization decision; for a protected business effect it is only the outer gate.
<!-- /program-kit:decision-rule -->
Do not create an application-root `Administration.Api` or `Platform.WebBoundary` project merely to
repeat generic host plumbing.

Each operation owns `Operations/<Operation>/Endpoint.cs`, its real `Request.cs` and `Response.cs`
when needed, local admission/mapping and route/metadata. Resolve endpoint instances per request with
explicit constructor dependencies; never capture scoped instances at startup. Composition assembles
operation registrations. A small/bodyless operation may remain a simple mapping with a reviewed
rationale; do not invent empty DTOs or a mediator. Peer operations do not use each other's helpers.

Use cohesive owner-specific Constants/keys types for route, schema, profile and replay identifiers;
prefer exported framework constants. Deployment limits belong to typed validated options, and
localized text to owned resources. Do not create a solution-wide Constants sink. Preserve canonical
bytes, hashes and replay versions; runtime `GetHashCode` is not a persistent identity. Large result
sections page independently and stay bounded through construction, storage, hashing and delivery.

Use public typed Foundation identity, problem contribution and JSON budget contracts when the
selected qualified version supplies them. Retained versions use named exact-version compatibility
adapters rather than private-provider conventions scattered across endpoints. Application ownership,
outcome policy and canonical ordering remain consumer semantics. Test managed and application error
paths together; unexpected programming exceptions must retain safe server-failure handling.

## Enforcement evidence

Keep ownership, semantic capability/event boundaries and dependency decisions in the existing
architecture model, plan and ADRs. Use ordinary engineering configuration such as
`eng/architecture.json` and the actual project/compiled graph for project roles, exact dependency
edges and capability bindings; no additional runtimeComposition dossier or catalog set is required.
Validate that planned graph after-plan, after-tasks and before affected implementation with
`python eng/repository_architecture.py --repository . --manifest eng/architecture.json --planned`.
List all selected owned runtime capabilities. Reject same-project bindings, relabeled Core/API roles,
EF in API/composition and `persistenceOwnerNamespaces` waivers. Actual activation, registration,
resolution and lifetime tests complement compiled interface/registration-method checks.
Enforce names, edges, cycles, public compatibility, capability
implementations, activation, provider-model leakage, endpoint authorization metadata, and data
ownership in CI.

Review serializers, native connection/deadline settings and other mechanisms hidden behind BCL-only
types explicitly in normal source review. A filename, namespace or dependency-prefix check cannot
certify semantic responsibility. Record source locations and dispositions in normal tasks/delivery
output. Upgrade diagnoses incompatible retained graphs while preserving ADRs and consumer settings;
it does not silently rewrite role authority or grant a namespace exception.
