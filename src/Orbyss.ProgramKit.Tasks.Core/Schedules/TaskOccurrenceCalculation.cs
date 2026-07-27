namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>Ordered pure occurrence-calculation result.</summary>
public sealed record TaskOccurrenceCalculation(
    ArtifactReference ScheduleRevision,
    DateTimeOffset EvaluatedThrough,
    ImmutableArray<TaskOccurrence> Occurrences);
