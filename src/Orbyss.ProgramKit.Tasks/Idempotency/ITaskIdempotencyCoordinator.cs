using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Idempotency;

/// <summary>Coordinates optional exact-definition/process/window idempotency.</summary>
public interface ITaskIdempotencyCoordinator
{
    /// <summary>Attempts to acquire one process-local claim.</summary>
    ValueTask<TaskIdempotencyResult> TryAcquireAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference proposedInstanceRevision,
        CancellationToken cancellationToken);

    /// <summary>Marks an acquired claim terminal for bounded retention.</summary>
    ValueTask CompleteAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference instanceRevision,
        CancellationToken cancellationToken);

    /// <summary>Releases a claim when acceptance did not complete.</summary>
    ValueTask AbandonAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference proposedInstanceRevision,
        CancellationToken cancellationToken);
}
