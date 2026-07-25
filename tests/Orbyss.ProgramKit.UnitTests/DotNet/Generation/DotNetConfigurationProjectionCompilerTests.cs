using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConfigurationProjectionCompilerTests
{
    [TestMethod]
    public void RepeatedProjectionIsByteForByteDeterministicAndComplete()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var first = sut.Compile(host);
        var second = sut.Compile(host);

        Assert.AreSequenceEqual(
            first.Select(static output => output.RelativePath).ToArray(),
            second.Select(static output => output.RelativePath).ToArray());
        for (var index = 0; index < first.Length; index++)
        {
            Assert.AreSequenceEqual(
                first[index].Content.ToArray(),
                second[index].Content.ToArray());
        }

        Assert.IsTrue(first.Any(static output =>
            output.RelativePath ==
            "configuration/generated/appsettings.generated.json"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "configuration/environment-map.json"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "configuration/key-per-file-map.json"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "configuration/provider-bindings.json"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "configuration/validation-report.json"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "configuration/provenance.json"));
        Assert.Contains(
            "\"collisionPolicy\": \"fail-never-merge-or-overwrite\"",
            Text(first, "configuration/ownership.json"));
    }

    [TestMethod]
    public void ProviderPrecedenceAndNamedOptionsAreRenderedExactly()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        var environmentProvider = DotNetTestContractFactory.Provider(
            DotNetConfigurationProviderKind.EnvironmentVariables);
        var environment = host.ConfigurationSources[0] with
        {
            Identity = DotNetTestContractFactory.Id(
                "configuration-source",
                "environment"),
            Order = 1,
            ProviderKind =
                DotNetConfigurationProviderKind.EnvironmentVariables,
            ProviderRevision = environmentProvider.ProviderRevision,
            Package = environmentProvider.Package,
            Path = null,
            Prefix = "SAMPLE_",
            Optional = true,
            StartupDisposition =
                DotNetConfigurationStartupDisposition.Optional,
            Reload = new DotNetConfigurationReload(
                false,
                DotNetConfigurationReloadCapability.None,
                null,
                null),
            FailureDisposition =
                DotNetConfigurationFailureDisposition.ContinueWithoutSource,
        };
        host = host with
        {
            ConfigurationSources =
                host.ConfigurationSources.Add(environment),
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    OptionsName = "secondary",
                    SourceIdentities =
                        host.ConfigurationBindings[0].SourceIdentities.Add(
                            environment.Identity),
                },
            ],
        };
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var registration = sut.RenderRegistration(host);

        var jsonIndex = registration.IndexOf(
            "AddJsonFile",
            StringComparison.Ordinal);
        var environmentIndex = registration.IndexOf(
            "AddEnvironmentVariables",
            StringComparison.Ordinal);
        Assert.IsGreaterThanOrEqualTo(0, jsonIndex);
        Assert.IsGreaterThan(jsonIndex, environmentIndex);
        Assert.Contains("AddOptions<global::GeneratedHost.Configuration.SampleClientOptions>(\"secondary\")", registration);
        Assert.Contains(
            "AddSingleton<global::Microsoft.Extensions.Options.IValidateOptions<global::GeneratedHost.Configuration.SampleClientOptions>, global::GeneratedHost.Configuration.SampleClientOptionsValidator>()",
            registration);
        Assert.Contains("GetRequiredSection(\"SampleClient\")", registration);
        Assert.Contains(".ValidateOnStart()", registration);
    }

    [TestMethod]
    public void NamedBindingsShareOneOwnedTypeAndConfigurationProjection()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
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
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var outputs = sut.Compile(host);
        var optionsOutputs = outputs.Count(static output =>
            output.RelativePath ==
            "ProgramKitGenerated/Configuration/SampleClientOptions.cs");
        var generatedBase = Text(
            outputs,
            "configuration/generated/appsettings.generated.json");

        Assert.AreEqual(1, optionsOutputs);
        Assert.AreEqual(
            generatedBase.IndexOf("\"SampleClient\"", StringComparison.Ordinal),
            generatedBase.LastIndexOf("\"SampleClient\"", StringComparison.Ordinal));
    }

    [TestMethod]
    public void MonitorScaffoldIsDisposableBoundedAndRedacted()
    {
        var host = WithReaction(
            DotNetConfigurationChangeReaction.RedactedDiagnostic);
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var outputs = sut.Compile(host);
        var source = Text(
            outputs,
            "ProgramKitGenerated/Configuration/SampleClientOptionsMonitorSubscription.cs");

        Assert.Contains("IDisposable", source);
        Assert.Contains("subscription?.Dispose()", source);
        Assert.Contains("values and references are redacted", source);
        Assert.DoesNotContain("Endpoint", source);
    }

    [TestMethod]
    public void NontrivialReactionUsesBoundedConsumerOwnedQueue()
    {
        var host = WithReaction(
            DotNetConfigurationChangeReaction.ConsumerOwnedQueue);
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var outputs = sut.Compile(host);
        var source = Text(
            outputs,
            "ProgramKitGenerated/Configuration/SampleClientOptionsMonitorSubscription.cs");

        Assert.Contains("Channel.CreateBounded", source);
        Assert.Contains("BoundedChannelFullMode.DropOldest", source);
        Assert.Contains("ISampleClientOptionsChangeConsumer", source);
        Assert.Contains("ConsumeAsync", source);
        Assert.Contains("subscription?.Dispose()", source);
    }

    [TestMethod]
    public void ExternalAndProgramKitOwnershipRemainExplicit()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        var external = host.ConfigurationBindings[0];
        var programKit = external with
        {
            OptionsName = "program-kit",
            Definition = external.Definition with
            {
                Identity = DotNetTestContractFactory.Id(
                    "configuration",
                    "program-kit-client"),
                OwnerIdentity = DotNetTestContractFactory.Id(
                    "package",
                    "program-kit"),
                OwnerKind = DotNetConfigurationOwnerKind.ProgramKit,
                TypeName = "ProgramKitClientOptions",
                Section = "ProgramKitClient",
            },
        };
        host = host with
        {
            ConfigurationBindings = [external, programKit],
        };
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var report = Text(
            sut.Compile(host),
            "configuration/validation-report.json");

        Assert.Contains("\"ownerKind\": \"external\"", report);
        Assert.Contains("\"ownerKind\": \"program-kit\"", report);
        Assert.Contains(
            "\"owner\": \"pkid:package:test:program-kit\"",
            report);
    }

    [TestMethod]
    public void UnsupportedExplicitRefreshFailsInsteadOfWeakeningGuarantees()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        host = host with
        {
            ConfigurationSources =
            [
                host.ConfigurationSources[0] with
                {
                    Reload = new DotNetConfigurationReload(
                        true,
                        DotNetConfigurationReloadCapability.ExplicitRefresh,
                        30,
                        DotNetTestContractFactory.Ref(
                            "refresh",
                            "configuration",
                            'a')),
                },
            ],
        };
        DotNetConfigurationProjectionCompiler sut = new(
            DotNetTestContractFactory.ProviderRegistry());

        var exception = Assert.ThrowsExactly<NotSupportedException>(
            () => sut.RenderRegistration(host));

        Assert.Contains("PKNET007", exception.Message);
    }

    private static DotNetHostDefinition WithReaction(
        DotNetConfigurationChangeReaction reaction)
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        return host with
        {
            ConfigurationBindings =
            [
                host.ConfigurationBindings[0] with
                {
                    Consumption = DotNetOptionsConsumption.Monitor,
                    ChangeReaction = reaction,
                },
            ],
        };
    }

    private static string Text(
        ImmutableArray<GeneratedOutput> outputs,
        string path) =>
        Encoding.UTF8.GetString(
            outputs.Single(output => output.RelativePath == path)
                .Content.Span);
}
