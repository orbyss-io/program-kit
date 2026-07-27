using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Tasks.Composition;

namespace Orbyss.ProgramKit.Tasks.Hosting.Health;

internal sealed class TaskRegistryHealthCheck : IHealthCheck
{
    private readonly ITaskRegistryCoordinator registryCoordinator;

    public TaskRegistryHealthCheck(
        ITaskRegistryCoordinator registryCoordinator)
    {
        this.registryCoordinator = registryCoordinator ??
            throw new ArgumentNullException(nameof(registryCoordinator));
    }

    public Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(
            registryCoordinator.IsFrozen
                ? HealthCheckResult.Healthy("Task registry is frozen and valid.")
                : HealthCheckResult.Unhealthy("Task registry is not frozen."));
    }
}
