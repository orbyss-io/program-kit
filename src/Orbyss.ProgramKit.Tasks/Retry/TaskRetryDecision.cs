namespace Orbyss.ProgramKit.Tasks.Retry;

/// <summary>Explicit retry decision for one failed attempt.</summary>
public sealed record TaskRetryDecision(bool Retry, TimeSpan Delay)
{
    /// <summary>Gets the default terminal no-retry decision.</summary>
    public static TaskRetryDecision Stop { get; } = new(false, TimeSpan.Zero);
}
