namespace Orbyss.ProgramKit.Tasks.Core.Diagnostics;

/// <summary>Stable diagnostics owned by Tasks.Core contracts.</summary>
public static class TasksCoreDiagnosticIds
{
    /// <summary>A task definition violates its contract.</summary>
    public const string InvalidTaskDefinition = "PKTSK001";
    /// <summary>A task request violates its contract.</summary>
    public const string InvalidTaskRequest = "PKTSK002";
    /// <summary>A task instance violates its contract.</summary>
    public const string InvalidTaskInstance = "PKTSK003";
    /// <summary>A task attempt violates its contract.</summary>
    public const string InvalidTaskAttempt = "PKTSK004";
    /// <summary>A task activation binding violates its contract.</summary>
    public const string InvalidTaskActivationBinding = "PKTSK005";
    /// <summary>A task schedule definition violates its contract.</summary>
    public const string InvalidTaskScheduleDefinition = "PKTSK006";
    /// <summary>A task occurrence violates its contract.</summary>
    public const string InvalidTaskOccurrence = "PKTSK007";
    /// <summary>A task lifecycle view violates its contract.</summary>
    public const string InvalidTaskLifecycleView = "PKTSK008";
}
