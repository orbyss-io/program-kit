namespace Orbyss.ProgramKit.DotNet.Operations;

/// <summary>
/// Generic host projection of one owned operation and consumer-owned typed
/// schema contracts.
/// </summary>
public sealed record DotNetOperationBinding(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("projectionRevision")] ArtifactReference ProjectionRevision,
    [property: JsonPropertyName("inputSchemaRevisions")] ImmutableArray<ArtifactReference> InputSchemaRevisions,
    [property: JsonPropertyName("resultSchemaRevisions")] ImmutableArray<ArtifactReference> ResultSchemaRevisions,
    [property: JsonPropertyName("diagnosticSchemaRevisions")] ImmutableArray<ArtifactReference> DiagnosticSchemaRevisions,
    [property: JsonPropertyName("relatedOperationRevisions")] ImmutableArray<ArtifactReference> RelatedOperationRevisions);
