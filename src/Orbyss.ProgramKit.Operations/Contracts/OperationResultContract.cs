namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Associates one exact result schema with its mechanical disposition.</summary>
public sealed record OperationResultContract(
    [property: JsonPropertyName("contractRevision")] ArtifactReference ContractRevision,
    [property: JsonPropertyName("disposition")] OperationResultDisposition Disposition);
