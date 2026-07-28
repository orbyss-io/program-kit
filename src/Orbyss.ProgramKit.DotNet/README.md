# Orbyss.ProgramKit.DotNet

This package contains the Program Kit's .NET 10 contracts, validation, and
deterministic source generators. Generated applications do not reference the
generator package at runtime.

## Generated typed Console hosts

Console generation accepts an Open Console document, an exact .NET binding
document, one digest-locked consumer reference assembly, and explicit
digest-locked compilation references. It verifies that every declared command
maps exactly to the consumer-owned request, handler, optional validator,
validation-result, and single CShells feature contracts before rendering.

The deterministic output is a complete executable project. It references the
consumer project in one direction and pins CShells 0.0.28,
Spectre.Console 0.55.0, and Spectre.Console.Cli 0.55.0 exactly. Per-command
settings, request factories, and Spectre commands are generated in stable
paths. Spectre owns parsing and native scalar conversion; generated settings
preserve whether each value was explicitly supplied.

The consumer owns only the referenced contracts and their implementations.
Generated runtime projects do not reference Program Kit tooling, perform
runtime source verification, or contain an untyped command-selection seam.

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

## Optional FastEndpoints projection

`DotNetFastEndpointsSelection` binds the exact compatible
`CShells.FastEndpoints` 0.0.28 and FastEndpoints 7.2.0 package pair. When an API
host selects it, the host generator projects every accepted OpenAPI operation
into one deterministic FastEndpoints endpoint and activates one generated
`IFastEndpointsShellFeature` per selected shell.

FastEndpoints remains a syntax adapter. Each projected endpoint neutralizes
FastEndpoints authorization with `AllowAnonymous()` and disables its exception
catching with `DontCatchExceptions()`. The existing generated ASP.NET Core
operation-authorization middleware, exception handlers, Problem Details
contracts, OpenAPI document, and explicit transport-failure mappings remain
authoritative.

Consumer code implements the generated
`IProgramKitFastEndpointOperationDispatcher`. It receives the exact operation
revision and current `HttpContext`, so request binding, response production,
operation behavior, and all domain meaning remain consumer-owned. Generated
applications do not reference `Orbyss.ProgramKit.DotNet` at runtime.

The mandatory source gate recognizes only the exact strong-named
FastEndpoints 7.2.0 endpoint base, Program Kit ownership header, canonical
`ProgramKitGenerated/Hosting` path, internal sealed inheritance shape, and two
required public overrides. Drift fails closed.
