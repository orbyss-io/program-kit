namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Versioned wire catalog for reviewed configuration-provider descriptors.</summary>
public sealed record DotNetConfigurationProviderCatalogDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("providers")] ImmutableArray<DotNetConfigurationProviderDescriptor> Providers);
