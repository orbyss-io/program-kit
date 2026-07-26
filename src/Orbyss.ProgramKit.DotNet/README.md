# Orbyss.ProgramKit.DotNet

This package contains the Program Kit's .NET 10 contracts, validation, and
deterministic source generators. Generated applications do not reference the
generator package at runtime.

## Aspire AppHost generation

`AspireAppHostGenerator` accepts one explicit `AspireAppHostDefinition` with
exact project, executable, digest-pinned container, configuration-backed
parameter, endpoint, environment binding, service-discovery reference, wait,
named-volume, and registered integration selections.

Generation produces:

- `AppHost.csproj` pinned to `Aspire.AppHost.Sdk` and
  `Aspire.Hosting.AppHost` 13.4.6;
- deterministic `Program.cs`;
- `global.json` pinned to .NET SDK 10.0.302;
- `apphost.model.json` containing the redacted low-level model shape; and
- `aspire-apphost.lock.json` containing exact portable SDK, package, source,
  selection, and input integrity.

Secret values and raw secret-reference identities are never generated.
Platform-specific Aspire dashboard and orchestration packages are selected by
the Aspire SDK during a separate human-started restore, so the portable lock
does not claim to be a universal NuGet dependency lock.

The generator never restores, discovers projects or containers, starts
resources, creates infrastructure, deploys, or assigns environment meaning.
