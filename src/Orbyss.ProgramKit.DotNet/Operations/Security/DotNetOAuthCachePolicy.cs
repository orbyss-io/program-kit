namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Bounded in-memory cache behavior for transport security material.</summary>
public sealed record DotNetOAuthCachePolicy(
    [property: JsonPropertyName("enabled")] bool Enabled,
    [property: JsonPropertyName("expirySkewSeconds")] int ExpirySkewSeconds,
    [property: JsonPropertyName("maximumLifetimeSeconds")] int MaximumLifetimeSeconds);
