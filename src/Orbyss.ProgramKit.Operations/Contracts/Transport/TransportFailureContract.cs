namespace Orbyss.ProgramKit.Operations.Contracts.Transport;

/// <summary>Explicit consumer-owned HTTP failure meaning without exception mechanics.</summary>
public sealed record TransportFailureContract(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("statusCode")] int StatusCode,
    [property: JsonPropertyName("type")] Uri Type,
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("productionDetail")] string ProductionDetail,
    [property: JsonPropertyName("developmentDetail")] string DevelopmentDetail,
    [property: JsonPropertyName("problemSchemaRevision")] ArtifactReference ProblemSchemaRevision,
    [property: JsonPropertyName("disclosure")] TransportFailureDisclosure Disclosure);
