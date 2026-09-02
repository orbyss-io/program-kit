using ProgramKit.Host.Health;

namespace ProgramKit.Host.Tests;

/// <summary>Fails once and then succeeds to model dependency recovery.</summary>
internal sealed class ScriptedProbe : IPostgreSqlReadinessProbe
{
    /// <summary>The number of completed probe attempts.</summary>
    private int _attempt;

    /// <inheritdoc />
    public Task ProbeAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (Interlocked.Increment(ref _attempt) == 1)
            throw new TimeoutException("scripted redacted dependency failure");
        return Task.CompletedTask;
    }
}
