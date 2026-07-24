namespace Orbyss.ProgramKit.DotNet.Documentation;

/// <summary>Exact source and generator revisions used to project a document.</summary>
public sealed record IntegratorDocumentProvenance(
    [property: JsonPropertyName("shellRevision")] ArtifactReference ShellRevision,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("operationRevisions")] ImmutableArray<ArtifactReference> OperationRevisions);
