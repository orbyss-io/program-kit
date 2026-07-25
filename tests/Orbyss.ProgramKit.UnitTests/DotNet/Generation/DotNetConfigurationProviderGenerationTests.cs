using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConfigurationProviderGenerationTests
{
    [TestMethod]
    public void AllBuiltInsRenderDeterministicallyInExplicitOrder()
    {
        var shell = DotNetTestContractFactory.Shell();
        var sources = Sources();
        var host = shell.Hosts[0] with
        {
            ConfigurationSources = sources,
            ConfigurationBindings =
            [
                shell.Hosts[0].ConfigurationBindings[0] with
                {
                    SourceIdentities = [sources[0].Identity],
                },
            ],
        };
        shell = shell with
        {
            Hosts = shell.Hosts
                .Select(item => item.Identity == host.Identity ? host : item)
                .ToImmutableArray(),
        };
        DotNetShellValidator validator = new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            DotNetTestContractFactory.ProviderCatalog());
        DotNetConfigurationProjectionCompiler compiler = new(
            DotNetTestContractFactory.ProviderRegistry());

        var validation = validator.Validate(shell);
        var first = compiler.RenderRegistration(host);
        var second = compiler.RenderRegistration(host);

        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(static diagnostic =>
                    diagnostic.Message)));
        Assert.AreEqual(first, second);
        Assert.Contains("AddJsonFile(", first);
        Assert.Contains("AddEnvironmentVariables(", first);
        Assert.Contains("AddCommandLine(args)", first);
        Assert.Contains("AddInMemoryCollection(", first);
        Assert.Contains("AddUserSecrets(", first);
        Assert.Contains("AddKeyPerFile(", first);
        Assert.Contains("AddConfiguration(", first);
        Assert.IsFalse(first.Contains("reflection", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(first.Contains("Assembly.Load", StringComparison.Ordinal));
        Assert.IsFalse(first.Contains("GetType(", StringComparison.Ordinal));
    }

    [TestMethod]
    public void ProviderBindingsExposeLimitationsButRedactValuesAndUserSecretsId()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0] with
        {
            ConfigurationSources = Sources(),
        };
        DotNetConfigurationProjectionCompiler compiler = new(
            DotNetTestContractFactory.ProviderRegistry());

        var output = compiler.Compile(host).Single(item =>
            item.RelativePath == "configuration/provider-bindings.json");
        var text = Encoding.UTF8.GetString(output.Content.Span);

        Assert.Contains("\"reloadMechanism\"", text);
        Assert.Contains("\"limitations\"", text);
        Assert.Contains("\"userSecretsIdPresent\": true", text);
        Assert.Contains("\"initialValueKeys\"", text);
        Assert.IsFalse(text.Contains(
            "program-kit-w030-tests",
            StringComparison.Ordinal));
        Assert.IsFalse(text.Contains(
            "public-fixture-value",
            StringComparison.Ordinal));
    }

    private static ImmutableArray<DotNetConfigurationSource> Sources() =>
    [
        Source(
            DotNetConfigurationProviderKind.JsonFile,
            0,
            path: "appsettings.json",
            reload: true,
            secret: DotNetConfigurationSecretClassification.ReferencesOnly),
        Source(
            DotNetConfigurationProviderKind.EnvironmentVariables,
            1,
            prefix: "PKHT_",
            secret: DotNetConfigurationSecretClassification.ProviderOwned),
        Source(
            DotNetConfigurationProviderKind.CommandLine,
            2,
            secret: DotNetConfigurationSecretClassification.ReferencesOnly),
        Source(
            DotNetConfigurationProviderKind.InMemory,
            3,
            initialValues:
            [
                new DotNetConfigurationInitialValue(
                    "Generated:Public",
                    "public-fixture-value",
                    DotNetConfigurationValueClassification.Public),
            ]),
        Source(
            DotNetConfigurationProviderKind.UserSecrets,
            4,
            optional: true,
            reload: true,
            userSecretsId: "program-kit-w030-tests",
            secret: DotNetConfigurationSecretClassification.ProviderOwned),
        Source(
            DotNetConfigurationProviderKind.KeyPerFile,
            5,
            path: "configuration-secrets",
            optional: true,
            reload: true,
            secret: DotNetConfigurationSecretClassification.ProviderOwned),
        Source(
            DotNetConfigurationProviderKind.ChainedConfiguration,
            6,
            initialValues:
            [
                new DotNetConfigurationInitialValue(
                    "Generated:Chained",
                    "chained",
                    DotNetConfigurationValueClassification.Public),
            ]),
    ];

    private static DotNetConfigurationSource Source(
        DotNetConfigurationProviderKind kind,
        int order,
        string? path = null,
        string? prefix = null,
        ImmutableArray<DotNetConfigurationInitialValue> initialValues = default,
        string? userSecretsId = null,
        bool optional = false,
        bool reload = false,
        DotNetConfigurationSecretClassification secret =
            DotNetConfigurationSecretClassification.PublicOnly)
    {
        var descriptor = DotNetTestContractFactory.Provider(kind);
        return new DotNetConfigurationSource(
            DotNetTestContractFactory.Id(
                "configuration-source",
                string.Concat("provider-", order)),
            order,
            kind,
            descriptor.ProviderRevision,
            descriptor.Package,
            path,
            prefix,
            initialValues.IsDefault ? [] : initialValues,
            userSecretsId,
            optional,
            optional
                ? DotNetConfigurationStartupDisposition.Optional
                : DotNetConfigurationStartupDisposition.Required,
            new DotNetConfigurationReload(
                reload,
                reload
                    ? DotNetConfigurationReloadCapability.ChangeToken
                    : DotNetConfigurationReloadCapability.None,
                null,
                null),
            secret,
            optional
                ? DotNetConfigurationFailureDisposition.ContinueWithoutSource
                : DotNetConfigurationFailureDisposition.Fail);
    }
}
