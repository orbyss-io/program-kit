namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>One exact diagnostic document and its exact governing schema.</summary>
public sealed record OperationDiagnosticDocument(
    [property: JsonPropertyName("contractRevision")] ArtifactReference ContractRevision,
    [property: JsonPropertyName("documentRevision")] ArtifactReference DocumentRevision);
