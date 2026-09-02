# Program Kit 0.8.1 corrective architecture evidence

Program Kit 0.8.1 uses the upstream `Elsa.Foundation.Host` at commit
[`aba0db62de380a7029a025e23ab88bee48066f56`](https://github.com/elsa-workflows/elsa-foundation/commit/aba0db62de380a7029a025e23ab88bee48066f56)
as its concrete shallow-host comparison.

The upstream project file describes the host as pure plumbing: Nuplane supplies runtime packages and
assemblies; CShells discovers and activates them; actual persistence, HTTP, and task behavior arrives as
features. Its `Program.cs` configures the Nuplane directory feed and loader, bridges loaded assemblies to
CShells, configures CShells routing, and maps shells. Its eager-activation service depends only on
`IShellRegistry` plus configuration/logging.

Program Kit applies the narrower subset requested for its host:

- retain Nuplane setup/loading, the assembly-provider bridge, CShells configuration/routing, and
  CShells-only eager activation;
- omit Elsa features, FastEndpoints, module-management, and health endpoints;
- compile no authentication, OpenAPI, database provider, task contract, bundle parser, release descriptor,
  feature metadata, or package-closure policy into the host;
- keep package closure, feature activation validation, configuration hashing, image identity, attestations,
  and deployment evidence in application release tooling.

This is also consistent with [ASP.NET Core's standard configuration model](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/?view=aspnetcore-10.0):
`appsettings.json`, environment variants, environment variables, and command-line values are application
configuration inputs rather than a custom archive protocol. `hostsettings.json` and `shells.json` are explicit
consumer-owned additions for Nuplane/CShells composition.

The previous 0.8.0 PostgreSQL readiness implementation was not merely moved: it was deleted. Provider
selection remains an opt-in feature/infrastructure decision. Feature-health aggregation is deliberately
undefined until CShells exposes an accepted contribution interface.
