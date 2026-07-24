using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Tasks.Coordination;

namespace Orbyss.ProgramKit.Tasks.Hosting.Health;

internal sealed class TaskRuntimeStartedHealthCheck : IHealthCheck
{
    private readonly ITaskRuntimeControl runtime;

    public TaskRuntimeStartedHealthCheck(ITaskRuntimeControl runtime)
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
            runtime.IsStarted
                ? HealthCheckResult.Healthy("Task runtime started.")
                : HealthCheckResult.Unhealthy("Task runtime is not started."));
    }
}
