using System.Collections.Concurrent;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Idempotency;
using Orbyss.ProgramKit.Tasks.InProcess.Composition;

namespace Orbyss.ProgramKit.Tasks.InProcess.Idempotency;

/// <summary>Bounded process-local exact-definition idempotency coordinator.</summary>
internal sealed class InProcessTaskIdempotencyCoordinator :
    ITaskIdempotencyCoordinator
{
    private readonly ConcurrentDictionary<string, InProcessIdempotencyEntry> entries =
        new(StringComparer.Ordinal);
    private readonly TimeProvider timeProvider;
    private readonly InProcessTaskRuntimeOptions options;

    public InProcessTaskIdempotencyCoordinator(
        TimeProvider timeProvider,
        InProcessTaskRuntimeOptions options)
    {
        this.timeProvider = timeProvider ??
            throw new ArgumentNullException(nameof(timeProvider));
        this.options = options ??
            throw new ArgumentNullException(nameof(options));
    }

    /// <inheritdoc />
    public ValueTask<TaskIdempotencyResult> TryAcquireAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference proposedInstanceRevision,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(claim);
        ArgumentNullException.ThrowIfNull(proposedInstanceRevision);
        cancellationToken.ThrowIfCancellationRequested();
        var now = timeProvider.GetUtcNow();
        var key = Key(claim);
        while (true)
        {
            if (entries.TryGetValue(key, out var existing))
            {
                if (existing.Completed && existing.ExpiresAt <= now)
                {
                    entries.TryRemove(
                        new KeyValuePair<string, InProcessIdempotencyEntry>(
                            key,
                            existing));
                    continue;
                }

                return ValueTask.FromResult(
                    new TaskIdempotencyResult(
                        existing.Completed
                            ? TaskIdempotencyDisposition.Completed
                            : TaskIdempotencyDisposition.Active,
                        existing.InstanceRevision));
            }

            var created = new InProcessIdempotencyEntry(
                proposedInstanceRevision,
                false,
                DateTimeOffset.MaxValue);
            if (entries.TryAdd(key, created))
            {
                return ValueTask.FromResult(
                    new TaskIdempotencyResult(
                        TaskIdempotencyDisposition.Acquired,
                        null));
            }
        }
    }

    /// <inheritdoc />
    public ValueTask CompleteAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference instanceRevision,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(claim);
        ArgumentNullException.ThrowIfNull(instanceRevision);
        cancellationToken.ThrowIfCancellationRequested();
        entries[Key(claim)] = new InProcessIdempotencyEntry(
            instanceRevision,
            true,
            timeProvider.GetUtcNow() + options.IdempotencyRetention);
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask AbandonAsync(
        TaskIdempotencyClaim claim,
        ArtifactReference proposedInstanceRevision,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(claim);
        ArgumentNullException.ThrowIfNull(proposedInstanceRevision);
        cancellationToken.ThrowIfCancellationRequested();
        var key = Key(claim);
        if (entries.TryGetValue(key, out var existing) &&
            !existing.Completed &&
            existing.InstanceRevision == proposedInstanceRevision)
        {
            entries.TryRemove(
                new KeyValuePair<string, InProcessIdempotencyEntry>(
                    key,
                    existing));
        }

        return ValueTask.CompletedTask;
    }

    private static string Key(TaskIdempotencyClaim claim) =>
        string.Join(
            "|",
            claim.PolicyRevision.Identity.Value,
            claim.PolicyRevision.Version.Value,
            claim.DefinitionRevision.Identity.Value,
            claim.DefinitionRevision.Version.Value,
            claim.Key);
}
