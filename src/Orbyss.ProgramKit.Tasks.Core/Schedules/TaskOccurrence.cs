namespace Orbyss.ProgramKit.Tasks.Core.Schedules;

/// <summary>One calculated schedule firing that may propose a normal request.</summary>
public sealed record TaskOccurrence(
    ArtifactReference Revision,
    ArtifactReference ScheduleRevision,
    ArtifactReference DefinitionRevision,
    ArtifactReference DescriptorRevision,
    ArtifactReference OccurrenceCalculatorProfile,
    long Sequence,
    DateTimeOffset ScheduledFor,
    DateTimeOffset EvaluatedAt);
