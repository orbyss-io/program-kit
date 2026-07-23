namespace Orbyss.ProgramKit.UnitTests.Modularity.Middleware;

[TestClass]
public sealed class InProcessMiddlewarePipelineTests
{
    public TestContext TestContext { get; set; } = null!;

    private static readonly string[] OrderedCalls =
    [
        "first-before",
        "second-before",
        "terminal",
        "second-after",
        "first-after",
    ];

    private static readonly string[] ReentrantCalls =
    [
        "outer-middleware",
        "inner-middleware",
        "inner-terminal",
        "inner-terminal-observed",
        "outer-terminal",
    ];

    [TestMethod]
    public async Task MiddlewareUsesDeterministicOrderAndAggregatesTheGenericResult()
    {
        var calls = new List<string>();
        var second = Descriptor("second", priority: -100);
        var first = Descriptor(
            "first",
            priority: 100,
            before: [second.Registration.Identity]);
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<string, string>(
        [
            Registration<string, string>(
                second,
                async (context, continuation, _) =>
                {
                    calls.Add("second-before");
                    var result = await continuation(string.Concat(context, "-second"));
                    calls.Add("second-after");
                    return string.Concat(result, "-second-result");
                }),
            Registration<string, string>(
                first,
                async (context, continuation, _) =>
                {
                    calls.Add("first-before");
                    var result = await continuation(string.Concat(context, "-first"));
                    calls.Add("first-after");
                    return string.Concat(result, "-first-result");
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<string, string>(registry);

        var result = await pipeline.ExecuteAsync(
            "start",
            (context, _) =>
            {
                calls.Add("terminal");
                return ValueTask.FromResult(string.Concat(context, "-terminal"));
            },
            TestContext.CancellationToken);

        Assert.AreSequenceEqual(OrderedCalls, calls);
        Assert.AreEqual(
            "start-first-second-terminal-second-result-first-result",
            result);
    }

    [TestMethod]
    public async Task EmptyRegistryInvokesTheTerminalExactlyOnce()
    {
        var terminalCalls = 0;
        var pipeline = new InProcessMiddlewarePipeline<int, int>(
            ModularityTestComposition.CreateMiddlewareRegistry<int, int>([]));

        var result = await pipeline.ExecuteAsync(
            3,
            (context, _) =>
            {
                terminalCalls++;
                return ValueTask.FromResult(context + 1);
            },
            TestContext.CancellationToken);

        Assert.AreEqual(4, result);
        Assert.AreEqual(1, terminalCalls);
    }

    [TestMethod]
    public async Task MiddlewareMayShortCircuitWithoutInvokingTheTerminal()
    {
        var terminalCalls = 0;
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("short-circuit"),
                (context, _, _) => ValueTask.FromResult(context + 10)),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var result = await pipeline.ExecuteAsync(
            5,
            (context, _) =>
            {
                terminalCalls++;
                return ValueTask.FromResult(context);
            },
            TestContext.CancellationToken);

        Assert.AreEqual(15, result);
        Assert.AreEqual(0, terminalCalls);
    }

    [TestMethod]
    public async Task ReentrantExecutionKeepsEachInvocationIndependent()
    {
        var calls = new List<string>();
        InProcessMiddlewarePipeline<string, string>? pipeline = null;
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<string, string>(
        [
            Registration<string, string>(
                Descriptor("reentrant"),
                async (context, continuation, cancellationToken) =>
                {
                    calls.Add(string.Concat(context, "-middleware"));
                    if (string.Equals(context, "outer", StringComparison.Ordinal))
                    {
                        var inner = await pipeline!.ExecuteAsync(
                            "inner",
                            Terminal,
                            cancellationToken);
                        calls.Add(string.Concat(inner, "-observed"));
                    }

                    return await continuation(context);
                }),
        ]);
        pipeline = new InProcessMiddlewarePipeline<string, string>(registry);

        var result = await pipeline.ExecuteAsync(
            "outer",
            Terminal,
            TestContext.CancellationToken);

        Assert.AreEqual("outer-terminal", result);
        Assert.AreSequenceEqual(ReentrantCalls, calls);

        ValueTask<string> Terminal(
            string context,
            CancellationToken cancellationToken)
        {
            calls.Add(string.Concat(context, "-terminal"));
            return ValueTask.FromResult(string.Concat(context, "-terminal"));
        }
    }

    [TestMethod]
    public async Task NextIsSingleUseAndMiddlewareFailuresPropagateWithoutRetry()
    {
        var terminalCalls = 0;
        var doubleNext = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("double-next"),
                async (context, continuation, _) =>
                {
                    await continuation(context);
                    return await continuation(context);
                }),
        ]);
        var doubleNextPipeline =
            new InProcessMiddlewarePipeline<int, int>(doubleNext);

        var contractFailure = await Assert.ThrowsExactlyAsync<ModularityPipelineException>(
            async () => await doubleNextPipeline.ExecuteAsync(
                1,
                (context, _) =>
                {
                    terminalCalls++;
                    return ValueTask.FromResult(context);
                },
                TestContext.CancellationToken));

        Assert.AreEqual(
            ModularityDiagnosticIds.MiddlewareNextInvokedMoreThanOnce,
            contractFailure.Diagnostic.Id);
        Assert.AreEqual(1, terminalCalls);

        var attempts = 0;
        var failing = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("failure"),
                (_, _, _) =>
                {
                    attempts++;
                    throw new TestMiddlewareException();
                }),
        ]);
        var failingPipeline = new InProcessMiddlewarePipeline<int, int>(failing);

        await Assert.ThrowsExactlyAsync<TestMiddlewareException>(
            async () => await failingPipeline.ExecuteAsync(
                1,
                static (context, _) => ValueTask.FromResult(context),
                TestContext.CancellationToken));
        Assert.AreEqual(1, attempts);
    }

    [TestMethod]
    public async Task CallerCancellationStopsBeforeMiddlewareOrTerminalExecution()
    {
        var calls = 0;
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("never"),
                (context, continuation, _) =>
                {
                    calls++;
                    return continuation(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await pipeline.ExecuteAsync(
                1,
                (context, _) =>
                {
                    calls++;
                    return ValueTask.FromResult(context);
                },
                cancellation.Token));
        Assert.AreEqual(0, calls);
    }

    [TestMethod]
    public async Task CallerCancellationDuringTerminalOrShortCircuitCannotBecomeSuccess()
    {
        var terminalPipeline =
            new InProcessMiddlewarePipeline<int, int>(
                ModularityTestComposition
                    .CreateMiddlewareRegistry<int, int>([]));
        using var terminalCancellation = new CancellationTokenSource();

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await terminalPipeline.ExecuteAsync(
                1,
                (context, _) =>
                {
                    terminalCancellation.Cancel();
                    return ValueTask.FromResult(context);
                },
                terminalCancellation.Token));

        using var shortCircuitCancellation = new CancellationTokenSource();
        var shortCircuit = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("cancel-short-circuit"),
                (context, _, _) =>
                {
                    shortCircuitCancellation.Cancel();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var shortCircuitPipeline =
            new InProcessMiddlewarePipeline<int, int>(shortCircuit);

        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            async () => await shortCircuitPipeline.ExecuteAsync(
                1,
                static (context, _) => ValueTask.FromResult(context),
                shortCircuitCancellation.Token));
    }

    [TestMethod]
    public async Task NextDelegateCannotEscapeItsOwningMiddlewareInvocation()
    {
        ProgramKitMiddlewareNext<int, int>? escaped = null;
        var terminalCalls = 0;
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("escaped-next"),
                (context, continuation, _) =>
                {
                    escaped = continuation;
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var result = await pipeline.ExecuteAsync(
            7,
            (context, _) =>
            {
                terminalCalls++;
                return ValueTask.FromResult(context);
            },
            TestContext.CancellationToken);
        Assert.AreEqual(7, result);

        var exception = await Assert.ThrowsExactlyAsync<ModularityPipelineException>(
            async () => await escaped!(8));
        Assert.AreEqual(
            ModularityDiagnosticIds.MiddlewareNextInvokedOutsideInvocation,
            exception.Diagnostic.Id);
        Assert.AreEqual(0, terminalCalls);
    }

    [TestMethod]
    public async Task InvokedNextMustCompleteBeforeMiddlewareReturns()
    {
        var terminalStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("unawaited-next"),
                (context, continuation, cancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var execution = pipeline.ExecuteAsync(
                9,
                async (context, cancellationToken) =>
                {
                    terminalStarted.SetResult();
                    await releaseTerminal.Task.WaitAsync(cancellationToken);
                    return context;
                },
                TestContext.CancellationToken)
            .AsTask();
        await terminalStarted.Task.WaitAsync(TestContext.CancellationToken);
        Assert.IsFalse(execution.IsCompleted);

        releaseTerminal.SetResult();
        var exception =
            await Assert.ThrowsExactlyAsync<ModularityPipelineException>(
                async () => await execution);
        Assert.AreEqual(
            ModularityDiagnosticIds.MiddlewareNextNotAwaited,
            exception.Diagnostic.Id);
        Assert.Contains(
            "pipeline joined the owned continuation",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public async Task FireAndForgetImmediateDownstreamFailureIsNeverLost()
    {
        var expected = new TestMiddlewareException();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("immediate-failure"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var observed = await Assert.ThrowsExactlyAsync<TestMiddlewareException>(
            async () => await pipeline.ExecuteAsync(
                13,
                (_, _) => ValueTask.FromException<int>(expected),
                TestContext.CancellationToken));

        Assert.AreSame(expected, observed);
    }

    [TestMethod]
    public async Task FireAndForgetImmediateDownstreamCancellationIsNeverLost()
    {
        using var downstreamCancellation = new CancellationTokenSource();
        downstreamCancellation.Cancel();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("immediate-cancellation"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var observed = await Assert.ThrowsAsync<OperationCanceledException>(
            async () => await pipeline.ExecuteAsync(
                17,
                (_, _) => ValueTask.FromCanceled<int>(
                    downstreamCancellation.Token),
                TestContext.CancellationToken));

        Assert.AreEqual(
            downstreamCancellation.Token,
            observed.CancellationToken);
    }

    [TestMethod]
    [Timeout(5_000, CooperativeCancellation = true)]
    public async Task FireAndForgetRacingDownstreamFailureIsJoinedAndPropagated()
    {
        var terminalStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var expected = new TestMiddlewareException();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("racing-failure"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var execution = pipeline.ExecuteAsync(
                19,
                async (_, cancellationToken) =>
                {
                    terminalStarted.SetResult();
                    await releaseTerminal.Task.WaitAsync(cancellationToken);
                    throw expected;
                },
                TestContext.CancellationToken)
            .AsTask();
        await terminalStarted.Task.WaitAsync(TestContext.CancellationToken);
        Assert.IsFalse(execution.IsCompleted);

        releaseTerminal.SetResult();
        var observed = await Assert.ThrowsExactlyAsync<TestMiddlewareException>(
            async () => await execution);
        Assert.AreSame(expected, observed);
    }

    [TestMethod]
    [Timeout(5_000, CooperativeCancellation = true)]
    public async Task FireAndForgetRacingDownstreamCancellationIsJoinedAndPropagated()
    {
        var terminalStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        using var downstreamCancellation = new CancellationTokenSource();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("racing-cancellation"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    return ValueTask.FromResult(context);
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var execution = pipeline.ExecuteAsync(
                23,
                async (_, cancellationToken) =>
                {
                    terminalStarted.SetResult();
                    await releaseTerminal.Task.WaitAsync(cancellationToken);
                    throw new OperationCanceledException(
                        downstreamCancellation.Token);
                },
                TestContext.CancellationToken)
            .AsTask();
        await terminalStarted.Task.WaitAsync(TestContext.CancellationToken);
        Assert.IsFalse(execution.IsCompleted);

        downstreamCancellation.Cancel();
        releaseTerminal.SetResult();
        var observed = await Assert.ThrowsAsync<OperationCanceledException>(
            async () => await execution);
        Assert.AreEqual(
            downstreamCancellation.Token,
            observed.CancellationToken);
    }

    [TestMethod]
    public async Task CallerCancellationPrecedesContinuationAndMiddlewareFailures()
    {
        using var callerCancellation = new CancellationTokenSource();
        var downstreamFailure = new TestMiddlewareException();
        var middlewareFailure = new TestMiddlewareException();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("caller-cancellation-precedence"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    callerCancellation.Cancel();
                    throw middlewareFailure;
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var observed =
            await Assert.ThrowsExactlyAsync<OperationCanceledException>(
                async () => await pipeline.ExecuteAsync(
                    29,
                    (_, _) => ValueTask.FromException<int>(downstreamFailure),
                    callerCancellation.Token));

        Assert.AreEqual(
            callerCancellation.Token,
            observed.CancellationToken);
    }

    [TestMethod]
    public async Task ContinuationFailurePrecedesMiddlewareFailure()
    {
        var downstreamFailure = new TestMiddlewareException();
        var middlewareFailure = new TestMiddlewareException();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("continuation-failure-precedence"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    throw middlewareFailure;
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var observed = await Assert.ThrowsExactlyAsync<TestMiddlewareException>(
            async () => await pipeline.ExecuteAsync(
                31,
                (_, _) => ValueTask.FromException<int>(downstreamFailure),
                TestContext.CancellationToken));

        Assert.AreSame(downstreamFailure, observed);
    }

    [TestMethod]
    [Timeout(5_000, CooperativeCancellation = true)]
    public async Task MiddlewareFailurePrecedesPendingSuccessViolation()
    {
        var terminalStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var middlewareFailure = new TestMiddlewareException();
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("middleware-failure-precedence"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    throw middlewareFailure;
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var execution = pipeline.ExecuteAsync(
                37,
                async (context, cancellationToken) =>
                {
                    terminalStarted.SetResult();
                    await releaseTerminal.Task.WaitAsync(cancellationToken);
                    return context;
                },
                TestContext.CancellationToken)
            .AsTask();
        await terminalStarted.Task.WaitAsync(TestContext.CancellationToken);
        Assert.IsFalse(execution.IsCompleted);

        releaseTerminal.SetResult();
        var observed = await Assert.ThrowsExactlyAsync<TestMiddlewareException>(
            async () => await execution);
        Assert.AreSame(middlewareFailure, observed);
    }

    [TestMethod]
    [DataRow("out-of-memory")]
    [DataRow("stack-overflow")]
    [DataRow("access-violation")]
    [Timeout(5_000, CooperativeCancellation = true)]
    public async Task ProcessFatalMiddlewareFailureDoesNotJoinPendingContinuation(
        string failureKind)
    {
        var terminalStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
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
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("process-fatal"),
                (context, continuation, ignoredCancellationToken) =>
                {
                    _ = continuation(context).AsTask();
                    throw fatalFailure;
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var execution = pipeline.ExecuteAsync(
                41,
                async (context, cancellationToken) =>
                {
                    terminalStarted.SetResult();
                    await releaseTerminal.Task.WaitAsync(cancellationToken);
                    return context;
                },
                TestContext.CancellationToken)
            .AsTask();
        await terminalStarted.Task.WaitAsync(TestContext.CancellationToken);

        try
        {
            Exception? observed = null;
            try
            {
                await execution.WaitAsync(TestContext.CancellationToken);
            }
            catch (Exception exception)
            {
                observed = exception;
            }

            Assert.AreSame(fatalFailure, observed);
            Assert.IsFalse(releaseTerminal.Task.IsCompleted);
        }
        finally
        {
            releaseTerminal.TrySetResult();
        }
    }

    [TestMethod]
    [Timeout(5_000, CooperativeCancellation = true)]
    public async Task ConcurrentDoubleNextFailsWithoutHoldingTheContinuationGate()
    {
        var terminalEntered = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var releaseTerminal = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        ModularityPipelineException? secondFailure = null;
        var registry = ModularityTestComposition
            .CreateMiddlewareRegistry<int, int>(
        [
            Registration<int, int>(
                Descriptor("concurrent-double-next"),
                async (context, continuation, cancellationToken) =>
                {
                    var first = Task.Run(
                        async () => await continuation(context),
                        cancellationToken);
                    await terminalEntered.Task.WaitAsync(cancellationToken);
                    try
                    {
                        await Task.Run(
                            async () => await continuation(context),
                            cancellationToken);
                    }
                    catch (ModularityPipelineException exception)
                    {
                        secondFailure = exception;
                    }
                    finally
                    {
                        releaseTerminal.SetResult();
                    }

                    return await first;
                }),
        ]);
        var pipeline = new InProcessMiddlewarePipeline<int, int>(registry);

        var result = await pipeline.ExecuteAsync(
            11,
            async (context, cancellationToken) =>
            {
                terminalEntered.SetResult();
                await releaseTerminal.Task.WaitAsync(cancellationToken);
                return context;
            },
            TestContext.CancellationToken);

        Assert.AreEqual(11, result);
        Assert.IsNotNull(secondFailure);
        Assert.AreEqual(
            ModularityDiagnosticIds.MiddlewareNextInvokedMoreThanOnce,
            secondFailure.Diagnostic.Id);
    }

    private static MiddlewareRegistration<TContext, TResult> Registration<TContext, TResult>(
        ModularityRegistrationDescriptor descriptor,
        Func<
            TContext,
            ProgramKitMiddlewareNext<TContext, TResult>,
            CancellationToken,
            ValueTask<TResult>> action) =>
        new(descriptor, new DelegateMiddleware<TContext, TResult>(action));

    private static ModularityRegistrationDescriptor Descriptor(
        string name,
        int priority = 0,
        ProgramKitIdentifier[]? before = null) =>
        new(
            new ArtifactReference(
                ProgramKitIdentifier.Parse(
                    string.Concat("pkid:middleware:program-kit:", name)),
                SemanticVersion.Parse("1.0.0"),
                Sha256Digest.Parse(
                    string.Concat("sha256:", new string('b', 64)))),
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
            new ModularityOrderDescriptor(
                priority,
                before is null ? [] : [.. before],
                []));

}
