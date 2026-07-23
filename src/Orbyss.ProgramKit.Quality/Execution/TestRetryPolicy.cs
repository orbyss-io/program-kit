namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Defines bounded retry behavior for a test execution.</summary>
public sealed record TestRetryPolicy(
    int MaximumAttempts,
    TimeSpan Delay);
