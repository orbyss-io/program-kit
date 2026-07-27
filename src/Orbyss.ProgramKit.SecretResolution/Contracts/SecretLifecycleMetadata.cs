namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Safe, material-free lifecycle metadata for one resolved capability.</summary>
public sealed record SecretLifecycleMetadata(
    [property: JsonPropertyName("generation")] long Generation,
    [property: JsonPropertyName("status")] SecretResolutionStatus Status,
    [property: JsonPropertyName("observedAt")] DateTimeOffset ObservedAt,
    [property: JsonPropertyName("expiresAt")] DateTimeOffset? ExpiresAt);
