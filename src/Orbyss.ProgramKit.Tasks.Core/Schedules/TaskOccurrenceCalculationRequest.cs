namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>Explicit controlled-time input for a typed occurrence calculator.</summary>
/// <typeparam name="TDescriptor">The typed schedule descriptor model.</typeparam>
public sealed record TaskOccurrenceCalculationRequest<TDescriptor>(
    TaskScheduleDefinition Schedule,
    TDescriptor Descriptor,
    DateTimeOffset ReferenceInstant,
    DateTimeOffset CursorExclusive,
    DateTimeOffset EvaluationInstant,
    DateTimeOffset? PreviousTerminalCompletionInstant,
    int MaximumOccurrences)
    where TDescriptor : notnull;
