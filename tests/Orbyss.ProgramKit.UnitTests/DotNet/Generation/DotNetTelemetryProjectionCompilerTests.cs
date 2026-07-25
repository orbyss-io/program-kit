using System.Text;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetTelemetryProjectionCompilerTests
{
    [TestMethod]
    public void ExactProfileGeneratesStableProviderNeutralEmissionAndPinnedAdapter()
    {
        var host = DotNetTestContractFactory.Shell().Hosts.Single(
            static item => item.Kind == DotNetHostKind.Api);
        DotNetTelemetryProjectionCompiler sut = new();

        var first = sut.Compile(host);
        var second = sut.Compile(host);
        var source = Encoding.UTF8.GetString(first.Single(
            static output => output.RelativePath.EndsWith(
                "ProgramKitTelemetry.cs",
                StringComparison.Ordinal)).Content.Span);
        var options = Encoding.UTF8.GetString(first.Single(
            static output => output.RelativePath.EndsWith(
                "ProgramKitTelemetryOptions.cs",
                StringComparison.Ordinal)).Content.Span);
        var registration = sut.RenderRegistration(host);

        Assert.HasCount(first.Length, second);
        for (var index = 0; index < first.Length; index++)
        {
            Assert.AreEqual(first[index].RelativePath, second[index].RelativePath);
            Assert.IsTrue(first[index].Content.Span.SequenceEqual(second[index].Content.Span));
        }

        Assert.Contains("[LoggerMessage(EventId = 1001", source);
        Assert.Contains(
            "ILogger<OrbyssTestOperationsCategory> logger",
            source);
        Assert.Contains("BeginOperationStartedScope", source);
        Assert.Contains("[\"operation.identity\"] = operationIdentity", source);
        Assert.Contains("ActivitySource", source);
        Assert.Contains("\"operation.execute\", ActivityKind.Internal", source);
        Assert.Contains("activity?.SetTag(\"operation.kind\", operationKind)", source);
        Assert.Contains("Meter", source);
        Assert.Contains("CreateHistogram<double>(\"operation.duration\", \"s\"", source);
        Assert.Contains("tags.Add(\"operation.outcome\", operationOutcome)", source);
        Assert.Contains("operationOutcome is not (\"cancelled\" or \"failed\" or \"succeeded\")", source);
        Assert.Contains("public Uri Endpoint", options);
        Assert.Contains("OptionsValidationException", options);
        Assert.Contains("ActivityIdFormat.W3C", registration);
        Assert.Contains("TraceContextPropagator", registration);
        Assert.DoesNotContain("BaggagePropagator", registration);
        Assert.AreEqual(2, Count(registration, "AddAspNetCoreInstrumentation"));
        Assert.AreEqual(2, Count(registration, "AddHttpClientInstrumentation"));
        Assert.Contains("options.RecordException = true", registration);
        Assert.Contains("ParentBasedSampler", registration);
        Assert.Contains("BatchExportProcessorOptions.MaxQueueSize = 2048", registration);
        Assert.Contains("AddOptions<global::GeneratedHost.Hosting.ProgramKitTelemetryOptions>()", registration);
        Assert.Contains("ValidateOnStart()", registration);
        Assert.Contains("builder.Logging.AddConfiguration", registration);
        Assert.Contains("HostOptions", registration);
        Assert.Contains("IncludeFormattedMessage = false", registration);
        Assert.Contains("IncludeScopes = true", registration);
        Assert.AreEqual("app.UseHttpLogging();" + Environment.NewLine, sut.RenderMiddleware(host));
    }

    [TestMethod]
    public void DisabledTelemetryGeneratesNoRuntimeOrRegistration()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0] with
        {
            Telemetry = null,
        };
        DotNetTelemetryProjectionCompiler sut = new();

        Assert.IsEmpty(sut.Compile(host));
        Assert.AreEqual(string.Empty, sut.RenderRegistration(host));
        Assert.AreEqual(string.Empty, sut.RenderMiddleware(host));
    }

    [TestMethod]
    public void SamplingSelectionsAreExplicitAndStartupFixed()
    {
        var host = DotNetTestContractFactory.Shell().Hosts[0];
        DotNetTelemetryProjectionCompiler sut = new();

        var alwaysOn = sut.RenderRegistration(host with
        {
            Telemetry = host.Telemetry! with
            {
                Sampling = new DotNetTelemetrySampling(
                    DotNetTelemetrySamplerKind.AlwaysOn,
                    null),
            },
        });
        var alwaysOff = sut.RenderRegistration(host with
        {
            Telemetry = host.Telemetry! with
            {
                Sampling = new DotNetTelemetrySampling(
                    DotNetTelemetrySamplerKind.AlwaysOff,
                    null),
            },
        });

        Assert.Contains("AlwaysOnSampler", alwaysOn);
        Assert.Contains("AlwaysOffSampler", alwaysOff);
        Assert.DoesNotContain("IOptionsMonitor", alwaysOn);
        Assert.DoesNotContain("IOptionsMonitor", alwaysOff);
    }

    private static int Count(string text, string value) =>
        text.Split(value, StringSplitOptions.None).Length - 1;
}
