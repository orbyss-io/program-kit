using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Tasks.Coordination;

namespace Orbyss.ProgramKit.Tasks.Hosting.Health;

internal sealed class TaskQueueHealthCheck : IHealthCheck
{
    private readonly ITaskRuntimeControl runtime;

    public TaskQueueHealthCheck(ITaskRuntimeControl runtime)
    {
        this.runtime = runtime ??
            throw new ArgumentNullException(nameof(runtime));
    }

    public Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(
            runtime.QueueDepth < runtime.QueueCapacity
                ? HealthCheckResult.Healthy("Bounded task queue has capacity.")
                : HealthCheckResult.Degraded("Bounded task queue is full."));
    }
}
