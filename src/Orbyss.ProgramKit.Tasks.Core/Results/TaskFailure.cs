namespace Orbyss.ProgramKit.Tasks.Core.Results;

/// <summary>
/// Typed failure reference without an unbounded exception or secret-bearing
/// message payload.
/// </summary>
public sealed record TaskFailure(
    ArtifactReference Revision,
    ArtifactReference InstanceRevision,
    ArtifactReference FailureContract,
    DateTimeOffset FailedAt,
    string Code,
    ImmutableArray<ArtifactReference> EvidenceReferences);
