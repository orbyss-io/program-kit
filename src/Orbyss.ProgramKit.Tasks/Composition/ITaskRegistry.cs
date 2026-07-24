using System.Collections.Immutable;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Frozen validated task registry selected by one host.</summary>
public interface ITaskRegistry
{
    /// <summary>Gets exact definitions in stable order.</summary>
    ImmutableArray<TaskDefinitionRegistration> Definitions { get; }

    /// <summary>Gets exact handler bridges in stable order.</summary>
    ImmutableArray<ITaskHandlerRegistration> Handlers { get; }

    /// <summary>Gets exact activation bindings in stable order.</summary>
    ImmutableArray<TaskActivationBindingRegistration> Bindings { get; }

    /// <summary>Gets available exact feature revisions in stable order.</summary>
    ImmutableArray<TaskFeatureRegistration> Features { get; }

    /// <summary>Gets dispatch middleware in execution order.</summary>
    ImmutableArray<TaskMiddlewareRegistration> DispatchMiddleware { get; }

    /// <summary>Gets execution middleware in execution order.</summary>
    ImmutableArray<TaskMiddlewareRegistration> ExecutionMiddleware { get; }

    /// <summary>Gets exact typed schedules in stable order.</summary>
    ImmutableArray<ITaskScheduleRegistration> Schedules { get; }

    /// <summary>Gets exact typed calculators in stable order.</summary>
    ImmutableArray<ITaskOccurrenceCalculatorRegistration> Calculators { get; }

    /// <summary>Gets typed occurrence request factories in stable order.</summary>
    ImmutableArray<ITaskOccurrenceRequestFactoryRegistration>
        OccurrenceRequestFactories
    { get; }

    /// <summary>Gets exact bounded misfire policies in stable order.</summary>
    ImmutableArray<TaskMisfirePolicyRegistration> MisfirePolicies { get; }

    /// <summary>Gets exact overlap policies in stable order.</summary>
    ImmutableArray<TaskOverlapPolicyRegistration> OverlapPolicies { get; }
}
