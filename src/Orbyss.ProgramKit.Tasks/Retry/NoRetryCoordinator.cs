namespace Orbyss.ProgramKit.Tasks.Retry;

/// <summary>Default retry coordinator that never retries.</summary>
internal sealed class NoRetryCoordinator : ITaskRetryCoordinator
{
    /// <inheritdoc />
    public ValueTask<TaskRetryDecision> DecideAsync(
        TaskRetryContext context,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(TaskRetryDecision.Stop);
    }
}
