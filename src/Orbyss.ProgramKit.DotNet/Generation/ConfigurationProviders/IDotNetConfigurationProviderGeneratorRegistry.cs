using Orbyss.ProgramKit.DotNet.Configuration;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>Resolves explicitly registered configuration-provider generators by exact revision.</summary>
public interface IDotNetConfigurationProviderGeneratorRegistry
{
    /// <summary>Gets the descriptor catalog validated by this registry.</summary>
    IDotNetConfigurationProviderCatalog Catalog { get; }

    /// <summary>Resolves the exact registered generator.</summary>
    IDotNetConfigurationProviderGenerator Resolve(
        ArtifactReference providerRevision);
}
