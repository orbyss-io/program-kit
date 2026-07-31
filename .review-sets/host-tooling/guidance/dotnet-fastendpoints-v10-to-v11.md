# .NET FastEndpoints migration from shell v10 to v11

Shell v11 adds one optional FastEndpoints syntax projection. Existing v10 hosts
migrate with `fastEndpoints` absent or `null` and retain their prior ASP.NET
Core and CShells behavior.

An enabled selection binds the exact Program Kit projection profile,
`CShells.FastEndpoints` 0.0.28, and the compatible FastEndpoints 7.2.0 runtime.
It is valid only for an API host that already declares the Program Kit
transport-failure and security profiles.

The accepted Operations descriptor, OpenAPI projection, named ASP.NET Core
policies, and transport-failure profile remain authoritative. Generated
FastEndpoints classes declare the exact method and route, opt out of
FastEndpoints exception catching, and neutralize its secure-by-default
endpoint behavior. The existing generated ASP.NET Core authorization middleware
and exception-handler pipeline therefore remain the sole security and
transport-failure owners.

The mandatory C# source gate recognizes only the strong-named FastEndpoints
`7.2.0.0` `EndpointWithoutRequest` contract for internal sealed, Program
Kit-owned generated endpoint sources directly below
`ProgramKitGenerated/Hosting`. Each such type implements the exact `IEndpoint`
contract and declares only `Configure()` and
`HandleAsync(CancellationToken)`. Changed package identity, source ownership,
path, accessibility, inheritance, or public behavior fails closed.

Each generated endpoint dispatches through a generated provider-neutral
interface using the exact operation revision and current `HttpContext`.
Consumer code owns request binding, response production, operation behavior,
and all domain meaning. The adapter neither generates a parallel OpenAPI
document nor infers roles, claims, permissions, scopes, or identity-provider
semantics.
