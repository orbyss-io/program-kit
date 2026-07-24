using System.Collections.Concurrent;
using System.Collections.Immutable;
using System.Threading.Channels;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Activation;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Cancellation;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Results;
using Orbyss.ProgramKit.Tasks.Idempotency;
using Orbyss.ProgramKit.Tasks.InProcess.Composition;
using Orbyss.ProgramKit.Tasks.InProcess.Coordination;
using Orbyss.ProgramKit.Tasks.InProcess.Diagnostics;
using Orbyss.ProgramKit.Tasks.InProcess.Observability;
using Orbyss.ProgramKit.Tasks.InProcess.State;
using Orbyss.ProgramKit.Tasks.Middleware;
using Orbyss.ProgramKit.Tasks.Observability;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Retry;

namespace Orbyss.ProgramKit.Tasks.InProcess.Execution;

/// <summary>
/// Bounded volatile single-process task runner and background dispatcher.
/// </summary>
internal sealed class InProcessTaskRuntime :
    ITaskRunner,
    ITaskDispatcher,
    ITaskStatusReader,
    ITaskCancellationRequester,
    IInProcessTaskRuntime,
    IAsyncDisposable
{
    private readonly ITaskRegistryCoordinator registryCoordinator;
    private readonly ITaskActivationScopeResolver activationScopeResolver;
    private readonly ITaskMiddlewarePipeline middlewarePipeline;
    private readonly ITaskRetryCoordinator retryCoordinator;
    private readonly ITaskIdempotencyCoordinator idempotencyCoordinator;
    private readonly ITaskLifecycleObserver lifecycleObserver;
    private readonly IInProcessTaskTelemetry telemetry;
    private readonly TimeProvider timeProvider;
    private readonly IServiceProvider rootServices;
    private readonly InProcessTaskRuntimeOptions options;
    private readonly ConcurrentDictionary<string, InProcessTaskRecord> records =
        new(StringComparer.Ordinal);
    private readonly Channel<InProcessTaskWorkItem> queue =
        Channel.CreateUnbounded<InProcessTaskWorkItem>(
            new UnboundedChannelOptions
            {
                SingleReader = false,
                SingleWriter = false,
            });
    private readonly SemaphoreSlim queueSlots;
    private readonly Lock lifecycleGate = new();
    private CancellationTokenSource? runtimeCancellation;
    private Task[] workers = [];
    private bool started;
    private bool accepting;
    private int queueDepth;
    private int activeExecutions;

    public InProcessTaskRuntime(
        ITaskRegistryCoordinator registryCoordinator,
        ITaskActivationScopeResolver activationScopeResolver,
        ITaskMiddlewarePipeline middlewarePipeline,
        ITaskRetryCoordinator retryCoordinator,
        ITaskIdempotencyCoordinator idempotencyCoordinator,
        ITaskLifecycleObserver lifecycleObserver,
        IInProcessTaskTelemetry telemetry,
        TimeProvider timeProvider,
        IServiceProvider rootServices,
        InProcessTaskRuntimeOptions options)
    {
        this.registryCoordinator = registryCoordinator ??
            throw new ArgumentNullException(nameof(registryCoordinator));
        this.activationScopeResolver = activationScopeResolver ??
            throw new ArgumentNullException(nameof(activationScopeResolver));
        this.middlewarePipeline = middlewarePipeline ??
            throw new ArgumentNullException(nameof(middlewarePipeline));
        this.retryCoordinator = retryCoordinator ??
            throw new ArgumentNullException(nameof(retryCoordinator));
        this.idempotencyCoordinator = idempotencyCoordinator ??
            throw new ArgumentNullException(nameof(idempotencyCoordinator));
        this.lifecycleObserver = lifecycleObserver ??
            throw new ArgumentNullException(nameof(lifecycleObserver));
        this.telemetry = telemetry ??
            throw new ArgumentNullException(nameof(telemetry));
        this.timeProvider = timeProvider ??
            throw new ArgumentNullException(nameof(timeProvider));
        this.rootServices = rootServices ??
            throw new ArgumentNullException(nameof(rootServices));
        this.options = options ??
            throw new ArgumentNullException(nameof(options));
        ValidateOptions(options);
        queueSlots = new SemaphoreSlim(options.QueueCapacity);
    }

    /// <inheritdoc />
    public bool IsStarted
    {
        get
        {
            lock (lifecycleGate)
            {
                return started;
            }
        }
    }

    /// <inheritdoc />
    public bool IsAccepting
    {
        get
        {
            lock (lifecycleGate)
            {
                return accepting;
            }
        }
    }

    /// <inheritdoc />
    public int QueueDepth => Volatile.Read(ref queueDepth);

    /// <inheritdoc />
    public int QueueCapacity => options.QueueCapacity;

    /// <inheritdoc />
    public async ValueTask<TaskExecutionOutcome<TResponse>> RunAsync<
        TRequest,
        TResponse>(
        TaskRequest<TRequest> request,
        CancellationToken cancellationToken)
        where TRequest : notnull
        where TResponse : notnull
    {
        ArgumentNullException.ThrowIfNull(request);
        if (cancellationToken.IsCancellationRequested)
        {
            return new TaskExecutionOutcome<TResponse>(
                request.Revision,
                TaskExecutionOutcomeKind.CancelledBeforeAcceptance,
                null,
                null,
                null,
                []);
        }

        if (!IsAccepting)
        {
            return Rejected<TResponse>(
                request.Revision,
                NotAcceptingDiagnostic());
        }

        var selection = Select(request.DefinitionRevision, typeof(TRequest));
        if (selection is null)
        {
            return Rejected<TResponse>(
                request.Revision,
                MissingSelectionDiagnostic());
        }

        var instance = CreateInstance(request);
        var claim = CreateClaim(
            selection.Value.Binding,
            request.IdempotencyKey);
        if (claim is not null)
        {
            var idempotency = await idempotencyCoordinator.TryAcquireAsync(
                claim,
                instance.Revision,
                cancellationToken).ConfigureAwait(false);
            if (idempotency.Disposition !=
                TaskIdempotencyDisposition.Acquired)
            {
                return Rejected<TResponse>(
                    request.Revision,
                    DuplicateDiagnostic());
            }
        }

        var record = new InProcessTaskRecord(instance);
        if (!records.TryAdd(Key(instance.Revision), record))
        {
            await AbandonClaimAsync(
                claim,
                instance.Revision).ConfigureAwait(false);
            return Rejected<TResponse>(
                request.Revision,
                DuplicateDiagnostic());
        }

        await ObserveAsync(
            TaskLifecycleKind.Accepted,
            instance,
            null,
            CancellationToken.None).ConfigureAwait(false);
        telemetry.RecordAccepted();
        var work = new InProcessTaskWorkItem(
            instance,
            typeof(TRequest),
            typeof(TResponse),
            request.Payload,
            cancellationToken);
        Interlocked.Increment(ref activeExecutions);
        TaskHandlerResult result;
        try
        {
            result = await ExecuteAsync(
                work,
                selection.Value.Binding,
                selection.Value.Handler,
                record,
                cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            Interlocked.Decrement(ref activeExecutions);
        }
        await CompleteClaimAsync(
            claim,
            instance.Revision).ConfigureAwait(false);
        return ToTypedOutcome<TResponse>(request.Revision, instance, result);
    }

    /// <inheritdoc />
    public async ValueTask<TaskDispatchResult> DispatchAsync<TRequest>(
        TaskRequest<TRequest> request,
        CancellationToken cancellationToken)
        where TRequest : notnull
    {
        ArgumentNullException.ThrowIfNull(request);
        if (cancellationToken.IsCancellationRequested)
        {
            return new TaskDispatchResult(
                request.Revision,
                TaskDispatchDisposition.CancelledBeforeAcceptance,
                null,
                []);
        }

        if (!IsAccepting)
        {
            return RejectedDispatch(
                request.Revision,
                InProcessTaskDiagnosticIds.NotAccepting,
                "The in-process task runtime is not accepting work.");
        }

        var selection = Select(request.DefinitionRevision, typeof(TRequest));
        if (selection is null)
        {
            return RejectedDispatch(
                request.Revision,
                InProcessTaskDiagnosticIds.MissingSelection,
                "No exact task definition, activation binding, and typed handler selection exists.");
        }

        var dispatchContext = new TaskDispatchContext(
            request.Revision,
            request.DefinitionRevision,
            typeof(TRequest),
            request);
        return await middlewarePipeline.ExecuteDispatchAsync(
            rootServices,
            SelectMiddleware(
                registryCoordinator.GetCurrent().DispatchMiddleware,
                selection.Value.Binding),
            dispatchContext,
            (_, token) => AcceptBackgroundAsync(
                request,
                selection.Value,
                token),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public ValueTask<TaskInstanceStatus?> ReadAsync(
        ArtifactReference instanceRevision,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(instanceRevision);
        cancellationToken.ThrowIfCancellationRequested();
        PruneTerminal();
        if (!records.TryGetValue(Key(instanceRevision), out var record))
        {
            return ValueTask.FromResult<TaskInstanceStatus?>(null);
        }

        lock (record.Gate)
        {
            return ValueTask.FromResult<TaskInstanceStatus?>(
                new TaskInstanceStatus(
                    record.Instance.Revision,
                    record.State,
                    record.AttemptCount,
                    record.CancellationRequested,
                    timeProvider.GetUtcNow(),
                    record.LatestAttemptRevision,
                    record.TerminalOutcomeRevision,
                    record.TerminalAt));
        }
    }

    /// <inheritdoc />
    public ValueTask<TaskCancellationResult> RequestAsync(
        TaskCancellationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        if (!records.TryGetValue(Key(request.InstanceRevision), out var record))
        {
            return ValueTask.FromResult(
                new TaskCancellationResult(
                    request.Revision,
                    request.InstanceRevision,
                    TaskCancellationDisposition.UnknownInstance,
                    []));
        }

        lock (record.Gate)
        {
            if (IsTerminal(record.State))
            {
                return ValueTask.FromResult(
                    new TaskCancellationResult(
                        request.Revision,
                        request.InstanceRevision,
                        TaskCancellationDisposition.AlreadyTerminal,
                        []));
            }

            if (record.CancellationRequested)
            {
                return ValueTask.FromResult(
                    new TaskCancellationResult(
                        request.Revision,
                        request.InstanceRevision,
                        TaskCancellationDisposition.AlreadyRequested,
                        []));
            }

            record.CancellationRequested = true;
            record.ExecutionCancellation.Cancel();
            return ValueTask.FromResult(
                new TaskCancellationResult(
                    request.Revision,
                    request.InstanceRevision,
                    TaskCancellationDisposition.Requested,
                    []));
        }
    }

    /// <inheritdoc />
    public ValueTask StartAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        lock (lifecycleGate)
        {
            if (started)
            {
                return ValueTask.CompletedTask;
            }

            registryCoordinator.Freeze();
            ValidateRuntimeSelection(registryCoordinator.GetCurrent());
            var selectedCancellation = new CancellationTokenSource();
            runtimeCancellation = selectedCancellation;
            workers = Enumerable
                .Range(0, options.MaximumConcurrency)
                .Select(_ => WorkerAsync(selectedCancellation.Token))
                .ToArray();
            started = true;
            accepting = true;
        }

        return ValueTask.CompletedTask;
    }

    private void ValidateRuntimeSelection(ITaskRegistry registry)
    {
        if (registry.Bindings.Any(
                binding =>
                    binding.Binding.RuntimeRevision !=
                    options.RuntimeRevision))
        {
            throw new InvalidOperationException(
                "Every activation binding must select the exact in-process runtime revision configured by the host.");
        }
    }

    /// <inheritdoc />
    public async ValueTask StopAsync(
        bool drain,
        CancellationToken cancellationToken)
    {
        Task[] selectedWorkers;
        CancellationTokenSource? selectedCancellation;
        lock (lifecycleGate)
        {
            accepting = false;
            if (!started)
            {
                return;
            }

            selectedWorkers = workers;
            selectedCancellation = runtimeCancellation;
            if (!drain)
            {
                selectedCancellation?.Cancel();
            }
        }

        if (drain)
        {
            while (QueueDepth > 0 ||
                   Volatile.Read(ref activeExecutions) > 0)
            {
                await Task.Delay(
                    TimeSpan.FromMilliseconds(10),
                    timeProvider,
                    cancellationToken).ConfigureAwait(false);
            }

            selectedCancellation?.Cancel();
        }

        await Task.WhenAll(selectedWorkers)
            .WaitAsync(cancellationToken)
            .ConfigureAwait(false);
        if (!drain)
        {
            CancelRemainingQueuedWork();
        }

        lock (lifecycleGate)
        {
            started = false;
            workers = [];
            selectedCancellation?.Dispose();
            runtimeCancellation = null;
        }
    }

    private async ValueTask<TaskDispatchResult> AcceptBackgroundAsync<TRequest>(
        TaskRequest<TRequest> request,
        (
            TaskActivationBindingRegistration Binding,
            ITaskHandlerRegistration Handler) selection,
        CancellationToken cancellationToken)
        where TRequest : notnull
    {
        if (!queueSlots.Wait(0, CancellationToken.None))
        {
            return RejectedDispatch(
                request.Revision,
                InProcessTaskDiagnosticIds.QueueFull,
                "The bounded in-process task queue is full.");
        }

        var instance = CreateInstance(request);
        var claim = CreateClaim(selection.Binding, request.IdempotencyKey);
        if (claim is not null)
        {
            var idempotency = await idempotencyCoordinator.TryAcquireAsync(
                claim,
                instance.Revision,
                cancellationToken).ConfigureAwait(false);
            if (idempotency.Disposition !=
                TaskIdempotencyDisposition.Acquired)
            {
                queueSlots.Release();
                return RejectedDispatch(
                    request.Revision,
                    InProcessTaskDiagnosticIds.DuplicateRequest,
                    "An equivalent process-local idempotency claim already exists.");
            }
        }

        var record = new InProcessTaskRecord(instance);
        if (!records.TryAdd(Key(instance.Revision), record))
        {
            await AbandonClaimAsync(
                claim,
                instance.Revision).ConfigureAwait(false);
            queueSlots.Release();
            return RejectedDispatch(
                request.Revision,
                InProcessTaskDiagnosticIds.DuplicateRequest,
                "The exact task instance already exists.");
        }

        await ObserveAsync(
            TaskLifecycleKind.Accepted,
            instance,
            null,
            CancellationToken.None).ConfigureAwait(false);
        telemetry.RecordAccepted();
        Interlocked.Increment(ref queueDepth);
        await queue.Writer.WriteAsync(
            new InProcessTaskWorkItem(
                instance,
                typeof(TRequest),
                selection.Handler.ResponseType,
                request.Payload,
                record.ExecutionCancellation.Token),
            CancellationToken.None).ConfigureAwait(false);
        return new TaskDispatchResult(
            request.Revision,
            TaskDispatchDisposition.Accepted,
            instance.Revision,
            []);
    }

    private async Task WorkerAsync(CancellationToken cancellationToken)
    {
        try
        {
            await foreach (var work in queue.Reader.ReadAllAsync(
                               cancellationToken).ConfigureAwait(false))
            {
                Interlocked.Decrement(ref queueDepth);
                queueSlots.Release();
                if (!records.TryGetValue(
                        Key(work.Instance.Revision),
                        out var record))
                {
                    continue;
                }

                var selection = Select(
                    work.Instance.DefinitionRevision,
                    work.RequestType);
                if (selection is null)
                {
                    SetTerminal(record, TaskInstanceState.Failed, null);
                    continue;
                }

                using var linked = CancellationTokenSource.CreateLinkedTokenSource(
                    cancellationToken,
                    work.ExecutionCancellationToken);
                Interlocked.Increment(ref activeExecutions);
                try
                {
                    await ExecuteAsync(
                        work,
                        selection.Value.Binding,
                        selection.Value.Handler,
                        record,
                        linked.Token).ConfigureAwait(false);
                }
                finally
                {
                    Interlocked.Decrement(ref activeExecutions);
                }
                var binding = selection.Value.Binding.Binding;
                var claim = work.Instance.IdempotencyKey is null
                    ? null
                    : new TaskIdempotencyClaim(
                        binding.IdempotencyPolicyRevision,
                        work.Instance.DefinitionRevision,
                        work.Instance.IdempotencyKey);
                await CompleteClaimAsync(
                    claim,
                    work.Instance.Revision).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
    }

    private async ValueTask<TaskHandlerResult> ExecuteAsync(
        InProcessTaskWorkItem work,
        TaskActivationBindingRegistration bindingRegistration,
        ITaskHandlerRegistration handler,
        InProcessTaskRecord record,
        CancellationToken cancellationToken)
    {
        var binding = bindingRegistration.Binding;
        var attemptNumber = 0;
        while (true)
        {
            attemptNumber++;
            var attemptRevision = TaskRuntimeIdentity.Create(
                "task-attempt",
                work.Instance.Revision,
                attemptNumber.ToString(
                    System.Globalization.CultureInfo.InvariantCulture));
            lock (record.Gate)
            {
                record.State = TaskInstanceState.Running;
                record.AttemptCount = attemptNumber;
                record.LatestAttemptRevision = attemptRevision;
            }

            await ObserveAsync(
                TaskLifecycleKind.AttemptStarted,
                work.Instance,
                attemptRevision,
                CancellationToken.None).ConfigureAwait(false);
            using var attemptObservation = telemetry.StartAttempt(
                work.Instance,
                attemptRevision);
            try
            {
                await using var scope = await activationScopeResolver
                    .CreateScopeAsync(
                        new TaskActivationRequest(
                            binding.ActivationIdentity,
                            binding.OwningFeatureRevision,
                            binding.HandlerRevision),
                        cancellationToken)
                    .ConfigureAwait(false);
                var handlerContext = new TaskHandlerContext(
                    work.Instance.DefinitionRevision,
                    work.Instance.Revision,
                    attemptRevision,
                    binding.Revision,
                    work.Instance.RequestContract,
                    work.Instance.ResponseContract,
                    work.Instance.FailureContract);
                var executionContext = new TaskExecutionContext(
                    handlerContext,
                    work.RequestType,
                    work.ResponseType,
                    work.Request);
                var invocation = await middlewarePipeline.ExecuteAttemptAsync(
                    scope.Services,
                    SelectMiddleware(
                        registryCoordinator.GetCurrent().ExecutionMiddleware,
                        bindingRegistration),
                    executionContext,
                    (_, token) => InvokeHandlerAsync(
                        handler,
                        scope.Services,
                        handlerContext,
                        work.Request,
                        token),
                    cancellationToken).ConfigureAwait(false);
                var outcomeRevision = TaskRuntimeIdentity.Create(
                    "task-outcome",
                    work.Instance.Revision,
                    "succeeded");
                SetTerminal(
                    record,
                    TaskInstanceState.Succeeded,
                    outcomeRevision);
                await ObserveAsync(
                    TaskLifecycleKind.Succeeded,
                    work.Instance,
                    attemptRevision,
                    CancellationToken.None).ConfigureAwait(false);
                return new TaskHandlerResult(
                    invocation.Response,
                    null,
                    TaskExecutionOutcomeKind.Succeeded);
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                var outcomeRevision = TaskRuntimeIdentity.Create(
                    "task-outcome",
                    work.Instance.Revision,
                    "cancelled");
                SetTerminal(
                    record,
                    TaskInstanceState.Cancelled,
                    outcomeRevision);
                await ObserveAsync(
                    TaskLifecycleKind.Cancelled,
                    work.Instance,
                    attemptRevision,
                    CancellationToken.None).ConfigureAwait(false);
                return new TaskHandlerResult(
                    null,
                    null,
                    TaskExecutionOutcomeKind.Cancelled);
            }
            catch (Exception)
            {
                var failureRevision = TaskRuntimeIdentity.Create(
                    "task-failure",
                    work.Instance.Revision,
                    attemptNumber.ToString(
                        System.Globalization.CultureInfo.InvariantCulture));
                var decision = await retryCoordinator.DecideAsync(
                    new TaskRetryContext(
                        binding.RetryPolicyRevision,
                        work.Instance.DefinitionRevision,
                        work.Instance.Revision,
                        attemptRevision,
                        attemptNumber,
                        "handler-failed"),
                    cancellationToken).ConfigureAwait(false);
                if (decision.Retry)
                {
                    lock (record.Gate)
                    {
                        record.State = TaskInstanceState.RetryWait;
                    }

                    await Task.Delay(
                        decision.Delay,
                        timeProvider,
                        cancellationToken).ConfigureAwait(false);
                    continue;
                }

                var failure = new TaskFailure(
                    failureRevision,
                    work.Instance.Revision,
                    work.Instance.FailureContract,
                    timeProvider.GetUtcNow(),
                    "handler-failed",
                    []);
                SetTerminal(
                    record,
                    TaskInstanceState.Failed,
                    failureRevision);
                await ObserveAsync(
                    TaskLifecycleKind.Failed,
                    work.Instance,
                    attemptRevision,
                    CancellationToken.None).ConfigureAwait(false);
                return new TaskHandlerResult(
                    null,
                    failure,
                    TaskExecutionOutcomeKind.Failed);
            }
        }
    }

    private (
        TaskActivationBindingRegistration Binding,
        ITaskHandlerRegistration Handler)? Select(
        ArtifactReference definitionRevision,
        Type requestType)
    {
        var registry = registryCoordinator.GetCurrent();
        var definition = registry.Definitions.SingleOrDefault(
            candidate => candidate.Definition.Revision == definitionRevision);
        var binding = registry.Bindings.SingleOrDefault(
            candidate =>
                candidate.Binding.DefinitionRevision == definitionRevision);
        if (definition is null || binding is null)
        {
            return null;
        }

        var handler = registry.Handlers.SingleOrDefault(
            candidate =>
                candidate.HandlerRevision ==
                    binding.Binding.HandlerRevision &&
                candidate.RequestType == requestType);
        return handler is null
            ? null
            : (binding, handler);
    }

    private static ImmutableArray<TaskMiddlewareRegistration> SelectMiddleware(
        ImmutableArray<TaskMiddlewareRegistration> orderedMiddleware,
        TaskActivationBindingRegistration binding) =>
        orderedMiddleware
            .Where(
                registration =>
                    binding.Binding.MiddlewareRevisions.Contains(
                        registration.Revision))
            .ToImmutableArray();

    private TaskInstance CreateInstance<TRequest>(TaskRequest<TRequest> request)
        where TRequest : notnull
    {
        var instanceRevision = TaskRuntimeIdentity.Create(
            "task-instance",
            request.Revision,
            request.IdempotencyKey ?? request.RequestedAt.UtcTicks.ToString(
                System.Globalization.CultureInfo.InvariantCulture));
        return new TaskInstance(
            instanceRevision,
            request.Revision,
            request.DefinitionRevision,
            request.RequestContract,
            request.ResponseContract,
            request.FailureContract,
            timeProvider.GetUtcNow(),
            request.IdempotencyKey,
            request.OccurrenceRevision);
    }

    private static async ValueTask<TaskHandlerInvocationResult> InvokeHandlerAsync(
        ITaskHandlerRegistration handler,
        IServiceProvider services,
        TaskHandlerContext context,
        object request,
        CancellationToken cancellationToken)
    {
        var response = await handler.InvokeAsync(
            services,
            context,
            request,
            cancellationToken).ConfigureAwait(false);
        return new TaskHandlerInvocationResult(response);
    }

    private TaskExecutionOutcome<TResponse> ToTypedOutcome<TResponse>(
        ArtifactReference requestRevision,
        TaskInstance instance,
        TaskHandlerResult result)
        where TResponse : notnull
    {
        TaskResponse<TResponse>? response = null;
        if (result.Kind == TaskExecutionOutcomeKind.Succeeded)
        {
            response = new TaskResponse<TResponse>(
                TaskRuntimeIdentity.Create(
                    "task-response",
                    instance.Revision,
                    "succeeded"),
                instance.Revision,
                instance.ResponseContract,
                timeProvider.GetUtcNow(),
                (TResponse)result.Response!);
        }

        return new TaskExecutionOutcome<TResponse>(
            requestRevision,
            result.Kind,
            instance.Revision,
            response,
            result.Failure,
            []);
    }

    private async ValueTask ObserveAsync(
        TaskLifecycleKind kind,
        TaskInstance instance,
        ArtifactReference? attemptRevision,
        CancellationToken cancellationToken)
    {
        try
        {
            await lifecycleObserver.ObserveAsync(
                new TaskLifecycleContribution(
                    kind,
                    instance.DefinitionRevision,
                    instance.Revision,
                    attemptRevision,
                    timeProvider.GetUtcNow()),
                cancellationToken).ConfigureAwait(false);
        }
        catch (Exception)
        {
            // State transitions are authoritative; optional observation cannot
            // retroactively fail or cancel them.
        }
    }

    private static TaskIdempotencyClaim? CreateClaim(
        TaskActivationBindingRegistration binding,
        string? key) =>
        key is null
            ? null
            : new TaskIdempotencyClaim(
                binding.Binding.IdempotencyPolicyRevision,
                binding.Binding.DefinitionRevision,
                key);

    private async ValueTask CompleteClaimAsync(
        TaskIdempotencyClaim? claim,
        ArtifactReference instanceRevision)
    {
        if (claim is not null)
        {
            await idempotencyCoordinator.CompleteAsync(
                claim,
                instanceRevision,
                CancellationToken.None).ConfigureAwait(false);
        }
    }

    private async ValueTask AbandonClaimAsync(
        TaskIdempotencyClaim? claim,
        ArtifactReference instanceRevision)
    {
        if (claim is not null)
        {
            await idempotencyCoordinator.AbandonAsync(
                claim,
                instanceRevision,
                CancellationToken.None).ConfigureAwait(false);
        }
    }

    private void SetTerminal(
        InProcessTaskRecord record,
        TaskInstanceState state,
        ArtifactReference? outcomeRevision)
    {
        lock (record.Gate)
        {
            record.State = state;
            record.TerminalOutcomeRevision = outcomeRevision;
            record.TerminalAt = timeProvider.GetUtcNow();
        }

        telemetry.RecordTerminal(state);
    }

    private void PruneTerminal()
    {
        var threshold = timeProvider.GetUtcNow() - options.TerminalRetention;
        foreach (var pair in records)
        {
            lock (pair.Value.Gate)
            {
                if (pair.Value.TerminalAt is { } terminalAt &&
                    terminalAt <= threshold)
                {
                    records.TryRemove(pair);
                }
            }
        }
    }

    private static TaskExecutionOutcome<TResponse> Rejected<TResponse>(
        ArtifactReference requestRevision,
        ProgramKitDiagnostic diagnostic)
        where TResponse : notnull =>
        new(
            requestRevision,
            TaskExecutionOutcomeKind.Rejected,
            null,
            null,
            null,
            [diagnostic]);

    private TaskDispatchResult RejectedDispatch(
        ArtifactReference requestRevision,
        string id,
        string message)
    {
        telemetry.RecordRejected(id);
        return new TaskDispatchResult(
            requestRevision,
            TaskDispatchDisposition.Rejected,
            null,
            [
                new ProgramKitDiagnostic(
                    id,
                    ProgramKitDiagnosticSeverity.Error,
                    message,
                    "/request"),
            ]);
    }

    private static ProgramKitDiagnostic MissingSelectionDiagnostic() =>
        new(
            InProcessTaskDiagnosticIds.MissingSelection,
            ProgramKitDiagnosticSeverity.Error,
            "No exact task definition, activation binding, and typed handler selection exists.",
            "/request/definitionRevision");

    private static ProgramKitDiagnostic DuplicateDiagnostic() =>
        new(
            InProcessTaskDiagnosticIds.DuplicateRequest,
            ProgramKitDiagnosticSeverity.Error,
            "The exact task instance already exists.",
            "/request/revision");

    private static ProgramKitDiagnostic NotAcceptingDiagnostic() =>
        new(
            InProcessTaskDiagnosticIds.NotAccepting,
            ProgramKitDiagnosticSeverity.Error,
            "The in-process task runtime is not accepting work.",
            "/request");

    private void CancelRemainingQueuedWork()
    {
        while (queue.Reader.TryRead(out var work))
        {
            Interlocked.Decrement(ref queueDepth);
            queueSlots.Release();
            if (!records.TryGetValue(
                    Key(work.Instance.Revision),
                    out var record))
            {
                continue;
            }

            lock (record.Gate)
            {
                record.CancellationRequested = true;
            }

            SetTerminal(
                record,
                TaskInstanceState.Cancelled,
                TaskRuntimeIdentity.Create(
                    "task-outcome",
                    work.Instance.Revision,
                    "cancelled-on-shutdown"));
        }
    }

    private static bool IsTerminal(TaskInstanceState state) =>
        state is TaskInstanceState.Succeeded or
            TaskInstanceState.Failed or
            TaskInstanceState.Cancelled;

    private static string Key(ArtifactReference reference) =>
        string.Join(
            "|",
            reference.Identity.Value,
            reference.Version.Value,
            reference.Digest.Value);

    private static void ValidateOptions(InProcessTaskRuntimeOptions options)
    {
        if (options.QueueCapacity <= 0 ||
            options.MaximumConcurrency <= 0 ||
            options.TerminalRetention < TimeSpan.Zero ||
            options.IdempotencyRetention < TimeSpan.Zero ||
            options.SchedulePollingInterval <= TimeSpan.Zero ||
            options.MaximumScheduleOccurrencesPerEvaluation <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(options),
                "Runtime capacity and concurrency must be positive and retention must be non-negative.");
        }
    }

    /// <inheritdoc />
    public async ValueTask DisposeAsync()
    {
        await StopAsync(
            drain: false,
            CancellationToken.None).ConfigureAwait(false);
        queueSlots.Dispose();
        foreach (var record in records.Values)
        {
            record.ExecutionCancellation.Dispose();
        }
    }
}
