# .NET profile

Persistence is separately admitted through `../persistence-profiles.md`; no provider is selected by
this general .NET profile or by an operational database health probe.

## Baseline

When .NET is detected, evaluate and normally enforce:

- a current supported SDK/runtime policy pinned in `global.json` where appropriate;
- nullable reference types enabled;
- compiler warnings and selected Roslyn/.NET analyzers treated as errors in CI;
- explicit cancellation propagation for cancellable I/O and long-running work;
- async APIs that do not block or hide background work;
- immutable or deliberately mutable public contracts with compatibility tests;
- central package/version management and locked/repeatable restore as appropriate;
- deterministic builds, Source Link, analyzers, formatting, dependency audit, SBOM, and provenance for distributed artifacts;
- unit, integration, architecture, contract, and acceptance tests selected by risk;
- ArchUnitNET or an equivalent deterministic check when project or assembly dependency rules need executable enforcement;
- Reqnroll when business-critical multistep behavior benefits from executable examples.

Explicit intake selections and the versioned Program Kit .NET defaults are adopted through the
bootstrap assessment gate. Choices outside that reviewed baseline remain Proposed until accepted by
ADR. ORM, serializer, and test-framework details use the baseline defaults when available rather
than becoming mandatory human questions.

The exact SDK in the selected Program Kit profile's managed `global.json` is authoritative even
when `dotnet --version` reports an older or different local SDK. Treat that mismatch as an actionable
install/upgrade requirement and urge exact, side-by-side remediation. Keep the local SDK as project
truth only after the user explicitly approves the `managed-toolchain-version` override recorded by
the bootstrap decision contract; current-version research alone is not an override.

## Modular DDD topology

Apply `modularity-and-contracts.md` and `vertical-slicing.md`. A default solution graph is:

```text
external ProgramKit.Host
  -> packaged Context.Feature.* selected by shells.json
  -> accepted runtime composition packages

Context.Domain
  -> .NET and a deliberately accepted SharedKernel only

Context.Contracts
  -> .NET and a deliberately accepted SharedKernel only

Context.Feature.Name
  -> Context.Domain
  -> Context.Contracts
  -> framework abstraction packages
  -> feature-local adapters when split into internal projects
```

The external host is the composition root and loads the selected feature package closure; the
consumer repository does not create a host project unless an explicit accepted opt-out selects a
custom runtime. Peer feature roots do not reference one another. Domain and contracts projects do not reference hosts, features,
transports, persistence, dependency-injection frameworks, or vendor SDKs.

For a complex feature family, application, infrastructure, HTTP, and composition projects may be
split beneath one owned feature boundary. Those are internal parts of that feature, not peer
features. Record the internal graph and keep infrastructure dependencies pointed toward domain or
application-owned ports.

Do not create a solution-wide `Core`, `Common`, or `Shared` project as a default dependency sink.
Prefer bounded-context-specific domain and contracts projects. Keep a SharedKernel small, jointly
owned, versioned, and backed by an Accepted ADR.

## Feature references and inheritance

- Implementations of a shared interface depend on its neutral Domain, Contracts, or Abstractions
  project; they do not depend on each other.
- A concrete feature-to-feature `ProjectReference` is forbidden by default.
- Concrete inheritance does not create an exception merely for code reuse.
- A feature-family extension may reference an explicitly designed abstraction or abstract base only
  under the ownership, substitutability, ADR, and allowlist rules in `modularity-and-contracts.md`.
- `InternalsVisibleTo` is limited to tightly controlled test assemblies unless an Accepted ADR states
  a different owner and compatibility boundary.
- CI validates the MSBuild project graph and compiled assembly dependencies. Exact Accepted
  exceptions are allowlisted; naming conventions alone are insufficient enforcement.

## Program Kit host and CShells profile mapping

When .NET is selected, adopt the shallow `ProgramKit.Host` and its CShells/Nuplane composition model as the
automatic Program Kit default unless intake explicitly opts out. This default uses CShells as the
runtime composition mechanism; it does not imply that shells are tenants or bounded contexts.
Record the preview packages and package sources as a material acknowledgement in the assessment
review packet. Do not download or restore them merely by approving architecture.

Treat Package Source Mapping as source routing, not as a Program Kit dependency allowlist. The
scaffolded configuration maps the protected `CShells` and `Nuplane` namespaces to their approved
preview feeds; a generic nuget.org mapping accepts other public packages and their transitive
closures. Consumers own dependency selection and may add private sources with specific namespace
mappings. Keep dependency approval in the consumer's version pins, lock files, architecture rules,
security checks, and accepted decisions rather than requiring Program Kit to enumerate package IDs.

An explicit opt-out may select a conventional ASP.NET Core host. Record why the Program Kit host is
not suitable and which composition, packaging, task, and deployment responsibilities the project
then owns.

When accepted:

- feature projects reference `CShells.Abstractions` or, for web composition,
  `CShells.AspNetCore.Abstractions`;
- only the host/composition project references the full `CShells` and `CShells.AspNetCore` runtimes;
- the host bridges Nuplane-loaded feature assemblies into CShells and owns only its runtime configuration;
- an `IShellFeature` or `IWebShellFeature` is a composition adapter, not the domain model;
- `ConfigureServices` registers implementations of owned domain or contract interfaces and contains
  no business policy;
- feature configuration is bound to feature-owned typed options using the accepted .NET options
  mechanism, with startup validation, safe defaults, and secret-free checked-in values;
- feature constructors use only permitted root services and shell construction context; behavior
  resolves composed services only after the shell provider exists;
- CShells `DependsOn` feature metadata expresses activation ordering and availability coupling, not
  permission to reference another feature's implementation or store;
- business features normally collaborate through contracts rather than feature dependencies;
- named platform-feature dependencies are documented with optionality, ordering, failure behavior,
  and compatibility treatment;
- all CShells packages are pinned to the same researched version and exercised through composition,
  isolation, routing, reload, drain, and upgrade tests appropriate to the accepted capabilities.

Shells are runtime isolation contexts; they are not bounded contexts. Verify tenant identity,
authorization, service lifetimes, root-service copying/exclusion, configuration isolation, route
ownership, background scopes, drain semantics, and recovery before treating a shell as a security or
tenancy boundary.

## ASP.NET Core Minimal API slices

Use built-in ASP.NET Core Minimal APIs as the default HTTP candidate when a vertical slice exposes an
HTTP boundary. A web feature maps a feature-owned `RouteGroupBuilder` from
`IWebShellFeature.MapEndpoints`; each slice contributes a small mapping method and co-located wire
contracts, policies, handler/orchestration, and tests.

Require every public operation to define:

- a stable route, HTTP method, endpoint name or operation identity, and owning feature;
- explicit authorization or a deliberate anonymous decision;
- request and response wire contracts distinct from domain entities and persistence models;
- validation and trust-boundary conversion;
- success and material failure statuses with a stable error schema;
- cancellation propagation and explicit timeout, retry, idempotency, and concurrency behavior where relevant;
- OpenAPI metadata and compatibility evidence when externally consumed;
- traceability to the owning vertical slice and verification of the observable outcome.

Endpoints remain thin transport adapters. They may coordinate a simple transaction script or invoke
application/domain behavior, but they do not own business invariants. Endpoint filters handle
transport-cross-cutting concerns only and must not become a hidden domain pipeline.

Register application-wide ASP.NET Core and OpenAPI services through an explicitly selected platform feature,
not `ProgramKit.Host`. Register feature-owned implementations, validators, policies, and translators through
the feature composition adapter.
Test route collisions, shell prefixes, authorization metadata, schema generation, problem responses,
and dynamic endpoint refresh when those CShells capabilities are used.

When the application has an authenticated browser boundary, an explicitly selected web-boundary feature owns
the versioned contract in `../secure-web-profiles.md`. It registers authentication and authorization,
claims normalization, antiforgery, CORS, Problem Details, correlation, security headers, identity
readiness, and middleware ordering exactly once. Feature endpoints declare a named policy or
explicit anonymous access; they do not select schemes, parse provider claims, implement login or
logout, or return tokens.

## Domain and persistence rules

- Model aggregates and rich domain behavior only where business complexity warrants them; simple
  slices may use transaction scripts without bypassing ownership and contract rules.
- Domain types are POCOs and do not depend on ASP.NET Core, CShells, EF Core, serializers, or DI.
- Persistence mappings and migrations belong to the owning feature/module adapter.
- A feature does not expose its `DbContext`, repository implementation, entity, or database schema to
  a peer feature.
- Generic repository and unit-of-work abstractions are rejected when they erase aggregate or domain
  language.
- Cross-module reads use an owned query contract, read model, published event projection, or API.
- Cross-module writes and shared transactions require an Accepted ADR.

## Profile evidence

Re-verify package APIs and supported framework versions during project research; do not treat this
profile as a package-version pin. Primary sources accessed 2026-08-25:

- [CShells](https://www.nuget.org/packages/CShells) and
  [CShells.AspNetCore](https://www.nuget.org/packages/CShells.AspNetCore) runtime capabilities;
- [CShells.AspNetCore.Abstractions](https://www.nuget.org/packages/CShells.AspNetCore.Abstractions)
  for lightweight `IWebShellFeature` feature projects;
- [ASP.NET Core Minimal API route handlers and route groups](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/route-handlers);
- [.NET DDD domain-model guidance](https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/net-core-microservice-domain-model)
  and [infrastructure dependency guidance](https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design).

## Program Kit runtime and engineering companions

When .NET is selected, `../dotnet-engineering.md` is the mandatory language/runtime profile and
`../dotnet-runtime-and-application-bundles.md` is the mandatory CShells hosting and deployment profile.
Installing Program Kit does not select .NET and does not scaffold these files. The optional sync is not a
prerequisite for technology-neutral governance or proposed quality gates. Run
`speckit.program-kit-dotnet.sync` in write mode only after an Accepted .NET technology decision, an Accepted
ADR selecting the Program Kit host/runtime, and explicit human approval for the pinned preview packages and
preview NuGet sources. The command installs or updates the hash-tracked repository baseline. The standard
runtime is `ProgramKit.Host`; consuming repositories generate
feature packages and a digest-identified runnable application image, not a custom host project.
