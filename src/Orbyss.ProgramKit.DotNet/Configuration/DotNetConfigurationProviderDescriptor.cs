using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Finite exact capabilities of one registered configuration provider revision.</summary>
public sealed record DotNetConfigurationProviderDescriptor(
    [property: JsonPropertyName("providerRevision")] ArtifactReference ProviderRevision,
    [property: JsonPropertyName("kind")] DotNetConfigurationProviderKind Kind,
    [property: JsonPropertyName("package")] DotNetPackageReference Package,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("supportedReloadCapabilities")] ImmutableArray<DotNetConfigurationReloadCapability> SupportedReloadCapabilities,
    [property: JsonPropertyName("reloadMechanism")] DotNetConfigurationReloadMechanism ReloadMechanism,
    [property: JsonPropertyName("developmentOnly")] bool DevelopmentOnly,
    [property: JsonPropertyName("allowedSecretClassifications")] ImmutableArray<DotNetConfigurationSecretClassification> AllowedSecretClassifications,
    [property: JsonPropertyName("limitations")] ImmutableArray<string> Limitations);
