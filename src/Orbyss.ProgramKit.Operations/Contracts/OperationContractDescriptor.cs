namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>
/// Describes one product-neutral operation contract without owning its domain
/// admission, authority conclusions, outcomes, receipts, or persistence.
/// </summary>
public sealed record OperationContractDescriptor(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("requestContractRevisions")] ImmutableArray<ArtifactReference> RequestContractRevisions,
    [property: JsonPropertyName("resultContracts")] ImmutableArray<OperationResultContract> ResultContracts,
    [property: JsonPropertyName("diagnosticContractRevisions")] ImmutableArray<ArtifactReference> DiagnosticContractRevisions,
    [property: JsonPropertyName("progressContractRevisions")] ImmutableArray<ArtifactReference> ProgressContractRevisions,
    [property: JsonPropertyName("relatedOperations")] ImmutableArray<RelatedOperationContract> RelatedOperations,
    [property: JsonPropertyName("effectContractRevision")] ArtifactReference? EffectContractRevision,
    [property: JsonPropertyName("authorityContractRevision")] ArtifactReference? AuthorityContractRevision,
    [property: JsonPropertyName("expectedRevisionPolicy")] OperationExpectedRevisionPolicy ExpectedRevisionPolicy,
    [property: JsonPropertyName("idempotencyPolicy")] OperationIdempotencyPolicy IdempotencyPolicy,
    [property: JsonPropertyName("cancellationPolicy")] OperationCancellationPolicy CancellationPolicy,
    [property: JsonPropertyName("progressPolicy")] OperationProgressPolicy ProgressPolicy,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("deprecation")] OperationDeprecation Deprecation);
