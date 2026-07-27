namespace Orbyss.ProgramKit.Tasks.Core.Definitions;

/// <summary>
/// Stable requested-work meaning and the exact contracts and policies governing
/// its use.
/// </summary>
public sealed record TaskDefinition(
    ArtifactReference Revision,
    ProgramKitIdentifier Owner,
    ArtifactReference RequestContract,
    ArtifactReference ResponseContract,
    ArtifactReference FailureContract,
    ArtifactReference AuthorityPolicy,
    ArtifactReference CancellationPolicy,
    ArtifactReference IdempotencyPolicy,
    ArtifactReference RetryPolicy,
    ArtifactReference ObservabilityPolicy,
    ArtifactReference ResourcePolicy);
