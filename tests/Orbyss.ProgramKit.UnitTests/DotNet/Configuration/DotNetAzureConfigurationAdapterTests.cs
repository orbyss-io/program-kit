using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Configuration.Azure;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Configuration;

[TestClass]
public sealed class DotNetAzureConfigurationAdapterTests
{
    [TestMethod]
    public void AzureCatalogIsExactOptionalAndExplicitlyRegistered()
    {
        DotNetConfigurationProviderComposition composition = new();
        var builtIn = composition.CreateBuiltInCatalog();
        var registry = DotNetAzureConfigurationProviderComposition.CreateRegistry();

        Assert.HasCount(builtIn.Providers.Length + 1, registry.Catalog.Providers);
        Assert.AreEqual(
            DotNetAzureConfigurationProviderCatalog.KeyVault,
            registry.Catalog.Providers[^1]);
        Assert.AreEqual(
            DotNetConfigurationProviderKind.RegisteredAdapter,
            DotNetAzureConfigurationProviderCatalog.KeyVault.Kind);
        Assert.AreEqual(
            "pkid:generator:program-kit:dotnet-azure-configuration",
            DotNetAzureConfigurationProviderCatalog.KeyVault
                .GeneratorRevision.Identity.Value);
        Assert.Contains(
            DotNetConfigurationSecretClassification.ProviderOwned,
            DotNetAzureConfigurationProviderCatalog.KeyVault
                .AllowedSecretClassifications);
        Assert.IsFalse(
            builtIn.Providers.Any(static descriptor =>
                descriptor.ProviderRevision.Identity.Value.Contains(
                    "azure",
                    StringComparison.Ordinal)));
    }

    [TestMethod]
    public void ExactKeyVaultCompositionValidatesProviderPolling()
    {
        var result = Validator().Validate(
            DotNetTestContractFactory.Shell() with
            {
                Hosts = [AzureHost()],
            });

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        " ",
                        diagnostic.Message))));
    }

    [TestMethod]
    public void UnsafeCredentialAndInactiveSecretAcceptanceFailClosed()
    {
        var host = AzureHost();
        var binding = host.AzureConfiguration!.Bindings[0];
        var unsafeCredential = SecretResolutionTestContractFactory.Contract(
            SecretResultKind.ConfigurationText,
            SecretConsumerReaction.HotReplacement,
            SecretConsumptionShape.Configuration,
            true,
            SecretRotationCapability.ChangeSignal,
            SecretResultLifetime.Consumer);
        var invalid = binding with
        {
            CredentialResolution = unsafeCredential,
            KeyVault = binding.KeyVault! with
            {
                ExcludeExpiredOrNotYetValidSecrets = false,
            },
        };
        var result = Validator().Validate(
            DotNetTestContractFactory.Shell() with
            {
                Hosts =
                [
                    host with
                    {
                        AzureConfiguration = host.AzureConfiguration with
                        {
                            Bindings = [invalid],
                        },
                    },
                ],
            });

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            DotNetDiagnosticIds.UnsafeAzureConfigurationMaterial));
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.InvalidAzureConfiguration));
    }

    [TestMethod]
    public void GenerationIsDeterministicRedactedAndUsesExactKeyVaultApi()
    {
        var host = AzureHost();
        var registry = DotNetAzureConfigurationProviderComposition.CreateRegistry();
        DotNetConfigurationProjectionCompiler compiler = new(registry);

        var first = compiler.Compile(host);
        var second = compiler.Compile(host);
        var registration = compiler.RenderRegistration(host);

        Assert.AreSequenceEqual(
            first.Select(static output =>
                string.Concat(
                    output.RelativePath,
                    ":",
                    Convert.ToHexString(output.Content.ToArray())))
                .ToArray(),
            second.Select(static output =>
                string.Concat(
                    output.RelativePath,
                    ":",
                    Convert.ToHexString(output.Content.ToArray())))
                .ToArray());
        Assert.Contains("AddAzureKeyVault", registration);
        Assert.Contains("ResolveProgramKitAzureCredential", registration);
        Assert.Contains(
            "new global::System.Threading.CancellationTokenSource",
            registration);
        Assert.Contains(
            "global::System.TimeSpan.FromSeconds(15)",
            registration);
        Assert.Contains(".Token", registration);
        Assert.DoesNotContain("DefaultAzureCredential", registration);
        Assert.DoesNotContain("clientSecret", registration);
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath.Contains(
                "IActiveKeyVaultSecretPolicy",
                StringComparison.Ordinal)));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath.Contains(
                "ActiveKeyVaultSecretManager",
                StringComparison.Ordinal)));
        Assert.IsTrue(first
            .Where(static output =>
                output.RelativePath.StartsWith(
                    "configuration/azure/",
                    StringComparison.Ordinal))
            .All(static output =>
            {
                var text = System.Text.Encoding.UTF8.GetString(
                    output.Content.Span);
                return text.Contains(
                           "\"operationalMetadataRedacted\": true",
                           StringComparison.Ordinal) &&
                       !text.Contains(
                           "https://",
                           StringComparison.Ordinal);
            }));
    }

    private static DotNetShellValidator Validator()
    {
        var registry = DotNetAzureConfigurationProviderComposition.CreateRegistry();
        return new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new SecretResolutionContractValidator(),
            registry.Catalog);
    }

    private static Orbyss.ProgramKit.DotNet.Shells.DotNetHostDefinition AzureHost()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0] with
        {
            ConfigurationBindings = [],
        };
        var keyVault = new DotNetConfigurationSource(
            DotNetTestContractFactory.Id("configuration-source", "key-vault"),
            0,
            DotNetConfigurationProviderKind.RegisteredAdapter,
            DotNetAzureConfigurationProviderCatalog.KeyVault.ProviderRevision,
            DotNetAzureConfigurationProviderCatalog.KeyVault.Package,
            null,
            null,
            [],
            null,
            false,
            DotNetConfigurationStartupDisposition.Required,
            new DotNetConfigurationReload(
                true,
                DotNetConfigurationReloadCapability.ProviderPolling,
                300,
                null),
            DotNetConfigurationSecretClassification.ProviderOwned,
            DotNetConfigurationFailureDisposition.Fail);
        return host with
        {
            ConfigurationSources = [keyVault],
            AzureConfiguration = new DotNetAzureConfigurationComposition(
                DotNetTestContractFactory.Ref(
                    "profile",
                    "azure-key-vault-configuration",
                    'c'),
                DotNetAzureConfigurationProviderCatalog.KeyVault
                    .GeneratorRevision,
                [
                    new DotNetAzureConfigurationBinding(
                        keyVault.Identity,
                        DotNetAzureConfigurationProviderKind.KeyVault,
                        new Uri("https://sample.vault.azure.net/"),
                        Credential(),
                        15,
                        new DotNetAzureKeyVaultConfiguration(
                            300,
                            SecretConsumerReaction.HotReplacement,
                            true),
                        true),
                ]),
        };
    }

    private static SecretResolutionContract Credential() =>
        SecretResolutionTestContractFactory.Contract(
            SecretResultKind.CredentialHandle,
            SecretConsumerReaction.ClientRecreation,
            SecretConsumptionShape.NativeCapability,
            true,
            SecretRotationCapability.ChangeSignal,
            SecretResultLifetime.Host);
}
