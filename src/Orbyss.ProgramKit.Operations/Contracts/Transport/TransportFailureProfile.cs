namespace Orbyss.ProgramKit.Operations.Contracts.Transport;

/// <summary>Finite consumer-owned transport failure catalog with one generic fallback.</summary>
public sealed record TransportFailureProfile(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("genericFallbackIdentity")] ProgramKitIdentifier GenericFallbackIdentity,
    [property: JsonPropertyName("failures")] ImmutableArray<TransportFailureContract> Failures);
