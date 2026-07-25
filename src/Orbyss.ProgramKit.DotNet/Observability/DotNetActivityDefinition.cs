namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>One stable activity emitted through a versioned ActivitySource.</summary>
public sealed record DotNetActivityDefinition(
    [property: JsonPropertyName("sourceName")] string SourceName,
    [property: JsonPropertyName("sourceVersion")] SemanticVersion SourceVersion,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("kind")] DotNetActivityKind Kind,
    [property: JsonPropertyName("attributes")] ImmutableArray<DotNetTelemetryAttributeDefinition> Attributes);
