namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>An explicitly typed relation to another exact operation contract.</summary>
public sealed record RelatedOperationContract(
    [property: JsonPropertyName("relationId")] ProgramKitIdentifier RelationId,
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("requestContractRevision")] ArtifactReference RequestContractRevision);
