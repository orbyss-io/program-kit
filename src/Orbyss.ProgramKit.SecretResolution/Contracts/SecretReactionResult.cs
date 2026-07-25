namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Material-free report for one consumer-owned change reaction.</summary>
public sealed record SecretReactionResult(
    [property: JsonPropertyName("referenceIdentity")] ProgramKitIdentifier ReferenceIdentity,
    [property: JsonPropertyName("generation")] long Generation,
    [property: JsonPropertyName("reaction")] SecretConsumerReaction Reaction,
    [property: JsonPropertyName("status")] SecretReactionStatus Status,
    [property: JsonPropertyName("safeDiagnosticCode")] ProgramKitIdentifier? SafeDiagnosticCode);
