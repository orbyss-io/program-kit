using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Configuration;

[TestClass]
public sealed class DotNetConfigurationProviderCatalogTests
{
    [TestMethod]
    public void BuiltInCatalogIsFiniteExactAndCapabilityComplete()
    {
        var catalog = DotNetTestContractFactory.ProviderCatalog();

        Assert.HasCount(7, catalog.Providers);
        Assert.AreSequenceEqual(
            new[]
            {
                DotNetConfigurationProviderKind.JsonFile,
                DotNetConfigurationProviderKind.EnvironmentVariables,
                DotNetConfigurationProviderKind.CommandLine,
                DotNetConfigurationProviderKind.InMemory,
                DotNetConfigurationProviderKind.UserSecrets,
                DotNetConfigurationProviderKind.KeyPerFile,
                DotNetConfigurationProviderKind.ChainedConfiguration,
            },
            catalog.Providers.Select(static descriptor => descriptor.Kind)
                .ToArray());
        Assert.HasCount(
            7,
            catalog.Providers
                .Select(static descriptor => descriptor.ProviderRevision)
                .Distinct()
                .ToArray());
        Assert.IsTrue(catalog.Providers.All(static descriptor =>
            descriptor.ProviderRevision.Version.Value == "10.0.10" &&
            descriptor.Package.Version.Value == "10.0.10" &&
            descriptor.GeneratorRevision.Version.Value == "1.0.0" &&
            !descriptor.Limitations.IsDefaultOrEmpty &&
            !descriptor.AllowedSecretClassifications.IsDefaultOrEmpty));
        Assert.IsFalse(catalog.Providers.Any(static descriptor =>
            descriptor.Kind ==
            DotNetConfigurationProviderKind.RegisteredAdapter));
    }

    [TestMethod]
    public void ReloadAndSecretCapabilitiesRemainProviderSpecific()
    {
        var catalog = DotNetTestContractFactory.ProviderCatalog();
        var reloadable = catalog.Providers
            .Where(static descriptor =>
                descriptor.SupportedReloadCapabilities.Contains(
                    DotNetConfigurationReloadCapability.ChangeToken))
            .Select(static descriptor => descriptor.Kind)
            .ToArray();

        Assert.AreSequenceEqual(
            new[]
            {
                DotNetConfigurationProviderKind.JsonFile,
                DotNetConfigurationProviderKind.UserSecrets,
                DotNetConfigurationProviderKind.KeyPerFile,
            },
            reloadable);
        Assert.IsTrue(catalog.Providers
            .Where(descriptor => reloadable.Contains(descriptor.Kind))
            .All(static descriptor =>
                descriptor.ReloadMechanism ==
                DotNetConfigurationReloadMechanism.FileProviderChangeToken));
        var userSecrets = catalog.Providers.Single(static descriptor =>
            descriptor.Kind == DotNetConfigurationProviderKind.UserSecrets);
        Assert.IsTrue(userSecrets.DevelopmentOnly);
        Assert.AreSequenceEqual(
            new[] { DotNetConfigurationSecretClassification.ProviderOwned },
            userSecrets.AllowedSecretClassifications.ToArray());
    }

    [TestMethod]
    public void RegistryRejectsUnknownExactRevisionWithStableDiagnostic()
    {
        var registry = DotNetTestContractFactory.ProviderRegistry();

        var exception = Assert.ThrowsExactly<NotSupportedException>(() =>
            registry.Resolve(DotNetTestContractFactory.Ref(
                "provider",
                "unknown",
                'f')));

        Assert.Contains("PKNET008", exception.Message);
    }

    [TestMethod]
    public void RegisteredAdapterRequiresExplicitCatalogAndGeneratorComposition()
    {
        var builtIn = DotNetTestContractFactory.Provider(
            DotNetConfigurationProviderKind.InMemory);
        var descriptor = builtIn with
        {
            ProviderRevision = DotNetTestContractFactory.Ref(
                "provider",
                "registered-adapter",
                '9'),
            Kind = DotNetConfigurationProviderKind.RegisteredAdapter,
        };
        DotNetConfigurationProviderComposition composition = new();
        var catalog = composition.CreateCatalog([descriptor]);
        TestConfigurationProviderGenerator generator = new(descriptor);
        var registry = composition.CreateRegistry(catalog, [generator]);

        var resolved = registry.Resolve(descriptor.ProviderRevision);

        Assert.AreSame(generator, resolved);
        Assert.AreEqual(descriptor, resolved.Descriptor);
    }

    [TestMethod]
    public void GeneratorAbiDoesNotConflateSecretResolverContracts()
    {
        var types = new[]
        {
            typeof(IDotNetConfigurationProviderGenerator),
            typeof(IDotNetConfigurationProviderGeneratorRegistry),
            typeof(IDotNetConfigurationProviderCatalog),
        };
        var exposed = types
            .SelectMany(static type =>
                type.GetMembers()
                    .Select(static member => member.ToString() ?? string.Empty))
            .ToArray();

        Assert.IsEmpty(exposed.Where(static signature =>
            signature.Contains(
                "SecretResolution",
                StringComparison.Ordinal)).ToArray());
    }
}
