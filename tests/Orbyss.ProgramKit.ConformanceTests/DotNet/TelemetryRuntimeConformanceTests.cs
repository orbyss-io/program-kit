using System.Diagnostics;
using System.Diagnostics.Metrics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Orbyss.ProgramKit.TelemetryConsumerFixture.Hosting;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
public sealed class TelemetryRuntimeConformanceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void ProviderNeutralEmissionUsesW3cStructuredLogsAndBoundedMetrics()
    {
        Activity? observed = null;
        using ActivityListener activityListener = new()
        {
            ShouldListenTo = static source =>
                source.Name == "Orbyss.ProgramKit.Fixture.Operations",
            Sample = static (ref ActivityCreationOptions<ActivityContext> _) =>
                ActivitySamplingResult.AllDataAndRecorded,
            ActivityStopped = activity => observed = activity,
        };
        ActivitySource.AddActivityListener(activityListener);
        List<(string Name, double Value, string Outcome)> measurements = [];
        using MeterListener meterListener = new();
        meterListener.InstrumentPublished = (instrument, listener) =>
        {
            if (instrument.Meter.Name ==
                "Orbyss.ProgramKit.Fixture.Operations")
            {
                listener.EnableMeasurementEvents(instrument);
            }
        };
        meterListener.SetMeasurementEventCallback<long>(
            (instrument, value, tags, _) =>
                measurements.Add((
                    instrument.Name,
                    value,
                    Outcome(tags))));
        meterListener.SetMeasurementEventCallback<double>(
            (instrument, value, tags, _) =>
                measurements.Add((
                    instrument.Name,
                    value,
                    Outcome(tags))));
        meterListener.Start();
        CaptureLogger<OrbyssProgramKitFixtureOperationsCategory>
            logger = new();

        using (var activity = ProgramKitTelemetry.StartOperation())
        {
            Assert.IsNotNull(activity);
            Assert.AreEqual(ActivityIdFormat.W3C, activity.IdFormat);
            using var scope = ProgramKitTelemetry.BeginOperationStartedScope(
                logger,
                "pkid:operation:test:run",
                "correlation-1");
            ProgramKitTelemetry.OperationStarted(
                logger,
                "pkid:operation:test:run",
                "correlation-1");
            ProgramKitTelemetry.RecordOperation("succeeded", 0.25);
        }

        Assert.IsNotNull(observed);
        Assert.AreEqual(ActivityKind.Internal, observed.Kind);
        Assert.AreEqual("operation.execute", observed.OperationName);
        Assert.HasCount(1, logger.Entries);
        Assert.AreEqual(1001, logger.Entries[0].EventId.Id);
        Assert.AreEqual("OperationStarted", logger.Entries[0].EventId.Name);
        Assert.ContainsSingle(logger.Scopes);
        Assert.AreEqual(
            "pkid:operation:test:run",
            logger.Scopes[0]["operation.identity"]);
        Assert.AreEqual(
            "correlation-1",
            logger.Scopes[0]["correlation.id"]);
        Assert.HasCount(
            1,
            measurements.Where(
                static item =>
                item.Name == "operation.count" &&
                item.Value == 1 &&
                item.Outcome == "succeeded"));
        Assert.HasCount(
            1,
            measurements.Where(
                static item =>
                item.Name == "operation.duration" &&
                item.Value == 0.25 &&
                item.Outcome == "succeeded"));
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(
            () => ProgramKitTelemetry.RecordOperation("customer-123", 1));
    }

    [TestMethod]
    public async Task StartupFixedOtlpOutageDoesNotChangeApplicationSuccessOrHangShutdown()
    {
        HostApplicationBuilder builder = new(
            new HostApplicationBuilderSettings
            {
                DisableDefaults = true,
            });
        builder.Configuration.AddInMemoryCollection(
            new Dictionary<string, string?>
            {
                ["Telemetry:Otlp:Endpoint"] = "http://127.0.0.1:1",
            });
        TelemetryComposition.AddReviewedTelemetry(builder);
        using var host = builder.Build();
        Assert.AreEqual(
            new Uri("http://127.0.0.1:1"),
            host.Services
                .GetRequiredService<IOptions<ProgramKitTelemetryOptions>>()
                .Value
                .Endpoint);
        Assert.ThrowsExactly<OptionsValidationException>(
            () => ProgramKitTelemetryOptions.ParseEndpoint(
                "file:///not-an-otlp-collector"));
        var stopwatch = Stopwatch.StartNew();

        await host.StartAsync(TestContext.CancellationToken);
        ProgramKitTelemetry.RecordOperation("succeeded", 0.01);
        await host.StopAsync(TestContext.CancellationToken);

        stopwatch.Stop();
        Assert.IsLessThan(
            TimeSpan.FromSeconds(5),
            stopwatch.Elapsed,
            "Exporter outage must remain bounded and cannot hang host shutdown.");
    }

    private static string Outcome(ReadOnlySpan<KeyValuePair<string, object?>> tags)
    {
        foreach (var tag in tags)
        {
            if (tag.Key == "operation.outcome")
            {
                return (string)tag.Value!;
            }
        }

        return string.Empty;
    }

}
