namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Canonical product-neutral carriage for one bounded invocation result.</summary>
public sealed record OperationResultDocument(
    [property: JsonPropertyName("invocationId")] string InvocationId,
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("resultContractRevision")] ArtifactReference ResultContractRevision,
    [property: JsonPropertyName("resultDocumentRevision")] ArtifactReference ResultDocumentRevision,
    [property: JsonPropertyName("disposition")] OperationResultDisposition Disposition,
    [property: JsonPropertyName("diagnostics")] ImmutableArray<OperationDiagnosticDocument> Diagnostics,
    [property: JsonPropertyName("relatedOperationRevision")] ArtifactReference? RelatedOperationRevision);
