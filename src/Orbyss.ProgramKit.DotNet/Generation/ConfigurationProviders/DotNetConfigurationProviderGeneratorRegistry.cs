using Orbyss.ProgramKit.DotNet.Configuration;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>Explicit exact-revision generator registry with no reflection or assembly scanning.</summary>
public sealed class DotNetConfigurationProviderGeneratorRegistry
    : IDotNetConfigurationProviderGeneratorRegistry
{
    private readonly ImmutableDictionary<ArtifactReference, IDotNetConfigurationProviderGenerator> generators;

    internal DotNetConfigurationProviderGeneratorRegistry(
        IDotNetConfigurationProviderCatalog catalog,
        ImmutableDictionary<
            ArtifactReference,
            IDotNetConfigurationProviderGenerator> generators)
    {
        Catalog = catalog;
        this.generators = generators;
    }

    /// <summary>Gets the descriptor catalog validated by this registry.</summary>
    public IDotNetConfigurationProviderCatalog Catalog { get; }

    /// <summary>Resolves the exact registered generator.</summary>
    public IDotNetConfigurationProviderGenerator Resolve(
        ArtifactReference providerRevision)
    {
        ArgumentNullException.ThrowIfNull(providerRevision);
        return generators.TryGetValue(providerRevision, out var generator)
            ? generator
            : throw new NotSupportedException(
                "PKNET008 The exact configuration provider generator is not registered.");
    }

}
