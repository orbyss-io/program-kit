using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Configuration.Azure;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>
/// Explicit opt-in composition for built-in and exact Azure configuration
/// adapters. No assembly scanning or ambient discovery occurs.
/// </summary>
public static class DotNetAzureConfigurationProviderComposition
{
    /// <summary>Creates the exact built-in-plus-Azure provider registry.</summary>
    public static IDotNetConfigurationProviderGeneratorRegistry CreateRegistry()
    {
        DotNetConfigurationProviderComposition composition = new();
        var descriptors =
            DotNetConfigurationProviderCatalog.BuiltInDescriptors.AddRange(
                DotNetAzureConfigurationProviderCatalog.Descriptors);
        var catalog = composition.CreateCatalog(descriptors);
        var generators = DotNetConfigurationProviderCatalog.BuiltInDescriptors
            .Select(static descriptor =>
                (IDotNetConfigurationProviderGenerator)
                    new DotNetBuiltInConfigurationProviderGenerator(descriptor))
            .Concat(
                DotNetAzureConfigurationProviderCatalog.Descriptors.Select(
                    static descriptor =>
                        (IDotNetConfigurationProviderGenerator)
                            new DotNetAzureConfigurationProviderGenerator(descriptor)));
        return composition.CreateRegistry(catalog, generators);
    }
}
