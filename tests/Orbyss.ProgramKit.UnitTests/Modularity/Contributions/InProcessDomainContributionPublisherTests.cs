namespace Orbyss.ProgramKit.UnitTests.Modularity.Contributions;

[TestClass]
public sealed class InProcessDomainContributionPublisherTests
{
    public TestContext TestContext { get; set; } = null!;

    private static readonly string[] OrderedCalls = ["first", "second"];
    private static readonly string[] ContinuedCalls = ["after"];
    private static readonly string[] BaseAndDerivedCalls = ["base", "derived"];
    private static readonly string[] ReentrantCalls =
        ["outer-start", "nested", "outer-end"];

    [TestMethod]
    public async Task ZeroHandlersReturnAnEmptySuccessfulAggregate()
    {
        var publisher =
            new InProcessDomainContributionPublisher(
                ModularityTestComposition
                    .CreateDomainContributionRegistry([]));

        var result = await publisher.PublishAsync(
            new RecordedContribution("zero"),
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);

        Assert.IsTrue(result.Succeeded);
        Assert.IsTrue(result.Handlers.IsEmpty);
    }

    [TestMethod]
    public async Task ManyHandlersExecuteInDeterministicTopologicalOrder()
    {
        var calls = new List<string>();
        var second = Descriptor("second", priority: -100);
        var first = Descriptor(
            "first",
            priority: 100,
            before: [second.Registration.Identity]);
        var registry =
            ModularityTestComposition.CreateDomainContributionRegistry(
        [
            Registration(second, (_, _) => Record(calls, "second")),
            Registration(first, (_, _) => Record(calls, "first")),
        ]);
        var publisher = new InProcessDomainContributionPublisher(registry);

        var result = await publisher.PublishAsync(
            new RecordedContribution("ordered"),
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);

        Assert.AreSequenceEqual(OrderedCalls, calls);
        Assert.IsTrue(result.Succeeded);
        Assert.HasCount(2, result.Handlers);
    }

    [TestMethod]
    public async Task ContinueAggregatesFailuresWhileFailFastStopsImmediately()
    {
        var continueCalls = new List<string>();
        var continuePublisher = Publisher(
            Registration(
                Descriptor("fail", priority: 0),
                (_, _) => throw new TestHandlerException()),
            Registration(
                Descriptor("after", priority: 1),
                (_, _) => Record(continueCalls, "after")));

        var continued = await continuePublisher.PublishAsync(
            new RecordedContribution("continue"),
            DomainContributionPublicationPolicy.Continue,
            TestContext.CancellationToken);

        Assert.IsFalse(continued.Succeeded);
        Assert.HasCount(2, continued.Handlers);
        Assert.AreEqual(
            DomainContributionHandlerExecutionStatus.Failed,
            continued.Handlers[0].Status);
        var continuedDiagnostic = continued.Handlers[0].Diagnostic;
        Assert.IsNotNull(continuedDiagnostic);
        Assert.AreEqual(
            ModularityDiagnosticIds.ContributionHandlerFailure,
            continuedDiagnostic.Id);
        Assert.AreSequenceEqual(ContinuedCalls, continueCalls);

        var failFastCalls = new List<string>();
        var failFastPublisher = Publisher(
            Registration(
                Descriptor("fail-fast", priority: 0),
                (_, _) => throw new TestHandlerException()),
            Registration(
                Descriptor("never", priority: 1),
                (_, _) => Record(failFastCalls, "never")));

        var exception =
            await Assert.ThrowsExactlyAsync<DomainContributionPublicationException>(
                async () => await failFastPublisher.PublishAsync(
                    new RecordedContribution("fail-fast"),
                    DomainContributionPublicationPolicy.FailFast,
                    TestContext.CancellationToken));

        Assert.HasCount(1, exception.Result.Handlers);
        Assert.AreEqual(
            ModularityDiagnosticIds.ContributionHandlerFailure,
            exception.Diagnostic.Id);
        Assert.IsEmpty(failFastCalls);
    }

    [TestMethod]
    [DataRow(DomainContributionFailurePolicy.Continue, "out-of-memory")]
    [DataRow(DomainContributionFailurePolicy.FailFast, "out-of-memory")]
    [DataRow(DomainContributionFailurePolicy.Continue, "stack-overflow")]
    [DataRow(DomainContributionFailurePolicy.FailFast, "stack-overflow")]
    [DataRow(DomainContributionFailurePolicy.Continue, "access-violation")]
    [DataRow(DomainContributionFailurePolicy.FailFast, "access-violation")]
    public async Task ProcessFatalFailuresAlwaysPropagateAndStopImmediately(
        DomainContributionFailurePolicy failurePolicy,
        string failureKind)
    {
        var laterCalls = new List<string>();
        var fatalType = failureKind switch
        {
            "out-of-memory" => typeof(OutOfMemoryException),
            "stack-overflow" => typeof(StackOverflowException),
            "access-violation" => typeof(AccessViolationException),
            _ => throw new ArgumentOutOfRangeException(
                nameof(failureKind),
                failureKind,
                "Unknown process-fatal failure fixture."),
        };
        var fatalFailure =
            Activator.CreateInstance(
                fatalType,
                ["Synthetic process-fatal failure."]) as Exception
            ?? throw new InvalidOperationException(
                "The process-fatal exception fixture could not be created.");
        var publisher = Publisher(
            Registration(
                Descriptor("process-fatal", priority: 0),
                (_, _) => ValueTask.FromException(fatalFailure)),
            Registration(
                Descriptor("never-after-process-fatal", priority: 1),
                (_, _) => Record(laterCalls, "unexpected")));
        var policy = new DomainContributionPublicationPolicy(
            failurePolicy,
            DomainContributionCancellationPolicy.Propagate);

        Exception? observed = null;
        try
        {
            await publisher.PublishAsync(
                new RecordedContribution(failureKind),
                policy,
                TestContext.CancellationToken);
        }
        catch (Exception exception)
        {
            observed = exception;
        }

        Assert.AreSame(fatalFailure, observed);
        Assert.IsEmpty(laterCalls);
    }

    [TestMethod]
    public async Task CancellationAlwaysStopsCallerCancellationAndPolicyControlsUnrequestedCancellation()
    {
        var calls = 0;
        var publisher = Publisher(
            Registration(
                Descriptor("cancel"),
                (_, _) => throw new OperationCanceledException()),
            Registration(
                Descriptor("after-cancel", priority: 1),
                (_, _) =>
                {
                    calls++;
                    return ValueTask.CompletedTask;
                }));

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await publisher.PublishAsync(
                new RecordedContribution("propagate"),
                DomainContributionPublicationPolicy.FailFast,
                TestContext.CancellationToken));

        var captured = await publisher.PublishAsync(
            new RecordedContribution("capture"),
            new DomainContributionPublicationPolicy(
                DomainContributionFailurePolicy.Continue,
                DomainContributionCancellationPolicy
                    .TreatUnrequestedCancellationAsFailure),
            TestContext.CancellationToken);

        Assert.AreEqual(1, calls);
        Assert.HasCount(2, captured.Handlers);
        Assert.AreEqual(
            DomainContributionHandlerExecutionStatus.Failed,
            captured.Handlers[0].Status);

        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();
        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await publisher.PublishAsync(
                new RecordedContribution("caller-canceled"),
                DomainContributionPublicationPolicy.Continue,
                cancellation.Token));
        Assert.AreEqual(1, calls);
    }

    [TestMethod]
    public async Task CallerCancellationDuringHandlerCannotBecomeSuccessOrHandlerFailure()
    {
        using var successCancellation = new CancellationTokenSource();
        var cancelThenReturn = Publisher(
            Registration(
                Descriptor("cancel-then-return"),
                (_, _) =>
                {
                    successCancellation.Cancel();
                    return ValueTask.CompletedTask;
                }));

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await cancelThenReturn.PublishAsync(
                new RecordedContribution("cancel-then-return"),
                DomainContributionPublicationPolicy.FailFast,
                successCancellation.Token));

        using var failureCancellation = new CancellationTokenSource();
        var cancelThenFail = Publisher(
            Registration(
                Descriptor("cancel-then-fail"),
                (_, _) =>
                {
                    failureCancellation.Cancel();
                    throw new TestHandlerException();
                }));

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await cancelThenFail.PublishAsync(
                new RecordedContribution("cancel-then-fail"),
                DomainContributionPublicationPolicy.FailFast,
                failureCancellation.Token));
    }

    [TestMethod]
    public async Task ReentrantPublicationUsesIndependentInvocationState()
    {
        var calls = new List<string>();
        InProcessDomainContributionPublisher? publisher = null;
        var outer = new TypedDomainContributionHandlerRegistration<RecordedContribution>(
            Descriptor("outer"),
            new DelegateHandler<RecordedContribution>(
                async (_, cancellationToken) =>
                {
                    calls.Add("outer-start");
                    await publisher!.PublishAsync(
                        new NestedContribution(),
                        DomainContributionPublicationPolicy.FailFast,
                        cancellationToken);
                    calls.Add("outer-end");
                }));
        var nested = new TypedDomainContributionHandlerRegistration<NestedContribution>(
            Descriptor("nested"),
            new DelegateHandler<NestedContribution>(
                (_, _) => Record(calls, "nested")));
        publisher = new InProcessDomainContributionPublisher(
            ModularityTestComposition.CreateDomainContributionRegistry(
                [outer, nested]));

        var result = await publisher.PublishAsync(
            new RecordedContribution("outer"),
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);

        Assert.IsTrue(result.Succeeded);
        Assert.AreSequenceEqual(ReentrantCalls, calls);
    }

    [TestMethod]
    public async Task GenericPublicationTypeControlsExactHandlerSelection()
    {
        var calls = new List<string>();
        var baseRegistration =
            new TypedDomainContributionHandlerRegistration<BaseContribution>(
                Descriptor("base"),
                new DelegateHandler<BaseContribution>(
                    (_, _) => Record(calls, "base")));
        var derivedRegistration =
            new TypedDomainContributionHandlerRegistration<DerivedContribution>(
                Descriptor("derived"),
                new DelegateHandler<DerivedContribution>(
                    (_, _) => Record(calls, "derived")));
        var publisher = new InProcessDomainContributionPublisher(
            ModularityTestComposition.CreateDomainContributionRegistry(
                [baseRegistration, derivedRegistration]));
        BaseContribution asBase = new DerivedContribution("typed");

        var baseResult = await publisher.PublishAsync(
            asBase,
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);
        var derivedResult = await publisher.PublishAsync(
            (DerivedContribution)asBase,
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);
        var interfaceResult = await publisher.PublishAsync<IDomainContribution>(
            asBase,
            DomainContributionPublicationPolicy.FailFast,
            TestContext.CancellationToken);

        Assert.AreSequenceEqual(
            BaseAndDerivedCalls,
            calls);
        Assert.HasCount(1, baseResult.Handlers);
        Assert.HasCount(1, derivedResult.Handlers);
        Assert.IsTrue(interfaceResult.Handlers.IsEmpty);
    }

    [TestMethod]
    public async Task UndefinedPoliciesFailWithCanonicalDiagnostics()
    {
        var publisher =
            new InProcessDomainContributionPublisher(
                ModularityTestComposition
                    .CreateDomainContributionRegistry([]));
        var invalid = new DomainContributionPublicationPolicy(
            (DomainContributionFailurePolicy)int.MaxValue,
            (DomainContributionCancellationPolicy)int.MaxValue);

        var exception = await Assert.ThrowsExactlyAsync<ModularityValidationException>(
            async () => await publisher.PublishAsync(
                new RecordedContribution("invalid-policy"),
                invalid,
                TestContext.CancellationToken));

        Assert.IsTrue(exception.Validation.Diagnostics.All(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.InvalidPublicationPolicy));
    }

    private static InProcessDomainContributionPublisher Publisher(
        params DomainContributionHandlerRegistration[] registrations) =>
        new(ModularityTestComposition.CreateDomainContributionRegistry(
            registrations));

    private static TypedDomainContributionHandlerRegistration<RecordedContribution>
        Registration(
            ModularityRegistrationDescriptor descriptor,
            Func<RecordedContribution, CancellationToken, ValueTask> action) =>
        new(descriptor, new DelegateHandler<RecordedContribution>(action));

    private static ModularityRegistrationDescriptor Descriptor(
        string name,
        int priority = 0,
        ProgramKitIdentifier[]? before = null) =>
        new(
            new ArtifactReference(
                ProgramKitIdentifier.Parse(
                    string.Concat("pkid:contribution:program-kit:", name)),
                SemanticVersion.Parse("1.0.0"),
                Sha256Digest.Parse(
                    string.Concat("sha256:", new string('a', 64)))),
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
            new ModularityOrderDescriptor(
                priority,
                before is null ? [] : [.. before],
                []));

    private static ValueTask Record(List<string> calls, string value)
    {
        calls.Add(value);
        return ValueTask.CompletedTask;
    }

}
