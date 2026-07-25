namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>One typed consumer-owned operation projected without owning its semantics.</summary>
public sealed record OpenApiOperationProjection(
    string Path,
    string Method,
    string OperationId,
    string Summary,
    ArtifactReference OperationRevision,
    ImmutableArray<ArtifactReference> InputSchemaRevisions,
    ImmutableArray<ArtifactReference> ResultSchemaRevisions,
    ImmutableArray<ArtifactReference> DiagnosticSchemaRevisions,
    ImmutableArray<ArtifactReference> RelatedOperationRevisions,
    ImmutableArray<OpenApiProblemDetailsResponseProjection> ProblemDetailsResponses = default);
