namespace Orbyss.ProgramKit.Tasks.Core.Attempts;

/// <summary>One handler invocation; retries create additional attempts.</summary>
public sealed record TaskAttempt(
    ArtifactReference Revision,
    ArtifactReference InstanceRevision,
    ArtifactReference ActivationBindingRevision,
    int Number,
    TaskAttemptState State,
    DateTimeOffset StartedAt,
    DateTimeOffset? CompletedAt,
    ArtifactReference? FailureRevision);
