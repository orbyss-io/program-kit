namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>Explicit request for the selected scheduler to evaluate one schedule.</summary>
public sealed record TaskScheduleEvaluationRequest(
    ArtifactReference ScheduleRevision,
    DateTimeOffset CursorExclusive,
    DateTimeOffset EvaluationInstant,
    int MaximumOccurrences);
