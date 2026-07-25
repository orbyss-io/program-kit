namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>One validated result lifetime and consumer-owned rotation reaction.</summary>
public sealed record SecretConsumptionBinding(
    [property: JsonPropertyName("requestedLifetime")] SecretResultLifetime RequestedLifetime,
    [property: JsonPropertyName("consumptionShape")] SecretConsumptionShape ConsumptionShape,
    [property: JsonPropertyName("rotationRequired")] bool RotationRequired,
    [property: JsonPropertyName("reaction")] SecretConsumerReaction Reaction);
