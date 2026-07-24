using System.Collections.Immutable;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

internal sealed class TaskRegistry : ITaskRegistry
{
    internal TaskRegistry(
        ImmutableArray<TaskDefinitionRegistration> definitions,
        ImmutableArray<ITaskHandlerRegistration> handlers,
        ImmutableArray<TaskActivationBindingRegistration> bindings,
        ImmutableArray<TaskFeatureRegistration> features,
        ImmutableArray<TaskMiddlewareRegistration> dispatchMiddleware,
        ImmutableArray<TaskMiddlewareRegistration> executionMiddleware,
        ImmutableArray<ITaskScheduleRegistration> schedules,
        ImmutableArray<ITaskOccurrenceCalculatorRegistration> calculators,
        ImmutableArray<ITaskOccurrenceRequestFactoryRegistration>
            occurrenceRequestFactories,
        ImmutableArray<TaskMisfirePolicyRegistration> misfirePolicies,
        ImmutableArray<TaskOverlapPolicyRegistration> overlapPolicies)
    {
        Definitions = definitions;
        Handlers = handlers;
        Bindings = bindings;
        Features = features;
        DispatchMiddleware = dispatchMiddleware;
        ExecutionMiddleware = executionMiddleware;
        Schedules = schedules;
        Calculators = calculators;
        OccurrenceRequestFactories = occurrenceRequestFactories;
        MisfirePolicies = misfirePolicies;
        OverlapPolicies = overlapPolicies;
    }

    public ImmutableArray<TaskDefinitionRegistration> Definitions { get; }

    public ImmutableArray<ITaskHandlerRegistration> Handlers { get; }

    public ImmutableArray<TaskActivationBindingRegistration> Bindings { get; }

    public ImmutableArray<TaskFeatureRegistration> Features { get; }

    public ImmutableArray<TaskMiddlewareRegistration> DispatchMiddleware { get; }

    public ImmutableArray<TaskMiddlewareRegistration> ExecutionMiddleware { get; }

    public ImmutableArray<ITaskScheduleRegistration> Schedules { get; }

    public ImmutableArray<ITaskOccurrenceCalculatorRegistration> Calculators { get; }

    public ImmutableArray<ITaskOccurrenceRequestFactoryRegistration>
        OccurrenceRequestFactories
    { get; }

    public ImmutableArray<TaskMisfirePolicyRegistration> MisfirePolicies
    {
        get;
    }

    public ImmutableArray<TaskOverlapPolicyRegistration> OverlapPolicies
    {
        get;
    }
}
