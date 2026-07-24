namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>
/// Scheduler evaluation result; only accepted occurrences acquire instances.
/// </summary>
public sealed record TaskScheduleEvaluationResult(
    ArtifactReference ScheduleRevision,
    DateTimeOffset EvaluatedThrough,
    ImmutableArray<TaskOccurrence> Occurrences,
    ImmutableArray<ArtifactReference> AcceptedInstanceRevisions,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics);
