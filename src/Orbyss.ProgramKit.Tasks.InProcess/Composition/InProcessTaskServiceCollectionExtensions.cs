using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Coordination;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Idempotency;
using Orbyss.ProgramKit.Tasks.InProcess.Coordination;
using Orbyss.ProgramKit.Tasks.InProcess.Execution;
using Orbyss.ProgramKit.Tasks.InProcess.Idempotency;
using Orbyss.ProgramKit.Tasks.InProcess.Observability;
using Orbyss.ProgramKit.Tasks.InProcess.Scheduling;

namespace Orbyss.ProgramKit.Tasks.InProcess.Composition;

/// <summary>Selects the bounded volatile task runtime implementation.</summary>
public static class InProcessTaskServiceCollectionExtensions
{
    /// <summary>
    /// Selects the in-process runtime with explicit capacity, concurrency, and
    /// retention limits.
    /// </summary>
    public static IServiceCollection UseInProcessTaskRuntime(
        this IServiceCollection services,
        InProcessTaskRuntimeOptions options)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(options);
        services.AddProgramKitTasks();
        services.TryAddSingleton(TimeProvider.System);
        services.TryAddSingleton(options);
        services.TryAddSingleton<
            ITaskIdempotencyCoordinator,
            InProcessTaskIdempotencyCoordinator>();
        services.TryAddSingleton<InProcessTaskRuntime>();
        services.TryAddSingleton<
            IInProcessTaskTelemetry,
            InProcessTaskTelemetry>();
        services.TryAddSingleton<IInProcessTaskRuntime>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntime>());
        services.TryAddSingleton<ITaskRunner>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntime>());
        services.TryAddSingleton<ITaskDispatcher>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntime>());
        services.TryAddSingleton<ITaskStatusReader>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntime>());
        services.TryAddSingleton<ITaskCancellationRequester>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntime>());
        services.TryAddSingleton<InProcessTaskScheduler>();
        services.TryAddSingleton<ITaskScheduler>(
            static provider =>
                provider.GetRequiredService<InProcessTaskScheduler>());
        services.TryAddSingleton<IInProcessTaskSchedulerControl>(
            static provider =>
                provider.GetRequiredService<InProcessTaskScheduler>());
        services.TryAddSingleton<InProcessTaskRuntimeControl>();
        services.TryAddSingleton<ITaskRuntimeControl>(
            static provider =>
                provider.GetRequiredService<InProcessTaskRuntimeControl>());
        return services;
    }
}
