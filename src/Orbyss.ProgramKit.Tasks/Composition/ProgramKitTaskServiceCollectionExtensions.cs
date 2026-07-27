using System.Collections.Immutable;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Core.Bindings;
using Orbyss.ProgramKit.Tasks.Core.Definitions;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Core.Validation;
using Orbyss.ProgramKit.Tasks.Middleware;
using Orbyss.ProgramKit.Tasks.Observability;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Retry;
using Orbyss.ProgramKit.Modularity.Contributions;

namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Explicit shell-scoped task registration extensions.</summary>
public static class ProgramKitTaskServiceCollectionExtensions
{
    /// <summary>Adds the task composition services and returns their catalog.</summary>
    public static ITaskRegistrationCatalog AddProgramKitTasks(
        this IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        var existing = FindCatalog(services);
        if (existing is not null)
        {
            return existing;
        }

        ITaskRegistrationCatalog catalog =
            new TaskRegistrationCatalog([], [], []);
        services.AddSingleton<ITaskRegistrationCatalog>(catalog);
        services.TryAddSingleton<
            IProgramKitSemanticValidator<ArtifactReference>,
            ArtifactReferenceValidator>();
        services.TryAddSingleton<ITaskContractValidator, TaskContractValidator>();
        services.TryAddSingleton<ITaskRegistryFactory, TaskRegistryFactory>();
        services.TryAddSingleton<ITaskMiddlewarePipeline, TaskMiddlewarePipeline>();
        services.TryAddSingleton<ITaskRetryCoordinator, NoRetryCoordinator>();
        services.TryAddSingleton<ITaskLifecycleObserver>(
            static provider =>
                new DomainContributionTaskLifecycleObserver(
                    provider.GetService<IDomainContributionPublisher>()));
        services.TryAddSingleton<
            ITaskRegistryCoordinator,
            TaskRegistryCoordinator>();
        services.TryAddSingleton(
            static provider =>
                provider.GetRequiredService<ITaskRegistryCoordinator>()
                    .GetCurrent());
        return catalog;
    }

    /// <summary>Registers one exact task definition.</summary>
    public static IServiceCollection AddTaskDefinition(
        this IServiceCollection services,
        TaskDefinition definition)
    {
        Catalog(services).Add(new TaskDefinitionRegistration(definition));
        return services;
    }

    /// <summary>Registers one exact feature available to task bindings.</summary>
    public static IServiceCollection AddTaskFeature(
        this IServiceCollection services,
        ArtifactReference featureRevision)
    {
        Catalog(services).Add(new TaskFeatureRegistration(featureRevision));
        return services;
    }

    /// <summary>Registers one typed consumer-owned task handler.</summary>
    public static IServiceCollection AddTaskHandler<
        TRequest,
        TResponse,
        THandler>(
        this IServiceCollection services,
        ArtifactReference handlerRevision,
        SemanticVersionRange supportedDefinitionVersions)
        where TRequest : notnull
        where TResponse : notnull
        where THandler : class, ITaskHandler<TRequest, TResponse>
    {
        ArgumentNullException.ThrowIfNull(services);
        services.TryAddTransient<THandler>();
        Catalog(services).Add(
            new TaskHandlerRegistration<TRequest, TResponse, THandler>(
                handlerRevision,
                supportedDefinitionVersions));
        return services;
    }

    /// <summary>Registers one exact task activation binding.</summary>
    public static IServiceCollection AddTaskActivationBinding(
        this IServiceCollection services,
        TaskActivationBinding binding)
    {
        Catalog(services).Add(
            new TaskActivationBindingRegistration(binding));
        return services;
    }

    /// <summary>Registers ordered dispatch or execution middleware.</summary>
    public static IServiceCollection AddTaskMiddleware<TMiddleware>(
        this IServiceCollection services,
        ArtifactReference revision,
        TaskMiddlewarePhase phase,
        int priority = 0,
        IEnumerable<ProgramKitIdentifier>? before = null,
        IEnumerable<ProgramKitIdentifier>? after = null)
        where TMiddleware : class
    {
        ArgumentNullException.ThrowIfNull(services);
        services.TryAddTransient<TMiddleware>();
        Catalog(services).Add(
            new TaskMiddlewareRegistration(
                revision,
                phase,
                typeof(TMiddleware),
                priority,
                before?.ToImmutableArray() ?? [],
                after?.ToImmutableArray() ?? []));
        return services;
    }

    /// <summary>Registers one exact typed schedule and descriptor artifact.</summary>
    public static IServiceCollection AddTaskSchedule<TDescriptor>(
        this IServiceCollection services,
        TaskScheduleDefinition schedule,
        TDescriptor descriptor)
        where TDescriptor : notnull
    {
        Catalog(services).Add(
            new TaskScheduleRegistration<TDescriptor>(
                schedule,
                descriptor));
        return services;
    }

    /// <summary>Registers one exact typed occurrence calculator profile.</summary>
    public static IServiceCollection AddTaskOccurrenceCalculator<
        TDescriptor,
        TCalculator>(
        this IServiceCollection services,
        ArtifactReference profile)
        where TDescriptor : notnull
        where TCalculator : class, ITaskOccurrenceCalculator<TDescriptor>
    {
        ArgumentNullException.ThrowIfNull(services);
        services.TryAddTransient<TCalculator>();
        Catalog(services).Add(
            new TaskOccurrenceCalculatorRegistration<
                TDescriptor,
                TCalculator>(profile));
        return services;
    }

    /// <summary>Registers one exact bounded misfire policy.</summary>
    public static IServiceCollection AddTaskMisfirePolicy(
        this IServiceCollection services,
        TaskMisfirePolicyRegistration policy)
    {
        Catalog(services).Add(policy);
        return services;
    }

    /// <summary>Registers one exact overlap policy.</summary>
    public static IServiceCollection AddTaskOverlapPolicy(
        this IServiceCollection services,
        TaskOverlapPolicyRegistration policy)
    {
        Catalog(services).Add(policy);
        return services;
    }

    /// <summary>Registers a typed occurrence-to-normal-request factory.</summary>
    public static IServiceCollection AddTaskOccurrenceRequestFactory<
        TRequest,
        TFactory>(
        this IServiceCollection services,
        ArtifactReference scheduleRevision)
        where TRequest : notnull
        where TFactory : class,
            Scheduling.ITaskOccurrenceRequestFactory<TRequest>
    {
        services.AddTransient<TFactory>();
        Catalog(services).Add(
            new TaskOccurrenceRequestFactoryRegistration<TRequest, TFactory>(
                scheduleRevision));
        return services;
    }

    private static ITaskRegistrationCatalog Catalog(
        IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        return FindCatalog(services) ??
            services.AddProgramKitTasks();
    }

    private static ITaskRegistrationCatalog? FindCatalog(
        IServiceCollection services)
    {
        ITaskRegistrationCatalog? catalog = null;
        foreach (var descriptor in services.Where(static descriptor =>
                     descriptor.ServiceType ==
                     typeof(ITaskRegistrationCatalog)))
        {
            if (catalog is not null ||
                descriptor.Lifetime != ServiceLifetime.Singleton ||
                descriptor.ImplementationInstance is not
                    ITaskRegistrationCatalog candidate)
            {
                throw new InvalidOperationException(
                    "The service collection contains a partial, duplicate, or foreign Program Kit task registration.");
            }

            catalog = candidate;
        }

        return catalog;
    }
}
