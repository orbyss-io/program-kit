namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>A reviewed, non-sensitive, bounded telemetry attribute.</summary>
public sealed record DotNetTelemetryAttributeDefinition(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("cardinalityLimit")] int CardinalityLimit,
    [property: JsonPropertyName("allowedValues")] ImmutableArray<string> AllowedValues);
