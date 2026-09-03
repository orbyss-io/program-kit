# Program Kit .NET runtime and runnable-host releases

Program Kit's .NET profile uses independently packaged CShells features and a deliberately shallow
`ProgramKit.Host`. Selecting .NET adopts that host unless intake records an explicit opt-out. Installing
Program Kit alone never creates .NET files.

## The shallow-host invariant

`ProgramKit.Host` compiles only the CShells and Nuplane runtime packages. Its code is limited to:

- loading standard ASP.NET Core configuration plus consumer-owned `hostsettings.json` and `shells.json`;
- configuring Nuplane's package source and runtime loader;
- bridging Nuplane-loaded assemblies into CShells discovery;
- configuring and mapping CShells; and
- optionally triggering shell activation through `IShellRegistry`.

It does not parse a Program Kit release descriptor, inspect package or feature metadata, own application
authentication/OpenAPI, connect to a database, or define feature dependency readiness. HTTP, identity,
persistence, tasks, and similar behavior arrive as packages through Nuplane and activate through CShells.
This follows the feature-free plumbing boundary documented by the upstream
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

The managed toolchain checker reads the exact SDK and Node pins, asks before system or network changes,
installs side-by-side where supported, and rechecks afterward. Persistence remains separately opt-in; a
Nuplane package source or host setting does not select a database technology.

## Feature creation and release-time closure

The authoritative activation shape remains `CShells:Shells:<shell>:Features:<feature>` in consumer-owned
`shells.json`. No runtime package is activated merely because it exists. A managed feature build emits
`program-kit/feature.json`; its package ID equals its assembly name and its host-supplied CShells/framework
abstractions are compile-time-private.

`eng/program-kit/Build.ps1` restores, builds, tests, and packs the application, then stages
`artifacts/runnable-host/` for an application image. The staging directory contains the validated runtime
NuGet closure plus `hostsettings.json` and `shells.json`. Closure, duplicate version/identity, missing
dependency, inactive feature, and route-collision failures are release-pipeline concerns. The shallow host
does not repeat them.

The generated application Dockerfile derives from an approved digest-pinned `ProgramKit.Host`, copies the
staged packages into `/app/packages`, and copies the two configuration files. The generated release workflow
publishes that fully runnable image, obtains its registry digest, and emits `runnable-host.json`. That
descriptor contains only application/version provenance, image repository/tag/digest, and the exact
secret-free Nuplane/CShells configuration with hashes. `ProgramKit.Host` never consumes it.

Managed OpenAPI verification separately remains a build concern. Consumer-owned MSBuild properties select
deterministic generation, canonical output, an explicit first baseline, pinned `oasdiff`, and hash-bound
approval for an intentional breaking change.

## Secure web and persistence profiles

SPA serving headers remain in the Vite/static-server adapter. Server-side authentication, authorization,
OpenAPI, and operational health must be supplied by explicitly selected runtime features; they are not
compiled into `ProgramKit.Host`. Production HSTS belongs to the TLS terminator.

Persistence is opt-in through `--persistence-profile`. Provider packages belong to feature-owned
infrastructure adapters, never the host. Domain projects remain free of EF/provider types, migrations are
governed deployment artifacts rather than startup behavior, and PostgreSQL/SQL Server correctness requires
provider-representative evidence.

## Upgrade note

The next sync safely replaces an unchanged Program Kit-managed `NuGet.config` with the source-routing
baseline and then transfers it to scaffold-once consumer ownership. A consumer-modified copy remains a
reported conflict. The protected `CShells` and `Nuplane` mappings must remain intact when adding sources.

The 0.8.1 sync removes the obsolete managed application-bundle schema and builder only when their recorded
installed hashes are unchanged. A consumer-modified copy is preserved as a conflict. Existing scaffold-once
`hostsettings.json` needs review because a shallow host no longer injects a package path; its Nuplane feed
must name `packages` (or another deployment-owned path) explicitly.
