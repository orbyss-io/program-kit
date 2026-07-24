namespace Orbyss.ProgramKit.Tasks.Idempotency;

/// <summary>Result of acquiring one idempotency claim.</summary>
public enum TaskIdempotencyDisposition
{
    /// <summary>The caller owns a new claim.</summary>
    Acquired,
    /// <summary>An equivalent request is already active.</summary>
    Active,
    /// <summary>An equivalent request already completed in the retention window.</summary>
    Completed,
}
