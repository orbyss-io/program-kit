using System.Collections.Concurrent;
using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.InProcess.Composition;
using Orbyss.ProgramKit.Tasks.InProcess.Diagnostics;
using Orbyss.ProgramKit.Tasks.Policies;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.InProcess.Scheduling;

/// <summary>
/// Controlled-time volatile scheduler over explicitly registered pure
/// calculators and bounded activation policies.
/// </summary>
internal sealed class InProcessTaskScheduler :
    ITaskScheduler,
    IInProcessTaskSchedulerControl,
    IAsyncDisposable
{
    private readonly ITaskRegistryCoordinator registryCoordinator;
    private readonly ITaskDispatcher dispatcher;
    private readonly ITaskStatusReader statusReader;
    private readonly IServiceProvider services;
    private readonly TimeProvider timeProvider;
    private readonly InProcessTaskRuntimeOptions options;
    private readonly ConcurrentDictionary<string, InProcessScheduleState>
        states = new(StringComparer.Ordinal);
    private readonly Lock lifecycleGate = new();
    private CancellationTokenSource? loopCancellation;
    private Task? loop;

    public InProcessTaskScheduler(
        ITaskRegistryCoordinator registryCoordinator,
        ITaskDispatcher dispatcher,
        ITaskStatusReader statusReader,
        IServiceProvider services,
        TimeProvider timeProvider,
        InProcessTaskRuntimeOptions options)
    {
        this.registryCoordinator = registryCoordinator ??
            throw new ArgumentNullException(nameof(registryCoordinator));
        this.dispatcher = dispatcher ??
            throw new ArgumentNullException(nameof(dispatcher));
        this.statusReader = statusReader ??
            throw new ArgumentNullException(nameof(statusReader));
        this.services = services ??
            throw new ArgumentNullException(nameof(services));
        this.timeProvider = timeProvider ??
            throw new ArgumentNullException(nameof(timeProvider));
        this.options = options ??
            throw new ArgumentNullException(nameof(options));
    }

    /// <inheritdoc />
    public async ValueTask<TaskScheduleEvaluationResult> EvaluateAsync(
        TaskScheduleEvaluationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        if (request.MaximumOccurrences <= 0 ||
            request.CursorExclusive > request.EvaluationInstant)
        {
            throw new ArgumentException(
                "Schedule evaluation requires a positive bound and ordered instants.",
                nameof(request));
        }

        var state = states.GetOrAdd(
            Key(request.ScheduleRevision),
            _ => new InProcessScheduleState(request.CursorExclusive));
        await state.Gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            return await EvaluateCoreAsync(
                request,
                state,
                cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            state.Gate.Release();
        }
    }

    public async ValueTask StartAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var registry = registryCoordinator.GetCurrent();
        foreach (var schedule in registry.Schedules)
        {
            var calculator = registry.Calculators.Single(
                candidate =>
                    candidate.Profile ==
                        schedule.Schedule.OccurrenceCalculatorProfile &&
                    candidate.DescriptorType == schedule.DescriptorType);
            await calculator.ValidateDescriptorAsync(
                services,
                schedule.Descriptor,
                cancellationToken).ConfigureAwait(false);
        }

        lock (lifecycleGate)
        {
            if (loop is not null)
            {
                return;
            }

            var selectedCancellation = new CancellationTokenSource();
            loopCancellation = selectedCancellation;
            loop = RunLoopAsync(selectedCancellation.Token);
        }
    }

    public async ValueTask StopAsync(CancellationToken cancellationToken)
    {
        Task? selectedLoop;
        CancellationTokenSource? selectedCancellation;
        lock (lifecycleGate)
        {
            selectedLoop = loop;
            selectedCancellation = loopCancellation;
            selectedCancellation?.Cancel();
        }

        if (selectedLoop is not null)
        {
            await selectedLoop.WaitAsync(cancellationToken)
                .ConfigureAwait(false);
        }

        lock (lifecycleGate)
        {
            loop = null;
            loopCancellation = null;
            selectedCancellation?.Dispose();
        }
    }

    private async ValueTask<TaskScheduleEvaluationResult> EvaluateCoreAsync(
        TaskScheduleEvaluationRequest request,
        InProcessScheduleState state,
        CancellationToken cancellationToken)
    {
        var registry = registryCoordinator.GetCurrent();
        var schedule = registry.Schedules.SingleOrDefault(
            candidate => candidate.Schedule.Revision == request.ScheduleRevision)
            ?? throw new KeyNotFoundException(
                "The exact task schedule is not registered.");
        var binding = registry.Bindings.Single(
            candidate =>
                candidate.Binding.ScheduleRevision == request.ScheduleRevision);
        var calculator = registry.Calculators.Single(
            candidate =>
                candidate.Profile ==
                    schedule.Schedule.OccurrenceCalculatorProfile &&
                candidate.DescriptorType == schedule.DescriptorType);
        var requestFactory = registry.OccurrenceRequestFactories.Single(
            candidate =>
                candidate.ScheduleRevision == request.ScheduleRevision);
        var misfirePolicy = registry.MisfirePolicies.Single(
            candidate =>
                candidate.Revision ==
                    binding.Binding.MisfirePolicyRevision);
        var overlapPolicy = registry.OverlapPolicies.Single(
            candidate =>
                candidate.Revision ==
                    binding.Binding.OverlapPolicyRevision);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var previousStatus = await ReadPreviousStatusAsync(
            state,
            diagnostics,
            cancellationToken).ConfigureAwait(false);
        if (state.LatestInstanceRevision is not null &&
            previousStatus is null)
        {
            return EmptyResult(request, diagnostics);
        }

        var active = previousStatus is not null &&
            !previousStatus.IsTerminal;
        if (calculator.RequiresPreviousTerminalCompletion && active)
        {
            return EmptyResult(request, diagnostics);
        }

        var calculation = await calculator.CalculateAsync(
            services,
            schedule.Schedule,
            schedule.Descriptor,
            state.ReferenceInstant,
            request.CursorExclusive,
            request.EvaluationInstant,
            previousStatus?.TerminalCompletionInstant,
            request.MaximumOccurrences,
            cancellationToken).ConfigureAwait(false);
        var candidates = SelectMisfires(
            calculation.Occurrences,
            misfirePolicy,
            request.EvaluationInstant);
        var accepted = ImmutableArray.CreateBuilder<ArtifactReference>();
        if (state.PendingOccurrence is { } pending && !active)
        {
            var pendingAccepted = await DispatchAsync(
                pending,
                requestFactory,
                state,
                accepted,
                diagnostics,
                cancellationToken).ConfigureAwait(false);
            if (!pendingAccepted)
            {
                state.CursorExclusive = calculation.EvaluatedThrough;
                return Result(
                    request.ScheduleRevision,
                    calculation,
                    accepted,
                    diagnostics);
            }

            active = true;
            state.PendingOccurrence = null;
        }

        foreach (var occurrence in candidates)
        {
            if (active && overlapPolicy.Kind != TaskOverlapPolicyKind.Allow)
            {
                if (overlapPolicy.Kind == TaskOverlapPolicyKind.QueueOne &&
                    state.PendingOccurrence is null)
                {
                    state.PendingOccurrence = occurrence;
                }

                continue;
            }

            var occurrenceAccepted = await DispatchAsync(
                occurrence,
                requestFactory,
                state,
                accepted,
                diagnostics,
                cancellationToken).ConfigureAwait(false);
            active |= occurrenceAccepted;
        }

        state.CursorExclusive = calculation.EvaluatedThrough;
        return Result(
            request.ScheduleRevision,
            calculation,
            accepted,
            diagnostics);
    }

    private async ValueTask<TaskInstanceStatus?> ReadPreviousStatusAsync(
        InProcessScheduleState state,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        CancellationToken cancellationToken)
    {
        if (state.LatestInstanceRevision is not { } instanceRevision)
        {
            return null;
        }

        var status = await statusReader.ReadAsync(
            instanceRevision,
            cancellationToken).ConfigureAwait(false);
        if (status is null)
        {
            diagnostics.Add(
                new ProgramKitDiagnostic(
                    InProcessTaskDiagnosticIds.ScheduleStateUnavailable,
                    ProgramKitDiagnosticSeverity.Error,
                    "The prior volatile scheduled instance is no longer observable; evaluation fails closed.",
                    "/schedule/latestInstanceRevision"));
        }

        return status;
    }

    private async ValueTask<bool> DispatchAsync(
        TaskOccurrence occurrence,
        ITaskOccurrenceRequestFactoryRegistration requestFactory,
        InProcessScheduleState state,
        ImmutableArray<ArtifactReference>.Builder accepted,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        CancellationToken cancellationToken)
    {
        var result = await requestFactory.DispatchAsync(
            services,
            dispatcher,
            occurrence,
            cancellationToken).ConfigureAwait(false);
        if (result.Disposition == TaskDispatchDisposition.Accepted &&
            result.InstanceRevision is { } instanceRevision)
        {
            accepted.Add(instanceRevision);
            state.LatestInstanceRevision = instanceRevision;
            diagnostics.AddRange(result.Diagnostics);
            return true;
        }

        diagnostics.AddRange(result.Diagnostics);
        return false;
    }

    private async Task RunLoopAsync(CancellationToken cancellationToken)
    {
        try
        {
            while (true)
            {
                await Task.Delay(
                    options.SchedulePollingInterval,
                    timeProvider,
                    cancellationToken).ConfigureAwait(false);
                var now = timeProvider.GetUtcNow();
                var registry = registryCoordinator.GetCurrent();
                foreach (var schedule in registry.Schedules)
                {
                    var state = states.GetOrAdd(
                        Key(schedule.Schedule.Revision),
                        _ => new InProcessScheduleState(now));
                    var request = new TaskScheduleEvaluationRequest(
                        schedule.Schedule.Revision,
                        state.CursorExclusive,
                        now,
                        options.MaximumScheduleOccurrencesPerEvaluation);
                    await EvaluateAsync(
                        request,
                        cancellationToken).ConfigureAwait(false);
                }
            }
        }
        catch (OperationCanceledException) when (
            cancellationToken.IsCancellationRequested)
        {
        }
    }

    private static ImmutableArray<TaskOccurrence> SelectMisfires(
        ImmutableArray<TaskOccurrence> occurrences,
        TaskMisfirePolicyRegistration policy,
        DateTimeOffset evaluationInstant)
    {
        if (occurrences.IsDefaultOrEmpty)
        {
            return [];
        }

        return policy.Kind switch
        {
            TaskMisfirePolicyKind.Skip =>
                occurrences
                    .Where(item => item.ScheduledFor == evaluationInstant)
                    .ToImmutableArray(),
            TaskMisfirePolicyKind.FireOnceNow => [occurrences[^1]],
            TaskMisfirePolicyKind.CatchUpBounded =>
                occurrences
                    .Take(policy.MaximumCatchUp)
                    .ToImmutableArray(),
            _ => [],
        };
    }

    private static TaskScheduleEvaluationResult EmptyResult(
        TaskScheduleEvaluationRequest request,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(
            request.ScheduleRevision,
            request.CursorExclusive,
            [],
            [],
            diagnostics.ToImmutable());

    private static TaskScheduleEvaluationResult Result(
        ArtifactReference scheduleRevision,
        TaskOccurrenceCalculation calculation,
        ImmutableArray<ArtifactReference>.Builder accepted,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(
            scheduleRevision,
            calculation.EvaluatedThrough,
            calculation.Occurrences,
            accepted.ToImmutable(),
            diagnostics.ToImmutable());

    private static string Key(ArtifactReference reference) =>
        string.Join(
            "|",
            reference.Identity.Value,
            reference.Version.Value,
            reference.Digest.Value);

    public async ValueTask DisposeAsync()
    {
        await StopAsync(CancellationToken.None).ConfigureAwait(false);
        foreach (var state in states.Values)
        {
            state.Dispose();
        }
    }
}
