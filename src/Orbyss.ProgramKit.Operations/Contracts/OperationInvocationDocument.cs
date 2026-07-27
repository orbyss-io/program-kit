namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Canonical product-neutral carriage for one bounded invocation.</summary>
public sealed record OperationInvocationDocument(
    [property: JsonPropertyName("invocationId")] string InvocationId,
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("requestContractRevision")] ArtifactReference RequestContractRevision,
    [property: JsonPropertyName("requestDocumentRevision")] ArtifactReference RequestDocumentRevision,
    [property: JsonPropertyName("correlationId")] string CorrelationId,
    [property: JsonPropertyName("causationId")] string? CausationId,
    [property: JsonPropertyName("cancellationSignalId")] string? CancellationSignalId,
    [property: JsonPropertyName("expectedRevision")] ArtifactReference? ExpectedRevision,
    [property: JsonPropertyName("idempotencyKey")] string? IdempotencyKey);
