namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Stages outputs privately and exposes them only through one atomic commit.</summary>
/// <remarks>
/// Atomic commit is a conformance obligation of each concrete workspace. An
/// implementation that cannot prove that commit failure exposes none of the
/// declared outputs must not implement this contract. The Workbench
/// coordinator cannot repair an implementation that publishes a partial commit.
/// This contract does not claim that unrelated filesystem effects or failed
/// private-staging cleanup can always be rolled back.
/// </remarks>
public interface IWorkbenchOutputTransaction
{
    /// <summary>Stages one complete output without publishing it.</summary>
    ValueTask StageAsync(
        GeneratedOutput output,
        CancellationToken cancellationToken);

    /// <summary>
    /// Atomically publishes every staged output, or fails while exposing none
    /// of the declared outputs.
    /// </summary>
    ValueTask CommitAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Discards all private staged state; failure means cleanup is unconfirmed,
    /// not that a declared output was successfully published.
    /// </summary>
    ValueTask RollbackAsync(CancellationToken cancellationToken);
}
