using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetShellValidatorTests
{
    [TestMethod]
    public void ValidReviewedShellPasses()
    {
        DotNetShellValidator sut = new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

        var result = sut.Validate(DotNetTestContractFactory.Shell());

        Assert.IsTrue(result.IsValid);
    }

    [TestMethod]
    public void ProviderAbiDriftFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        shell = shell with
        {
            Composition = shell.Composition with
            {
                AbiVersion = new SemanticVersion("0.0.29"),
            },
        };
        DotNetShellValidator sut = new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

        var result = sut.Validate(shell);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidShell));
    }

    [TestMethod]
    public void PortZeroFailsClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Api);
        var health = api.Health!;
        var listener = health.Listeners[0] with { Port = 0 };
        api = api with { Health = health with { Listeners = [listener] } };
        shell = shell with
        {
            Hosts = shell.Hosts.Select(host =>
                host.Kind == DotNetHostKind.Api ? api : host).ToImmutableArray(),
        };
        DotNetShellValidator sut = new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

        var result = sut.Validate(shell);

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidHealthConfiguration));
    }

    [TestMethod]
    public void ConfigurationSourceOrderMustBeExactAndContiguous()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationSources =
            [
                host.ConfigurationSources[0] with { Order = 1 },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Path.EndsWith(
                "/configurationSources/order",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void RequiredOptionsMustValidateOnStartup()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    ValidateOnStart = false,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Path.EndsWith(
                "/validateOnStart",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void SnapshotOptionsCannotFlowIntoSingletonConsumer()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    Consumption = DotNetOptionsConsumption.Snapshot,
                    ConsumerLifetime = DotNetServiceLifetime.Singleton,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Message.Contains("IOptionsSnapshot", StringComparison.Ordinal)));
    }

    [TestMethod]
    public void MonitorAcceptsChangeTokenAndSingletonConsumer()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    Consumption = DotNetOptionsConsumption.Monitor,
                    ConsumerLifetime = DotNetServiceLifetime.Singleton,
                    ChangeReaction =
                        DotNetConfigurationChangeReaction.RedactedDiagnostic,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static item => item.Message)));
    }

    [TestMethod]
    public void MonitorRejectsSourceWithoutReloadSignal()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var environmentProvider = DotNetTestContractFactory.Provider(
            DotNetConfigurationProviderKind.EnvironmentVariables);
        var source = host.ConfigurationSources[0] with
        {
            ProviderKind = DotNetConfigurationProviderKind.EnvironmentVariables,
            ProviderRevision = environmentProvider.ProviderRevision,
            Package = environmentProvider.Package,
            Path = null,
            Prefix = "SAMPLE_",
            Reload = new DotNetConfigurationReload(
                false,
                DotNetConfigurationReloadCapability.None,
                null,
                null),
        };
        host = host with
        {
            ConfigurationSources = [source],
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    SourceIdentities = [source.Identity],
                    Consumption = DotNetOptionsConsumption.Monitor,
                    ChangeReaction =
                        DotNetConfigurationChangeReaction.RedactedDiagnostic,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Message.Contains("IOptionsMonitor", StringComparison.Ordinal)));
    }

    [TestMethod]
    public void MonitorRejectsRestartRequiredTopology()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    Consumption = DotNetOptionsConsumption.Monitor,
                    ChangeReaction =
                        DotNetConfigurationChangeReaction.RedactedDiagnostic,
                    RestartRequired = true,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Path.EndsWith(
                "/restartRequired",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void SensitiveAndReferenceValuesCannotLeakIntoGeneratedExamples()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var binding = host.ConfigurationBindings[0];
        var property = binding.Definition.Properties[0] with
        {
            Classification =
                DotNetConfigurationValueClassification.SecretReference,
        };
        binding = binding with
        {
            Definition = binding.Definition with { Properties = [property] },
        };
        host = host with { ConfigurationBindings = [binding] };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Message.Contains(
                "secret references",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void NamedOptionsMayReuseOneExactDefinitionRevision()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0],
                host.ConfigurationBindings[0] with
                {
                    OptionsName = "secondary",
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.IsValid, string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic => diagnostic.Message)));
    }

    [TestMethod]
    public void OneDefinitionRevisionCannotCarryConflictingContent()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0],
                host.ConfigurationBindings[0] with
                {
                    OptionsName = "secondary",
                    Definition = host.ConfigurationBindings[0].Definition with
                    {
                        Section = "ConflictingSection",
                    },
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "conflicting owner-authored content",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void ProviderPathCannotCollideWithGeneratedOwnershipArtifact()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationSources =
            [
                host.ConfigurationSources[0] with
                {
                    Path = "configuration/ownership.json",
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "cannot collide",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void NumericDefaultsMustBeSafeJsonAndCSharpLiterals()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var binding = host.ConfigurationBindings[0];
        var property = binding.Definition.Properties[0] with
        {
            ValueKind = DotNetConfigurationValueKind.DecimalNumber,
            DefaultValue = "1,000",
            ExampleValue = null,
        };
        binding = binding with
        {
            Definition = binding.Definition with
            {
                Properties = [property],
            },
        };
        host = host with { ConfigurationBindings = [binding] };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "parse exactly",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void UnknownProviderRevisionFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        host = host with
        {
            ConfigurationSources =
            [
                host.ConfigurationSources[0] with
                {
                    ProviderRevision = DotNetTestContractFactory.Ref(
                        "provider",
                        "unknown",
                        'f'),
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            DotNetDiagnosticIds.UnknownConfigurationProvider));
    }

    [TestMethod]
    public void ProviderPackageDriftFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var source = host.ConfigurationSources[0];
        host = host with
        {
            ConfigurationSources =
            [
                source with
                {
                    Package = source.Package with
                    {
                        Sha256 = new Sha256Digest(
                            string.Concat("sha256:", new string('f', 64))),
                    },
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            DotNetDiagnosticIds.ConfigurationProviderPackageMismatch));
    }

    [TestMethod]
    public void UnsupportedReloadFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var descriptor = DotNetTestContractFactory.Provider(
            DotNetConfigurationProviderKind.EnvironmentVariables);
        host = host with
        {
            ConfigurationSources =
            [
                host.ConfigurationSources[0] with
                {
                    ProviderKind =
                        DotNetConfigurationProviderKind.EnvironmentVariables,
                    ProviderRevision = descriptor.ProviderRevision,
                    Package = descriptor.Package,
                    Path = null,
                    Prefix = "PKHT_",
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            DotNetDiagnosticIds.UnsupportedProviderReload));
    }

    [TestMethod]
    public void DuplicateExactProviderSelectionFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var source = host.ConfigurationSources[0];
        host = host with
        {
            ConfigurationSources =
            [
                source,
                source with
                {
                    Identity = DotNetTestContractFactory.Id(
                        "configuration-source",
                        "duplicate"),
                    Order = 1,
                },
            ],
        };

        var result = CreateValidator().Validate(ReplaceHost(shell, host));

        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            DotNetDiagnosticIds.ConfigurationProviderConflict));
    }

    private static DotNetShellValidator CreateValidator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

    private static DotNetShellDocument ReplaceHost(
        DotNetShellDocument shell,
        DotNetHostDefinition host) =>
        shell with
        {
            Hosts = shell.Hosts
                .Select(item => item.Identity == host.Identity ? host : item)
                .ToImmutableArray(),
        };
}
