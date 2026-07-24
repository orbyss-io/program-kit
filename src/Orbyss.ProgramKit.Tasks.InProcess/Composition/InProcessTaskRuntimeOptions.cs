using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.InProcess.Composition;

/// <summary>Explicit bounded volatile runtime limits.</summary>
public sealed record InProcessTaskRuntimeOptions
{
    /// <summary>
    /// Gets or initializes the exact runtime revision selected by the host.
    /// </summary>
    public required ArtifactReference RuntimeRevision { get; init; }

    /// <summary>Gets or initializes the maximum accepted queued work.</summary>
    public int QueueCapacity { get; init; } = 256;

    /// <summary>Gets or initializes maximum simultaneous handler attempts.</summary>
    public int MaximumConcurrency { get; init; } = 1;

    /// <summary>Gets or initializes terminal status retention.</summary>
    public TimeSpan TerminalRetention { get; init; } = TimeSpan.FromMinutes(15);

    /// <summary>Gets or initializes completed idempotency retention.</summary>
    public TimeSpan IdempotencyRetention { get; init; } =
        TimeSpan.FromMinutes(15);

    /// <summary>Gets or initializes the volatile schedule polling interval.</summary>
    public TimeSpan SchedulePollingInterval { get; init; } =
        TimeSpan.FromSeconds(1);

    /// <summary>
    /// Gets or initializes the finite per-schedule occurrence calculation bound.
    /// </summary>
    public int MaximumScheduleOccurrencesPerEvaluation { get; init; } = 32;
}
