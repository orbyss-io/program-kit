namespace Orbyss.ProgramKit.DotNet.Configuration.Azure;

/// <summary>Exact optional Azure configuration adapter composition.</summary>
public sealed record DotNetAzureConfigurationComposition(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("bindings")] ImmutableArray<DotNetAzureConfigurationBinding> Bindings);
