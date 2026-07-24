namespace Orbyss.ProgramKit.Tasks.Core.Instances;

/// <summary>One accepted logical execution pinned to exact contracts.</summary>
public sealed record TaskInstance(
    ArtifactReference Revision,
    ArtifactReference RequestRevision,
    ArtifactReference DefinitionRevision,
    ArtifactReference RequestContract,
    ArtifactReference ResponseContract,
    ArtifactReference FailureContract,
    DateTimeOffset AcceptedAt,
    string? IdempotencyKey,
    ArtifactReference? OccurrenceRevision);
