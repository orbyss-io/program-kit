# Orbyss.ProgramKit.DotNet

This package contains the Program Kit's .NET 10 contracts, validation, and
deterministic source generators. Generated applications do not reference the
generator package at runtime.

## Generated Console command dispatch

Console host generation preserves the typed Open Console parser and adds one
host-local internal `IProgramKitConsoleCommandDispatcher`. Consumer-owned
source implements that interface and registers exactly one implementation
through the generated `Program` partial method:

```csharp
static partial void ConfigureProgramKitConsoleServices(
    IServiceCollection services)
{
    services.AddSingleton<
        IProgramKitConsoleCommandDispatcher,
        ConsumerConsoleCommandDispatcher>();
}
```

Parse failures, help, and completion return before host composition. For a
successfully parsed command, generated code builds the host, requires exactly
one dispatcher before start, starts once, dispatches once with
`IHostApplicationLifetime.ApplicationStopping`, attempts a bounded stop in
`finally`, and returns the dispatcher's integer unchanged.

The consumer owns command selection, output, exceptions, and exit-code
meaning. Missing or duplicate dispatcher registration fails closed; Program
Kit does not map consumer results. Plain service dispatch may use zero feature
activations and no CShells feature package, although dotnet-shell v11 still
requires one shell identity and the base `CShells` 0.0.28 package.

Generation emits a deterministic dispatch lock and evidence record binding the
exact Open Console document revision, dispatcher contract, parser and
parse-result digests, registration seam, lifecycle, and pass-through policy.
Generated runtime projects do not reference Program Kit tooling.

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
