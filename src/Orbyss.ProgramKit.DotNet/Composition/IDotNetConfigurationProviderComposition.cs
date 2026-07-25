using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Creates finite configuration-provider catalogs and exact generator registries.</summary>
public interface IDotNetConfigurationProviderComposition
{
    /// <summary>Creates the reviewed built-in provider catalog.</summary>
    IDotNetConfigurationProviderCatalog CreateBuiltInCatalog();

    /// <summary>Creates the reviewed built-in provider generator registry.</summary>
    IDotNetConfigurationProviderGeneratorRegistry CreateBuiltInRegistry();

    /// <summary>Creates a catalog from an explicit finite descriptor selection.</summary>
    IDotNetConfigurationProviderCatalog CreateCatalog(
        IEnumerable<DotNetConfigurationProviderDescriptor> providers);

    /// <summary>Creates an exact registry without discovery or scanning.</summary>
    IDotNetConfigurationProviderGeneratorRegistry CreateRegistry(
        IDotNetConfigurationProviderCatalog catalog,
        IEnumerable<IDotNetConfigurationProviderGenerator> generators);
}
