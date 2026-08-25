# Tool and integration selection

Select capabilities before products. Research current options at bootstrap time because ecosystems, compatibility, maintenance, and security change.

For each candidate record:

- capability and risk addressed;
- fit with detected technologies and architecture;
- active maintenance, release recency, license, adoption, and exit cost;
- Spec Kit compatibility and integration mechanism;
- permissions, scripts, network behavior, and supply-chain trust;
- enforcement strength and false-positive/false-negative profile;
- lifecycle trigger, version pin, upgrade test, and removal path;
- alternatives and reasons for selection or rejection.

Community Spec Kit catalogs are discovery inputs, not endorsements. Inspect extension commands, hooks, scripts, and transitive tools. Mandatory quality controls belong in deterministic CI even when Spec Kit hooks give earlier feedback.

Evaluate rather than automatically install:

- Architecture Governance for ADR/architecture artifact gates.
- ADR tooling or a local adapter when the current ADR kit adapter is incompatible.
- API Evolve when an externally versioned contract appears.
- Reqnroll BDD for valuable multistep executable examples in .NET contexts.
- ArchUnitNET for compiled .NET dependency and layering rules.
- Structurizr DSL/C4 and arc42 when architecture-as-code and navigable documentation fit.

When .NET is detected, evaluate CShells and CShells.AspNetCore when the architecture requires runtime
feature composition, per-shell or per-tenant service isolation, configuration-driven feature sets,
or dynamic activation and reload. Their presence is not a default architecture choice. Inspect the
current package maturity, supported target frameworks, abstraction/runtime package split, lifecycle,
security, routing, unload, and upgrade behavior. Pin all accepted CShells packages to one verified
version and test the composed shell graph.

Use ASP.NET Core Minimal APIs as the default built-in HTTP candidate for a .NET vertical slice when
HTTP is required. Evaluate public-schema generation and compatibility, route and operation identity,
authorization, validation, error contracts, cancellation, and OpenAPI behavior. A third-party
endpoint framework requires a separate capability gap and ADR; it is not implied by vertical slicing.

For modular dependency enforcement, evaluate a deterministic MSBuild/project-graph check and an
assembly architecture test such as ArchUnitNET. Prefer the smallest combination that can fail CI on
forbidden module and feature references, cycles, and unauthorized exceptions.
