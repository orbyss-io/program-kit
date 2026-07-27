using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Tasks.Coordination;

namespace Orbyss.ProgramKit.Tasks.Hosting.Health;

internal sealed class TaskAcceptanceHealthCheck : IHealthCheck
{
    private readonly ITaskRuntimeControl runtime;

    public TaskAcceptanceHealthCheck(ITaskRuntimeControl runtime)
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
            runtime.IsAccepting
                ? HealthCheckResult.Healthy("Task runtime accepts work.")
                : HealthCheckResult.Unhealthy("Task runtime does not accept work."));
    }
}
