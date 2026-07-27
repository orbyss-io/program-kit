using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Runtime-neutral bridge for one typed occurrence calculator.</summary>
public interface ITaskOccurrenceCalculatorRegistration
{
    /// <summary>Gets the exact calculator profile.</summary>
    ArtifactReference Profile { get; }

    /// <summary>Gets the typed descriptor model type.</summary>
    Type DescriptorType { get; }

    /// <summary>Gets the calculator implementation type.</summary>
    Type CalculatorType { get; }

    /// <summary>
    /// Gets whether this calculator requires the previous bound instance's
    /// terminal-completion instant before it may calculate another occurrence.
    /// </summary>
    bool RequiresPreviousTerminalCompletion { get; }

    /// <summary>Validates the exact typed descriptor before activation.</summary>
    ValueTask ValidateDescriptorAsync(
        IServiceProvider services,
        object descriptor,
        CancellationToken cancellationToken);

    /// <summary>Calculates typed occurrences through an opaque bridge.</summary>
    ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        IServiceProvider services,
        TaskScheduleDefinition schedule,
        object descriptor,
        DateTimeOffset referenceInstant,
        DateTimeOffset cursorExclusive,
        DateTimeOffset evaluationInstant,
        DateTimeOffset? previousTerminalCompletionInstant,
        int maximumOccurrences,
        CancellationToken cancellationToken);
}
