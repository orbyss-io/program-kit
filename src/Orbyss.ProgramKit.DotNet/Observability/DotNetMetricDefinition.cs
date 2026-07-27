namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>One stable metric instrument with bounded dimensions.</summary>
public sealed record DotNetMetricDefinition(
    [property: JsonPropertyName("meterName")] string MeterName,
    [property: JsonPropertyName("meterVersion")] SemanticVersion MeterVersion,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("kind")] DotNetMetricInstrumentKind Kind,
    [property: JsonPropertyName("unit")] string Unit,
    [property: JsonPropertyName("description")] string Description,
    [property: JsonPropertyName("attributes")] ImmutableArray<DotNetTelemetryAttributeDefinition> Attributes);
