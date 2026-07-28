namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Binds one Console host to every exact typed-generation input revision.</summary>
public sealed record DotNetConsoleGenerationInputBinding(
    [property: JsonPropertyName("hostIdentity")]
    ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("bindingRevision")]
    ArtifactReference BindingRevision,
    [property: JsonPropertyName("consumerReferenceAssemblyRevision")]
    ArtifactReference ConsumerReferenceAssemblyRevision,
    [property: JsonPropertyName("compilationReferenceRevisions")]
    ImmutableArray<ArtifactReference> CompilationReferenceRevisions);
