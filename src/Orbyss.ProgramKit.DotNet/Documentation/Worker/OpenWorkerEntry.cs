namespace Orbyss.ProgramKit.DotNet.Documentation.Worker;

/// <summary>Small operation-backed worker activation contract.</summary>
public sealed record OpenWorkerEntry(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("featureIdentity")] ProgramKitIdentifier FeatureIdentity,
    [property: JsonPropertyName("activationIdentity")] ProgramKitIdentifier ActivationIdentity,
    [property: JsonPropertyName("taskDefinitionRevision")] ArtifactReference? TaskDefinitionRevision,
    [property: JsonPropertyName("triggerKind")] string TriggerKind,
    [property: JsonPropertyName("triggerConfigurationSchemaRevision")] ArtifactReference TriggerConfigurationSchemaRevision,
    [property: JsonPropertyName("inputSchemaRevisions")] ImmutableArray<ArtifactReference> InputSchemaRevisions,
    [property: JsonPropertyName("outputSchemaRevisions")] ImmutableArray<ArtifactReference> OutputSchemaRevisions,
    [property: JsonPropertyName("errorSchemaRevisions")] ImmutableArray<ArtifactReference> ErrorSchemaRevisions,
    [property: JsonPropertyName("authorityRevision")] ArtifactReference AuthorityRevision,
    [property: JsonPropertyName("cancellationRevision")] ArtifactReference CancellationRevision,
    [property: JsonPropertyName("deprecation")] string? Deprecation,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility);
