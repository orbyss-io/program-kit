using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Finite explicit input used to construct one frozen task registry.</summary>
public sealed class TaskRegistrationSet
{
    /// <summary>Initializes one explicit finite registration input.</summary>
    public TaskRegistrationSet(
        ImmutableArray<TaskDefinitionRegistration> definitions,
        ImmutableArray<ITaskHandlerRegistration> handlers,
        ImmutableArray<TaskActivationBindingRegistration> bindings,
        ImmutableArray<TaskFeatureRegistration> features,
        ImmutableArray<TaskMiddlewareRegistration> middleware,
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
        Middleware = middleware;
        Schedules = schedules;
        Calculators = calculators;
        OccurrenceRequestFactories = occurrenceRequestFactories;
        MisfirePolicies = misfirePolicies;
        OverlapPolicies = overlapPolicies;
    }

    /// <summary>Gets task definitions.</summary>
    public ImmutableArray<TaskDefinitionRegistration> Definitions { get; }

    /// <summary>Gets typed handler registrations.</summary>
    public ImmutableArray<ITaskHandlerRegistration> Handlers { get; }

    /// <summary>Gets activation bindings.</summary>
    public ImmutableArray<TaskActivationBindingRegistration> Bindings { get; }

    /// <summary>Gets feature revisions.</summary>
    public ImmutableArray<TaskFeatureRegistration> Features { get; }

    /// <summary>Gets middleware registrations.</summary>
    public ImmutableArray<TaskMiddlewareRegistration> Middleware { get; }

    /// <summary>Gets typed schedule registrations.</summary>
    public ImmutableArray<ITaskScheduleRegistration> Schedules { get; }

    /// <summary>Gets typed occurrence-calculator registrations.</summary>
    public ImmutableArray<ITaskOccurrenceCalculatorRegistration> Calculators
    {
        get;
    }

    /// <summary>Gets typed occurrence request factory registrations.</summary>
    public ImmutableArray<ITaskOccurrenceRequestFactoryRegistration>
        OccurrenceRequestFactories
    { get; }

    /// <summary>Gets exact bounded misfire-policy registrations.</summary>
    public ImmutableArray<TaskMisfirePolicyRegistration> MisfirePolicies
    {
        get;
    }

    /// <summary>Gets exact overlap-policy registrations.</summary>
    public ImmutableArray<TaskOverlapPolicyRegistration> OverlapPolicies
    {
        get;
    }
}
