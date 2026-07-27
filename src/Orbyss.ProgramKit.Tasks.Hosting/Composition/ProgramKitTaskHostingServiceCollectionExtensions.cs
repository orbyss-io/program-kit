using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Orbyss.ProgramKit.Tasks.Hosting.Health;
using Orbyss.ProgramKit.Tasks.Hosting.Hosting;

namespace Orbyss.ProgramKit.Tasks.Hosting.Composition;

/// <summary>Adds Generic Host lifecycle and named health registrations.</summary>
public static class ProgramKitTaskHostingServiceCollectionExtensions
{
    /// <summary>
    /// Adds lifecycle integration and named checks without mapping any endpoint.
    /// </summary>
    public static IServiceCollection AddProgramKitTaskHosting(
        this IServiceCollection services,
        TaskHostingOptions options)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(options);
        services.TryAddSingleton(options);
        services.TryAddEnumerable(
            ServiceDescriptor.Singleton<
                Microsoft.Extensions.Hosting.IHostedService,
                ProgramKitTaskHostedService>());
        services.AddHealthChecks()
            .AddCheck<TaskRuntimeStartedHealthCheck>(
                "program-kit-tasks-runtime-started",
                tags: ["startup", "ready"])
            .AddCheck<TaskAcceptanceHealthCheck>(
                "program-kit-tasks-accepting",
                tags: ["ready"])
            .AddCheck<TaskQueueHealthCheck>(
                "program-kit-tasks-queue",
                tags: ["ready"])
            .AddCheck<TaskRegistryHealthCheck>(
                "program-kit-tasks-registry",
                tags: ["startup", "ready"])
            .AddCheck<TaskScheduleHealthCheck>(
                "program-kit-tasks-schedules",
                tags: ["startup", "ready"]);
        return services;
    }
}
