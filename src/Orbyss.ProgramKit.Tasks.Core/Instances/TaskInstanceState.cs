namespace Orbyss.ProgramKit.Tasks.Core.Instances;

/// <summary>Authoritative lifecycle state of an accepted task instance.</summary>
public enum TaskInstanceState
{
    /// <summary>The request was accepted.</summary>
    Accepted,
    /// <summary>The instance is waiting for activation.</summary>
    Waiting,
    /// <summary>An attempt is running.</summary>
    Running,
    /// <summary>The instance is waiting before another attempt.</summary>
    RetryWait,
    /// <summary>The instance completed successfully.</summary>
    Succeeded,
    /// <summary>The instance completed with a failure.</summary>
    Failed,
    /// <summary>The instance completed through cancellation.</summary>
    Cancelled,
}
