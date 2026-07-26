namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact OAuth JWT resource-server profile.</summary>
public sealed record DotNetJwtResourceServerProfile(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("scheme")] string Scheme,
    [property: JsonPropertyName("authority")] Uri Authority,
    [property: JsonPropertyName("metadataAddress")] Uri MetadataAddress,
    [property: JsonPropertyName("issuer")] string Issuer,
    [property: JsonPropertyName("audience")] string Audience,
    [property: JsonPropertyName("allowedAlgorithms")] ImmutableArray<string> AllowedAlgorithms,
    [property: JsonPropertyName("accessTokenProfile")] DotNetJwtAccessTokenProfile AccessTokenProfile,
    [property: JsonPropertyName("claimMapping")] DotNetTransportClaimMapping ClaimMapping,
    [property: JsonPropertyName("clockSkewSeconds")] int ClockSkewSeconds,
    [property: JsonPropertyName("requireHttpsMetadata")] bool RequireHttpsMetadata,
    [property: JsonPropertyName("saveToken")] bool SaveToken);
