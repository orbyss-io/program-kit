namespace Orbyss.ProgramKit.Tasks.Core.Attempts;

/// <summary>Lifecycle state of one handler invocation.</summary>
public enum TaskAttemptState
{
    /// <summary>The handler invocation is running.</summary>
    Running,
    /// <summary>The handler invocation completed successfully.</summary>
    Succeeded,
    /// <summary>The handler invocation completed with a failure.</summary>
    Failed,
    /// <summary>The handler invocation observed cancellation.</summary>
    Cancelled,
}
