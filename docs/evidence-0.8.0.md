# Program Kit 0.8.0 design evidence

> Withdrawn: 0.8.0 encoded an incorrect host boundary. Use the corrective 0.8.1 release and
> [architecture evidence](evidence-0.8.1.md).

Primary documentation and release metadata reviewed on 2026-09-02 ground the release decisions:

- Spec Kit 1.0.1's installed extension implementation accepts hook lists, stable-sorts ascending
  priorities, defaults `auto_execute_hooks` to true, and replaces only the updating extension's hook
  entries. Program Kit tests the installed implementation to preserve unrelated hooks idempotently.
- [ASP.NET Core build-time OpenAPI generation](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/aspnetcore-openapi?view=aspnetcore-10.0)
  uses `Microsoft.Extensions.ApiDescription.Server` and `OpenApiDocumentsDirectory`; Program Kit adds
  canonical JSON, stable operation IDs, committed-output freshness, and compatibility policy around
  that supported generation point. [oasdiff 1.29.1](https://www.oasdiff.com/whats-new) is the stable
  version pinned at review time; its `breaking` command is intended for CI compatibility gates.
- Microsoft's [DDD-oriented domain model guidance](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model)
  treats aggregates as transactional consistency boundaries, while its
  [persistence-layer guidance](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design)
  keeps persistence implementations outside the domain and notes that custom/generic repositories
  are not mandatory. This supports feature-owned ports/adapters and no shared generic repository.
- Microsoft's [DbContext guidance](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/)
  defines a short-lived, non-thread-safe unit of work. Its
  [efficient-query guidance](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying)
  recommends projections and warns that lazy loading readily creates N+1 round trips. Its
  [migration guidance](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying)
  documents reviewed scripts/bundles, pending-model checks, locking, and provider-specific
  idempotent-script limitations. These facts ground the governed EF profiles.
- Stable package metadata at release time is EF Core 10.0.11 for Microsoft providers,
  Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, Npgsql 10.0.3, and Testcontainers 4.14.0. The major
  versions are mutually compatible with the repository's .NET 10 target; no preview provider is used.
- Microsoft's [ASP.NET Core health guidance](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-10.0)
  distinguishes process liveness from dependency/startup readiness. Docker's
  [Compose startup guidance](https://docs.docker.com/compose/how-tos/startup-order/) waits on
  healthchecks rather than container creation. Program Kit therefore keeps liveness process-only,
  makes readiness dependency-aware, and uses Compose `--wait` with an application healthcheck.
- Nuplane 0.0.9-preview.61's shipped API documentation defines `HostIntegrated` as the load mode for
  application-lifetime framework integration and documents startup reconciliation as blocking until
  packages are loaded. Program Kit therefore selects that mode explicitly before eager CShells
  discovery and makes readiness wait for the eager-activation pass. Its public builder and matcher
  explicitly support an empty token for unsigned shared assemblies, while its options validator
  currently rejects that same value. The host replaces only that validator adapter for the three
  exact unsigned abstraction contracts and preserves every other Nuplane validation error.
- Microsoft's [`global.json` guidance](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json)
  documents exact SDK selection and side-by-side SDKs. Node's
  [official download page](https://nodejs.org/en/download) identifies 24.20.0 as LTS at review time.
  Program Kit reads managed pins, asks before system/network changes, installs side-by-side where
  supported, respects the selected Node manager, and rechecks exact versions.
- Vite exposes development and preview response headers through its
  [server](https://vite.dev/config/server-options#server-headers) and
  [preview](https://vite.dev/config/preview-options#preview-headers) configuration. MDN documents
  [CSP and `frame-ancestors`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP), including
  that `frame-ancestors 'none'` prevents embedding. Program Kit keeps the local adapter and production
  static-server contract aligned while assigning HSTS to the production TLS terminator.

The five-second Docker daemon timeout is a bounded Program Kit local-tooling default, not a product
availability SLO. Consumer SLOs, database/provider choices, CSP resource exceptions, and production
transport policy remain explicit architecture/deployment decisions.
