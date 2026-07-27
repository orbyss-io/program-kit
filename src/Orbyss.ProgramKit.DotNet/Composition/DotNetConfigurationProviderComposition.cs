using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Explicit composition boundary for configuration-provider tooling.</summary>
public sealed class DotNetConfigurationProviderComposition :
    IDotNetConfigurationProviderComposition
{
    /// <inheritdoc />
    public IDotNetConfigurationProviderCatalog CreateBuiltInCatalog() =>
        new DotNetConfigurationProviderCatalog(
            DotNetConfigurationProviderCatalog.BuiltInDescriptors);

    /// <inheritdoc />
    public IDotNetConfigurationProviderGeneratorRegistry CreateBuiltInRegistry()
    {
        var catalog = CreateBuiltInCatalog();
        return CreateRegistry(
            catalog,
            catalog.Providers.Select(static descriptor =>
                new DotNetBuiltInConfigurationProviderGenerator(descriptor)));
    }

    /// <inheritdoc />
    public IDotNetConfigurationProviderCatalog CreateCatalog(
        IEnumerable<DotNetConfigurationProviderDescriptor> providers) =>
        new DotNetConfigurationProviderCatalog(providers);

    /// <inheritdoc />
    public IDotNetConfigurationProviderGeneratorRegistry CreateRegistry(
        IDotNetConfigurationProviderCatalog catalog,
        IEnumerable<IDotNetConfigurationProviderGenerator> generators)
    {
        ArgumentNullException.ThrowIfNull(catalog);
        ArgumentNullException.ThrowIfNull(generators);
        var supplied = generators.ToImmutableArray();
        if (supplied.Any(static generator => generator is null))
        {
            throw new ArgumentException(
                "Configuration provider generators cannot contain null.",
                nameof(generators));
        }

        var builder = ImmutableDictionary.CreateBuilder<
            ArtifactReference,
            IDotNetConfigurationProviderGenerator>();
        foreach (var generator in supplied)
        {
            if (catalog.Resolve(generator.Descriptor.ProviderRevision) !=
                    generator.Descriptor ||
                !builder.TryAdd(generator.Descriptor.ProviderRevision, generator))
            {
                throw new ArgumentException(
                    "Every generator must match one exact unique catalog descriptor.",
                    nameof(generators));
            }
        }

        if (builder.Count != catalog.Providers.Length)
        {
            throw new ArgumentException(
                "Every catalog provider requires exactly one explicitly registered generator.",
                nameof(generators));
        }

        return new DotNetConfigurationProviderGeneratorRegistry(
            catalog,
            builder.ToImmutable());
    }
}
