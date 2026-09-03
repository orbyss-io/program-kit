# Program Kit .NET runtime and runnable-host releases

Program Kit's .NET profile uses independently packaged CShells features and an application-neutral
`ProgramKit.Host`. Selecting .NET adopts that host unless intake records an explicit opt-out. Installing
Program Kit alone never creates .NET files.

## The application-neutral host invariant

`ProgramKit.Host` compiles the CShells/Nuplane runtime and Program Kit's versioned secure-web
profile implementation. Its code is limited to:

- loading standard ASP.NET Core configuration plus consumer-owned `hostsettings.json` and `shells.json`;
- configuring Nuplane's package source and runtime loader;
- bridging Nuplane-loaded assemblies into CShells discovery;
- configuring and mapping CShells; and
- configuring authentication, common authorization/HTTP middleware, and standard BFF protocol
  endpoints from the selected `ProgramKit:Web` profile; and
- optionally triggering shell activation through `IShellRegistry`.

It does not parse a Program Kit release descriptor, inspect package or feature metadata, connect to a
database, or define feature dependency readiness. Standard authenticated web plumbing is supplied by
the host's accepted Program Kit web profile; persistence, tasks, business endpoints, and other
behavior arrive as packages through Nuplane and activate through CShells.
It remains application-neutral: no business endpoint, permission identity, data provider, or
consumer feature is compiled into the host. Its modular runtime boundary is inspired by the upstream
[`Elsa.Foundation.Host`](https://github.com/elsa-workflows/elsa-foundation/tree/main/src/Apps/Elsa.Foundation.Host).

Until CShells defines a feature-health contribution contract, Program Kit does not pretend to aggregate
feature dependencies into host readiness. Container health policy belongs to the application deployment
that knows its selected features and operational dependencies.

## Repository baseline

Run `speckit.program-kit-dotnet.sync` in write mode only after Accepted evidence selects .NET,
`ProgramKit.Host`, and the disclosed preview feeds. Root `Directory.*`, `VERSION`, `shells.json`, and
`hostsettings.json` and `NuGet.config` are scaffold-once, consumer-owned files. Program Kit hash-manages
`global.json`, `.editorconfig`, generated workflows, and `eng/program-kit`. A changed managed file is a
reported conflict, never an overwrite.

Package Source Mapping is a source-routing boundary, not a Program Kit package allowlist. The generated
`NuGet.config` routes the protected `CShells` and `Nuplane` namespaces to their approved preview feeds and
uses nuget.org as the default for other public packages. Consumers choose their direct dependencies and
may add their own private feeds with specific namespace mappings. Exact version pins, lock files,
architecture policy, vulnerability checks, and accepted decisions govern dependency selection.
Sync accepts those consumer additions when the default public route and protected namespace routes
remain intact; it reports an explicit conflict for malformed or unsafe routing.

The managed toolchain checker reads the exact SDK, Node, and npm pins, resolves their executable paths
once into `.program-kit/evidence/toolchain.json`, asks before system or network changes, installs
side-by-side where supported, and rechecks afterward. Every managed npm subprocess (OpenAPI, web tests,
and governance dependency-graph research) re-verifies and uses those exact paths rather than bare PATH
commands. npm uses `.program-kit/cache/npm`, strict TLS, and either bundled or system CA trust. Set
`PROGRAMKIT_NODE_TRUST_MODE=system` when an organization roots TLS through the OS trust store, or set
`PROGRAMKIT_NODE_EXTRA_CA_CERTS` to a reviewed PEM file; disabling strict SSL is rejected.

Managed .NET and local-tool restores explicitly use the consumer-owned, reviewed `NuGet.config`, with
package and HTTP caches below `.program-kit/cache/nuget`. The managed `global.json` selects
`Microsoft.Testing.Platform` for .NET 10 test execution, and `Build.ps1` passes the generated solution
through the MTP-aware `dotnet test --solution` form.

The common managed package baseline centrally pins the dependency-injection and logging abstraction
packages to the same 10.0.11 servicing line used by the .NET 10 profile. A package such as
Testcontainers may request an older compatible abstraction transitively, but central transitive
pinning converges the resulting consumer graph; it does not add either abstraction to projects that
do not otherwise need it.

## Feature creation and release-time closure

The authoritative activation shape remains `CShells:Shells:<shell>:Features:<feature>` in consumer-owned
`shells.json`. No runtime package is activated merely because it exists. A managed feature build emits
`program-kit/feature.json`; its package ID equals its assembly name and its host-supplied CShells/framework
abstractions are compile-time-private.

`eng/program-kit/Build.ps1` restores, builds, tests, and packs the application, then stages
`artifacts/runnable-host/` for an application image. The staging directory contains the validated runtime
NuGet closure plus `hostsettings.json` and `shells.json`. Closure, duplicate version/identity, missing
dependency, inactive feature, and route-collision failures are release-pipeline concerns. The application-neutral host
does not repeat them. Activated built-in features (`ProgramKitTasks` and `ProgramKit.DomainEvents`)
are seeded from
`ProgramKit.Packages.props` even when no consumer project needs a compile-time reference to their package.

The generated application Dockerfile derives from an approved digest-pinned `ProgramKit.Host`, copies the
staged packages into `/app/packages`, and copies the two configuration files. The generated release workflow
publishes that fully runnable image, obtains its registry digest, and emits `runnable-host.json`. That
descriptor contains only application/version provenance, image repository/tag/digest, and the exact
secret-free Nuplane/CShells configuration with hashes. `ProgramKit.Host` never consumes it.

Managed OpenAPI verification separately remains a build concern. A consumer registers contract files in
`.program-kit/openapi-contracts.json`; an empty registry does nothing and restores no exporter or npm
dependencies. Each registered contract selects the managed exporter version, shell and contributing feature
identities, the validated `artifacts/runnable-host/packages` closure, raw/canonical/baseline outputs, pinned
`oasdiff`, an isolated generator package/lock/script/output, and the consuming application package/lock/type
check. `Build.ps1` executes that chain after staging and writes hash-bound evidence. Use
`-InitializeOpenApiBaseline` only for the reviewed first baseline and `-UpdateOpenApiArtifact` only for a
reviewed generated-contract revision.

`ProgramKit.OpenApi.Exporter` is packaged as a .NET local tool (a console application with the
`programkit-openapi-export` command). Consumers do not install it globally or invoke its project directly:
the synchronized local tool manifest pins it, and `openapi_pipeline.py` restores and runs that exact local
version only when at least one OpenAPI contract is registered.

## Secure web and persistence profiles

SPA serving headers remain in the Vite/static-server adapter. The accepted web profile configures
ProgramKit.Host authentication, common authorization, and HTTP plumbing from `hostsettings.json`;
consumer `.Api` packages own endpoint permission metadata and custom protocol behavior. Production
HSTS belongs to the TLS terminator.

Persistence is opt-in through `--persistence-profile`. Provider packages are context-owned named
implementations, never the host. Core projects remain free of EF/provider types, migrations are
governed deployment artifacts rather than startup behavior, and PostgreSQL/SQL Server correctness requires
provider-representative evidence.

## Upgrade note

The next sync safely replaces an unchanged Program Kit-managed `NuGet.config` with the source-routing
baseline and then transfers it to scaffold-once consumer ownership. A consumer-modified copy remains a
reported conflict. The protected `CShells` and `Nuplane` mappings must remain intact when adding sources.

The 0.8.1 sync removes the obsolete managed application-bundle schema and builder only when their recorded
installed hashes are unchanged. A consumer-modified copy is preserved as a conflict. Existing scaffold-once
`hostsettings.json` needs review because the application-neutral host no longer injects a package path; its Nuplane feed
must name `packages` (or another deployment-owned path) explicitly.
