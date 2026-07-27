namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Canonical compiler contract from Open Console to one consumer assembly.</summary>
public sealed record DotNetConsoleBindingDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("openConsoleDocumentRevision")]
    ArtifactReference OpenConsoleDocumentRevision,
    [property: JsonPropertyName("consumerProject")]
    DotNetConsoleConsumerProject ConsumerProject,
    [property: JsonPropertyName("featureType")]
    DotNetConsoleClrTypeDescriptor FeatureType,
    [property: JsonPropertyName("validationResultType")]
    DotNetConsoleClrTypeDescriptor ValidationResultType,
    [property: JsonPropertyName("operations")]
    ImmutableArray<DotNetConsoleOperationBinding> Operations);
