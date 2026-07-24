using Orbyss.ProgramKit.Tasks.Composition;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>
/// Mutable-before-freeze registration catalog used during feature composition.
/// </summary>
public interface ITaskRegistrationCatalog
{
    /// <summary>Gets whether this catalog has frozen successfully.</summary>
    bool IsFrozen { get; }

    /// <summary>Adds one exact definition registration.</summary>
    void Add(TaskDefinitionRegistration registration);

    /// <summary>Adds one exact typed handler registration.</summary>
    void Add(ITaskHandlerRegistration registration);

    /// <summary>Adds one exact activation binding registration.</summary>
    void Add(TaskActivationBindingRegistration registration);

    /// <summary>Adds one exact owning feature registration.</summary>
    void Add(TaskFeatureRegistration registration);

    /// <summary>Adds one exact middleware registration.</summary>
    void Add(TaskMiddlewareRegistration registration);

    /// <summary>Adds one exact typed schedule registration.</summary>
    void Add(ITaskScheduleRegistration registration);

    /// <summary>Adds one exact typed occurrence calculator registration.</summary>
    void Add(ITaskOccurrenceCalculatorRegistration registration);

    /// <summary>Adds one typed occurrence request factory registration.</summary>
    void Add(ITaskOccurrenceRequestFactoryRegistration registration);

    /// <summary>Adds one exact bounded misfire policy registration.</summary>
    void Add(TaskMisfirePolicyRegistration registration);

    /// <summary>Adds one exact overlap policy registration.</summary>
    void Add(TaskOverlapPolicyRegistration registration);

    /// <summary>Imports one explicit finite registration set before freeze.</summary>
    void Import(TaskRegistrationSet registrations);

    /// <summary>Exports an immutable snapshot for generated composition.</summary>
    TaskRegistrationSet Export();

    /// <summary>Validates and atomically freezes this catalog.</summary>
    ITaskRegistry Freeze(ITaskRegistryFactory factory);
}
