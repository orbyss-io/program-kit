namespace Orbyss.ProgramKit.Tasks.Core.Results;

/// <summary>Outcome of immediate task execution.</summary>
public enum TaskExecutionOutcomeKind
{
    /// <summary>The request was rejected before an instance existed.</summary>
    Rejected,
    /// <summary>Cancellation occurred before request acceptance.</summary>
    CancelledBeforeAcceptance,
    /// <summary>The accepted instance completed successfully.</summary>
    Succeeded,
    /// <summary>The accepted instance completed with a failure.</summary>
    Failed,
    /// <summary>The accepted instance completed through cancellation.</summary>
    Cancelled,
}
