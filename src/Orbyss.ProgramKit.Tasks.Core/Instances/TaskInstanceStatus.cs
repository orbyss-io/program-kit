namespace Orbyss.ProgramKit.Tasks.Core.Instances;

/// <summary>Immutable status observation for one accepted task instance.</summary>
public sealed record TaskInstanceStatus(
    ArtifactReference InstanceRevision,
    TaskInstanceState State,
    int AttemptCount,
    bool CancellationRequested,
    DateTimeOffset ObservedAt,
    ArtifactReference? LatestAttemptRevision,
    ArtifactReference? TerminalOutcomeRevision,
    DateTimeOffset? TerminalCompletionInstant)
{
    /// <summary>Gets whether the observed lifecycle state is terminal.</summary>
    public bool IsTerminal =>
        State is TaskInstanceState.Succeeded or
            TaskInstanceState.Failed or
            TaskInstanceState.Cancelled;
}
