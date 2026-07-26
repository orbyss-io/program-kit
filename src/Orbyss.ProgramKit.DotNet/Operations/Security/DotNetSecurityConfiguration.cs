namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact ASP.NET Core transport security composition.</summary>
public sealed record DotNetSecurityConfiguration(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("defaults")] DotNetAuthenticationDefaults Defaults,
    [property: JsonPropertyName("oidcConfidentialInteractive")] DotNetOidcConfidentialInteractiveProfile? OidcConfidentialInteractive,
    [property: JsonPropertyName("jwtResourceServer")] DotNetJwtResourceServerProfile? JwtResourceServer,
    [property: JsonPropertyName("policies")] ImmutableArray<DotNetNamedHostPolicyReference> Policies,
    [property: JsonPropertyName("operationBindings")] ImmutableArray<DotNetOperationSecurityBinding> OperationBindings);
