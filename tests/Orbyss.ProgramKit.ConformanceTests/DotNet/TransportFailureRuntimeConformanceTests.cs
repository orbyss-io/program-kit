using System.Diagnostics;
using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
[DoNotParallelize]
public sealed class TransportFailureRuntimeConformanceTests
{
    private const string RawSecret = "raw-secret-value-must-never-escape";

    [TestMethod]
    public async Task ExplicitMappingProducesSanitizedProductionProblemAndOneDiagnosticOutcome()
    {
        using var activity = StartRecordedActivity();

        var result = await TransportFailureHarness.RunAsync(
            new InvalidOperationException(RawSecret));

        Assert.IsTrue(result.Handled);
        Assert.AreEqual(409, result.StatusCode);
        Assert.Contains(
            "The request conflicts with the current state.",
            result.Body);
        Assert.DoesNotContain(RawSecret, result.Body);
        Assert.DoesNotContain(RawSecret, result.LogText);
        Assert.AreEqual(1, result.LogCount);
        Assert.AreEqual(1, result.MeasurementCount);
        Assert.AreEqual(ActivityStatusCode.Error, activity.Status);
        Assert.AreEqual(
            "pkid:failure:transport:conflict",
            activity.GetTagItem("program_kit.failure.identity"));
    }

    [TestMethod]
    public async Task UnmappedFailureUsesSafeGenericFallback()
    {
        var result = await TransportFailureHarness.RunAsync(
            new InvalidDataException(RawSecret));

        Assert.IsTrue(result.Handled);
        Assert.AreEqual(500, result.StatusCode);
        Assert.Contains("The request could not be completed.", result.Body);
        Assert.DoesNotContain(RawSecret, result.Body);
        Assert.DoesNotContain(RawSecret, result.LogText);
        Assert.AreEqual(1, result.LogCount);
        Assert.AreEqual(1, result.MeasurementCount);
    }

    [TestMethod]
    public async Task DevelopmentDisclosureUsesOnlyDeclaredDevelopmentDetail()
    {
        var result = await TransportFailureHarness.RunAsync(
            new InvalidOperationException(RawSecret),
            development: true);

        Assert.Contains(
            "The declared operation conflict occurred.",
            result.Body);
        Assert.DoesNotContain(RawSecret, result.Body);
        Assert.DoesNotContain(RawSecret, result.LogText);
    }

    [TestMethod]
    public async Task UnsupportedAcceptStillHandlesWithoutInventingARepresentation()
    {
        var result = await TransportFailureHarness.RunAsync(
            new InvalidOperationException(RawSecret),
            accept: "text/plain");

        Assert.IsTrue(result.Handled);
        Assert.AreEqual(409, result.StatusCode);
        Assert.AreEqual(string.Empty, result.Body);
        Assert.AreEqual(1, result.LogCount);
        Assert.AreEqual(1, result.MeasurementCount);
    }

    [TestMethod]
    public async Task SelectedStatusCodePagesUseProblemDetailsContentNegotiation()
    {
        var supported = await TransportFailureHarness.RunStatusCodePageAsync();
        var unsupported = await TransportFailureHarness.RunStatusCodePageAsync(
            "text/plain");

        Assert.AreEqual(404, supported.StatusCode);
        Assert.Contains("\"status\":404", supported.Body);
        Assert.AreEqual(404, unsupported.StatusCode);
        Assert.AreEqual(string.Empty, unsupported.Body);
    }

    [TestMethod]
    public async Task NonDisconnectCancellationRemainsUnhandled()
    {
        var result = await TransportFailureHarness.RunAsync(
            new OperationCanceledException(RawSecret));

        Assert.IsFalse(result.Handled);
        Assert.AreEqual(0, result.LogCount);
        Assert.AreEqual(0, result.MeasurementCount);
        Assert.AreEqual(string.Empty, result.Body);
    }

    [TestMethod]
    public async Task RequestAbortCancellationIsClassifiedWithoutWritingAResponse()
    {
        var result = await TransportFailureHarness.RunAsync(
            new OperationCanceledException(RawSecret),
            clientAborted: true);

        Assert.IsTrue(result.Handled);
        Assert.AreEqual(string.Empty, result.Body);
        Assert.DoesNotContain(RawSecret, result.LogText);
        Assert.AreEqual(1, result.LogCount);
        Assert.AreEqual(1, result.MeasurementCount);
    }

    [TestMethod]
    public async Task StartedResponseIsNeverRewrittenOrClaimed()
    {
        var result = await TransportFailureHarness.RunAsync(
            new InvalidOperationException(RawSecret),
            responseStarted: true);

        Assert.IsFalse(result.Handled);
        Assert.AreEqual(0, result.LogCount);
        Assert.AreEqual(0, result.MeasurementCount);
        Assert.AreEqual(string.Empty, result.Body);
    }

    private static Activity StartRecordedActivity()
    {
        Activity.DefaultIdFormat = ActivityIdFormat.W3C;
        var activity = new Activity("transport-failure-fixture");
        activity.Start();
        return activity;
    }
}
