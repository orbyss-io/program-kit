namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>A bounded, droppable, redacted, non-authoritative progress observation.</summary>
public sealed record OperationProgressDocument(
    [property: JsonPropertyName("invocationId")] string InvocationId,
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("sequence")] long Sequence,
    [property: JsonPropertyName("progressContractRevision")] ArtifactReference ProgressContractRevision,
    [property: JsonPropertyName("progressDocumentRevision")] ArtifactReference ProgressDocumentRevision);
