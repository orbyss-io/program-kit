namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact named host-policy reference without consumer-domain meaning.</summary>
public sealed record DotNetNamedHostPolicyReference(
    [property: JsonPropertyName("policyRevision")] ArtifactReference PolicyRevision,
    [property: JsonPropertyName("policyName")] string PolicyName,
    [property: JsonPropertyName("authenticationSchemes")] ImmutableArray<string> AuthenticationSchemes,
    [property: JsonPropertyName("registrationOwnership")] DotNetPolicyRegistrationOwnership RegistrationOwnership);
