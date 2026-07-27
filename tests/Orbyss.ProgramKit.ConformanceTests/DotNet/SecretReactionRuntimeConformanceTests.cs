using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
public sealed class SecretReactionRuntimeConformanceTests
{
    /// <summary>Gets the current test context.</summary>
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task GeneratedSubscriptionBoundsQueueAndDisposesCallback()
    {
        TaskCompletionSource started =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        TaskCompletionSource release =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        FixtureChangeSource source = new();
        FixtureOutcomeSink sink = new();
        FixtureReactionConsumer consumer = new(
            async (request, cancellationToken) =>
            {
                started.TrySetResult();
                await release.Task.WaitAsync(cancellationToken);
                return Success(request);
            });
        FixtureSecretSubscription subscription =
            new(source, consumer, sink);

        await subscription.StartAsync(TestContext.CancellationToken);
        source.Emit(Signal(2));
        await started.Task.WaitAsync(
            TimeSpan.FromSeconds(5),
            TestContext.CancellationToken);
        source.Emit(Signal(3));
        source.Emit(Signal(4));

        Assert.IsTrue(await WaitUntilAsync(
            () => sink.Results.Any(static result =>
                result.Status == SecretReactionStatus.Rejected),
            TimeSpan.FromSeconds(5),
            TestContext.CancellationToken));
        release.TrySetResult();
        Assert.IsTrue(await WaitUntilAsync(
            () => sink.Results.Length == 3,
            TimeSpan.FromSeconds(5),
            TestContext.CancellationToken));

        subscription.Dispose();

        Assert.IsTrue(source.SubscriptionDisposed);
        Assert.HasCount(
            1,
            sink.Results.Where(static result =>
                result.Status == SecretReactionStatus.Rejected));
        Assert.HasCount(
            2,
            sink.Results.Where(static result =>
                result.Status == SecretReactionStatus.Succeeded));
    }

    [TestMethod]
    public async Task GeneratedSubscriptionRejectsFalseSuccess()
    {
        FixtureChangeSource source = new();
        FixtureOutcomeSink sink = new();
        FixtureReactionConsumer consumer = new(
            (request, cancellationToken) =>
            {
                _ = cancellationToken;
                return ValueTask.FromResult(
                    new SecretReactionResult(
                        request.Signal.ReferenceIdentity,
                        request.Signal.Lifecycle.Generation,
                        SecretConsumerReaction.Manual,
                        SecretReactionStatus.Succeeded,
                        null));
            });
        FixtureSecretSubscription subscription =
            new(source, consumer, sink);

        await subscription.StartAsync(TestContext.CancellationToken);
        source.Emit(Signal(2));
        Assert.IsTrue(await WaitUntilAsync(
            () => sink.Results.Length == 1,
            TimeSpan.FromSeconds(5),
            TestContext.CancellationToken));
        subscription.Dispose();

        Assert.AreEqual(SecretReactionStatus.Failed, sink.Results[0].Status);
        var invalidResultCode = sink.Results[0].SafeDiagnosticCode;
        Assert.IsTrue(invalidResultCode.HasValue);
        Assert.AreEqual(
            "pkid:diagnostic:program-kit:secret-reaction-invalid-result",
            invalidResultCode.GetValueOrDefault().Value);
    }

    [TestMethod]
    public async Task GeneratedSubscriptionConvertsConsumerFailureToSafeStatus()
    {
        FixtureChangeSource source = new();
        FixtureOutcomeSink sink = new();
        FixtureReactionConsumer consumer = new(
            static (request, cancellationToken) =>
            {
                _ = request;
                _ = cancellationToken;
                throw new InvalidOperationException("provider payload must not escape");
            });
        FixtureSecretSubscription subscription =
            new(source, consumer, sink);

        await subscription.StartAsync(TestContext.CancellationToken);
        source.Emit(Signal(2));
        Assert.IsTrue(await WaitUntilAsync(
            () => sink.Results.Length == 1,
            TimeSpan.FromSeconds(5),
            TestContext.CancellationToken));
        subscription.Dispose();

        Assert.AreEqual(SecretReactionStatus.Failed, sink.Results[0].Status);
        var consumerFailureCode = sink.Results[0].SafeDiagnosticCode;
        Assert.IsTrue(consumerFailureCode.HasValue);
        Assert.AreEqual(
            "pkid:diagnostic:program-kit:secret-reaction-consumer-failed",
            consumerFailureCode.GetValueOrDefault().Value);
        Assert.IsEmpty(sink.Results.Where(static result =>
            result.SafeDiagnosticCode?.Value.Contains(
                "payload",
                StringComparison.Ordinal) == true).ToArray());
    }

    private static SecretChangeSignal Signal(long generation) =>
        new(
            new ProgramKitIdentifier(
                "pkid:secret-reference:fixture:service-credential"),
            SecretChangeKind.GenerationChanged,
            generation - 1,
            new SecretLifecycleMetadata(
                generation,
                SecretResolutionStatus.Available,
                new DateTimeOffset(2026, 7, 25, 10, 0, 0, TimeSpan.Zero),
                null));

    private static SecretReactionResult Success(
        SecretReactionRequest request) =>
        new(
            request.Signal.ReferenceIdentity,
            request.Signal.Lifecycle.Generation,
            request.Reaction,
            SecretReactionStatus.Succeeded,
            null);

    private static async Task<bool> WaitUntilAsync(
        Func<bool> predicate,
        TimeSpan timeout,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow + timeout;
        while (DateTimeOffset.UtcNow < deadline)
        {
            if (predicate())
            {
                return true;
            }

            await Task.Delay(
                TimeSpan.FromMilliseconds(10),
                cancellationToken);
        }

        return predicate();
    }
}
