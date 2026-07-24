namespace Orbyss.ProgramKit.Tasks.Retry;

/// <summary>Resolves an explicit retry decision without owning execution.</summary>
public interface ITaskRetryCoordinator
{
    /// <summary>Gets the decision for one failed attempt.</summary>
    ValueTask<TaskRetryDecision> DecideAsync(
        TaskRetryContext context,
        CancellationToken cancellationToken);
}
