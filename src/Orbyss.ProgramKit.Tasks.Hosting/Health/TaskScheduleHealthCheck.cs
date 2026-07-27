using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Tasks.Composition;

namespace Orbyss.ProgramKit.Tasks.Hosting.Health;

internal sealed class TaskScheduleHealthCheck : IHealthCheck
{
    private readonly ITaskRegistryCoordinator registryCoordinator;

    public TaskScheduleHealthCheck(
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
        if (!registryCoordinator.IsFrozen)
        {
            return Task.FromResult(
                HealthCheckResult.Unhealthy(
                    "Schedule validity is unavailable before registry freeze."));
        }

        var registry = registryCoordinator.GetCurrent();
        var valid = registry.Schedules.All(
            schedule => registry.Calculators.Any(
                calculator =>
                    calculator.Profile ==
                        schedule.Schedule.OccurrenceCalculatorProfile &&
                    calculator.DescriptorType == schedule.DescriptorType));
        return Task.FromResult(
            valid
                ? HealthCheckResult.Healthy("Task schedules are valid.")
                : HealthCheckResult.Unhealthy(
                    "A task schedule has no exact typed occurrence calculator."));
    }
}
