namespace Orbyss.ProgramKit.DotNet.Operations;

/// <summary>
/// .NET host projection of one canonical product-neutral operation descriptor.
/// </summary>
public sealed record DotNetOperationBinding(
    [property: JsonPropertyName("operationContract")] OperationContractDescriptor OperationContract,
    [property: JsonPropertyName("projectionRevision")] ArtifactReference ProjectionRevision)
{
    /// <summary>Gets the exact request schemas from the canonical descriptor.</summary>
    public ImmutableArray<ArtifactReference> GetInputSchemaRevisions() =>
        OperationContract.RequestContractRevisions;

    /// <summary>Gets the exact result schemas from the canonical descriptor.</summary>
    public ImmutableArray<ArtifactReference> GetResultSchemaRevisions() =>
        OperationContract.ResultContracts
            .Select(static result => result.ContractRevision)
            .ToImmutableArray();

    /// <summary>Gets exact diagnostic schemas from the canonical descriptor.</summary>
    public ImmutableArray<ArtifactReference> GetDiagnosticSchemaRevisions() =>
        OperationContract.DiagnosticContractRevisions;

    /// <summary>Gets exact related operations from the canonical descriptor.</summary>
    public ImmutableArray<ArtifactReference> GetRelatedOperationRevisions() =>
        OperationContract.RelatedOperations
            .Select(static relation => relation.OperationRevision)
            .ToImmutableArray();
}
